"""Persistent, local work-order storage for recorded machine failures."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
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


def get_work_orders(status: str = "All", priority: str = "All") -> pd.DataFrame:
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
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with _connection() as connection:
        return pd.read_sql_query(
            f"SELECT * FROM work_orders {where} ORDER BY CASE status WHEN 'Open' THEN 0 WHEN 'In Progress' THEN 1 ELSE 2 END, created_at DESC",
            connection,
            params=values,
        )


def update_work_order(order_id: int, priority: str, status: str) -> None:
    """Persist a queue item's editable priority and status."""
    if priority not in VALID_PRIORITIES or status not in VALID_STATUSES:
        raise ValueError("Invalid priority or status.")
    initialise_work_orders()
    with _connection() as connection:
        connection.execute(
            "UPDATE work_orders SET priority = ?, status = ?, updated_at = ? WHERE order_id = ?",
            (priority, status, datetime.now().isoformat(timespec="seconds"), order_id),
        )
