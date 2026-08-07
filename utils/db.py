"""
utils/db.py — SQLite database layer for the Work Order system and
              Preventive Maintenance Management (Module 7).

All database interaction lives here so that pages stay pure UI code.
The database file (work_orders.db) is created automatically on first use.
"""

import sqlite3
import os
from datetime import datetime, timedelta

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

# ── PM constants ──────────────────────────────────────────────────────────────

PM_STATUSES      = ["Scheduled", "Upcoming", "In Progress", "Completed", "Overdue"]
PM_FREQUENCIES   = ["Daily", "Weekly", "Bi-Weekly", "Monthly", "Quarterly", "Semi-Annual", "Annual"]

# Days between maintenance for each frequency
PM_FREQUENCY_DAYS: dict[str, int] = {
    "Daily":       1,
    "Weekly":      7,
    "Bi-Weekly":  14,
    "Monthly":    30,
    "Quarterly":  91,
    "Semi-Annual": 182,
    "Annual":     365,
}

# Default checklist items per maintenance task
PM_DEFAULT_CHECKLISTS: dict[str, list[str]] = {
    "General Inspection": [
        "Inspect overall machine condition",
        "Check for abnormal noise or vibration",
        "Verify all safety guards are in place",
        "Clean machine exterior",
        "Document inspection findings",
    ],
    "Lubrication Service": [
        "Check lubrication oil level",
        "Inspect for oil leaks",
        "Lubricate all moving parts per schedule",
        "Replace oil filter if required",
        "Log lubrication service",
    ],
    "Tool Wear Inspection": [
        "Measure tool wear against tolerance limits",
        "Inspect tool holder alignment",
        "Replace worn tooling components",
        "Verify tool clamping force",
        "Record tool wear readings",
    ],
    "Cooling System Check": [
        "Verify coolant level",
        "Inspect heat exchanger for fouling",
        "Check fan/blower operation",
        "Test coolant temperature differential",
        "Clean cooling vents",
    ],
    "Electrical Inspection": [
        "Check power supply connections",
        "Test circuit breaker operation",
        "Inspect motor drive units",
        "Verify voltage and current readings",
        "Inspect cable insulation",
    ],
    "Sensor Calibration": [
        "Calibrate temperature sensors",
        "Calibrate RPM / speed sensors",
        "Calibrate torque sensors",
        "Verify sensor output against reference",
        "Update sensor calibration log",
    ],
    "Full Preventive Maintenance": [
        "Inspect overall machine condition",
        "Lubricate all moving parts",
        "Check and replace worn tooling",
        "Inspect cooling system",
        "Test electrical connections",
        "Calibrate all sensors",
        "Run functional test at reduced load",
        "Document all findings and actions taken",
    ],
}


