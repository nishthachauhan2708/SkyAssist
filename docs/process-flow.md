# SkyAssist Process Flow

This document details the step-by-step sequence of operations executed by SkyAssist when processing customer inquiries and disruption resolution requests.

```mermaid
sequenceDiagram
    autonumber
    actor Customer
    participant UI as SkyAssist Frontend UI
    participant Orchestrator as Agent Orchestrator
    participant KB as Policy Knowledge Base
    participant Validator as Backend Authority Guardrail
    participant DB as SQLite DB & Audit Log

    Customer->>UI: Types message / Clicks quick prompt
    UI->>Orchestrator: POST /api/agent/chat { pnr, message }
    
    Orchestrator->>DB: Lookup Customer & Booking (PNR / Name)
    DB-->>Orchestrator: Return Customer Profile & Flight Operational Status
    
    Orchestrator->>KB: Retrieve relevant disruption policy (POL-1..5)
    KB-->>Orchestrator: Return grounded policy rules
    
    Orchestrator->>Validator: Validate requested action & entitlement rules
    
    alt Request within Authority (e.g. Refund for Cancellation / Meal Voucher)
        Validator->>DB: Execute Action Tool (ACT-XXXX) & write Audit Log
        DB-->>Validator: Action Success
        Validator-->>Orchestrator: Return Action Result
        Orchestrator-->>UI: Return empathetic response + Action Confirmation Card
    else Request exceeds Authority (e.g. ₹2,000 Fare Waiver / Legal Threat)
        Validator->>DB: Create Escalation Record (ESC-XXXX) & write Audit Log
        DB-->>Validator: Escalation Logged
        Validator-->>Orchestrator: Return Escalation Details
        Orchestrator-->>UI: Return explanation + Escalated Status Card
    end
    
    UI->>Customer: Display response, Policy Source, & Live Audit Activity
```

---

## Detailed Step Sequence

1. **User Message Reception**: Passenger sends message or selects assessment scenario.
2. **Identity & Booking Resolution**: Orchestrator queries DB using PNR (`SK4821X`, `TR1190B`, `WL7742`) or passenger name.
3. **Operational Status & Policy Retrieval**: Query DB flights table and load matching policy (`POL-1` to `POL-5`).
4. **Guardrail Authority Evaluation**:
   - Check if request contains legal threat -> mandatory immediate escalation.
   - Check if refund requested to alternate payment method -> refuse & escalate.
   - Check if fare waiver exceeds ₹1,500 threshold -> refuse & escalate.
   - Check if hotel requested for delay ≤ 5h or full night stay -> refuse & escalate.
5. **Action Execution & Audit Trail**: Allowed actions create unique action IDs (`ACT-REF-XXXX`, `ACT-VOU-XXXX`, `ACT-LNG-XXXX`, `ACT-HTL-XXXX`) and write timestamped audit entries.
6. **Response Generation & Source Presentation**: Display grounded response, active policy source card, and live audit timeline.
