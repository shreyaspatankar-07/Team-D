"""
utils/styles.py — Global CSS (sidebar + native Streamlit components only) + UI helpers.

DESIGN PRINCIPLE: All custom HTML cards use INLINE STYLES only, never CSS classes.
CSS classes here target Streamlit's own native components (sidebar, buttons, metrics, etc.)
"""

import streamlit as st

# ── Colour Palette ────────────────────────────────────────────────────────────

COLORS = {
    "blue":   "#3b82f6",
    "red":    "#ef4444",
    "green":  "#22c55e",
    "amber":  "#f59e0b",
    "purple": "#8b5cf6",
    "slate":  "#64748b",
    "navy":   "#1e3a5f",
    "dark":   "#1e293b",
}

PALETTE = [COLORS["blue"], COLORS["red"], COLORS["green"], COLORS["amber"], COLORS["purple"]]

# ── Badge background helper ───────────────────────────────────────────────────

def _badge_colors(kind: str) -> tuple:
    """Return (bg, text_color) for a badge kind."""
    return {
        "success": ("#dcfce7", "#15803d"),
        "warning": ("#fef3c7", "#92400e"),
        "danger":  ("#fee2e2", "#b91c1c"),
        "info":    ("#dbeafe", "#1e40af"),
        "neutral": ("#f1f5f9", "#475569"),
    }.get(kind, ("#dbeafe", "#1e40af"))


# ── CSS String ────────────────────────────────────────────────────────────────
# Only targets Streamlit's own native components, never custom HTML classes.

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body, [class*="css"] {
    font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
}

/* ═══════════ HIDE STREAMLIT MULTIPAGE NAV ══════════════════════════════════ */
[data-testid="stSidebarNav"] { display: none !important; }
section[data-testid="stSidebarNav"] { display: none !important; }

/* ═══════════ SIDEBAR ═══════════════════════════════════════════════════════ */

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a0f1e 0%, #111827 40%, #0d1424 100%) !important;
    border-right: 1px solid rgba(255,255,255,0.06) !important;
}

