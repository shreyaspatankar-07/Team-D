"""
utils/db.py — SQLite database layer for the Work Order system.

All database interaction lives here so that pages stay pure UI code.
The database file (work_orders.db) is created automatically on first use.
"""

import sqlite3
import os
from datetime import datetime

# ── Database path (relative to project root so it travels with the project) ───

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "work_orders.db")

# ── Valid status values (single source of truth) ──────────────────────────────

STATUSES = ["Open", "Assigned", "In Progress", "Completed", "Closed"]

# ── Valid priority values ──────────────────────────────────────────────────────

PRIORITIES = ["Low", "Medium", "High", "Critical"]

# ── Valid machine types ────────────────────────────────────────────────────────

MACHINE_TYPES = ["L", "M", "H"]

# ── Valid failure types ────────────────────────────────────────────────────────

FAILURE_TYPES = ["TWF", "HDF", "PWF", "OSF", "RNF"]

# ── Technician roster (type → list of names) ──────────────────────────────────
# Single source of truth — reused by Work Order Creation and Management pages.

TECHNICIAN_TYPES = [
    "Preventive Maintenance",
    "Mechanical Maintenance",
    "Electrical Maintenance",
    "Electronics & Sensors",
    "Quality Inspection",
    "Emergency Repair",
]

TECHNICIANS: dict[str, list[str]] = {
    "Preventive Maintenance": [
        "John Smith",
        "Rahul Kumar",
        "David Lee",
        "Arjun Nair",
        "Michael Scott",
    ],
    "Mechanical Maintenance": [
        "Ravi Patel",
        "Ahmed Khan",
        "Daniel Thomas",
        "Kevin Wilson",
        "Joseph Roy",
    ],
    "Electrical Maintenance": [
        "Vikram Singh",
        "Ethan Brown",
        "Praveen Kumar",
        "Samuel George",
        "Chris Martin",
    ],
    "Electronics & Sensors": [
        "Neha Sharma",
        "Sarah Wilson",
        "Priya Menon",
        "Emily Davis",
        "Robert James",
    ],
    "Quality Inspection": [
        "Anil Das",
        "Sophia Taylor",
        "Karthik R",
        "Olivia White",
        "Ryan Cooper",
    ],
    "Emergency Repair": [
        "Manoj Varma",
        "Jacob Miller",
        "Alan Joseph",
        "Richard Hall",
        "Akash N",
    ],
}

# Flat list of all technicians (used when no type filter is active)
ALL_TECHNICIANS: list[str] = [name for names in TECHNICIANS.values() for name in names]

# ── Failure type → recommended Technician Type ────────────────────────────────

FAILURE_TO_TECH_TYPE: dict[str, str] = {
    "TWF": "Mechanical Maintenance",
    "HDF": "Mechanical Maintenance",
    "PWF": "Electrical Maintenance",
    "OSF": "Mechanical Maintenance",
    "RNF": "Emergency Repair",
}
HEALTHY_TECH_TYPE = "Preventive Maintenance"

# ── Failure type → recommended Priority ───────────────────────────────────────

FAILURE_TO_PRIORITY: dict[str, str] = {
    "TWF": "High",
    "HDF": "High",
    "PWF": "Critical",
    "OSF": "High",
    "RNF": "Critical",
}
HEALTHY_PRIORITY = "Low"

# ── Auto-description templates ────────────────────────────────────────────────

FAILURE_DESCRIPTIONS: dict[str, str] = {
    "TWF": (
        "Tool Wear Failure detected on this machine. "
        "Inspect the cutting tool condition, measure wear against tolerance limits, "
        "and replace worn components as necessary. Verify tool holder alignment before resuming operation."
    ),
    "HDF": (
        "Machine shows signs of Heat Dissipation Failure. "
        "Immediate inspection of the cooling system and thermal components is recommended. "
        "Check coolant levels, clean heat exchangers, and verify fan/blower operation."
    ),
    "PWF": (
        "Power Failure detected. The machine is operating outside its rated power envelope. "
        "Inspect power supply connections, circuit breakers, and motor drive units. "
        "Verify voltage and current readings under load before restarting."
    ),
    "OSF": (
        "Overstrain Failure identified. Excessive torque has been applied relative to the machine grade. "
        "Inspect drive train components, gearbox, and coupling units. "
        "Review the production schedule to ensure load levels remain within specification."
    ),
    "RNF": (
        "Random Failure detected — no single dominant root cause identified. "
        "Perform a comprehensive diagnostic inspection covering all subsystems: "
        "mechanical, electrical, and sensor components. Log all findings for trend analysis."
    ),
}
HEALTHY_DESCRIPTION = (
    "Routine preventive maintenance recommended. "
    "Inspect overall machine condition, clean all accessible components, "
    "lubricate moving parts per the service schedule, and verify sensor readings are within normal range."
)


# ── Connection helper ─────────────────────────────────────────────────────────

