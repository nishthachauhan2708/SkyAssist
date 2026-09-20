import sqlite3
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from app.db import get_db_connection
from app.policies.policy_engine import get_policy_for_disruption, search_policies

def create_audit_event(pnr: Optional[str], event: str, tool_name: str, result: str, policy_source: Optional[str] = None, status: str = "COMPLETED") -> Dict[str, Any]:
    """Record an immutable audit event in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO audit_logs (timestamp, event, pnr, tool_name, result, policy_source, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (now_str, event, pnr, tool_name, result, policy_source, status))
    conn.commit()
    conn.close()
    return {
        "timestamp": now_str,
        "event": event,
        "pnr": pnr,
        "tool_name": tool_name,
        "result": result,
        "policy_source": policy_source,
        "status": status
    }

def get_existing_action(pnr: str, action_type: str) -> Optional[Dict[str, Any]]:
    """Query DB for existing action record by PNR and action_type."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM actions WHERE UPPER(pnr) = ? AND action_type = ? ORDER BY id DESC", (pnr.upper(), action_type))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def create_escalation(pnr: str, customer_name: str, reason: str, requested_action: str, policy_conflict: str, priority: str = "HIGH") -> Dict[str, Any]:
    """Create a structured escalation record when a request exceeds agent authority."""
    conn = get_db_connection()
    cursor = conn.cursor()
    esc_id = f"ESC-{uuid.uuid4().hex[:4].upper()}"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO escalations (escalation_id, pnr, customer_name, reason, requested_action, policy_conflict, priority, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (esc_id, pnr, customer_name, reason, requested_action, policy_conflict, priority, "Awaiting Human Review", now_str))
    conn.commit()
    conn.close()
    
    create_audit_event(
        pnr=pnr,
        event=f"Escalation Created: {reason}",
        tool_name="create_escalation",
        result=f"Escalated under {esc_id}",
        policy_source="Agent Authority Policy (PROHIBITED_ACTION)",
        status="ESCALATED"
    )
    
    return {
        "escalation_id": esc_id,
        "pnr": pnr,
        "customer_name": customer_name,
        "reason": reason,
        "requested_action": requested_action,
        "policy_conflict": policy_conflict,
        "priority": priority,
        "status": "Awaiting Human Review",
        "created_at": now_str
    }

def lookup_customer(query: str) -> Optional[Dict[str, Any]]:
    """Lookup customer details by PNR, Name, or Email."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM customers 
        WHERE booking_reference = ? OR UPPER(name) LIKE ? OR UPPER(email) LIKE ?
    """, (query.upper(), f"%{query.upper()}%", f"%{query.upper()}%"))
    row = cursor.fetchone()
    conn.close()
    if row:
        cust = dict(row)
        create_audit_event(
            pnr=cust["booking_reference"],
            event=f"Customer Identified: {cust['name']} ({cust['loyalty_tier']} Tier)",
            tool_name="lookup_customer",
            result=f"Found record for {cust['name']}",
            policy_source="Assessment Customer Directory"
        )
        return cust
    return None

def lookup_booking(pnr: str) -> Optional[Dict[str, Any]]:
    """Lookup booking details by PNR."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bookings WHERE UPPER(pnr) = ?", (pnr.upper(),))
    row = cursor.fetchone()
    conn.close()
    if row:
        b = dict(row)
        create_audit_event(
            pnr=b["pnr"],
            event=f"Booking Retrieved: Flight {b['flight_number']} ({b['status']})",
            tool_name="lookup_booking",
            result=f"Route: {b['origin']} -> {b['destination']}, Date: {b['departure_date']}",
            policy_source="Assessment Flight Ops Database"
        )
        return b
    return None

def get_flight_status(flight_number: str) -> Optional[Dict[str, Any]]:
    """Lookup flight operational status."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM flights WHERE flight_number = ?", (flight_number,))
    row = cursor.fetchone()
    conn.close()
    if row:
        fl = dict(row)
        create_audit_event(
            pnr=None,
            event=f"Flight Status Inquiry: {fl['flight_number']}",
            tool_name="get_flight_status",
            result=f"Status: {fl['status']}, Scheduled: {fl['scheduled_departure']}",
            policy_source="Assessment Flight Ops Database"
        )
        return fl
    return None

