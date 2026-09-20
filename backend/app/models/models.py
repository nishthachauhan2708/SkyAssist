from pydantic import BaseModel, Field
from typing import Optional, List, Any

class CustomerModel(BaseModel):
    id: int
    name: str
    loyalty_tier: str
    booking_reference: str
    email: str
    phone: str
    flight_count_12m: int
    prior_complaint_count: int
    last_complaint_type: Optional[str] = None
    last_resolution: Optional[str] = None

class BookingModel(BaseModel):
    pnr: str
    customer_name: str
    flight_number: str
    origin: str
    destination: str
    departure_date: str
    scheduled_departure: str
    status: str
    reason: Optional[str] = None
    new_departure: Optional[str] = None
    return_route: Optional[str] = None
    return_date: Optional[str] = None
    return_departure: Optional[str] = None
    return_status: Optional[str] = None
    original_payment_method: str

class FlightModel(BaseModel):
    flight_number: str
    origin: str
    destination: str
    date: str
    scheduled_departure: str
    status: str
    new_departure: Optional[str] = None
    reason: Optional[str] = None

class PolicyModel(BaseModel):
    code: str
    name: str
    category: str
    summary: str
    content: str

class EntitlementModel(BaseModel):
    pnr: str
    customer_name: str
    disruption_type: str # CANCELLED, DELAY_4H, DELAY_6H, etc.
    meal_voucher_eligible: bool
    meal_voucher_amount: int
    lounge_access_eligible: bool
    hotel_eligible: bool
    hotel_details: str
    rebooking_eligible: bool
    refund_eligible: bool
    loyalty_priority: str
    applicable_policy_code: str
    applicable_policy_name: str

class ActionRequest(BaseModel):
    pnr: str
    action_type: str # refund, rebook, meal_voucher, lounge_access, hotel, fare_waiver
    requested_amount: Optional[float] = 0.0
    details: Optional[str] = ""

class ActionResult(BaseModel):
    success: bool
    action: str
    action_id: Optional[str] = None
    status: str
    policy_source: str
    details: Optional[str] = ""
    escalation_id: Optional[str] = None
    reason: Optional[str] = None

class EscalationRecord(BaseModel):
    escalation_id: str
    pnr: str
    customer_name: str
    reason: str
    requested_action: str
    policy_conflict: str
    priority: str
    status: str
    created_at: str

class AuditEvent(BaseModel):
    id: Optional[int] = None
    timestamp: str
    event: str
    pnr: Optional[str] = None
    tool_name: str
    result: str
    policy_source: Optional[str] = None
    status: str

class ChatRequest(BaseModel):
    pnr: Optional[str] = None
    customer_name: Optional[str] = None
    message: str

class SourcePolicyDisplay(BaseModel):
    policy_code: str
    policy_name: str
    reason: str
    decision: str
    summary: str

class ChatResponse(BaseModel):
    reply: str
    pnr: Optional[str] = None
    customer: Optional[CustomerModel] = None
    booking: Optional[BookingModel] = None
    entitlements: Optional[EntitlementModel] = None
    actions_taken: List[ActionResult] = []
    source_policy: Optional[SourcePolicyDisplay] = None
    escalated: bool = False
    escalation_id: Optional[str] = None