def init_db() -> None:
    """
    Create the work_orders, pm_schedules, pm_checklists, and pm_history
    tables if they do not already exist.
    Safe to call on every app start — all DDL uses CREATE TABLE IF NOT EXISTS.
    """
    ddl_work_orders = """
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

    ddl_pm_schedules = """
    CREATE TABLE IF NOT EXISTS pm_schedules (
        schedule_id         INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id          TEXT    NOT NULL,
        machine_type        TEXT    NOT NULL DEFAULT '',
        task_name           TEXT    NOT NULL,
        description         TEXT    DEFAULT '',
        frequency           TEXT    NOT NULL,
        technician_type     TEXT    NOT NULL DEFAULT '',
        assigned_technician TEXT    NOT NULL DEFAULT '',
        priority            TEXT    NOT NULL DEFAULT 'Medium',
        last_maintenance    TEXT    DEFAULT '',
        next_maintenance    TEXT    NOT NULL,
        status              TEXT    NOT NULL DEFAULT 'Scheduled',
        work_order_id       INTEGER DEFAULT NULL,
        created_date        TEXT    NOT NULL,
        updated_date        TEXT    NOT NULL
    );
    """

    ddl_pm_checklists = """
    CREATE TABLE IF NOT EXISTS pm_checklists (
        checklist_id        INTEGER PRIMARY KEY AUTOINCREMENT,
        schedule_id         INTEGER NOT NULL,
        item_text           TEXT    NOT NULL,
        is_completed        INTEGER NOT NULL DEFAULT 0,
        completed_date      TEXT    DEFAULT '',
        sort_order          INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY (schedule_id) REFERENCES pm_schedules(schedule_id)
    );
    """

    ddl_pm_history = """
    CREATE TABLE IF NOT EXISTS pm_history (
        history_id          INTEGER PRIMARY KEY AUTOINCREMENT,
        schedule_id         INTEGER NOT NULL,
        product_id          TEXT    NOT NULL,
        machine_type        TEXT    NOT NULL DEFAULT '',
        task_name           TEXT    NOT NULL,
        assigned_technician TEXT    NOT NULL DEFAULT '',
        completed_date      TEXT    NOT NULL,
        notes               TEXT    DEFAULT '',
        checklist_total     INTEGER DEFAULT 0,
        checklist_done      INTEGER DEFAULT 0,
        work_order_id       INTEGER DEFAULT NULL,
        created_date        TEXT    NOT NULL
    );
    """

    with get_connection() as conn:
        conn.execute(ddl_work_orders)
        conn.execute(ddl_pm_schedules)
        conn.execute(ddl_pm_checklists)
        conn.execute(ddl_pm_history)
        # Migration: add technician_type column to pre-existing work_orders databases
        try:
            conn.execute("ALTER TABLE work_orders ADD COLUMN technician_type TEXT NOT NULL DEFAULT ''")
        except Exception:
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


# ══════════════════════════════════════════════════════════════════════════════
# MODULE 7 — Preventive Maintenance CRUD
# ══════════════════════════════════════════════════════════════════════════════

# ── PM Schedules ──────────────────────────────────────────────────────────────

def insert_pm_schedule(
    product_id: str,
    machine_type: str,
    task_name: str,
    description: str,
    frequency: str,
    technician_type: str,
    assigned_technician: str,
    priority: str,
    next_maintenance: str,
    last_maintenance: str = "",
    status: str = "Scheduled",
    work_order_id: int | None = None,
    checklist_items: list[str] | None = None,
) -> int:
    """
    Insert one PM schedule record and its default checklist items.
    Returns the new schedule_id.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sql = """
    INSERT INTO pm_schedules
        (product_id, machine_type, task_name, description, frequency,
         technician_type, assigned_technician, priority,
         last_maintenance, next_maintenance, status, work_order_id,
         created_date, updated_date)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    with get_connection() as conn:
        cur = conn.execute(
            sql,
            (product_id, machine_type, task_name, description, frequency,
             technician_type, assigned_technician, priority,
             last_maintenance, next_maintenance, status, work_order_id, now, now),
        )
        schedule_id = cur.lastrowid
        # Insert checklist items
        items = checklist_items or PM_DEFAULT_CHECKLISTS.get(task_name, [])
        for i, item_text in enumerate(items):
            conn.execute(
                "INSERT INTO pm_checklists (schedule_id, item_text, sort_order) VALUES (?, ?, ?)",
                (schedule_id, item_text, i),
            )
        conn.commit()
    return schedule_id


def fetch_all_pm_schedules() -> list[dict]:
    """Return all PM schedules as list of dicts, newest first."""
    sql = """
    SELECT s.*,
           (SELECT COUNT(*) FROM pm_checklists c WHERE c.schedule_id = s.schedule_id) AS checklist_total,
           (SELECT COUNT(*) FROM pm_checklists c WHERE c.schedule_id = s.schedule_id AND c.is_completed = 1) AS checklist_done
    FROM pm_schedules s
    ORDER BY s.next_maintenance ASC
    """
    with get_connection() as conn:
        rows = conn.execute(sql).fetchall()
    return [dict(r) for r in rows]


def fetch_pm_schedule_by_id(schedule_id: int) -> dict | None:
    """Return a single PM schedule or None."""
    sql = "SELECT * FROM pm_schedules WHERE schedule_id = ?"
    with get_connection() as conn:
        row = conn.execute(sql, (schedule_id,)).fetchone()
    return dict(row) if row else None


def update_pm_schedule(
    schedule_id: int,
    product_id: str,
    machine_type: str,
    task_name: str,
    description: str,
    frequency: str,
    technician_type: str,
    assigned_technician: str,
    priority: str,
    next_maintenance: str,
    last_maintenance: str = "",
    status: str = "Scheduled",
    work_order_id: int | None = None,
) -> None:
    """Full update of all editable PM schedule fields."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sql = """
    UPDATE pm_schedules
    SET product_id=?, machine_type=?, task_name=?, description=?,
        frequency=?, technician_type=?, assigned_technician=?, priority=?,
        last_maintenance=?, next_maintenance=?, status=?,
        work_order_id=?, updated_date=?
    WHERE schedule_id=?
    """
    with get_connection() as conn:
        conn.execute(
            sql,
            (product_id, machine_type, task_name, description, frequency,
             technician_type, assigned_technician, priority,
             last_maintenance, next_maintenance, status, work_order_id, now, schedule_id),
        )
        conn.commit()


def update_pm_schedule_status(schedule_id: int, new_status: str) -> None:
    """Update only the status of a PM schedule."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        conn.execute(
            "UPDATE pm_schedules SET status=?, updated_date=? WHERE schedule_id=?",
            (new_status, now, schedule_id),
        )
        conn.commit()


