import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "skyassist.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        loyalty_tier TEXT NOT NULL,
        booking_reference TEXT UNIQUE NOT NULL,
        email TEXT NOT NULL,
        phone TEXT NOT NULL,
        flight_count_12m INTEGER NOT NULL,
        prior_complaint_count INTEGER NOT NULL,
        last_complaint_type TEXT,
        last_resolution TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pnr TEXT UNIQUE NOT NULL,
        customer_name TEXT NOT NULL,
        flight_number TEXT NOT NULL,
        origin TEXT NOT NULL,
        destination TEXT NOT NULL,
        departure_date TEXT NOT NULL,
        scheduled_departure TEXT NOT NULL,
        status TEXT NOT NULL,
        reason TEXT,
        new_departure TEXT,
        return_route TEXT,
        return_date TEXT,
        return_departure TEXT,
        return_status TEXT,
        original_payment_method TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS flights (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        flight_number TEXT NOT NULL,
        origin TEXT NOT NULL,
        destination TEXT NOT NULL,
        date TEXT NOT NULL,
        scheduled_departure TEXT NOT NULL,
        status TEXT NOT NULL,
        new_departure TEXT,
        reason TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS policies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        summary TEXT NOT NULL,
        content TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS actions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action_id TEXT UNIQUE NOT NULL,
        pnr TEXT NOT NULL,
        action_type TEXT NOT NULL,
        status TEXT NOT NULL,
        details TEXT NOT NULL,
        policy_source TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS escalations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        escalation_id TEXT UNIQUE NOT NULL,
        pnr TEXT NOT NULL,
        customer_name TEXT NOT NULL,
        reason TEXT NOT NULL,
        requested_action TEXT NOT NULL,
        policy_conflict TEXT NOT NULL,
        priority TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        event TEXT NOT NULL,
        pnr TEXT,
        tool_name TEXT NOT NULL,
        result TEXT NOT NULL,
        policy_source TEXT,
        status TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pnr TEXT NOT NULL,
        role TEXT NOT NULL,
        message TEXT NOT NULL,
        timestamp TEXT NOT NULL
    )
    """)

    conn.commit()
    seed_db(conn)
    conn.close()

def seed_db(conn):
    cursor = conn.cursor()

    # Clear existing data to ensure clean seed matching assignment specs exactly
    cursor.execute("DELETE FROM customers")
    cursor.execute("DELETE FROM bookings")
    cursor.execute("DELETE FROM flights")
    cursor.execute("DELETE FROM policies")
    cursor.execute("DELETE FROM actions")
    cursor.execute("DELETE FROM escalations")
    cursor.execute("DELETE FROM audit_logs")
    cursor.execute("DELETE FROM conversations")

    # Seed Customers
    customers_data = [
        ("Priya Nair", "Gold", "SK4821X", "priya.nair@example.com", "+91-98xxxxxxx1", 6, 1, "delayed baggage", "voucher"),
        ("Arvind Kulkarni", "Silver", "TR1190B", "arvind.kulkarni@example.com", "+91-98xxxxxxx2", 3, 0, None, None),
        ("Meher Kaur", "Platinum", "WL7742", "meher.kaur@example.com", "+91-98xxxxxxx3", 10, 1, "overbooking", "tier-status upgrade"),
    ]
    cursor.executemany("""
        INSERT INTO customers (name, loyalty_tier, booking_reference, email, phone, flight_count_12m, prior_complaint_count, last_complaint_type, last_resolution)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, customers_data)

    # Seed Bookings
    bookings_data = [
        ("SK4821X", "Priya Nair", "SK-204", "Delhi", "Goa", "2026-09-23", "18:40", "CANCELLED", "operational reasons", None, "Goa → Delhi", "2026-09-25", "16:20", "Unaffected", "original payment method"),
        ("TR1190B", "Arvind Kulkarni", "SK-118", "Mumbai", "Bengaluru", "2026-09-23", "07:10", "Delayed 4 hours", "operational reasons", "11:10", None, None, None, None, "original payment method"),
        ("WL7742", "Meher Kaur", "SK-305", "Delhi", "Hyderabad", "2026-09-23", "14:00", "Delayed 6 hours", "operational reasons", "20:00", None, None, None, None, "original payment method"),
    ]
    cursor.executemany("""
        INSERT INTO bookings (pnr, customer_name, flight_number, origin, destination, departure_date, scheduled_departure, status, reason, new_departure, return_route, return_date, return_departure, return_status, original_payment_method)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, bookings_data)

    # Seed Flights
    flights_data = [
        ("SK-204", "Delhi", "Goa", "2026-09-23", "18:40", "CANCELLED", None, "operational reasons"),
        ("SK-118", "Mumbai", "Bengaluru", "2026-09-23", "07:10", "Delayed 4 hours", "11:10", "operational reasons"),
        ("SK-305", "Delhi", "Hyderabad", "2026-09-23", "14:00", "Delayed 6 hours", "20:00", "operational reasons"),
    ]
    cursor.executemany("""
        INSERT INTO flights (flight_number, origin, destination, date, scheduled_departure, status, new_departure, reason)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, flights_data)

    # Seed Policies
    policies_data = [
        ("POL-1", "Cancellation Rebooking & Refund", "cancellation",
         "Free rebooking within 24h or full refund to original payment method within 7 business days.",
         "If a flight is cancelled by the airline: customer is entitled to free rebooking on the next available flight within 24 hours OR full refund (customer's choice). Refund is processed in 7 business days to original payment method only."),

        ("POL-2", "Delay Compensation Tiers", "delay",
         "<3h delay: ₹500 meal. >3h delay: meal + lounge. >5h delay: meal + lounge + hotel for delayed hours.",
         "Delay under 3h: ₹500 meal voucher. Delay >3h: meal voucher + lounge access. Delay >5h: meal voucher + lounge access + hotel accommodation for delayed hours only (NOT a full night's stay)."),

        ("POL-3", "Refund Processing Rule", "refund",
         "100% full refund for airline cancellations within 7 business days to original payment method.",
         "For airline-caused cancellations: full refund processed within 7 business days strictly to original payment method only."),

        ("POL-4", "Fare Difference & Waiver Threshold", "fare_difference",
         "Customer pays fare difference for voluntary higher-fare flight. Agent authority limit is ₹1,500.",
         "If customer voluntarily chooses a higher-fare flight: customer pays fare difference. Agent cannot waive fare differences above ₹1,500 without supervisor approval."),

        ("POL-5", "Loyalty Tier Perks", "loyalty",
         "Priority rebooking for Gold/Platinum members. No extra monetary compensation beyond policy.",
         "Gold and Platinum members receive priority rebooking and first access to next-available seats. No additional compensation beyond standard policy."),
    ]
    cursor.executemany("""
        INSERT INTO policies (code, name, category, summary, content)
        VALUES (?, ?, ?, ?, ?)
    """, policies_data)

    conn.commit()

if __name__ == "__main__":
    init_db()
    print("Database initialized and seeded successfully.")
