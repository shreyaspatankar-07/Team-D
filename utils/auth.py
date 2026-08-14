"""
utils/auth.py — Lightweight session-based authentication for the
               Machine Failure Analysis Platform.

Credentials are stored in the 'users' table in work_orders.db and
verified via utils.db.verify_user_credentials().

Auth state is stored in st.session_state["logged_in_user"].
"""

import streamlit as st

# ── Supported Users ───────────────────────────────────────────────────────────

# Maps user_id → display label shown in the sidebar badge.
# Keep in sync with the 'role' column values seeded in db.py.
USERS: dict[str, str] = {
    "admin":    "Admin",
    "employee": "Employee",
}


# ── Auth Helpers ──────────────────────────────────────────────────────────────

def is_logged_in() -> bool:
    """Return True if a user is currently authenticated."""
    return bool(st.session_state.get("logged_in_user"))


def get_current_user() -> str | None:
    """Return the logged-in user ID (username), or None if not authenticated."""
    return st.session_state.get("logged_in_user")


def verify_credentials(username: str, password: str) -> bool:
    """
    Verify username and password against the database.
    Returns True if both are correct; False otherwise.
    Does NOT reveal which field was wrong.
    """
    from utils.db import verify_user_credentials  # local import to avoid circular deps
    result = verify_user_credentials(username, password)
    return result is not None


def login(user_id: str) -> None:
    """
    Store the authenticated user_id (username) in session state
    and navigate to the dashboard.
    """
    st.session_state["logged_in_user"] = user_id
    st.session_state["page"] = "dashboard"


def logout() -> None:
    """
    Clear the current user session and reset the page to 'dashboard'
    so the next login lands on the main dashboard.
    """
    st.session_state.pop("logged_in_user", None)
    st.session_state["page"] = "dashboard"
