"""
SAATHI ONE — Autonomous Multilingual AI Business Receptionist Platform
TWO-WINDOW ARCHITECTURE:
  Window 1 (Left)  → Business Owner Panel (Setup, Services, Hours, Demo Number)
  Window 2 (Right) → Continuous Hands-Free Phone Call (Talk naturally, AI responds in voice, 1 End Call button)

Powered by Groq High-Speed LLaMA + MongoDB + Native Web Voice Engine.
"""

import sys
import os
import time
from datetime import datetime, timezone
from bson import ObjectId
import streamlit as st
import streamlit.components.v1 as components

sys.path.insert(0, os.path.dirname(__file__))

from config import (
    BUSINESS_TYPES,
    SUPPORTED_LANGUAGES,
    DEFAULT_WORKING_HOURS,
    RESOURCE_TYPE_LABELS,
    GROQ_API_KEY,
    GROQ_MODEL,
)
from database import (
    ensure_indexes,
    check_connection,
    businesses_col,
    services_col,
    resources_col,
    bookings_col,
    customers_col,
    ai_employees_col,
    calls_col,
    tool_executions_col,
    conversations_col,
)
from models import (
    new_business,
    new_service,
    new_resource,
    new_ai_employee,
)
from auth import (
    init_session,
    register_user,
    login_user,
    set_authenticated,
    logout,
    require_auth,
    get_current_user_id,
    get_current_business_id,
    set_current_business,
)
from telephony.provider import demo_provider
from ui.styles import get_main_css
from ui.components import (
    page_header,
    metric_card,
    status_badge,
    activity_log_display,
    conversation_display,
    sidebar_brand_card,
    empty_state,
    section_header,
    divider,
)

# ═══════════════════════════════════════════════════════════════
# STREAMLIT CONFIG
# ═══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="SAATHI ONE — AI Business Receptionist",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(get_main_css(), unsafe_allow_html=True)
init_session()

@st.cache_resource(show_spinner=False)
def _start_api_server():
    """Start FastAPI server as a subprocess — once per Streamlit process lifetime.
    Works locally and on Streamlit Cloud (no separate terminal needed).
    """
    import subprocess, time, sys
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api:app",
         "--host", "127.0.0.1", "--port", "8000",
         "--log-level", "error"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(2)   # Give it a moment to boot
    return proc

@st.cache_resource(show_spinner=False)
def _init_db_once():
    """Run DB setup exactly once per server process — not on every rerun."""
    ensure_indexes()
    return True

_start_api_server()
_init_db_once()


