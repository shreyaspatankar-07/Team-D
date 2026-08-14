"""
pages/login.py — Login page for the Machine Failure Analysis Platform.

Theme-adaptive design:
  - No forced dark background override; Streamlit's selected theme controls it.
  - Card uses var(--secondary-background-color) so it adapts automatically.
  - Text elements use inherited/theme colors (no hardcoded light/dark values).
  - Blue accent (button, icon, borders) works on both light and dark backgrounds.
  - Interactive widgets remain plain native Streamlit components.
"""

import streamlit as st
from utils import auth


# ── CSS — theme-adaptive ──────────────────────────────────────────────────────

_CSS = """
<style>
/* ── Sidebar (always hidden on login page) ── */
[data-testid="stSidebar"]                 { display: none !important; }
[data-testid="stSidebarCollapsedControl"] { display: none !important; }

/* ── Top Header (transparent to remove white strip) ── */
[data-testid="stHeader"]                  { background: transparent !important; }
header                                    { background: transparent !important; }

/* ── Dark navy background — always applied, regardless of Streamlit theme.
      In light theme: dark bg + white card = premium mixed look.
      In dark  theme: dark bg + dark card  = consistent dark look.      ── */
.stApp {
    background: linear-gradient(135deg,
        #060d1a 0%, #0a1628 40%, #0f1f3d 100%) !important;
}

/* Subtle dot-grid overlay */
.stApp::before {
    content  : '';
    position : fixed;
    inset    : 0;
    background-image :
        radial-gradient(circle, rgba(59,130,246,0.18) 1px, transparent 1px);
    background-size  : 36px 36px;
    pointer-events   : none;
    z-index          : 0;
}

/* Soft blue radial glow behind the card */
.stApp::after {
    content   : '';
    position  : fixed;
    top       : 50%;
    left      : 50%;
    transform : translate(-50%, -50%);
    width     : 700px;
    height    : 700px;
    background: radial-gradient(circle,
        rgba(59,130,246,0.07) 0%, transparent 68%);
    pointer-events: none;
    z-index   : 0;
}

/* ── Page padding ── */
.main .block-container {
    padding-top    : 5vh !important;
    padding-bottom : 0   !important;
}

/* ── Card — transparent to match the dark blue background ── */
[data-testid="stVerticalBlockBorderWrapper"] {
    background    : transparent                           !important;
    border        : 1px solid rgba(59,130,246,0.28)       !important;
    border-radius : 20px                                  !important;
    padding       : 44px 40px 36px 40px                  !important;
    box-shadow    :
        0  2px  8px rgba(0,0,0,0.25),
        0 24px 64px rgba(0,0,0,0.45),
        0  0   0 1px rgba(59,130,246,0.08)                !important;
}

/* ── All heading/paragraph text inside the card — bright white for contrast ── */
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMarkdownContainer"] h1,
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMarkdownContainer"] h2,
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMarkdownContainer"] h3,
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMarkdownContainer"] h4,
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMarkdownContainer"] p {
    color : #ffffff !important;
}

/* ── Caption / subtitle ── */
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stCaptionContainer"] p {
    color : #cbd5e1 !important;
}

/* ── Input labels ── */
[data-testid="stTextInput"] label p {
    color          : #cbd5e1   !important;
    font-size      : 0.70rem   !important;
    font-weight    : 700       !important;
    text-transform : uppercase !important;
    letter-spacing : 0.10em   !important;
}

/* ── Inputs ── */
[data-testid="stTextInput"] input {
    background    : #f8fafc                         !important;
    color         : #1e293b                         !important;
    border        : 1px solid rgba(59,130,246,0.22) !important;
    border-radius : 10px                            !important;
    font-size     : 0.92rem                         !important;
    padding       : 11px 15px                       !important;
    transition    : border-color 0.2s, box-shadow 0.2s !important;
}
[data-testid="stTextInput"] input::placeholder { color: #94a3b8 !important; }
[data-testid="stTextInput"] input:focus {
    border-color : #3b82f6                         !important;
    box-shadow   : 0 0 0 3px rgba(59,130,246,0.18) !important;
    outline      : none                            !important;
}

/* ── Sign In button ── */
[data-testid="stButton"] > button {
    background    : linear-gradient(135deg, #1d4ed8 0%, #3b82f6 100%) !important;
    border        : none                                               !important;
    border-radius : 10px                                               !important;
    color         : #ffffff                                            !important;
    font-weight   : 700                                                !important;
    font-size     : 0.88rem                                            !important;
    letter-spacing: 0.07em                                             !important;
    text-transform: uppercase                                          !important;
    padding       : 12px 0                                             !important;
    box-shadow    :
        0 4px 18px rgba(59,130,246,0.45),
        inset 0 1px 0 rgba(255,255,255,0.15)                          !important;
    transition    : all 0.18s ease                                     !important;
}
[data-testid="stButton"] > button:hover {
    background : linear-gradient(135deg, #1e40af 0%, #2563eb 100%) !important;
    box-shadow : 0 6px 28px rgba(59,130,246,0.60)                  !important;
    transform  : translateY(-1px)                                  !important;
}
[data-testid="stButton"] > button:active {
    transform  : translateY(0)                     !important;
    box-shadow : 0 2px 10px rgba(59,130,246,0.40) !important;
}

/* ── Divider ── */
[data-testid="stDivider"] hr {
    margin: 2px 0 14px 0 !important;
}

/* ── Error alert ── */
[data-testid="stAlert"] {
    border-radius: 10px !important;
}
</style>
"""

