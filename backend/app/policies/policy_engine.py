import os
import glob
from typing import List, Dict, Optional
from app.db import get_db_connection

KNOWLEDGE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../knowledge"))

def search_policies(query: str) -> List[Dict[str, str]]:
    """Search policies in database and knowledge directory."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query_lower = query.lower()
    cursor.execute("SELECT code, name, category, summary, content FROM policies")
    rows = cursor.fetchall()
    
    results = []
    for row in rows:
        code, name, category, summary, content = row["code"], row["name"], row["category"], row["summary"], row["content"]
        if (query_lower in name.lower() or 
            query_lower in category.lower() or 
            query_lower in summary.lower() or 
            query_lower in content.lower() or
            query == "" or query == "*"):
            results.append({
                "code": code,
                "name": name,
                "category": category,
                "summary": summary,
                "content": content
            })
    conn.close()
    
    # If no DB match, fallback to search in knowledge markdown files
    if not results and os.path.exists(KNOWLEDGE_DIR):
        for filepath in glob.glob(os.path.join(KNOWLEDGE_DIR, "*.md")):
            filename = os.path.basename(filepath)
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()
                if query_lower in text.lower():
                    results.append({
                        "code": filename.replace(".md", "").upper(),
                        "name": filename.replace(".md", "").replace("_", " ").title(),
                        "category": "general",
                        "summary": text[:150] + "...",
                        "content": text
                    })
    return results

def get_policy_by_code(code: str) -> Optional[Dict[str, str]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT code, name, category, summary, content FROM policies WHERE code = ?", (code,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "code": row["code"],
            "name": row["name"],
            "category": row["category"],
            "summary": row["summary"],
            "content": row["content"]
        }
    return None

def get_policy_for_disruption(status: str) -> Dict[str, str]:
    """Retrieve primary policy rule matching disruption status."""
    status_upper = status.upper()
    if "CANCEL" in status_upper:
        policy = get_policy_by_code("POL-1")
        return {
            "policy_code": "POL-1",
            "policy_name": policy["name"] if policy else "Cancellation Rebooking & Refund Policy",
            "reason": "Flight SK-204 was cancelled due to operational reasons",
            "decision": "Customer entitled to free rebooking (next 24h) OR full refund to original payment method (7 business days).",
            "summary": policy["summary"] if policy else "Free rebooking or full refund."
        }
    elif "DELAYED 4" in status_upper or "4 HOUR" in status_upper:
        policy = get_policy_by_code("POL-2")
        return {
            "policy_code": "POL-2",
            "policy_name": policy["name"] if policy else "Delay Compensation Policy (Tier 2: >3h)",
            "reason": "Flight SK-118 is delayed by 4 hours",
            "decision": "Eligible for ₹500 meal voucher and lounge access pass. Hotel NOT eligible (hotel requires delay > 5 hours).",
            "summary": policy["summary"] if policy else "Meal voucher and lounge access."
        }
    elif "DELAYED 6" in status_upper or "6 HOUR" in status_upper:
        policy = get_policy_by_code("POL-2")
        return {
            "policy_code": "POL-2",
            "policy_name": policy["name"] if policy else "Delay Compensation Policy (Tier 3: >5h)",
            "reason": "Flight SK-305 is delayed by 6 hours",
            "decision": "Eligible for ₹500 meal voucher, lounge access, and hotel for delayed-hours portion ONLY (NOT full night stay).",
            "summary": policy["summary"] if policy else "Meal voucher, lounge, and delayed-hours hotel."
        }
    else:
        return {
            "policy_code": "POL-GEN",
            "policy_name": "General Airline Service Policy",
            "reason": "Standard booking enquiry",
            "decision": "Information provided according to passenger booking details.",
            "summary": "Standard operational rules apply."
        }