def delete_pm_schedule(schedule_id: int) -> None:
    """Delete a PM schedule and its checklist items."""
    with get_connection() as conn:
        conn.execute("DELETE FROM pm_checklists WHERE schedule_id = ?", (schedule_id,))
        conn.execute("DELETE FROM pm_schedules WHERE schedule_id = ?", (schedule_id,))
        conn.commit()


# ── PM Checklists ─────────────────────────────────────────────────────────────

def fetch_checklist_items(schedule_id: int) -> list[dict]:
    """Return all checklist items for a schedule, in sort order."""
    sql = "SELECT * FROM pm_checklists WHERE schedule_id = ? ORDER BY sort_order ASC"
    with get_connection() as conn:
        rows = conn.execute(sql, (schedule_id,)).fetchall()
    return [dict(r) for r in rows]


def toggle_checklist_item(checklist_id: int, is_completed: bool) -> None:
    """Mark a checklist item as completed or pending."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S") if is_completed else ""
    with get_connection() as conn:
        conn.execute(
            "UPDATE pm_checklists SET is_completed=?, completed_date=? WHERE checklist_id=?",
            (1 if is_completed else 0, now, checklist_id),
        )
        conn.commit()


def reset_pm_checklists(schedule_id: int) -> None:
    """Reset all checklist items for a given schedule to pending."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE pm_checklists SET is_completed=0, completed_date='' WHERE schedule_id=?",
            (schedule_id,)
        )
        conn.commit()


def add_checklist_item(schedule_id: int, item_text: str) -> int:
    """Append a custom checklist item to a PM schedule."""
    with get_connection() as conn:
        max_order_row = conn.execute(
            "SELECT MAX(sort_order) FROM pm_checklists WHERE schedule_id=?", (schedule_id,)
        ).fetchone()
        next_order = (max_order_row[0] or 0) + 1
        cur = conn.execute(
            "INSERT INTO pm_checklists (schedule_id, item_text, sort_order) VALUES (?,?,?)",
            (schedule_id, item_text, next_order),
        )
        conn.commit()
        return cur.lastrowid


# ── PM History ────────────────────────────────────────────────────────────────

def insert_pm_history(
    schedule_id: int,
    product_id: str,
    machine_type: str,
    task_name: str,
    assigned_technician: str,
    completed_date: str,
    notes: str = "",
    checklist_total: int = 0,
    checklist_done: int = 0,
    work_order_id: int | None = None,
) -> int:
    """Record a completed PM event in history."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sql = """
    INSERT INTO pm_history
        (schedule_id, product_id, machine_type, task_name, assigned_technician,
         completed_date, notes, checklist_total, checklist_done,
         work_order_id, created_date)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    with get_connection() as conn:
        cur = conn.execute(
            sql,
            (schedule_id, product_id, machine_type, task_name, assigned_technician,
             completed_date, notes, checklist_total, checklist_done,
             work_order_id, now),
        )
        conn.commit()
        return cur.lastrowid


