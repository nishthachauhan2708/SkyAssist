import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any

from app.db import init_db, get_db_connection
from app.models.models import ChatRequest, ChatResponse, ActionRequest
from app.agents.orchestrator import process_chat_message
from app.tools.agent_tools import (
    lookup_customer, lookup_booking, get_flight_status,
    calculate_entitlements, initiate_refund, create_rebooking_request,
    issue_meal_voucher, grant_lounge_access, arrange_delay_hotel,
    waive_fare_difference, create_escalation
)
from app.policies.policy_engine import search_policies

app = FastAPI(
    title="SkyAssist — Airline Disruption Resolution Agent API",
    description="Assessment prototype for AIONOS Assignment 3",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_db():
    init_db()

@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "service": "SkyAssist API",
        "date": "Wednesday, 23 September 2026",
        "environment": "Assessment Prototype"
    }

@app.get("/api/customers/{pnr}")
def get_customer(pnr: str):
    cust = lookup_customer(pnr)
    if not cust:
        raise HTTPException(status_code=404, detail=f"Customer with PNR {pnr} not found")
    return cust

@app.get("/api/bookings/{pnr}")
def get_booking(pnr: str):
    booking = lookup_booking(pnr)
    if not booking:
        raise HTTPException(status_code=404, detail=f"Booking with PNR {pnr} not found")
    ent = calculate_entitlements(pnr)
    return {"booking": booking, "entitlements": ent}

@app.get("/api/flights/{flight_number}")
def get_flight(flight_number: str):
    fl = get_flight_status(flight_number)
    if not fl:
        raise HTTPException(status_code=404, detail=f"Flight {flight_number} not found")
    return fl

@app.get("/api/policies")
def list_policies(query: str = ""):
    return search_policies(query)

@app.post("/api/agent/chat", response_model=ChatResponse)
def agent_chat(req: ChatRequest):
    if not req.message or not req.message.strip():
        raise HTTPException(status_code=400, detail="Empty message received")
    res = process_chat_message(
        message=req.message,
        pnr=req.pnr,
        customer_name=req.customer_name
    )
    return res

@app.post("/api/actions/rebook")
def action_rebook(req: ActionRequest):
    return create_rebooking_request(req.pnr, req.details)

@app.post("/api/actions/refund")
def action_refund(req: ActionRequest):
    return initiate_refund(req.pnr, req.requested_amount, req.details)

@app.post("/api/actions/voucher")
def action_voucher(req: ActionRequest):
    amt = int(req.requested_amount) if req.requested_amount else 500
    return issue_meal_voucher(req.pnr, amt)

@app.post("/api/actions/lounge")
def action_lounge(req: ActionRequest):
    return grant_lounge_access(req.pnr)

@app.post("/api/actions/hotel")
def action_hotel(req: ActionRequest):
    full_night = "full" in (req.details or "").lower()
    return arrange_delay_hotel(req.pnr, requested_full_night=full_night)

@app.post("/api/escalations")
def get_escalations(pnr: Optional[str] = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if pnr and pnr != "ALL":
        cursor.execute("SELECT * FROM escalations WHERE UPPER(pnr) = ? ORDER BY id DESC", (pnr.upper(),))
    else:
        cursor.execute("SELECT * FROM escalations ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/api/audit/{pnr}")
def get_audit_logs(pnr: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    if pnr.upper() == "ALL":
        cursor.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 50")
    else:
        cursor.execute("SELECT * FROM audit_logs WHERE UPPER(pnr) = ? OR pnr IS NULL ORDER BY id DESC LIMIT 30", (pnr.upper(),))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
