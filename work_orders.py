"""Persistent, local work-order storage for recorded machine failures."""

from __future__ import annotations

import sqlite3
import calendar
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from pathlib import Path
from collections.abc import Iterator
from typing import Any

import pandas as pd


DATABASE_FILE = Path(__file__).with_name("maintenance_work_orders.db")
FAILURE_ACTIONS = {
    "TWF": "Inspect the cutting tool for wear and replace it if it exceeds the approved limit.",
    "HDF": "Inspect cooling flow, heat dissipation surfaces, and the process-temperature control path.",
    "PWF": "Inspect the power train, electrical supply, and operating load before returning the machine to service.",
    "OSF": "Inspect torque, rotational load, and mechanical alignment for overstrain conditions.",
    "RNF": "Perform a qualified diagnostic inspection and review recent maintenance history before release.",
}
FAILURE_LABELS = {
    "TWF": "Tool wear",
    "HDF": "Heat dissipation",
    "PWF": "Power",
    "OSF": "Overstrain",
    "RNF": "Random",
}
VALID_PRIORITIES = ("Low", "Medium", "High", "Critical")
VALID_STATUSES = ("Open", "In Progress", "Closed")
VALID_FREQUENCIES = ("Daily", "Weekly", "Monthly", "Quarterly", "Yearly")