def fetch_pm_history(product_id: str | None = None) -> list[dict]:
    """Return PM history records, optionally filtered by product_id."""
    if product_id:
        sql = "SELECT * FROM pm_history WHERE product_id=? ORDER BY completed_date DESC"
        with get_connection() as conn:
            rows = conn.execute(sql, (product_id,)).fetchall()
    else:
        sql = "SELECT * FROM pm_history ORDER BY completed_date DESC"
        with get_connection() as conn:
            rows = conn.execute(sql).fetchall()
    return [dict(r) for r in rows]


# ── PM KPIs ───────────────────────────────────────────────────────────────────

def fetch_pm_kpis() -> dict:
    """
    Return aggregated KPIs for the Preventive Maintenance dashboard.
    Statuses are re-computed dynamically before querying so overdue detection is fresh.
    """
    # Refresh overdue status first
    refresh_pm_statuses()

    sql = """
    SELECT
        COUNT(*)                                                             AS total_scheduled,
        SUM(CASE WHEN status IN ('Upcoming')       THEN 1 ELSE 0 END)       AS upcoming_count,
        SUM(CASE WHEN status = 'Overdue'           THEN 1 ELSE 0 END)       AS overdue_count,
        SUM(CASE WHEN status = 'In Progress'       THEN 1 ELSE 0 END)       AS in_progress_count,
        SUM(CASE WHEN work_order_id IS NOT NULL    THEN 1 ELSE 0 END)       AS with_work_orders
    FROM pm_schedules
    """
    # Get completed this month
    hist_sql = """
    SELECT 
        COUNT(*) AS total_history,
        SUM(CASE WHEN strftime('%Y-%m', completed_date) = strftime('%Y-%m', 'now', 'localtime') THEN 1 ELSE 0 END) AS completed_this_month
    FROM pm_history
    """

    with get_connection() as conn:
        row     = conn.execute(sql).fetchone()
        h_row   = conn.execute(hist_sql).fetchone()

    kpis = dict(row) if row else {}
    kpis["completed_this_month"] = h_row["completed_this_month"] if h_row and h_row["completed_this_month"] else 0
    kpis["total_history"]        = h_row["total_history"] if h_row else 0
    
    total = kpis.get("total_scheduled", 0)
    # Completion rate based on total history vs total scheduled isn't very meaningful for recurring tasks.
    # We will just pass the raw data out.
    return kpis


def refresh_pm_statuses() -> None:
    """
    Auto-update pm_schedule statuses based on next_maintenance date:
    - next_maintenance <= today  AND status not Completed/In Progress  → Overdue
    - next_maintenance within 7 days AND status = Scheduled            → Upcoming
    """
    today = datetime.now().date()
    upcoming_threshold = today + timedelta(days=7)

    with get_connection() as conn:
        # Mark overdue
        conn.execute(
            """
            UPDATE pm_schedules
            SET status = 'Overdue', updated_date = ?
            WHERE date(next_maintenance) < ?
              AND status NOT IN ('Completed', 'In Progress', 'Overdue')
            """,
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), today.isoformat()),
        )
        # Mark upcoming (within 7 days, not already overdue/completed/in progress)
        conn.execute(
            """
            UPDATE pm_schedules
            SET status = 'Upcoming', updated_date = ?
            WHERE date(next_maintenance) >= ?
              AND date(next_maintenance) <= ?
              AND status = 'Scheduled'
            """,
            (
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                today.isoformat(),
                upcoming_threshold.isoformat(),
            ),
        )
        conn.commit()


def compute_next_maintenance_date(frequency: str, from_date: str | None = None) -> str:
    """
    Given a frequency string, return the ISO next maintenance date (YYYY-MM-DD).
    from_date defaults to today if not supplied.
    """
    days = PM_FREQUENCY_DAYS.get(frequency, 30)
    base = datetime.strptime(from_date, "%Y-%m-%d").date() if from_date else datetime.now().date()
    return (base + timedelta(days=days)).isoformat()


def schedule_exists_for_product_task(product_id: str, task_name: str) -> bool:
    """Return True if a non-completed schedule already exists for this product+task."""
    sql = """
    SELECT 1 FROM pm_schedules
    WHERE product_id=? AND task_name=? AND status NOT IN ('Completed')
    LIMIT 1
    """
    with get_connection() as conn:
        row = conn.execute(sql, (product_id, task_name)).fetchone()
    return row is not None