# ═══════════════════════════════════════════════════════════════
# INTRO SCREEN & AUTHENTICATION
# ═══════════════════════════════════════════════════════════════
def render_auth():
    # Futuristic Hologram Splash Animation
    st.markdown("""
    <div class="intro-splash-container">
        <div class="hologram-orb">
            <div class="hologram-ring"></div>
            <div class="hologram-ring-2"></div>
            🎙️
        </div>
        <span class="brand-badge">⚡ SAATHI ONE NEURAL PLATFORM</span>
        <h1 class="shimmer-title">SAATHI ONE</h1>
        <p class="pulse-subtitle">One Business · One Number · One Autonomous AI Employee</p>
        <div class="loader-bar-wrap"><div class="loader-bar-fill"></div></div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.3, 1])
    with col2:
        if not check_connection():
            st.error("⚠️ Cannot connect to MongoDB Atlas. Check your internet connection or MONGODB_URI in .env")
            st.stop()

        tab_login, tab_signup = st.tabs(["🔑 SIGN IN", "✨ CREATE ACCOUNT"])

        with tab_login:
            with st.form("login_form"):
                email = st.text_input("Business Email", key="login_email", placeholder="owner@business.com")
                password = st.text_input("Password", type="password", key="login_password")
                submitted = st.form_submit_button("SIGN IN TO DASHBOARD ➜", use_container_width=True)
                if submitted:
                    if email and password:
                        user = login_user(email.strip(), password)
                        if user:
                            set_authenticated(user)
                            biz = businesses_col().find_one({"owner_id": str(user["_id"])})
                            if biz:
                                set_current_business(biz)
                            st.rerun()
                        else:
                            st.error("❌ Invalid email or password. Check your credentials and try again.")
                            st.caption("Tip: Passwords are case-sensitive. Try creating a new account if you've forgotten yours.")
                    else:
                        st.warning("Please enter your email and password.")

        with tab_signup:
            with st.form("signup_form"):
                name = st.text_input("Owner Full Name", key="signup_name", placeholder="e.g. Yash Patil")
                email = st.text_input("Business Email", key="signup_email", placeholder="owner@business.com")
                password = st.text_input("Create Password (min 6 chars)", type="password", key="signup_password")
                if st.form_submit_button("CREATE ACCOUNT & DEPLOY AI ➜", use_container_width=True):
                    if name and email and password:
                        if len(password) < 6:
                            st.error("Password must be at least 6 characters.")
                        else:
                            user = register_user(email, password, name)
                            if user:
                                set_authenticated(user)
                                st.rerun()
                            else:
                                st.error("Email already registered.")
                    else:
                        st.warning("All fields are required.")


# ═══════════════════════════════════════════════════════════════
# TOP NAVBAR
# ═══════════════════════════════════════════════════════════════
def render_topbar():
    biz_id = get_current_business_id()
    biz_name = st.session_state.get("business_name", "") if biz_id else ""
    demo_num = demo_provider.get_business_number(biz_id) if biz_id else ""

    cols = st.columns([3.5, 1.2, 1.2, 1])
    with cols[0]:
        st.markdown("""
        <div style="display:flex;align-items:center;gap:12px;padding:4px 0">
            <span style="font-size:1.6rem">🎙️</span>
            <div>
                <div style="font-weight:800;font-size:1.25rem;letter-spacing:-0.03em;color:#fff">SAATHI ONE</div>
                <div style="color:var(--text-muted);font-size:0.78rem">Autonomous AI Business Receptionist · Hands-Free Multilingual Engine</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with cols[1]:
        if biz_name:
            st.markdown(f'<div style="text-align:right;font-size:0.84rem;color:#f8fafc;padding-top:10px">🏢 <strong>{biz_name}</strong></div>', unsafe_allow_html=True)
    with cols[2]:
        if demo_num:
            st.markdown(f'<div style="text-align:center;font-size:0.85rem;font-family:JetBrains Mono,monospace;color:#c4b5fd;font-weight:700;padding-top:10px">📞 {demo_num}</div>', unsafe_allow_html=True)
    with cols[3]:
        if st.button("🚪 Sign Out", key="top_logout_btn", use_container_width=True):
            logout()
            st.rerun()

    st.markdown('<hr style="border:none;border-top:1px solid var(--border-subtle);margin:6px 0 16px 0">', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# MAIN 2-WINDOW LAYOUT
# ═══════════════════════════════════════════════════════════════
def render_main():
    render_topbar()

    tab_demo, tab_bookings, tab_telemetry = st.tabs([
        "🎙️  LIVE TWO-WINDOW DEMO (Owner & Client Call)",
        "📅  Live Bookings & Client Registry",
        "📊  Call Audit Logs & Telemetry",
    ])

    with tab_demo:
        _render_two_windows()
    with tab_bookings:
        _render_bookings_view()
    with tab_telemetry:
        _render_telemetry_view()


def _render_two_windows():
    biz_id = get_current_business_id()
    left, divider_col, right = st.columns([1, 0.03, 1.2])

    # ────────────────────────────────────────────────────────────
    # WINDOW 1 (LEFT): BUSINESS OWNER PANEL
    # ────────────────────────────────────────────────────────────
    with left:
        st.markdown("""
        <div style="background:linear-gradient(135deg, rgba(139,92,246,0.12) 0%, rgba(99,102,241,0.06) 100%);
                    border:1px solid rgba(139,92,246,0.3);border-radius:14px;padding:16px 18px 12px 18px;margin-bottom:16px">
            <div style="display:flex;align-items:center;justify-content:space-between">
                <div style="display:flex;align-items:center;gap:10px">
                    <span style="font-size:1.4rem">🏢</span>
                    <div>
                        <div style="font-weight:800;font-size:1.1rem;color:#fff">Window 1: Business Owner Panel</div>
                        <div style="font-size:0.75rem;color:var(--text-muted)">Configure your business → Get Demo Number</div>
                    </div>
                </div>
                <span class="status-pill pill-active">Owner</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if not biz_id:
            _render_owner_onboarding()
        else:
            _render_owner_dashboard(biz_id)

    # ────────────────────────────────────────────────────────────
    # DIVIDER
    # ────────────────────────────────────────────────────────────
    with divider_col:
        st.markdown('<div style="border-left:1px solid var(--border-subtle);height:100%;min-height:650px;margin:0 auto"></div>', unsafe_allow_html=True)

    # ────────────────────────────────────────────────────────────
    # WINDOW 2 (RIGHT): CLIENT PHONE CALL INTERFACE
    # ────────────────────────────────────────────────────────────
    with right:
        st.markdown("""
        <div style="background:linear-gradient(135deg, rgba(6,182,212,0.12) 0%, rgba(16,185,129,0.06) 100%);
                    border:1px solid rgba(6,182,212,0.3);border-radius:14px;padding:16px 18px 12px 18px;margin-bottom:16px">
            <div style="display:flex;align-items:center;justify-content:space-between">
                <div style="display:flex;align-items:center;gap:10px">
                    <span style="font-size:1.4rem">📞</span>
                    <div>
                        <div style="font-weight:800;font-size:1.1rem;color:#fff">Window 2: Client Phone Call Panel</div>
                        <div style="font-size:0.75rem;color:var(--text-muted)">Dial Demo Number → Continuous Hands-Free Call</div>
                    </div>
                </div>
                <span class="status-pill pill-active" style="background:rgba(6,182,212,0.15);color:#67e8f9;border-color:rgba(6,182,212,0.35)">Customer</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        _render_client_handsfree_phone()


# ═══════════════════════════════════════════════════════════════
# OWNER: Onboarding
# ═══════════════════════════════════════════════════════════════
def _render_owner_onboarding():
    st.markdown("""
    <div style="padding:14px;background:rgba(139,92,246,0.08);border:1px solid rgba(139,92,246,0.25);border-radius:10px;margin-bottom:14px;font-size:0.83rem;color:#c4b5fd">
        👋 <strong>Set up your business:</strong> Enter your details below. Once saved, you will immediately receive a <strong>Demo Number</strong> that customers use to call your AI!
    </div>
    """, unsafe_allow_html=True)

    with st.form("new_biz_form"):
        name = st.text_input("Business Name *", placeholder="e.g. Yash Restaurant / Mumbai Royal Barbers")
        btype = st.selectbox("Business Domain * (AI adapts its questions to this domain)", BUSINESS_TYPES)

        c1, c2 = st.columns(2)
        with c1:
            phone = st.text_input("Phone Number", placeholder="+91 98200 12345")
        with c2:
            address = st.text_input("Address / City", placeholder="Bandra West, Mumbai")

        desc = st.text_area(
            "What do you offer? (Description)",
            placeholder="e.g. Fine dining Indian restaurant with table dining, private party bookings, and North Indian delicacies.",
            height=90,
        )
        instructions = st.text_area(
            "Owner Custom Knowledge / FAQs / Policies (AI uses this exact info)",
            placeholder="e.g. Free basement parking. We accept UPI and Cards. Monday closed. 10% discount on orders above ₹1000.",
            height=110,
        )

        if st.form_submit_button("🚀 DEPLOY AI RECEPTIONIST & GET NUMBER ➜", use_container_width=True):
            if not name.strip():
                st.error("Business name is required.")
            else:
                user_id = get_current_user_id()
                biz = new_business(
                    owner_id=user_id, name=name.strip(), business_type=btype,
                    description=desc.strip(), address=address.strip(),
                    phone=phone.strip(), email="", instructions=instructions.strip(),
                )
                result = businesses_col().insert_one(biz)
                biz["_id"] = result.inserted_id
                set_current_business(biz)
                biz_id_str = str(result.inserted_id)

                demo_provider.assign_number(biz_id_str)
                ai_employees_col().insert_one(new_ai_employee(biz_id_str))

                domain_svcs = {
                    "Restaurant": [("Table for 2 (Dinner)", 90, 0), ("Table for 4 (Dinner)", 90, 0), ("Private Dining Hall", 120, 2500)],
                    "Salon": [("Haircut & Styling", 30, 250), ("Facial & Glow", 60, 600), ("Hair Color", 90, 900)],
                    "Barber": [("Haircut", 20, 150), ("Beard Trim & Shape", 15, 100), ("Head Massage", 20, 150)],
                    "Clinic": [("General Physician Consultation", 20, 400), ("Specialist Doctor Consultation", 30, 700)],
                    "Doctor": [("Doctor Consultation", 20, 500), ("Follow-up Consultation", 15, 250)],
                    "Dentist": [("Dental Checkup & X-Ray", 30, 350), ("Teeth Cleaning & Scaling", 45, 800)],
                    "Hotel": [("Deluxe AC Room", 1440, 2500), ("Executive Suite", 1440, 4500)],
                    "Gym": [("Monthly Gym Membership", 0, 1200), ("Personal Trainer Session", 60, 500)],
                    "Consultant": [("1-on-1 Advisory Session", 45, 1500)],
                    "Repair Service": [("Appliance Inspection & Repair", 60, 400)],
                }
                for s_name, dur, price in domain_svcs.get(btype, [("Standard Appointment", 30, 0)]):
                    services_col().insert_one(new_service(biz_id_str, s_name, dur, float(price)))

                st.success(f"🎉 Business '{name}' deployed!")
                st.rerun()


# ═══════════════════════════════════════════════════════════════
# OWNER: Active Dashboard
# ═══════════════════════════════════════════════════════════════
def _render_owner_dashboard(biz_id: str):
    business = businesses_col().find_one({"_id": ObjectId(biz_id)})
    if not business:
        st.session_state.business_id = None
        st.rerun()

    demo_num = demo_provider.get_business_number(biz_id) or "DEMO-9001"
    biz_type = business.get("business_type", "Restaurant")

    # Big Demo Number Banner
    st.markdown(f"""
    <div style="background:linear-gradient(135deg, rgba(139,92,246,0.2) 0%, rgba(99,102,241,0.15) 100%);
                border:1px solid rgba(139,92,246,0.4);border-radius:12px;padding:16px;text-align:center;margin-bottom:14px">
        <div style="font-size:0.72rem;font-weight:700;color:#c4b5fd;letter-spacing:0.08em;text-transform:uppercase">Assigned Demo Phone Number</div>
        <div style="font-family:JetBrains Mono,monospace;font-size:2.2rem;font-weight:800;color:#fff;letter-spacing:0.04em;margin:4px 0">{demo_num}</div>
        <div style="font-size:0.78rem;color:var(--text-muted)">Enter this number in Window 2 on the right to call your AI</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px">
        <span class="status-pill" style="background:rgba(6,182,212,0.12);color:#67e8f9;border-color:rgba(6,182,212,0.3)">🏷️ {biz_type}</span>
        <span class="status-pill pill-active">⚡ AI Receptionist Online</span>
    </div>
    """, unsafe_allow_html=True)

    tab_info, tab_svcs, tab_hours = st.tabs(["📋 Business Info & FAQs", "💼 Services & Pricing", "⏰ Working Hours"])

    with tab_info:
        with st.form("edit_owner_info"):
            name = st.text_input("Business Name", value=business.get("name", ""))
            btype = st.selectbox("Business Domain", BUSINESS_TYPES, index=BUSINESS_TYPES.index(biz_type) if biz_type in BUSINESS_TYPES else 0)
            desc = st.text_area("Description", value=business.get("description", ""), height=90)
            address = st.text_input("Address", value=business.get("address", ""))
            phone = st.text_input("Phone", value=business.get("phone", ""))
            instructions = st.text_area(
                "Owner Custom Instructions / FAQs (What AI should know)",
                value=business.get("instructions", ""),
                height=120,
                help="The AI receptionist uses this exact text to answer custom customer questions.",
            )
            if st.form_submit_button("SAVE BUSINESS DATA ➜", use_container_width=True):
                businesses_col().update_one(
                    {"_id": ObjectId(biz_id)},
                    {"$set": {
                        "name": name, "business_type": btype, "description": desc,
                        "address": address, "phone": phone, "instructions": instructions,
                        "updated_at": datetime.now(timezone.utc),
                    }},
                )
                st.session_state.business_name = name
                st.success("Business profile & AI knowledge updated!")
                st.rerun()

    with tab_svcs:
        st.markdown('<div style="font-size:0.8rem;color:var(--text-secondary);margin-bottom:8px">Services the AI will quote and book:</div>', unsafe_allow_html=True)
        svcs = list(services_col().find({"business_id": biz_id}).sort("created_at", -1))
        for s in svcs:
            c1, c2 = st.columns([4.5, 1])
            with c1:
                p_str = f"₹{s.get('price', 0):,.0f}" if s.get('price') else "Free"
                st.markdown(f"""
                <div style="padding:8px 12px;background:rgba(255,255,255,0.03);border:1px solid var(--border-subtle);border-radius:6px;display:flex;justify-content:space-between;margin-bottom:4px">
                    <strong style="color:#fff;font-size:0.88rem">{s['name']}</strong>
                    <span style="font-family:JetBrains Mono,monospace;color:#c4b5fd;font-size:0.82rem">{p_str} · {s.get('duration_minutes', 30)}m</span>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                if st.button("🗑️", key=f"del_svc_{s['_id']}", use_container_width=True):
                    services_col().delete_one({"_id": s["_id"]})
                    st.rerun()

        with st.form("add_svc_form", clear_on_submit=True):
            s1, s2, s3 = st.columns([2.5, 1, 1])
            with s1:
                s_name = st.text_input("New Service", placeholder="e.g. VIP Table / Haircut")
            with s2:
                s_dur = st.number_input("Mins", 5, 480, 30, 5, label_visibility="collapsed")
            with s3:
                s_pr = st.number_input("₹ Price", 0.0, 99999.0, 0.0, 50.0, label_visibility="collapsed")
            if st.form_submit_button("+ ADD SERVICE", use_container_width=True) and s_name.strip():
                services_col().insert_one(new_service(biz_id, s_name.strip(), int(s_dur), float(s_pr)))
                st.rerun()

    with tab_hours:
        wh = business.get("working_hours", DEFAULT_WORKING_HOURS)
        with st.form("wh_owner_form"):
            new_wh = {}
            for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
                d_info = wh.get(day, DEFAULT_WORKING_HOURS.get(day, {}))
                d1, d2, d3 = st.columns([1.5, 1, 1])
                with d1:
                    is_open = st.checkbox(day.capitalize(), value=d_info.get("is_open", True), key=f"wh_{day}")
                with d2:
                    op = st.text_input("Open", value=d_info.get("open", "09:00"), key=f"op_{day}", disabled=not is_open)
                with d3:
                    cl = st.text_input("Close", value=d_info.get("close", "23:00"), key=f"cl_{day}", disabled=not is_open)
                new_wh[day] = {"open": op, "close": cl, "is_open": is_open}
            if st.form_submit_button("SAVE WORKING HOURS ➜", use_container_width=True):
                businesses_col().update_one({"_id": ObjectId(biz_id)}, {"$set": {"working_hours": new_wh}})
                st.success("Working hours saved!")
                st.rerun()

    divider()
    m1, m2 = st.columns(2)
    with m1:
        metric_card("Total Bookings", bookings_col().count_documents({"business_id": biz_id}), "📅")
    with m2:
        metric_card("Registered Clients", customers_col().count_documents({"business_id": biz_id}), "👥")


# ═══════════════════════════════════════════════════════════════
# CLIENT: Continuous Hands-Free Phone Call Simulator (Window 2)
# ═══════════════════════════════════════════════════════════════
def _render_client_handsfree_phone():
    biz_id = get_current_business_id()
    default_demo_num = demo_provider.get_business_number(biz_id) if biz_id else "DEMO-9001"

    # All available demo numbers for quick dialing
    all_businesses = list(businesses_col().find({}, {"name": 1, "business_type": 1}))
    options_html = ""
    for b in all_businesses:
        b_num = demo_provider.get_business_number(str(b["_id"]))
        if b_num:
            options_html += f'<button class="quick-dial-btn" onclick="setDemoNum(\'{b_num}\')">{b.get("name")} ({b_num})</button>'

    # Embed the Full Interactive Hands-Free Phone Call Web Component
    phone_html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&family=JetBrains+Mono:wght@400;600;700&display=swap');

* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
    background: transparent;
    font-family: 'Plus Jakarta Sans', sans-serif;
    color: #f8fafc;
    overflow-x: hidden;
}}

.phone-wrapper {{
    background: rgba(14, 14, 26, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 20px;
    padding: 20px;
    backdrop-filter: blur(20px);
    box-shadow: 0 15px 40px rgba(0, 0, 0, 0.6);
    position: relative;
    overflow: hidden;
}}

.dialer-box {{
    display: flex;
    flex-direction: column;
    gap: 14px;
}}

.quick-dial-container {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 6px;
}}

.quick-dial-btn {{
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.15);
    color: #cbd5e1;
    border-radius: 20px;
    padding: 5px 12px;
    font-size: 0.76rem;
    cursor: pointer;
    font-family: 'Plus Jakarta Sans', sans-serif;
    transition: all 0.2s;
}}
.quick-dial-btn:hover {{
    background: rgba(139, 92, 246, 0.2);
    border-color: #8b5cf6;
    color: #fff;
}}

.input-row {{
    display: flex;
    gap: 10px;
}}

.demo-input {{
    flex: 1;
    background: rgba(8, 8, 16, 0.9);
    border: 1px solid rgba(139, 92, 246, 0.4);
    border-radius: 10px;
    padding: 12px 16px;
    color: #fff;
    font-size: 1.1rem;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: 0.05em;
    font-weight: 700;
    outline: none;
}}
.demo-input:focus {{
    border-color: #06b6d4;
    box-shadow: 0 0 15px rgba(6, 182, 212, 0.3);
}}

.call-btn {{
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    border: 1px solid rgba(255, 255, 255, 0.2);
    color: #fff;
    font-weight: 800;
    font-size: 0.95rem;
    padding: 12px 24px;
    border-radius: 10px;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 8px;
    transition: all 0.2s;
    box-shadow: 0 4px 20px rgba(16, 185, 129, 0.4);
}}
.call-btn:hover {{
    transform: translateY(-2px);
    box-shadow: 0 6px 25px rgba(16, 185, 129, 0.6);
}}

/* In-Call Active State */
.in-call-screen {{
    display: none;
    flex-direction: column;
    gap: 14px;
}}

.call-hero-header {{
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(6, 182, 212, 0.1) 100%);
    border: 1px solid rgba(16, 185, 129, 0.35);
    border-radius: 14px;
    padding: 16px 18px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}}

.ai-avatar {{
    width: 52px;
    height: 52px;
    border-radius: 50%;
    background: linear-gradient(135deg, #7c3aed 0%, #06b6d4 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5rem;
    box-shadow: 0 0 25px rgba(124, 58, 237, 0.6);
    border: 2px solid rgba(255, 255, 255, 0.3);
    animation: avatar-pulse 1.8s infinite alternate;
}}

@keyframes avatar-pulse {{
    0% {{ transform: scale(1); box-shadow: 0 0 15px rgba(124, 58, 237, 0.5); }}
    100% {{ transform: scale(1.08); box-shadow: 0 0 35px rgba(6, 182, 212, 0.8); }}
}}

.status-badge {{
    padding: 4px 12px;
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid rgba(16, 185, 129, 0.4);
    border-radius: 20px;
    font-size: 0.76rem;
    color: #34d399;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
    display: inline-flex;
    align-items: center;
    gap: 6px;
}}

.dot {{
    width: 8px;
    height: 8px;
    background: #10b981;
    border-radius: 50%;
    animation: blink 1.2s infinite;
}}
@keyframes blink {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.2; }} }}

.soundwave {{
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 5px;
    height: 24px;
    margin: 8px 0;
}}
.wave-bar {{
    width: 4px;
    height: 8px;
    background: #06b6d4;
    border-radius: 2px;
    animation: sound 1s ease-in-out infinite alternate;
}}
.wave-bar:nth-child(1) {{ animation-delay: 0.1s; height: 14px; }}
.wave-bar:nth-child(2) {{ animation-delay: 0.3s; height: 24px; background: #8b5cf6; }}
.wave-bar:nth-child(3) {{ animation-delay: 0.2s; height: 30px; }}
.wave-bar:nth-child(4) {{ animation-delay: 0.4s; height: 20px; background: #8b5cf6; }}
.wave-bar:nth-child(5) {{ animation-delay: 0.15s; height: 12px; }}

@keyframes sound {{
    0% {{ transform: scaleY(0.3); }}
    100% {{ transform: scaleY(1); }}
}}

/* Dialogue Stream */
.transcript-box {{
    max-height: 240px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 10px;
    padding: 10px;
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 12px;
}}

.msg-bubble {{
    padding: 10px 14px;
    border-radius: 10px;
    font-size: 0.88rem;
    line-height: 1.4;
    max-width: 88%;
}}
.msg-caller {{
    align-self: flex-start;
    background: rgba(255, 255, 255, 0.06);
    border-left: 3px solid #06b6d4;
    color: #e2e8f0;
}}
.msg-ai {{
    align-self: flex-end;
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.25) 0%, rgba(30, 27, 75, 0.5) 100%);
    border-right: 3px solid #8b5cf6;
    color: #f8fafc;
}}

.confirmed-ticket {{
    display: none;
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.25) 0%, rgba(6, 78, 59, 0.5) 100%);
    border: 2px solid #10b981;
    border-radius: 12px;
    padding: 14px 18px;
    box-shadow: 0 0 30px rgba(16, 185, 129, 0.35);
    animation: ticket-glow 2s infinite alternate;
}}
@keyframes ticket-glow {{
    0% {{ box-shadow: 0 0 20px rgba(16, 185, 129, 0.3); }}
    100% {{ box-shadow: 0 0 40px rgba(16, 185, 129, 0.6); }}
}}

.hangup-btn {{
    background: linear-gradient(135deg, #f43f5e 0%, #e11d48 100%);
    border: 1px solid rgba(255, 255, 255, 0.2);
    color: #fff;
    font-weight: 800;
    font-size: 1rem;
    padding: 14px 20px;
    border-radius: 12px;
    cursor: pointer;
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    transition: all 0.2s;
    box-shadow: 0 4px 20px rgba(244, 63, 94, 0.4);
}}
.hangup-btn:hover {{
    background: linear-gradient(135deg, #fb7185 0%, #f43f5e 100%);
    transform: translateY(-2px);
    box-shadow: 0 6px 30px rgba(244, 63, 94, 0.6);
}}
</style>
</head>
<body>

<div class="phone-wrapper">
    <!-- DIALER SCREEN -->
    <div id="dialerScreen" class="dialer-box">
        <div style="text-align:center;padding:10px 0">
            <div style="font-size:2rem;margin-bottom:4px">📱</div>
            <div style="font-weight:800;font-size:1.15rem;color:#fff">Phone Call Simulator</div>
            <div style="font-size:0.8rem;color:#94a3b8">Enter Demo Number → Hands-Free Conversation</div>
        </div>

        <div style="font-size:0.75rem;color:#94a3b8;font-weight:700">Quick Dial Available:</div>
        <div class="quick-dial-container">
            {options_html}
        </div>

        <div class="input-row">
            <input type="text" id="demoNumInput" class="demo-input" value="{default_demo_num}" placeholder="DEMO-9001">
            <button class="call-btn" onclick="startHandsFreeCall()">📞 CALL</button>
        </div>
    </div>

    <!-- IN-CALL SCREEN -->
    <div id="inCallScreen" class="in-call-screen">
        <div class="call-hero-header">
            <div style="display:flex;align-items:center;gap:12px">
                <div class="ai-avatar">🎙️</div>
                <div>
                    <div id="callBizName" style="font-weight:800;font-size:1.1rem;color:#fff">Business</div>
                    <div id="callSubtitle" style="font-size:0.76rem;color:#a7f3d0">AI Receptionist</div>
                </div>
            </div>
            <div class="status-badge"><span class="dot"></span> <span id="callTimer">00:00</span></div>
        </div>

        <div class="soundwave">
            <div class="wave-bar"></div>
            <div class="wave-bar"></div>
            <div class="wave-bar"></div>
            <div class="wave-bar"></div>
            <div class="wave-bar"></div>
        </div>

        <div id="statusNotice" style="text-align:center;font-size:0.82rem;color:#67e8f9;padding:4px">
            Connecting neural audio stream...
        </div>

        <div id="confirmedTicket" class="confirmed-ticket">
            <div style="font-size:0.75rem;font-weight:800;color:#34d399;text-transform:uppercase">🎉 APPOINTMENT CONFIRMED!</div>
            <div id="ticketCustomer" style="font-size:1.1rem;font-weight:800;color:#fff;margin-top:2px">Client Name</div>
            <div id="ticketDetails" style="font-size:0.82rem;color:#a7f3d0">Date & Time</div>
            <div id="ticketRef" style="font-family:'JetBrains Mono',monospace;font-size:0.78rem;color:#fff;margin-top:4px">Ref: BK-XXXX</div>
        </div>

        <div id="transcriptBox" class="transcript-box">
            <!-- Messages added dynamically -->
        </div>

        <button class="hangup-btn" id="hangupBtn"
            onmousedown="startHangupHold(event)" onmouseup="cancelHangupHold()" ontouchstart="startHangupHold(event)" ontouchend="cancelHangupHold()"
            title="Hold for 2 seconds to hang up">
            🔴 HOLD TO END CALL
        </button>
        <div id="hangupProgress" style="height:4px;background:#ff4757;border-radius:4px;width:0%;transition:width 2s linear;margin-top:4px;display:none"></div>
    </div>
</div>

<script>
let currentCallId = null;
let isCallActive = false;
let callStartTime = 0;
let timerInterval = null;
let recognition = null;
let isSpeaking = false;
let isRecognizing = false;
let hangupTimer = null;
let preferredVoice = null;

// Pre-load best voice on page load
function loadBestVoice() {{
    const voices = window.speechSynthesis.getVoices();
    if (!voices.length) return;
    // Priority: Google Hindi India > Microsoft India > any hi-IN > any IN > fallback
    preferredVoice =
        voices.find(v => v.name.includes('Google') && v.lang === 'hi-IN') ||
        voices.find(v => v.name.includes('Microsoft') && v.lang.includes('IN')) ||
        voices.find(v => v.lang === 'hi-IN') ||
        voices.find(v => v.lang.includes('hi')) ||
        voices.find(v => v.lang.includes('IN')) ||
        voices.find(v => v.name.toLowerCase().includes('india')) ||
        voices.find(v => v.lang.startsWith('en-IN')) ||
        voices[0];
    console.log('Selected voice:', preferredVoice?.name, preferredVoice?.lang);
}}
window.speechSynthesis.onvoiceschanged = loadBestVoice;
loadBestVoice();

// Warm-up Web Speech API (prevents first-utterance silence bug in Chrome)
function warmUpSpeech() {{
    const u = new SpeechSynthesisUtterance('');
    u.volume = 0;
    window.speechSynthesis.speak(u);
}}

// Hold-to-End-Call logic
function startHangupHold(e) {{
    e.preventDefault();
    if (!isCallActive) return;
    const prog = document.getElementById('hangupProgress');
    prog.style.display = 'block';
    prog.style.width = '0%';
    // Force reflow
    void prog.offsetWidth;
    prog.style.width = '100%';
    hangupTimer = setTimeout(() => {{
        endHandsFreeCall();
    }}, 2000);
}}

function cancelHangupHold() {{
    if (hangupTimer) {{
        clearTimeout(hangupTimer);
        hangupTimer = null;
    }}
    const prog = document.getElementById('hangupProgress');
    prog.style.transition = 'none';
    prog.style.width = '0%';
    prog.style.display = 'none';
}}

function setDemoNum(num) {{
    document.getElementById('demoNumInput').value = num;
}}

// Initialize Speech Recognition
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
if (SpeechRecognition) {{
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'hi-IN';

    recognition.onstart = function() {{
        isRecognizing = true;
        document.getElementById('statusNotice').innerHTML = "👂 <strong>LISTENING... Speak naturally now!</strong>";
    }};

    recognition.onresult = function(event) {{
        const text = event.results[0][0].transcript;
        if (text && text.trim().length > 0) {{
            appendMessage('caller', text);
            sendUserSpeechToAI(text);
        }}
    }};

    recognition.onerror = function(event) {{
        console.log("Speech recognition error:", event.error);
        if (isCallActive && !isSpeaking) {{
            setTimeout(startListeningSafe, 1000);
        }}
    }};

    recognition.onend = function() {{
        isRecognizing = false;
        if (isCallActive && !isSpeaking) {{
            // Auto restart listening after short pause
            setTimeout(startListeningSafe, 500);
        }}
    }};
}}

function startListeningSafe() {{
    if (!isCallActive || isSpeaking || isRecognizing) return;
    try {{
        recognition.start();
    }} catch(e) {{
        console.log("Could not start recognition:", e);
    }}
}}

async function startHandsFreeCall() {{
    const demoNum = document.getElementById('demoNumInput').value.trim();
    if (!demoNum) return;

    // Warm up speech engine right on user gesture (Chrome requires this)
    warmUpSpeech();
    // Reload best voice now (browsers load voices async)
    loadBestVoice();

    try {{
        const res = await fetch('http://127.0.0.1:8000/api/call/start', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ demo_number: demoNum }})
        }});

        if (!res.ok) {{
            alert("Could not connect: Business number not found.");
            return;
        }}

        const data = await res.json();
        currentCallId = data.call_id;
        isCallActive = true;
        callStartTime = Date.now();

        // Switch to In-Call Screen
        document.getElementById('dialerScreen').style.display = 'none';
        document.getElementById('inCallScreen').style.display = 'flex';
        document.getElementById('callBizName').innerText = data.business_name;
        document.getElementById('callSubtitle').innerText = data.ai_name + " · " + data.business_type;
        document.getElementById('transcriptBox').innerHTML = '';
        document.getElementById('confirmedTicket').style.display = 'none';

        // Start Call Timer
        timerInterval = setInterval(updateTimer, 1000);

        // AI speaks initial greeting aloud
        appendMessage('ai', data.greeting);
        speakAloud(data.greeting, data.language || 'hi');

    }} catch (err) {{
        alert("API connection failed. Make sure server is running on port 8000.");
        console.error(err);
    }}
}}

async function sendUserSpeechToAI(userText) {{
    if (!isCallActive || !currentCallId) return;

    document.getElementById('statusNotice').innerHTML = "⚡ <strong>AI is thinking & checking data...</strong>";

    try {{
        const res = await fetch('http://127.0.0.1:8000/api/call/message', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ call_id: currentCallId, message: userText }})
        }});

        const data = await res.json();
        if (data.response) {{
            appendMessage('ai', data.response);

            // If appointment confirmed, show glowing ticket!
            if (data.confirmed_booking) {{
                const b = data.confirmed_booking;
                document.getElementById('ticketCustomer').innerText = b.customer_name + " · " + b.service_name;
                document.getElementById('ticketDetails').innerText = "📅 " + b.date + " at " + b.time;
                document.getElementById('ticketRef').innerText = "Reference: " + b.booking_ref;
                document.getElementById('confirmedTicket').style.display = 'block';
            }}

            // AI speaks its reply aloud
            speakAloud(data.response, data.language || 'hi');
        }}

    }} catch (err) {{
        console.error(err);
        document.getElementById('statusNotice').innerText = "Error reaching AI.";
    }}
}}

function speakAloud(text, lang) {{
    if (!window.speechSynthesis) {{
        startListeningSafe();
        return;
    }}

    window.speechSynthesis.cancel();
    isSpeaking = true;
    if (recognition && isRecognizing) {{
        try {{ recognition.stop(); }} catch(e) {{}}
    }}

    document.getElementById('statusNotice').innerHTML = "🔊 <strong>Maya is speaking...</strong>";

    // Clean text: remove markdown, HTML tags, think tags
    let cleanText = text
        .replace(/<[^>]*>/g, '')
        .replace(/[*_#`]/g, '')
        .replace(/\[.*?\]/g, '')
        .trim();

    // Split into natural human speech chunks on punctuation
    // This creates natural pauses like a real human speaking
    const chunks = cleanText
        .split(/(?<=[।.!?;,…])/)
        .map(c => c.trim())
        .filter(c => c.length > 0);

    if (chunks.length === 0) {{
        isSpeaking = false;
        if (isCallActive) startListeningSafe();
        return;
    }}

    let chunkIndex = 0;

    function speakNextChunk() {{
        if (chunkIndex >= chunks.length || !isCallActive) {{
            isSpeaking = false;
            if (isCallActive) {{
                document.getElementById('statusNotice').innerHTML = "👂 <strong>LISTENING... Speak naturally now!</strong>";
                setTimeout(startListeningSafe, 300);
            }}
            return;
        }}

        const chunk = chunks[chunkIndex++];
        if (!chunk || chunk.length === 0) {{ speakNextChunk(); return; }}

        const utter = new SpeechSynthesisUtterance(chunk);

        // VOLUME: Always maximum
        utter.volume = 1.0;

        // RATE: Slightly slower than default = sounds more human, not robotic
        utter.rate = 0.92;

        // PITCH: Slightly higher = sounds warm/friendly female voice
        utter.pitch = 1.1;

        // Apply best loaded voice
        if (preferredVoice) utter.voice = preferredVoice;
        utter.lang = preferredVoice ? preferredVoice.lang : 'hi-IN';

        utter.onend = function() {{
            // Small natural pause between chunks (80–150ms)
            setTimeout(speakNextChunk, 90);
        }};

        utter.onerror = function(e) {{
            console.warn('Speech chunk error:', e.error);
            setTimeout(speakNextChunk, 100);
        }};

        window.speechSynthesis.speak(utter);
    }}

    speakNextChunk();

    // Chrome TTS watchdog: Chrome sometimes stops mid-speech after 15s
    // Resume if still speaking
    const watchdog = setInterval(() => {{
        if (!isSpeaking) {{ clearInterval(watchdog); return; }}
        if (window.speechSynthesis.paused) {{
            window.speechSynthesis.resume();
        }}
    }}, 5000);
}}

async function endHandsFreeCall() {{
    isCallActive = false;
    isSpeaking = false;
    if (timerInterval) clearInterval(timerInterval);
    if (window.speechSynthesis) window.speechSynthesis.cancel();
    if (recognition) {{ try {{ recognition.stop(); }} catch(e) {{}} }}

    if (currentCallId) {{
        try {{
            await fetch('http://127.0.0.1:8000/api/call/end', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{ call_id: currentCallId }})
            }});
        }} catch(e) {{}}
        currentCallId = null;
    }}

    // Switch back to dialer
    document.getElementById('inCallScreen').style.display = 'none';
    document.getElementById('dialerScreen').style.display = 'flex';
}}

function appendMessage(role, text) {{
    const box = document.getElementById('transcriptBox');
    const div = document.createElement('div');
    div.className = 'msg-bubble ' + (role === 'caller' ? 'msg-caller' : 'msg-ai');
    div.innerHTML = '<strong>' + (role === 'caller' ? '👤 Caller' : '🤖 Maya (AI)') + ':</strong> ' + text;
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
}}

function updateTimer() {{
    if (!isCallActive) return;
    const sec = Math.floor((Date.now() - callStartTime) / 1000);
    const m = String(Math.floor(sec / 60)).padStart(2, '0');
    const s = String(sec % 60).padStart(2, '0');
    document.getElementById('callTimer').innerText = m + ':' + s;
}}
</script>
</body>
</html>
    """

    components.html(phone_html, height=580, scrolling=False)


# ═══════════════════════════════════════════════════════════════
# TAB 2: BOOKINGS VIEW
# ═══════════════════════════════════════════════════════════════
def _render_bookings_view():
    page_header("Live Bookings & Client Registry", "Real MongoDB Appointments Created by Voice AI & Dashboard", badge="REAL DATABASE")

    biz_id = get_current_business_id()
    if not biz_id:
        empty_state("Please set up your business in the Demo tab first.", "📅")
        return

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    today_count = bookings_col().count_documents({"business_id": biz_id, "date": today_str, "status": "confirmed"})
    total_count = bookings_col().count_documents({"business_id": biz_id})
    cust_count = customers_col().count_documents({"business_id": biz_id})

    m1, m2, m3 = st.columns(3)
    with m1:
        metric_card("Today's Appointments", today_count, "📅")
    with m2:
        metric_card("Total Bookings", total_count, "⚡")
    with m3:
        metric_card("Registered Clients", cust_count, "👥")

    divider()
    tab_b_list, tab_c_list = st.tabs(["📅 ALL APPOINTMENTS & RESERVATIONS", "👥 CUSTOMER DIRECTORY"])

    with tab_b_list:
        bookings = list(bookings_col().find({"business_id": biz_id}).sort("created_at", -1))
        if bookings:
            for b in bookings:
                cust = customers_col().find_one({"_id": ObjectId(b["customer_id"])}) if b.get("customer_id") else None
                cust_name = cust.get("name", "Client") if cust else "Client"
                cust_phone = cust.get("phone", "") if cust else ""
                svc = services_col().find_one({"_id": ObjectId(b["service_id"])}) if b.get("service_id") and b["service_id"] != "any" else None
                svc_name = svc.get("name", "Service") if svc else "Appointment"

                st.markdown(f"""
                <div style="background:rgba(255,255,255,0.03);border:1px solid var(--border-subtle);border-radius:12px;padding:16px;margin-bottom:10px;display:flex;align-items:center;justify-content:space-between">
                    <div>
                        <div style="font-weight:700;font-size:1.05rem;color:#fff">{cust_name} {f'<span style=\"color:var(--text-muted);font-size:0.8rem\">({cust_phone})</span>' if cust_phone else ''}</div>
                        <div style="color:#c4b5fd;font-size:0.88rem;margin-top:2px">{svc_name}</div>
                        <div style="font-family:JetBrains Mono,monospace;font-size:0.8rem;color:var(--text-muted);margin-top:6px">
                            📅 {b.get('date')} &nbsp;·&nbsp; ⏰ {b.get('start_time')} - {b.get('end_time')} &nbsp;·&nbsp; 🏷️ Ref: {b.get('booking_ref', 'BK-AUTO')}
                        </div>
                    </div>
                    <div>
                        {status_badge(b.get('status', 'confirmed'))}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            empty_state("No bookings recorded yet. Call the AI in Window 2 to create your first real booking!", "📅")

    with tab_c_list:
        custs = list(customers_col().find({"business_id": biz_id}).sort("created_at", -1))
        if custs:
            for c in custs:
                lang = SUPPORTED_LANGUAGES.get(c.get("language_preference", "en"), "English")
                st.markdown(f"""
                <div style="background:rgba(255,255,255,0.03);border:1px solid var(--border-subtle);border-radius:10px;padding:12px 16px;margin-bottom:8px;display:flex;align-items:center;justify-content:space-between">
                    <div>
                        <strong style="color:#fff">{c.get('name', 'Client')}</strong>
                        <span style="color:var(--text-muted);margin-left:8px;font-family:JetBrains Mono,monospace;font-size:0.82rem">{c.get('phone', 'No phone')}</span>
                    </div>
                    <span class="status-pill pill-idle">Language: {lang}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            empty_state("No clients registered yet.", "👥")


# ═══════════════════════════════════════════════════════════════
# TAB 3: TELEMETRY VIEW
# ═══════════════════════════════════════════════════════════════
def _render_telemetry_view():
    page_header("AI Telemetry & Call Logs", "Live Audit Trail of Conversations & Tool Invocations", badge="AUDIT LOGS")

    biz_id = get_current_business_id()
    if not biz_id:
        empty_state("Please set up your business first.", "📊")
        return

    tab_calls, tab_tools = st.tabs(["📞 CALL TRANSCRIPTS & SESSIONS", "⚡ TOOL EXECUTION AUDIT"])

    with tab_calls:
        calls = list(calls_col().find({"business_id": biz_id}).sort("started_at", -1).limit(25))
        if calls:
            for c in calls:
                started = c.get("started_at").strftime("%Y-%m-%d %H:%M:%S") if c.get("started_at") else "—"
                lang = SUPPORTED_LANGUAGES.get(c.get("language", ""), c.get("language", "Auto"))
                outcome = c.get("outcome", "completed")

                st.markdown(f"""
                <div style="background:rgba(255,255,255,0.03);border:1px solid var(--border-subtle);border-radius:10px;padding:14px;margin-bottom:12px">
                    <div style="display:flex;justify-content:space-between;align-items:center">
                        <div>
                            <span style="font-family:JetBrains Mono,monospace;font-weight:700;color:#fff">Session: {str(c['_id'])[:12]}...</span>
                            <span style="color:var(--text-muted);margin-left:10px;font-size:0.8rem">{started}</span>
                        </div>
                        <div>
                            <span class="bubble-pill">Language: {lang}</span>
                            {status_badge(outcome)}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                transcript = c.get("transcript", [])
                if transcript:
                    with st.expander(f"View Transcript ({len(transcript)} messages)"):
                        conversation_display(transcript)
        else:
            empty_state("No calls recorded yet. Complete a call in Window 2 to view audit logs.", "📞")

    with tab_tools:
        executions = list(tool_executions_col().find({"business_id": biz_id}).sort("timestamp", -1).limit(40))
        if executions:
            for ex in executions:
                ts = ex.get("timestamp").strftime("%H:%M:%S") if ex.get("timestamp") else "—"
                tool_name = ex.get("tool_name", "tool")
                success = ex.get("success", False)

                st.markdown(f"""
                <div style="background:rgba(255,255,255,0.02);border:1px solid var(--border-subtle);border-radius:8px;padding:10px 14px;margin-bottom:6px;display:flex;justify-content:space-between;align-items:center">
                    <div>
                        <strong style="font-family:JetBrains Mono,monospace;color:#c4b5fd">{tool_name}</strong>
                        <span style="color:var(--text-muted);font-size:0.75rem;margin-left:12px">{ts}</span>
                    </div>
                    {status_badge('success' if success else 'failed')}
                </div>
                """, unsafe_allow_html=True)
                with st.expander("Payload & Response Data"):
                    st.json({"Input": ex.get("input"), "Result": ex.get("result")})
        else:
            empty_state("No tool executions logged yet.", "⚡")


# ═══════════════════════════════════════════════════════════════
# MAIN ROUTER
# ═══════════════════════════════════════════════════════════════
def main():
    if not require_auth():
        render_auth()
        return
    render_main()


if __name__ == "__main__":
    main()
