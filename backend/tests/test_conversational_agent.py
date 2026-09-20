import pytest
import os
import sys

# Ensure backend directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db import init_db
from app.agents.orchestrator import process_chat_message
from app.tools.agent_tools import initiate_refund, arrange_delay_hotel, waive_fare_difference

@pytest.fixture(autouse=True)
def setup_database():
    """Re-initialize DB before each test."""
    init_db()

def test_1_hi_greeting():
    res = process_chat_message("hi", pnr="SK4821X")
    assert "Priya" in res["reply"]
    assert "help" in res["reply"].lower()
    assert "SK-204" not in res["reply"]
    assert "CANCELLED" not in res["reply"]

def test_2_hello_greeting():
    res = process_chat_message("hello", pnr="TR1190B")
    assert "Arvind" in res["reply"]
    assert "help" in res["reply"].lower()
    assert "SK-118" not in res["reply"]
    assert "delayed" not in res["reply"].lower()

def test_3_how_are_you_small_talk():
    res = process_chat_message("how are you?", pnr="WL7742")
    assert "doing well" in res["reply"].lower()
    assert "SK-305" not in res["reply"]

def test_4_thanks_polite_response():
    res = process_chat_message("thanks!", pnr="SK4821X")
    assert "welcome" in res["reply"].lower()

def test_5_capability_question():
    res = process_chat_message("what can you do?", pnr="SK4821X")
    assert "flight status" in res["reply"].lower() or "refunds" in res["reply"].lower()
    assert "SK-204" not in res["reply"]

def test_6_customer_pnr_query():
    res = process_chat_message("what is my pnr?", pnr="SK4821X")
    assert "SK4821X" in res["reply"]
    assert "SK-204" not in res["reply"]
    assert "CANCELLED" not in res["reply"]

def test_7_check_my_flight_query():
    res_priya = process_chat_message("Check my flight", pnr="SK4821X")
    assert "SK-204" in res_priya["reply"]
    assert "cancelled" in res_priya["reply"].lower()
    assert len(res_priya["actions_taken"]) == 0

    res_arvind = process_chat_message("Check my flight", pnr="TR1190B")
    assert "SK-118" in res_arvind["reply"]
    assert "delayed" in res_arvind["reply"].lower()
    assert len(res_arvind["actions_taken"]) == 0

    res_meher = process_chat_message("Check my flight", pnr="WL7742")
    assert "SK-305" in res_meher["reply"]
    assert "delayed" in res_meher["reply"].lower()
    assert len(res_meher["actions_taken"]) == 0

def test_8_refund_options_query_does_not_execute_refund():
    res = process_chat_message("Refund options", pnr="SK4821X")
    assert "full-refund option" in res["reply"].lower() or "refund" in res["reply"].lower()
    assert len(res["actions_taken"]) == 0  # CRITICAL: Information query MUST NOT execute refund action

def test_9_rebooking_options_query_does_not_execute_rebooking():
    res = process_chat_message("Rebooking options", pnr="SK4821X")
    assert "free rebooking" in res["reply"].lower() or "rebooking" in res["reply"].lower()
    assert len(res["actions_taken"]) == 0  # CRITICAL: Information query MUST NOT execute rebooking action

def test_10_fare_difference_policy_query():
    res = process_chat_message("What is the fare difference policy?", pnr="SK4821X")
    assert "1,500" in res["reply"] or "supervisor" in res["reply"]
    assert len(res["actions_taken"]) == 0

def test_11_general_cancellation_policy_question():
    res = process_chat_message("What happens if a flight is cancelled?", pnr="SK4821X")
    assert "24 hours" in res["reply"]
    assert "7 business days" in res["reply"]

def test_12_general_refund_policy_question():
    res = process_chat_message("How long do refunds take?", pnr="SK4821X")
    assert "7 business days" in res["reply"]
    assert "original payment method" in res["reply"]

def test_13_general_hotel_policy_question():
    res = process_chat_message("When is hotel accommodation provided for delays?", pnr="SK4821X")
    assert "5 hours" in res["reply"] or "delayed hours" in res["reply"]

def test_14_unsupported_terminal_question():
    res = process_chat_message("What terminal is my flight from?", pnr="SK4821X")
    assert "terminal" in res["reply"].lower()
    assert "don't have" in res["reply"].lower() or "not available" in res["reply"].lower()

def test_15_contextual_follow_up():
    res = process_chat_message("how long does that take?", pnr="SK4821X")
    assert "7 business days" in res["reply"]
    assert "SK-204" not in res["reply"]

def test_16_casual_message_must_not_trigger_flight_policy_dump():
    res = process_chat_message("okay", pnr="SK4821X")
    assert "POL-1" not in res["reply"]
    assert "SK-204" not in res["reply"]