# ── Static brand block ────────────────────────────────────────────────────────
# No hardcoded dark/light text colors — inherits current theme text color.
# Only the blue accent (icon, badge) is hardcoded; blue works on both themes.

_BRAND = """
<div style="text-align:center; margin-bottom:4px;">

  <div style="margin-bottom:14px;">
    <svg xmlns="http://www.w3.org/2000/svg" width="50" height="50"
         viewBox="0 0 24 24" fill="none" stroke="#3b82f6"
         stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="12" r="3"/>
      <path d="M12 1v3M12 20v3M4.22 4.22l2.12 2.12M17.66 17.66l2.12 2.12
               M1 12h3M20 12h3M4.22 19.78l2.12-2.12M17.66 6.34l2.12-2.12"/>
      <circle cx="12" cy="12" r="7" stroke="rgba(59,130,246,0.20)"/>
    </svg>
  </div>

  <div style="font-size:1.45rem; font-weight:900; color:#ffffff;
              letter-spacing:-0.025em; line-height:1.2;">
    Machine Failure
  </div>
  <div style="font-size:1.45rem; font-weight:900; color:#ffffff;
              letter-spacing:-0.025em; line-height:1.2; margin-bottom:12px;">
    Analysis Platform
  </div>

  <span style="display:inline-block; font-size:0.60rem;
               text-transform:uppercase; letter-spacing:0.10em;
               color:#3b82f6;
               background:rgba(59,130,246,0.10);
               border:1px solid rgba(59,130,246,0.22);
               border-radius:999px; padding:3px 14px;">
    AI4I 2020 &nbsp;&middot;&nbsp; Predictive Maintenance
  </span>
</div>
"""

# ── Footer ────────────────────────────────────────────────────────────────────

_FOOTER = """
<p style="text-align:center; font-size:0.60rem;
          letter-spacing:0.05em; margin:0; color:#94a3b8;">
  Infosys &nbsp;&middot;&nbsp; Machine Failure Analysis Platform
</p>
"""


# ── Page render ───────────────────────────────────────────────────────────────

def render() -> None:
    """Render the Login page."""

    st.markdown(_CSS, unsafe_allow_html=True)

    _, col, _ = st.columns([1, 1.15, 1])

    with col:
        with st.container(border=True):

            # Icon + brand (static HTML — no interactive elements inside)
            st.markdown(_BRAND, unsafe_allow_html=True)

            st.divider()

            # Welcome message — custom HTML for styling and center alignment
            st.markdown(
                """
                <div style="text-align: center;">
                    <h3 style="color: #ffffff !important; margin-bottom: 4px; padding-bottom: 0; margin-top: 0;">Welcome Back</h3>
                    <p style="color: #ffffff !important; font-size: 0.90rem; margin-top: 0; padding-top: 0;">Sign in to access the Machine Failure Analysis Platform</p>
                </div>
                """,
                unsafe_allow_html=True
            )

            st.write("")

            # ── Username & password ───────────────────────────────────────────
            username = st.text_input(
                "Username",
                placeholder="Enter your username",
                key="login_username",
            )
            password = st.text_input(
                "Password",
                placeholder="Enter your password",
                type="password",
                key="login_password",
            )

            st.write("")

            # ── Sign In ───────────────────────────────────────────────────────
            if st.button("Sign In", use_container_width=True, key="btn_sign_in"):
                u = username.strip()
                if auth.verify_credentials(u, password):
                    st.session_state["logged_in_user"] = u
                    st.session_state["page"] = "dashboard"
                    st.rerun()
                else:
                    st.error("Username or password is incorrect.")

            st.write("")

            st.markdown(_FOOTER, unsafe_allow_html=True)