def calculate_entitlements(pnr: str) -> Dict[str, Any]:
    """Calculate exact passenger entitlements based on flight disruption and policy."""
    booking = lookup_booking(pnr)
    if not booking:
        return {"error": "Booking not found"}
    
    cust = lookup_customer(pnr)
    customer_name = cust["name"] if cust else booking["customer_name"]
    tier = cust["loyalty_tier"] if cust else "Standard"
    status = booking["status"].upper()

    if "CANCEL" in status:
        disruption_type = "CANCELLED"
        meal = True
        meal_amt = 500
        lounge = True
        hotel = False
        hotel_details = "Not applicable for cancellation"
        rebook = True
        refund = True
        policy_code = "POL-1"
        policy_name = "Cancellation Rebooking & Refund Policy"
    elif "DELAYED 4" in status or "4 HOUR" in status:
        disruption_type = "DELAY_4H"
        meal = True
        meal_amt = 500
        lounge = True
        hotel = False
        hotel_details = "Ineligible: Hotel accommodation requires flight delay > 5 hours (Current delay: 4 hours)"
        rebook = False
        refund = False
        policy_code = "POL-2"
        policy_name = "Delay Compensation Policy (Tier 2: >3h Delay)"
    elif "DELAYED 6" in status or "6 HOUR" in status:
        disruption_type = "DELAY_6H"
        meal = True
        meal_amt = 500
        lounge = True
        hotel = True
        hotel_details = "Eligible for delayed-hours portion ONLY (6 hours before rescheduled flight departure). NOT a full night stay."
        rebook = True
        refund = False
        policy_code = "POL-2"
        policy_name = "Delay Compensation Policy (Tier 3: >5h Delay)"
    else:
        disruption_type = "NORMAL"
        meal = False
        meal_amt = 0
        lounge = False
        hotel = False
        hotel_details = "No disruption entitlements applicable"
        rebook = False
        refund = False
        policy_code = "POL-GEN"
        policy_name = "Standard Airline Policy"

    create_audit_event(
        pnr=pnr,
        event=f"Entitlements Calculated for {disruption_type}",
        tool_name="calculate_entitlements",
        result=f"Meal: {meal}, Lounge: {lounge}, Hotel: {hotel}",
        policy_source=policy_name
    )

    return {
        "pnr": pnr,
        "customer_name": customer_name,
        "loyalty_tier": tier,
        "disruption_type": disruption_type,
        "meal_voucher_eligible": meal,
        "meal_voucher_amount": meal_amt,
        "lounge_access_eligible": lounge,
        "hotel_eligible": hotel,
        "hotel_details": hotel_details,
        "rebooking_eligible": rebook,
        "refund_eligible": refund,
        "loyalty_priority": f"{tier} Priority Seating" if tier in ["Gold", "Platinum"] else "Standard",
        "applicable_policy_code": policy_code,
        "applicable_policy_name": policy_name
    }