@contextmanager
def _connection() -> Iterator[sqlite3.Connection]:
    """Open, commit, and close a SQLite connection on every operation."""
    connection = sqlite3.connect(DATABASE_FILE)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def initialise_work_orders() -> None:
    """Create the local work-order table and active-order duplicate guard."""
    with _connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS work_orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id TEXT NOT NULL,
                failure_reason TEXT NOT NULL,
                priority TEXT NOT NULL DEFAULT 'High',
                status TEXT NOT NULL DEFAULT 'Open',
                recommended_action TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        existing_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(work_orders)").fetchall()
        }
        for column, definition in {
            "schedule_id": "INTEGER",
            "technician": "TEXT",
            "due_date": "TEXT",
            "completed_at": "TEXT",
            "work_order_type": "TEXT NOT NULL DEFAULT 'Corrective'",
            "maintenance_notes": "TEXT NOT NULL DEFAULT ''",
        }.items():
            if column not in existing_columns:
                connection.execute(f"ALTER TABLE work_orders ADD COLUMN {column} {definition}")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS maintenance_schedules (
                schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                frequency TEXT NOT NULL,
                next_due_date TEXT NOT NULL,
                technician TEXT NOT NULL DEFAULT '',
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS maintenance_checklists (
                checklist_id INTEGER PRIMARY KEY AUTOINCREMENT,
                schedule_id INTEGER NOT NULL,
                item TEXT NOT NULL,
                required INTEGER NOT NULL DEFAULT 1,
                active INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY(schedule_id) REFERENCES maintenance_schedules(schedule_id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS maintenance_history (
                history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                work_order_id INTEGER NOT NULL,
                schedule_id INTEGER,
                product_id TEXT NOT NULL,
                technician TEXT NOT NULL DEFAULT '',
                completed_at TEXT NOT NULL,
                notes TEXT NOT NULL DEFAULT '',
                FOREIGN KEY(work_order_id) REFERENCES work_orders(order_id),
                FOREIGN KEY(schedule_id) REFERENCES maintenance_schedules(schedule_id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS maintenance_checklist_results (
                work_order_id INTEGER NOT NULL,
                checklist_id INTEGER NOT NULL,
                completed INTEGER NOT NULL DEFAULT 0,
                completed_at TEXT,
                PRIMARY KEY(work_order_id, checklist_id),
                FOREIGN KEY(work_order_id) REFERENCES work_orders(order_id),
                FOREIGN KEY(checklist_id) REFERENCES maintenance_checklists(checklist_id)
            )
            """
        )
        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS one_active_order_per_machine
            ON work_orders(product_id)
            WHERE status != 'Closed'
            """
        )


def failure_details(machine: Any) -> tuple[str, str]:
    """Return recorded failure labels and safe rule-based next actions."""
    codes = [code for code in FAILURE_LABELS if int(machine[code]) == 1]
    labels = [FAILURE_LABELS[code] for code in codes]
    actions = [FAILURE_ACTIONS[code] for code in codes]
    reason = ", ".join(labels) if labels else "Recorded machine failure"
    action = " ".join(actions) if actions else "Arrange a qualified diagnostic inspection before returning the machine to service."
    return reason, action


def create_work_order(machine: Any) -> tuple[bool, str]:
    """Create one Open work order for a failed machine, unless one is already active."""
    if int(machine["Machine failure"]) != 1:
        return False, "Work orders can only be created for machines with a recorded failure."

    initialise_work_orders()
    reason, action = failure_details(machine)
    now = datetime.now().isoformat(timespec="seconds")
    try:
        with _connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO work_orders
                    (product_id, failure_reason, priority, status, recommended_action, created_at, updated_at)
                VALUES (?, ?, 'High', 'Open', ?, ?, ?)
                """,
                (str(machine["Product ID"]), reason, action, now, now),
            )
        return True, f"Work order #{cursor.lastrowid} created for {machine['Product ID']}."
    except sqlite3.IntegrityError:
        return False, f"{machine['Product ID']} already has an active work order."


def get_work_orders(status: str = "All", priority: str = "All", search: str = "") -> pd.DataFrame:
    """Return the persistent queue, newest first, with optional filters."""
    initialise_work_orders()
    clauses: list[str] = []
    values: list[str] = []
    if status != "All":
        clauses.append("status = ?")
        values.append(status)
    if priority != "All":
        clauses.append("priority = ?")
        values.append(priority)
    if search.strip():
        search_term = f"%{search.strip()}%"
        clauses.append(
            "(CAST(order_id AS TEXT) LIKE ? OR product_id LIKE ? OR failure_reason LIKE ? OR recommended_action LIKE ?)"
        )
        values.extend([search_term] * 4)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with _connection() as connection:
        return pd.read_sql_query(
            f"SELECT * FROM work_orders {where} ORDER BY CASE status WHEN 'Open' THEN 0 WHEN 'In Progress' THEN 1 ELSE 2 END, created_at DESC",
            connection,
            params=values,
        )


def delete_work_order(order_id: int) -> bool:
    """Delete one work order and report whether a record was removed."""
    initialise_work_orders()
    with _connection() as connection:
        cursor = connection.execute("DELETE FROM work_orders WHERE order_id = ?", (order_id,))
        return cursor.rowcount > 0


def update_work_order(order_id: int, priority: str, status: str) -> None:
    """Persist a queue item's editable priority and status."""
    if priority not in VALID_PRIORITIES or status not in VALID_STATUSES:
        raise ValueError("Invalid priority or status.")
    initialise_work_orders()
    with _connection() as connection:
        connection.execute(
            "UPDATE work_orders SET priority = ?, status = ?, updated_at = ?, completed_at = CASE WHEN ? = 'Closed' THEN COALESCE(completed_at, ?) ELSE completed_at END WHERE order_id = ?",
            (priority, status, datetime.now().isoformat(timespec="seconds"), status, datetime.now().isoformat(timespec="seconds") if status == "Closed" else None, order_id),
        )


def _next_due(current: date, frequency: str) -> date:
    if frequency not in VALID_FREQUENCIES:
        raise ValueError("Invalid maintenance frequency.")
    if frequency == "Daily":
        return current + timedelta(days=1)
    if frequency == "Weekly":
        return current + timedelta(weeks=1)
    if frequency == "Monthly":
        month = current.month % 12 + 1
        year = current.year + (current.month // 12)
        return current.replace(year=year, month=month, day=min(current.day, calendar.monthrange(year, month)[1]))
    if frequency == "Quarterly":
        month_index = current.month - 1 + 3
        year, month_zero = current.year + month_index // 12, month_index % 12
        month = month_zero + 1
        return current.replace(year=year, month=month, day=min(current.day, calendar.monthrange(year, month)[1]))
    year = current.year + 1
    return current.replace(year=year, day=min(current.day, calendar.monthrange(year, current.month)[1]))


def create_schedule(product_id: str, title: str, description: str, frequency: str, next_due_date: str, technician: str = "") -> int:
    if frequency not in VALID_FREQUENCIES:
        raise ValueError("Invalid maintenance frequency.")
    date.fromisoformat(next_due_date)
    initialise_work_orders()
    now = datetime.now().isoformat(timespec="seconds")
    with _connection() as connection:
        cursor = connection.execute(
            "INSERT INTO maintenance_schedules (product_id, title, description, frequency, next_due_date, technician, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (product_id, title.strip(), description.strip(), frequency, next_due_date, technician.strip(), now, now),
        )
        return int(cursor.lastrowid)


def get_schedules(active_only: bool = False) -> pd.DataFrame:
    initialise_work_orders()
    where = "WHERE active = 1" if active_only else ""
    with _connection() as connection:
        return pd.read_sql_query(f"SELECT * FROM maintenance_schedules {where} ORDER BY next_due_date, product_id", connection)


def get_checklist(schedule_id: int) -> pd.DataFrame:
    initialise_work_orders()
    with _connection() as connection:
        return pd.read_sql_query("SELECT * FROM maintenance_checklists WHERE schedule_id = ? AND active = 1 ORDER BY checklist_id", connection, params=(schedule_id,))


def get_schedule_work_orders(schedule_id: int) -> pd.DataFrame:
    initialise_work_orders()
    with _connection() as connection:
        return pd.read_sql_query("SELECT * FROM work_orders WHERE schedule_id = ? ORDER BY due_date DESC, created_at DESC", connection, params=(schedule_id,))


def add_checklist_item(schedule_id: int, item: str, required: bool = True) -> None:
    if not item.strip():
        raise ValueError("Checklist item cannot be empty.")
    initialise_work_orders()
    with _connection() as connection:
        connection.execute("INSERT INTO maintenance_checklists (schedule_id, item, required) VALUES (?, ?, ?)", (schedule_id, item.strip(), int(required)))


def set_checklist_item(work_order_id: int, checklist_id: int, completed: bool) -> None:
    initialise_work_orders()
    with _connection() as connection:
        connection.execute(
            "INSERT INTO maintenance_checklist_results (work_order_id, checklist_id, completed, completed_at) VALUES (?, ?, ?, ?) ON CONFLICT(work_order_id, checklist_id) DO UPDATE SET completed = excluded.completed, completed_at = excluded.completed_at",
            (work_order_id, checklist_id, int(completed), datetime.now().isoformat(timespec="seconds") if completed else None),
        )


def required_checklist_complete(work_order_id: int) -> bool:
    initialise_work_orders()
    with _connection() as connection:
        pending = connection.execute(
            "SELECT COUNT(*) FROM maintenance_checklists c JOIN work_orders w ON w.schedule_id = c.schedule_id LEFT JOIN maintenance_checklist_results r ON r.checklist_id = c.checklist_id AND r.work_order_id = w.order_id WHERE w.order_id = ? AND c.required = 1 AND c.active = 1 AND COALESCE(r.completed, 0) = 0",
            (work_order_id,),
        ).fetchone()[0]
    return pending == 0


def get_checklist_progress(work_order_id: int) -> pd.DataFrame:
    initialise_work_orders()
    with _connection() as connection:
        return pd.read_sql_query(
            "SELECT c.checklist_id, c.item, c.required, COALESCE(r.completed, 0) AS completed FROM maintenance_checklists c JOIN work_orders w ON w.schedule_id = c.schedule_id LEFT JOIN maintenance_checklist_results r ON r.checklist_id = c.checklist_id AND r.work_order_id = w.order_id WHERE w.order_id = ? AND c.active = 1 ORDER BY c.checklist_id",
            connection,
            params=(work_order_id,),
        )


def generate_due_work_orders(as_of: date | None = None) -> int:
    initialise_work_orders()
    as_of = as_of or date.today()
    created = 0
    with _connection() as connection:
        schedules = connection.execute("SELECT * FROM maintenance_schedules WHERE active = 1 AND next_due_date <= ?", (as_of.isoformat(),)).fetchall()
        for schedule in schedules:
            existing = connection.execute("SELECT 1 FROM work_orders WHERE schedule_id = ? AND due_date = ?", (schedule["schedule_id"], schedule["next_due_date"])).fetchone()
            if existing:
                continue
            now = datetime.now().isoformat(timespec="seconds")
            cursor = connection.execute(
                "INSERT INTO work_orders (product_id, failure_reason, priority, status, recommended_action, created_at, updated_at, schedule_id, technician, due_date, work_order_type) VALUES (?, ?, 'Medium', 'Open', ?, ?, ?, ?, ?, ?, 'Preventive')",
                (schedule["product_id"], schedule["title"], schedule["description"] or "Complete the scheduled preventive maintenance checklist.", now, now, schedule["schedule_id"], schedule["technician"], schedule["next_due_date"]),
            )
            next_date = _next_due(date.fromisoformat(schedule["next_due_date"]), schedule["frequency"])
            connection.execute("UPDATE maintenance_schedules SET next_due_date = ?, updated_at = ? WHERE schedule_id = ?", (next_date.isoformat(), now, schedule["schedule_id"]))
            created += 1
    return created


def get_maintenance_history() -> pd.DataFrame:
    initialise_work_orders()
    with _connection() as connection:
        return pd.read_sql_query("SELECT * FROM maintenance_history ORDER BY completed_at DESC", connection)


def record_maintenance_completion(order_id: int, technician: str, notes: str) -> None:
    initialise_work_orders()
    if not required_checklist_complete(order_id):
        raise ValueError("Complete all required checklist items before closing this work order.")
    now = datetime.now().isoformat(timespec="seconds")
    with _connection() as connection:
        order = connection.execute("SELECT * FROM work_orders WHERE order_id = ?", (order_id,)).fetchone()
        if not order:
            raise ValueError("Work order not found.")
        connection.execute("UPDATE work_orders SET status = 'Closed', technician = ?, completed_at = ?, maintenance_notes = ?, updated_at = ? WHERE order_id = ?", (technician.strip(), now, notes.strip(), now, order_id))
        connection.execute("INSERT INTO maintenance_history (work_order_id, schedule_id, product_id, technician, completed_at, notes) VALUES (?, ?, ?, ?, ?, ?)", (order_id, order["schedule_id"], order["product_id"], technician.strip(), now, notes.strip()))