def get_connection() -> sqlite3.Connection:
    """
    Return a sqlite3 connection with row_factory set so rows behave like dicts.
    check_same_thread=False is safe here because Streamlit reruns are sequential.
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


# ── Schema initialisation ─────────────────────────────────────────────────────

def init_db() -> None:
    """
    Create the work_orders table if it does not already exist.
    Also runs a non-destructive ALTER TABLE migration to add the
    technician_type column to existing databases.
    Safe to call on every app start.
    """
    ddl = """
    CREATE TABLE IF NOT EXISTS work_orders (
        work_order_id       INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id          TEXT    NOT NULL,
        machine_type        TEXT    NOT NULL,
        failure_type        TEXT    NOT NULL,
        priority            TEXT    NOT NULL,
        technician_type     TEXT    NOT NULL DEFAULT '',
        assigned_technician TEXT    NOT NULL,
        description         TEXT    DEFAULT '',
        status              TEXT    NOT NULL DEFAULT 'Open',
        created_date        TEXT    NOT NULL,
        updated_date        TEXT    NOT NULL
    );
    """
    with get_connection() as conn:
        conn.execute(ddl)
        # Migration: add technician_type column to pre-existing databases
        try:
            conn.execute("ALTER TABLE work_orders ADD COLUMN technician_type TEXT NOT NULL DEFAULT ''")
        except Exception:
            # Column already exists — ignore
            pass
        conn.commit()


# ── CRUD — Insert ─────────────────────────────────────────────────────────────

def insert_work_order(
    product_id: str,
    machine_type: str,
    failure_type: str,
    priority: str,
    technician_type: str,
    assigned_technician: str,
    description: str = "",
    status: str = "Open",
) -> int:
    """
    Insert one work order record.
    Returns the newly created work_order_id (auto-increment integer).
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sql = """
    INSERT INTO work_orders
        (product_id, machine_type, failure_type, priority, technician_type,
         assigned_technician, description, status, created_date, updated_date)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    with get_connection() as conn:
        cursor = conn.execute(
            sql,
            (product_id, machine_type, failure_type, priority, technician_type,
             assigned_technician, description, status, now, now),
        )
        conn.commit()
        return cursor.lastrowid


# ── CRUD — Read ───────────────────────────────────────────────────────────────

def fetch_all_work_orders() -> list[dict]:
    """
    Return every work order as a list of plain dicts (oldest first).
    """
    sql = """
    SELECT
        work_order_id,
        product_id,
        machine_type,
        failure_type,
        priority,
        technician_type,
        assigned_technician,
        description,
        status,
        created_date,
        updated_date
    FROM work_orders
    ORDER BY work_order_id ASC
    """
    with get_connection() as conn:
        rows = conn.execute(sql).fetchall()
    return [dict(row) for row in rows]


def fetch_work_order_by_id(work_order_id: int) -> dict | None:
    """Return a single work order dict, or None if not found."""
    sql = "SELECT * FROM work_orders WHERE work_order_id = ?"
    with get_connection() as conn:
        row = conn.execute(sql, (work_order_id,)).fetchone()
    return dict(row) if row else None


# ── CRUD — Update ─────────────────────────────────────────────────────────────

def update_work_order_status(work_order_id: int, new_status: str) -> None:
    """
    Update only the status field (and refresh updated_date) for a given WO.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sql = "UPDATE work_orders SET status = ?, updated_date = ? WHERE work_order_id = ?"
    with get_connection() as conn:
        conn.execute(sql, (new_status, now, work_order_id))
        conn.commit()


def update_work_order(
    work_order_id: int,
    product_id: str,
    machine_type: str,
    failure_type: str,
    priority: str,
    technician_type: str,
    assigned_technician: str,
    description: str,
    status: str,
) -> None:
    """Full update of all editable fields for a given work order."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sql = """
    UPDATE work_orders
    SET product_id = ?, machine_type = ?, failure_type = ?,
        priority = ?, technician_type = ?, assigned_technician = ?,
        description = ?, status = ?, updated_date = ?
    WHERE work_order_id = ?
    """
    with get_connection() as conn:
        conn.execute(
            sql,
            (product_id, machine_type, failure_type, priority,
             technician_type, assigned_technician, description, status, now, work_order_id),
        )
        conn.commit()


# ── CRUD — Delete ─────────────────────────────────────────────────────────────

def delete_work_order(work_order_id: int) -> None:
    """Permanently delete a work order from the database."""
    sql = "DELETE FROM work_orders WHERE work_order_id = ?"
    with get_connection() as conn:
        conn.execute(sql, (work_order_id,))
        conn.commit()


# ── KPI Aggregations ──────────────────────────────────────────────────────────

def fetch_kpis() -> dict:
    """
    Return counts for each status plus a total.
    Used by the Work Order Management KPI cards.
    """
    sql = """
    SELECT
        COUNT(*)                                                  AS total,
        SUM(CASE WHEN status = 'Open'        THEN 1 ELSE 0 END)  AS open_count,
        SUM(CASE WHEN status = 'Assigned'    THEN 1 ELSE 0 END)  AS assigned_count,
        SUM(CASE WHEN status = 'In Progress' THEN 1 ELSE 0 END)  AS in_progress_count,
        SUM(CASE WHEN status = 'Completed'   THEN 1 ELSE 0 END)  AS completed_count,
        SUM(CASE WHEN status = 'Closed'      THEN 1 ELSE 0 END)  AS closed_count
    FROM work_orders
    """
    with get_connection() as conn:
        row = conn.execute(sql).fetchone()
    if row:
        return dict(row)
    return {
        "total": 0,
        "open_count": 0,
        "assigned_count": 0,
        "in_progress_count": 0,
        "completed_count": 0,
        "closed_count": 0,
    }
