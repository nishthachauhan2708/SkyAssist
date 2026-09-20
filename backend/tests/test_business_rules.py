import pytest
import os
import sys

# Ensure backend directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db import init_db, get_db_connection
from app.tools.agent_tools import (
    calculate_entitlements, initiate_refund, arrange_delay_hotel,
    waive_fare_difference, create_rebooking_request, lookup_customer
)
from app.agents.orchestrator import process_chat_message

@pytest.fixture(autouse=True)
def setup_database():
    """Re-initialize DB before each test."""
    init_db()

def test_1_cancelled_flight_rebooking_or_refund():
    """TEST 1: Cancelled flight -> free rebooking or full refund choice."""
    ent = calculate_entitlements("SK4821X")
    assert ent["disruption_type"] == "CANCELLED"
    assert ent["rebooking_eligible"] is True
    assert ent["refund_eligible"] is True

    # Test refund execution
    res = initiate_refund("SK4821X")
    assert res["success"] is True
    assert res["action"] == "refund_request"
    assert res["status"] == "initiated"

def test_2_four_hour_delay_compensation():
    """TEST 2: 4-hour delay -> meal + lounge, NO hotel."""
    ent = calculate_entitlements("TR1190B")
    assert ent["disruption_type"] == "DELAY_4H"
    assert ent["meal_voucher_eligible"] is True
    assert ent["lounge_access_eligible"] is True
    assert ent["hotel_eligible"] is False

    # Attempt arranging hotel for 4h delay -> MUST escalate
    hotel_res = arrange_delay_hotel("TR1190B")
    assert hotel_res["success"] is False
    assert hotel_res["status"] == "escalation_required"
    assert hotel_res["escalation_id"] is not None

def test_3_six_hour_delay_compensation():
    """TEST 3: 6-hour delay -> meal + lounge + delayed-hours hotel."""
    ent = calculate_entitlements("WL7742")
    assert ent["disruption_type"] == "DELAY_6H"
    assert ent["meal_voucher_eligible"] is True
    assert ent["lounge_access_eligible"] is True
    assert ent["hotel_eligible"] is True
    assert "delayed-hours portion ONLY" in ent["hotel_details"]

    # Attempt arranging standard delayed-hours hotel -> SUCCESS
    hotel_res = arrange_delay_hotel("WL7742", requested_full_night=False)
    assert hotel_res["success"] is True

    # Attempt requesting FULL NIGHT hotel -> MUST ESCALATE
    full_night_res = arrange_delay_hotel("WL7742", requested_full_night=True)
    assert full_night_res["success"] is False
    assert full_night_res["status"] == "escalation_required"

def test_4_fare_waiver_within_threshold():
    """TEST 4: ₹1,500 fare waiver -> within authority limit (approved)."""
    res = waive_fare_difference("WL7742", 1500.0)
    assert res["success"] is True
    assert res["status"] == "approved"

def test_5_fare_waiver_exceeds_threshold():
    """TEST 5: ₹2,000 fare waiver -> exceeds ₹1,500 cap, MUST escalate."""
    res = waive_fare_difference("WL7742", 2000.0)
    assert res["success"] is False
    assert res["status"] == "escalation_required"
    assert res["escalation_id"] is not None
    assert "exceeds agent authority" in res["reason"]

def test_6_loyalty_perks_no_extra_compensation():
    """TEST 6: Gold/Platinum -> priority rebooking but no extra monetary compensation."""
    priya_ent = calculate_entitlements("SK4821X") # Gold
    meher_ent = calculate_entitlements("WL7742") # Platinum

    assert "Gold Priority Seating" in priya_ent["loyalty_priority"]
    assert "Platinum Priority Seating" in meher_ent["loyalty_priority"]

    # Gold requesting business class upgrade -> ESCALATED
    upg_res = create_rebooking_request("SK4821X", requested_cabin="Business")
    assert upg_res["success"] is False
    assert upg_res["status"] == "escalation_required"

def test_7_refund_original_payment_method_only():
    """TEST 7: Refund -> original payment method only (escalates on different method)."""
    # Refund to original -> SUCCESS
    res_orig = initiate_refund("SK4821X", target_payment_method="original payment method")
    assert res_orig["success"] is True

    # Refund to different payment method -> ESCALATE
    res_diff = initiate_refund("SK4821X", target_payment_method="Crypto Wallet 0x123")
    assert res_diff["success"] is False
    assert res_diff["status"] == "escalation_required"

def test_8_legal_threat_immediate_escalation():
    """TEST 8: Threat of legal action -> immediate escalation."""
    res = process_chat_message("I am furious! If you don't refund me right now I am calling my lawyer to sue!", pnr="SK4821X")
    assert res["escalated"] is True
    assert res["escalation_id"] is not None
    assert "supervisor" in res["reply"]

def test_9_unknown_customer_clarification():
    """TEST 9: Unknown customer -> request PNR clarification."""
    res = process_chat_message("Hi, my flight was delayed.")
    assert res["pnr"] is None
    assert "booking reference" in res["reply"]

def test_10_unknown_policy_information():
    """TEST 10: Unknown policy/information -> clear statement of unavailability."""
    # When asking about invalid PNR, agent explicitly states record is not found
    res = process_chat_message("Where is my flight?", pnr="INVALID999")
    assert "No booking record was found" in res["reply"]

def test_11_rebooking_no_fictional_flight():
    """TEST 11: Rebooking refers strictly to next available flight within 24h without fictional flight numbers."""
    res = create_rebooking_request("SK4821X")
    assert res["success"] is True
    assert "next available flight within 24 hours" in res["details"]
    assert "SK-206" not in res["details"]

def test_12_informational_query_no_unintended_actions():
    """TEST 12: General entitlement inquiry explains eligibility without executing voucher actions."""
    res = process_chat_message("What meal vouchers and lounge access am I entitled to for a 4 hour delay?", pnr="TR1190B")
    assert res["pnr"] == "TR1190B"
    assert len(res["actions_taken"]) == 0
    assert "qualifies for" in res["reply"]

def test_13_no_duplicate_refund_action():
    """TEST 13: Repeating a refund request when already initiated does NOT create duplicate action records."""
    res1 = process_chat_message("I want a full refund for my cancelled flight.", pnr="SK4821X")
    assert len(res1["actions_taken"]) == 1

    res2 = process_chat_message("Can I get a full cash refund for my cancelled flight?", pnr="SK4821X")
    assert len(res2["actions_taken"]) == 0
    assert "already been initiated" in res2["reply"]