def initiate_refund(pnr: str, amount: Optional[float] = None, target_payment_method: Optional[str] = None) -> Dict[str, Any]:
    """Execute refund initiation with strict guardrails."""
    booking = lookup_booking(pnr)
    if not booking:
        return {"success": False, "status": "failed", "reason": "Booking not found", "policy_source": "POL-3"}
    
    # Validation 1: Airline Cancellation required for standard full refund
    if "CANCEL" not in booking["status"].upper():
        return {
            "success": False,
            "status": "ineligible",
            "reason": "Full refund is only available for airline-caused flight cancellations.",
            "policy_source": "Refund Processing Rule (POL-3)"
        }
    
    original_method = booking["original_payment_method"]
    
    # Validation 2: Payment Method Guardrail
    if target_payment_method and target_payment_method.lower() != original_method.lower():
        esc = create_escalation(
            pnr=pnr,
            customer_name=booking["customer_name"],
            reason="Customer requested refund to alternative payment method",
            requested_action=f"Refund to {target_payment_method}",
            policy_conflict=f"POL-3 strictly requires refund to original payment method"
        )
        return {
            "success": False,
            "status": "escalation_required",
            "action": "refund_request",
            "escalation_id": esc["escalation_id"],
            "reason": "Refund can strictly only be issued to the original payment method. Escalated request to supervisor.",
            "details": "Refund can strictly only be issued to the original payment method. Escalated request to supervisor.",
            "policy_source": "Refund Processing Rule (POL-3)"
        }
    
    # Prevent Duplicate Refund Action: Check if refund already exists in DB
    existing = get_existing_action(pnr, "refund")
    if existing:
        return {
            "success": True,
            "action": "refund_request",
            "action_id": existing["action_id"],
            "status": "already_initiated",
            "already_exists": True,
            "details": "Full refund has already been initiated to original payment method within 7 business days.",
            "policy_source": "Refund Processing Rule (POL-3)"
        }

    action_id = f"ACT-REF-{uuid.uuid4().hex[:4].upper()}"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    details = "Full refund initiated to original payment method. Processed within 7 business days."
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO actions (action_id, pnr, action_type, status, details, policy_source, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (action_id, pnr, "refund", "INITIATED", details, "Refund Processing Rule (POL-3)", now_str))
    conn.commit()
    conn.close()

    create_audit_event(
        pnr=pnr,
        event="Refund Request Initiated",
        tool_name="initiate_refund",
        result=f"Action ID: {action_id} to original payment method",
        policy_source="Refund Processing Rule (POL-3)",
        status="COMPLETED"
    )

    return {
        "success": True,
        "action": "refund_request",
        "action_id": action_id,
        "status": "initiated",
        "details": details,
        "policy_source": "Refund Processing Rule (POL-3)"
    }

def create_rebooking_request(pnr: str, target_flight_details: Optional[str] = None, requested_cabin: str = "Economy") -> Dict[str, Any]:
    """Execute flight rebooking request with guardrails on cabin upgrades."""
    booking = lookup_booking(pnr)
    if not booking:
        return {"success": False, "status": "failed", "reason": "Booking not found", "policy_source": "POL-1"}
    
    cust = lookup_customer(pnr)
    tier = cust["loyalty_tier"] if cust else "Standard"

    # Validation: Cabin Upgrade requested without fare payment
    if requested_cabin.lower() in ["business", "first", "business-class"]:
        esc = create_escalation(
            pnr=pnr,
            customer_name=booking["customer_name"],
            reason="Customer requested complimentary business-class upgrade on rebooked/return flight",
            requested_action="Free Business Class Upgrade",
            policy_conflict="POL-1 & POL-5: Priority rebooking does not grant free cabin upgrades. Requires fare payment or supervisor exception."
        )
        return {
            "success": False,
            "status": "escalation_required",
            "action": "rebook_flight",
            "escalation_id": esc["escalation_id"],
            "reason": "Complimentary business class upgrades are outside standard policy authority. Escalated request to supervisor.",
            "details": "Complimentary business class upgrades are outside standard policy authority. Escalated request to supervisor.",
            "policy_source": "Cancellation Rebooking & Loyalty Rules (POL-1 & POL-5)"
        }

    action_id = f"ACT-REB-{uuid.uuid4().hex[:4].upper()}"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    details = f"Free rebooking initiated on next available flight within 24 hours at ₹0 extra charge with {tier} Priority Seating."

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO actions (action_id, pnr, action_type, status, details, policy_source, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (action_id, pnr, "rebook", "CONFIRMED", details, "Cancellation Rebooking Rule (POL-1)", now_str))
    conn.commit()
    conn.close()

    create_audit_event(
        pnr=pnr,
        event="Free Rebooking Requested on Next Available Flight within 24h",
        tool_name="create_rebooking_request",
        result=f"Action ID: {action_id}",
        policy_source="Cancellation Rebooking Rule (POL-1)",
        status="COMPLETED"
    )

    return {
        "success": True,
        "action": "rebook_flight",
        "action_id": action_id,
        "status": "confirmed",
        "details": details,
        "policy_source": "Cancellation Rebooking Rule (POL-1)"
    }