def test_17_no_unsolicited_disruption_dump_on_small_talk():
    res = process_chat_message("how are you doing today?", pnr="TR1190B")
    assert "TR1190B" not in res["reply"]
    assert "SK-118" not in res["reply"]
    assert "4-hour" not in res["reply"]

def test_18_no_duplicate_refund_action():
    res1 = process_chat_message("I want a full refund for my cancelled flight.", pnr="SK4821X")
    assert len(res1["actions_taken"]) == 1
    res2 = process_chat_message("Can I get a full cash refund for my cancelled flight?", pnr="SK4821X")
    assert len(res2["actions_taken"]) == 0
    assert "already been initiated" in res2["reply"]

def test_19_explicit_rebooking_action():
    res = process_chat_message("rebook me", pnr="SK4821X")
    assert len(res["actions_taken"]) == 1
    assert "rebook" in res["actions_taken"][0]["action"]

def test_20_existing_delay_rules_pass():
    res = process_chat_message("I want hotel accommodation for my 4 hour delay", pnr="TR1190B")
    assert res["escalated"] is True
    assert "escalation_id" in res

def test_21_existing_escalation_rules_pass():
    res = process_chat_message("Waive 2000 from fare difference", pnr="WL7742")
    assert res["escalated"] is True
    assert "1,500" in res["reply"] or "exceeds" in res["reply"].lower() or "authority" in res["reply"].lower()

def test_22_check_delay_query_all_customers():
    # Priya (SK4821X - Cancelled)
    res_p = process_chat_message("Check delay", pnr="SK4821X")
    assert "cancelled" in res_p["reply"].lower()
    assert "SK-204" in res_p["reply"]
    assert len(res_p["actions_taken"]) == 0

    # Arvind (TR1190B - 4h delay)
    res_a = process_chat_message("Check delay", pnr="TR1190B")
    assert "4 hours" in res_a["reply"]
    assert "11:10" in res_a["reply"]
    assert len(res_a["actions_taken"]) == 0

    # Meher (WL7742 - 6h delay)
    res_m = process_chat_message("Check delay", pnr="WL7742")
    assert "6 hours" in res_m["reply"]
    assert "20:00" in res_m["reply"]
    assert len(res_m["actions_taken"]) == 0

def test_23_meal_lounge_query_all_customers():
    res_a = process_chat_message("Meal & lounge", pnr="TR1190B")
    assert "500" in res_a["reply"]
    assert "lounge access" in res_a["reply"].lower()
    assert len(res_a["actions_taken"]) == 0

    res_m = process_chat_message("Meal & lounge", pnr="WL7742")
    assert "500" in res_m["reply"]
    assert "lounge access" in res_m["reply"].lower()
    assert len(res_m["actions_taken"]) == 0

def test_24_hotel_eligibility_query_all_customers():
    res_a = process_chat_message("Hotel eligibility", pnr="TR1190B")
    assert "exceeding 5 hours" in res_a["reply"].lower() or "not included" in res_a["reply"].lower()
    assert len(res_a["actions_taken"]) == 0

    res_m = process_chat_message("Hotel eligibility", pnr="WL7742")
    assert "eligible" in res_m["reply"].lower() or "6-hour delay" in res_m["reply"].lower()
    assert len(res_m["actions_taken"]) == 0

def test_25_casual_queries_for_arvind_and_meher():
    res_a_hi = process_chat_message("hi", pnr="TR1190B")
    assert "Arvind" in res_a_hi["reply"]
    assert "SK-118" not in res_a_hi["reply"]

    res_m_thanks = process_chat_message("thanks", pnr="WL7742")
    assert "welcome" in res_m_thanks["reply"].lower()
    assert "SK-305" not in res_m_thanks["reply"]

def test_26_fastapi_chat_endpoint_response_validation():
    from app.models.models import ChatResponse

    # Test 1: Arvind (Check delay)
    res_a = process_chat_message("Check delay", pnr="TR1190B")
    validated_a = ChatResponse(**res_a)
    assert validated_a.source_policy is not None
    assert validated_a.source_policy.policy_code is not None
    assert validated_a.source_policy.policy_name is not None
    assert validated_a.source_policy.reason is not None
    assert validated_a.source_policy.decision is not None

    # Test 2: Meher (Hotel eligibility)
    res_m = process_chat_message("Hotel eligibility", pnr="WL7742")
    validated_m = ChatResponse(**res_m)
    assert validated_m.source_policy is not None
    assert validated_m.source_policy.policy_code == "POL-2"
    assert validated_m.source_policy.policy_name is not None
    assert validated_m.source_policy.reason is not None
    assert validated_m.source_policy.decision is not None

    # Test 3: General policy query (delay >5h)
    res_pol = process_chat_message("What happens if delay is >5h?", pnr="TR1190B")
    validated_p = ChatResponse(**res_pol)
    assert validated_p.source_policy is not None
    assert validated_p.source_policy.policy_code == "POL-2"
    assert validated_p.source_policy.decision is not None