[data-testid="stSidebar"] * { color: #cbd5e1 !important; }

/* Nav buttons */
[data-testid="stSidebar"] [data-testid="stButton"] > button {
    width: 100% !important;
    text-align: left !important;
    justify-content: flex-start !important;
    border-radius: 8px !important;
    margin: 2px 0 !important;
    padding: 10px 14px !important;
    font-size: 0.88rem !important;
    transition: all 0.15s ease !important;
    border: none !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
}

[data-testid="stSidebar"] [data-testid="stButton"] > button[kind="primary"] {
    background: linear-gradient(90deg, rgba(59,130,246,0.35) 0%, rgba(59,130,246,0.1) 100%) !important;
    border-left: 3px solid #3b82f6 !important;
    color: #ffffff !important;
    font-weight: 700 !important;
}

[data-testid="stSidebar"] [data-testid="stButton"] > button[kind="secondary"] {
    background: transparent !important;
    color: rgba(203,213,225,0.75) !important;
    font-weight: 400 !important;
}

[data-testid="stSidebar"] [data-testid="stButton"] > button[kind="secondary"]:hover {
    background: rgba(255,255,255,0.06) !important;
    color: #ffffff !important;
}

/* Selectbox & Multiselect in sidebar */
[data-testid="stSidebar"] .stSelectbox > div > div,
[data-testid="stSidebar"] .stMultiSelect > div > div {
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(255,255,255,0.13) !important;
    border-radius: 8px !important;
}

[data-testid="stSidebar"] [data-baseweb="select"] span { color: #e2e8f0 !important; }

/* Multiselect chips — high contrast white on blue */
[data-testid="stSidebar"] [data-baseweb="tag"] {
    background: #2563eb !important;
    color: #ffffff !important;
    border: 1px solid #3b82f6 !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
    font-size: 0.75rem !important;
}

/* Chip close button */
[data-testid="stSidebar"] [data-baseweb="tag"] svg { fill: rgba(255,255,255,0.8) !important; }

/* Radio buttons in sidebar */
[data-testid="stSidebar"] .stRadio > div { gap: 4px !important; }
[data-testid="stSidebar"] .stRadio label { color: #cbd5e1 !important; font-size: 0.85rem !important; }
[data-testid="stSidebar"] .stRadio input:checked + div { border-color: #3b82f6 !important; }
[data-testid="stSidebar"] .stRadio input:checked + div + div { color: #93c5fd !important; }

/* Sidebar text */
[data-testid="stSidebar"] .stMarkdown p { color: #94a3b8 !important; font-size: 0.82rem !important; }
[data-testid="stSidebar"] .stMarkdown label { color: #94a3b8 !important; }

/* ═══════════ MAIN CONTENT ══════════════════════════════════════════════════ */

.main .block-container {
    padding-top: 1.5rem;
    padding-bottom: 3rem;
    background-color: #f8fafc;
}

/* ═══════════ KPI METRIC CARDS ══════════════════════════════════════════════ */

[data-testid="metric-container"] {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 12px !important;
    padding: 18px 20px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
}

[data-testid="metric-container"] [data-testid="stMetricLabel"] {
    font-size: 0.73rem !important;
    font-weight: 700 !important;
    color: #64748b !important;
    text-transform: uppercase !important;
    letter-spacing: 0.07em !important;
}

[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-size: 1.85rem !important;
    font-weight: 800 !important;
    color: #1e293b !important;
}

[data-testid="metric-container"] [data-testid="stMetricDelta"] {
    font-size: 0.78rem !important;
    font-weight: 500 !important;
}

/* ═══════════ DATAFRAME ═════════════════════════════════════════════════════ */

[data-testid="stDataFrame"] {
    border-radius: 10px !important;
    border: 1px solid #e2e8f0 !important;
    overflow: hidden !important;
}

/* ═══════════ TABS ══════════════════════════════════════════════════════════ */

[data-testid="stTab"] button { font-weight: 600 !important; font-size: 0.85rem !important; }
[data-testid="stTab"] button[aria-selected="true"] { color: #3b82f6 !important; }

/* ═══════════ EXPANDER ══════════════════════════════════════════════════════ */

[data-testid="stExpander"] {
    border: 1px solid #e2e8f0 !important;
    border-radius: 10px !important;
    overflow: hidden !important;
    background: #ffffff !important;
}

/* ═══════════ CHAT MESSAGES ═════════════════════════════════════════════════ */

[data-testid="stChatMessage"] {
    border: 1px solid #e2e8f0 !important;
    border-radius: 12px !important;
    background: #ffffff !important;
    margin-bottom: 8px !important;
}

/* ═══════════ PROGRESS BAR ══════════════════════════════════════════════════ */

[data-testid="stProgress"] > div > div {
    border-radius: 8px !important;
}
"""


# ── Injection ─────────────────────────────────────────────────────────────────

def inject_css() -> None:
    """Inject the global CSS into the Streamlit app."""
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)


# ── Login-Page CSS ────────────────────────────────────────────────────────────
# Applied only when the login page is active; hides the sidebar completely.

LOGIN_CSS = """
/* Hide sidebar and its collapse control on the login page */
[data-testid="stSidebar"]                { display: none !important; }
[data-testid="stSidebarCollapsedControl"] { display: none !important; }

/* Full-screen dark gradient background */
.stApp {
    background: linear-gradient(135deg, #060d1a 0%, #0a1628 40%, #0f1f3d 100%) !important;
}

/* Remove default padding so the login card centres cleanly */
.main .block-container {
    padding-top: 0 !important;
    padding-bottom: 0 !important;
    max-width: 100% !important;
}
"""


def inject_login_css() -> None:
    """Inject login-page-specific CSS (hides sidebar, sets dark background)."""
    st.markdown(f"<style>{LOGIN_CSS}</style>", unsafe_allow_html=True)


# ── UI Helper Functions (all using inline styles — no CSS classes) ─────────────

def page_header(icon: str, title: str, subtitle: str) -> None:
    """Render a full-width gradient page header banner."""
    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg, #1e3a5f 0%, #1e40af 60%, #1d4ed8 100%);
                    border-radius:16px; padding:28px 32px; margin-bottom:24px;
                    color:white; position:relative; overflow:hidden;">
            <h1 style="font-size:1.55rem; font-weight:800; color:#ffffff; margin:0 0 8px 0; line-height:1.2;">
                {icon} {title}
            </h1>
            <p style="color:rgba(255,255,255,0.72); font-size:0.88rem; margin:0;">
                {subtitle}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_header(title: str, desc: str = "") -> None:
    """Render a styled section header with a left accent bar (inline styles only)."""
    desc_html = f'<p style="color:#64748b; font-size:0.8rem; margin:2px 0 0 0;">{desc}</p>' if desc else ""
    st.markdown(
        f"""
        <div style="border-left:4px solid #3b82f6; padding:2px 0 2px 14px; margin:20px 0 14px 0;">
            <h2 style="color:#1e293b; font-size:1.05rem; font-weight:700; margin:0 0 2px 0;
                       font-family:'Inter',sans-serif;">
                {title}
            </h2>
            {desc_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def observation(text: str) -> None:
    """Render an observation/insight box (inline styles)."""
    st.markdown(
        f"""
        <div style="background:#eff6ff; border-left:4px solid #3b82f6;
                    border-radius:0 8px 8px 0; padding:12px 16px; margin-top:8px;
                    font-size:0.83rem; color:#1e3a5f; line-height:1.6;">
            {text}
        </div>
        """,
        unsafe_allow_html=True,
    )


def divider() -> None:
    """Render a subtle horizontal rule."""
    st.markdown(
        '<hr style="border:none; border-top:1px solid #e2e8f0; margin:16px 0;">',
        unsafe_allow_html=True,
    )


def badge(text: str, kind: str = "info") -> str:
    """Return an inline-style HTML badge string. kind: success|warning|danger|info|neutral"""
    bg, tc = _badge_colors(kind)
    return (
        f'<span style="background:{bg}; color:{tc}; padding:4px 12px; border-radius:9999px; '
        f'font-size:0.72rem; font-weight:700; letter-spacing:0.05em; text-transform:uppercase; '
        f'white-space:nowrap; display:inline-block;">{text}</span>'
    )


def status_badge_html(has_failed: bool, category: str) -> str:
    """Return inline HTML badge for machine status."""
    if has_failed:
        bg, tc, txt = "#fee2e2", "#b91c1c", "⚠ Failed"
    elif category == "Warning":
        bg, tc, txt = "#fef3c7", "#92400e", "⚡ Warning"
    elif category in ("Good", "Excellent"):
        bg, tc, txt = "#dcfce7", "#15803d", "✓ Healthy"
    else:
        bg, tc, txt = "#fee2e2", "#b91c1c", "Critical"
    return (
        f'<span style="background:{bg}; color:{tc}; padding:4px 12px; border-radius:9999px; '
        f'font-size:0.75rem; font-weight:700; text-transform:uppercase; letter-spacing:0.04em; '
        f'display:inline-block;">{txt}</span>'
    )


def health_progress_html(score: int, category: str, color: str) -> str:
    """Return inline-style HTML for a health progress bar."""
    return f"""
    <div style="margin:4px 0 10px 0;">
        <div style="background:#f1f5f9; border-radius:8px; overflow:hidden; height:10px;">
            <div style="background:{color}; width:{score}%; height:100%; border-radius:8px;
                        transition:width 0.3s ease;"></div>
        </div>
        <div style="display:flex; justify-content:space-between; margin-top:4px; font-size:0.72rem;">
            <span style="color:#94a3b8;">0</span>
            <span style="font-weight:700; color:{color};">{score}/100 &mdash; {category}</span>
            <span style="color:#94a3b8;">100</span>
        </div>
    </div>
    """


def sensor_status_badge_html(status: str, color: str) -> str:
    """Return inline-style HTML pill badge for a sensor status."""
    bg_map = {
        "#22c55e": "#dcfce7",
        "#f59e0b": "#fef3c7",
        "#ef4444": "#fee2e2",
        "#3b82f6": "#dbeafe",
        "#94a3b8": "#f1f5f9",
    }
    bg = bg_map.get(color, "#f1f5f9")
    tc = color if color != "#94a3b8" else "#475569"
    return (
        f'<span style="background:{bg}; color:{tc}; padding:2px 9px; border-radius:9999px; '
        f'font-size:0.68rem; font-weight:700; text-transform:uppercase; letter-spacing:0.04em; '
        f'white-space:nowrap;">{status}</span>'
    )