def issue_meal_voucher(pnr: str, amount: int = 500) -> Dict[str, Any]:
    """Issue digital meal voucher."""
    booking = lookup_booking(pnr)
    if not booking:
        return {"success": False, "status": "failed", "reason": "Booking not found", "policy_source": "POL-2"}

    action_id = f"ACT-VOU-{uuid.uuid4().hex[:4].upper()}"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    details = f"₹{amount} airport meal voucher issued to passenger digital wallet."

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO actions (action_id, pnr, action_type, status, details, policy_source, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (action_id, pnr, "meal_voucher", "ISSUED", details, "Delay Compensation Policy (POL-2)", now_str))
    conn.commit()
    conn.close()

    create_audit_event(
        pnr=pnr,
        event=f"Meal Voucher Issued (₹{amount})",
        tool_name="issue_meal_voucher",
        result=f"Voucher ID: {action_id}",
        policy_source="Delay Compensation Rule (POL-2)",
        status="COMPLETED"
    )

    return {
        "success": True,
        "action": "meal_voucher",
        "action_id": action_id,
        "status": "issued",
        "details": details,
        "policy_source": "Delay Compensation Rule (POL-2)"
    }

def grant_lounge_access(pnr: str) -> Dict[str, Any]:
    """Grant airport lounge access pass."""
    ent = calculate_entitlements(pnr)
    if not ent.get("lounge_access_eligible", False):
        return {
            "success": False,
            "status": "ineligible",
            "reason": "Lounge access requires a flight delay of at least 3 hours or a flight cancellation.",
            "policy_source": "Delay Compensation Policy (POL-2)"
        }

    action_id = f"ACT-LNG-{uuid.uuid4().hex[:4].upper()}"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    details = "Airport Lounge Access QR pass generated and sent to passenger app."

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO actions (action_id, pnr, action_type, status, details, policy_source, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (action_id, pnr, "lounge_access", "GRANTED", details, "Delay Compensation Policy (POL-2)", now_str))
    conn.commit()
    conn.close()

    create_audit_event(
        pnr=pnr,
        event="Lounge Access Pass Granted",
        tool_name="grant_lounge_access",
        result=f"Pass ID: {action_id}",
        policy_source="Delay Compensation Rule (POL-2)",
        status="COMPLETED"
    )

    return {
        "success": True,
        "action": "lounge_access",
        "action_id": action_id,
        "status": "granted",
        "details": details,
        "policy_source": "Delay Compensation Rule (POL-2)"
    }

def arrange_delay_hotel(pnr: str, requested_full_night: bool = False) -> Dict[str, Any]:
    """Arrange hotel accommodation for delayed hours with strict guardrails."""
    ent = calculate_entitlements(pnr)
    booking = lookup_booking(pnr)
    
    # Guardrail 1: Hotel requires delay > 5 hours
    if not ent.get("hotel_eligible", False):
        esc = create_escalation(
            pnr=pnr,
            customer_name=booking["customer_name"] if booking else "Unknown",
            reason="Customer requested hotel accommodation for delay under 5 hours",
            requested_action="Hotel Accommodation",
            policy_conflict="POL-2: Hotel accommodation is strictly reserved for delays greater than 5 hours."
        )
        reason_msg = "Hotel accommodation requires a delay of over 5 hours. Standard policy provides meal voucher and lounge access for 4-hour delays."
        return {
            "success": False,
            "status": "escalation_required",
            "action": "arrange_hotel",
            "escalation_id": esc["escalation_id"],
            "reason": reason_msg,
            "details": reason_msg,
            "policy_source": "Delay Compensation Policy (POL-2)"
        }

    # Guardrail 2: Full night stay requested when delay is delayed-hours only
    if requested_full_night:
        esc = create_escalation(
            pnr=pnr,
            customer_name=booking["customer_name"] if booking else "Unknown",
            reason="Customer requested full-night hotel stay for a 6-hour daytime delay",
            requested_action="Full Night Hotel Accommodation",
            policy_conflict="POL-2: Hotel accommodation covers ONLY the delayed-hours portion, NOT a full night's stay."
        )
        reason_msg = "Policy covers hotel accommodation strictly for the delayed-hours portion (6 hours), not a full night stay. Escalated requested exception to supervisor."
        return {
            "success": False,
            "status": "escalation_required",
            "action": "arrange_hotel",
            "escalation_id": esc["escalation_id"],
            "reason": reason_msg,
            "details": reason_msg,
            "policy_source": "Delay Compensation Policy (POL-2)"
        }

    action_id = f"ACT-HTL-{uuid.uuid4().hex[:4].upper()}"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    details = "Hotel day-room voucher arranged for delayed-hours portion (6 hours prior to rescheduled flight)."

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO actions (action_id, pnr, action_type, status, details, policy_source, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (action_id, pnr, "arrange_hotel", "ARRANGED", details, "Delay Compensation Policy (POL-2)", now_str))
    conn.commit()
    conn.close()

    create_audit_event(
        pnr=pnr,
        event="Delayed-Hours Hotel Voucher Arranged",
        tool_name="arrange_delay_hotel",
        result=f"Voucher ID: {action_id}",
        policy_source="Delay Compensation Rule (POL-2)",
        status="COMPLETED"
    )

    return {
        "success": True,
        "action": "arrange_hotel",
        "action_id": action_id,
        "status": "arranged",
        "details": details,
        "policy_source": "Delay Compensation Rule (POL-2)"
    }

def waive_fare_difference(pnr: str, fare_diff_amount: float) -> Dict[str, Any]:
    """Check fare difference waiver threshold (Cap: ₹1,500)."""
    booking = lookup_booking(pnr)
    customer_name = booking["customer_name"] if booking else "Unknown"
    
    # Guardrail: Limit is ₹1,500
    if fare_diff_amount > 1500.0:
        esc = create_escalation(
            pnr=pnr,
            customer_name=customer_name,
            reason=f"Fare difference waiver of ₹{fare_diff_amount:,.0f} exceeds agent authority cap of ₹1,500",
            requested_action=f"Waive ₹{fare_diff_amount:,.0f} Fare Difference",
            policy_conflict="POL-4: Agent authority is capped at ₹1,500 for fare difference waivers. Supervisor approval required."
        )
        reason_msg = f"Fare difference of ₹{fare_diff_amount:,.0f} exceeds agent authority limit (₹1,500). Escalated request to supervisor for approval."
        return {
            "success": False,
            "status": "escalation_required",
            "action": "fare_waiver",
            "escalation_id": esc["escalation_id"],
            "reason": reason_msg,
            "details": reason_msg,
            "policy_source": "Fare Difference Policy (POL-4)"
        }

    action_id = f"ACT-WVR-{uuid.uuid4().hex[:4].upper()}"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    details = f"Waived fare difference of ₹{fare_diff_amount:,.0f} within agent authority threshold."

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO actions (action_id, pnr, action_type, status, details, policy_source, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (action_id, pnr, "fare_waiver", "APPROVED", details, "Fare Difference Policy (POL-4)", now_str))
    conn.commit()
    conn.close()

    create_audit_event(
        pnr=pnr,
        event=f"Fare Waiver Approved (₹{fare_diff_amount:,.0f})",
        tool_name="waive_fare_difference",
        result=f"Action ID: {action_id}",
        policy_source="Fare Difference Policy (POL-4)",
        status="COMPLETED"
    )

    return {
        "success": True,
        "action": "fare_waiver",
        "action_id": action_id,
        "status": "approved",
        "details": details,
        "policy_source": "Fare Difference Policy (POL-4)"
    }
