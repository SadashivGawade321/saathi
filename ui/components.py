"""
SAATHI ONE — UI Component Library
High-Tech Glassmorphism Components for Streamlit Dashboard.
"""

import textwrap
import streamlit as st
from config import SUPPORTED_LANGUAGES


def page_header(title: str, subtitle: str = "", badge: str = ""):
    """Render a clean, modern page header."""
    badge_html = f'<span class="brand-badge" style="margin-bottom:8px">{badge}</span>' if badge else ''
    subtitle_html = f'<div style="color:var(--text-muted);font-size:0.88rem;margin-top:4px;font-weight:400">{subtitle}</div>' if subtitle else ''
    
    html = textwrap.dedent(f"""
<div style="margin-bottom: 1.75rem; border-bottom: 1px solid var(--border-subtle); padding-bottom: 1.25rem;">
{badge_html}
<h1 style="margin: 0; font-size: 1.85rem; font-weight: 800; letter-spacing: -0.03em;">{title}</h1>
{subtitle_html}
</div>
    """).strip()
    st.markdown(html, unsafe_allow_html=True)


def sidebar_brand_card(business_name: str = "", demo_number: str = "", ai_name: str = "Maya", ai_active: bool = True):
    """Render the luxury sidebar brand container."""
    status_dot = '<span class="pulsing-dot" style="background:#10b981"></span>' if ai_active else '<span class="pulsing-dot" style="background:#64748b"></span>'
    status_text = "AI Online" if ai_active else "AI Offline"
    
    biz_html = f'<div style="color:#fff;font-weight:700;font-size:0.95rem;margin-top:6px">{business_name}</div>' if business_name else '<div style="color:var(--text-muted);font-size:0.8rem;margin-top:6px">No Business Active</div>'
    num_html = f'<div style="color:#c4b5fd;font-family:JetBrains Mono, monospace;font-size:0.8rem;margin-top:2px">{demo_number}</div>' if demo_number else ''

    html = textwrap.dedent(f"""
<div class="brand-container">
<div class="brand-badge">⚡ SAATHI ONE</div>
<div class="brand-name">AI Receptionist</div>
<div class="brand-tagline">One Business · One Number · One AI</div>
<div style="margin-top:12px;padding-top:10px;border-top:1px solid rgba(255,255,255,0.08);display:flex;align-items:center;justify-content:space-between">
<div>
{biz_html}
{num_html}
</div>
<div style="text-align:right">
<span class="status-pill pill-active" style="padding:2px 8px;font-size:0.7rem">{status_dot} {status_text}</span>
</div>
</div>
</div>
    """).strip()
    st.markdown(html, unsafe_allow_html=True)


def metric_card(label: str, value, icon: str = "", delta: str = ""):
    """Render a high-contrast metric card."""
    delta_html = f'<div style="color:#34d399;font-size:0.75rem;margin-top:4px;font-weight:600">{delta}</div>' if delta else ''
    icon_html = f'<span style="font-size:1.2rem;opacity:0.7">{icon}</span>' if icon else ''

    html = textwrap.dedent(f"""
<div class="metric-box">
<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px">
<span class="metric-label" style="margin:0">{label}</span>
{icon_html}
</div>
<div class="metric-num">{value}</div>
{delta_html}
</div>
    """).strip()
    st.markdown(html, unsafe_allow_html=True)


def status_badge(status: str, label: str = ""):
    """Return an HTML string for a status badge."""
    display = label or status.replace("_", " ").upper()
    s_low = status.lower()
    if s_low in ("confirmed", "active", "completed", "success"):
        css = "pill-active"
        dot_color = "#34d399"
    elif s_low in ("pending", "busy", "processing"):
        css = "pill-busy"
        dot_color = "#fbbf24"
    elif s_low in ("cancelled", "failed", "inactive"):
        css = "pill-cancelled"
        dot_color = "#fb7185"
    else:
        css = "pill-idle"
        dot_color = "#94a3b8"

    return f'<span class="status-pill {css}"><span class="pulsing-dot" style="background:{dot_color}"></span>{display}</span>'


def activity_log_display(activities: list):
    """Render the live AI thought & execution stream."""
    if not activities:
        st.markdown('<div style="color:var(--text-muted);font-size:0.8rem;padding:8px 0">Waiting for call activity...</div>', unsafe_allow_html=True)
        return

    items_html = ""
    for item in activities:
        msg = item if isinstance(item, str) else item.get("message", "")
        items_html += f'<div class="step-item"><span class="step-icon">✔</span> {msg}</div>\n'

    html = textwrap.dedent(f"""
<div style="background:rgba(0,0,0,0.25);border:1px solid var(--border-subtle);border-radius:var(--radius-md);padding:12px">
<div style="font-size:0.72rem;font-weight:700;text-transform:uppercase;color:var(--text-muted);letter-spacing:0.08em;margin-bottom:8px">Live AI Brain & Tool Execution</div>
{items_html}
</div>
    """).strip()
    st.markdown(html, unsafe_allow_html=True)


def conversation_display(messages: list):
    """Render conversation message bubbles."""
    if not messages:
        return

    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        language = msg.get("language", "")

        if role == "user":
            lang_str = SUPPORTED_LANGUAGES.get(language, language).upper() if language else "CLIENT"
            lang_pill = f'<span class="bubble-pill">{lang_str}</span>'
            html = textwrap.dedent(f"""
<div class="bubble-user">
<div class="bubble-header">
<span>CLIENT</span>
{lang_pill}
</div>
<div>{content}</div>
</div>
            """).strip()
            st.markdown(html, unsafe_allow_html=True)

        elif role == "assistant":
            html = textwrap.dedent(f"""
<div class="bubble-ai">
<div class="bubble-header">
<span style="color:#c4b5fd">AI RECEPTIONIST (MAYA)</span>
<span class="bubble-pill" style="background:rgba(139,92,246,0.2);color:#c4b5fd;border-color:rgba(139,92,246,0.4)">AUDIO GENERATED 🔊</span>
</div>
<div>{content}</div>
</div>
            """).strip()
            st.markdown(html, unsafe_allow_html=True)

        elif role == "system":
            html = textwrap.dedent(f"""
<div style="padding:6px 12px;background:rgba(139,92,246,0.06);border-left:2px solid var(--brand-violet);border-radius:4px;font-family:JetBrains Mono,monospace;font-size:0.75rem;color:#c4b5fd;margin:4px 0">
⚡ {content}
</div>
            """).strip()
            st.markdown(html, unsafe_allow_html=True)


def voice_hero_display(ai_name: str, biz_name: str, status: str = "idle"):
    """Render the glowing voice console hero."""
    is_active = status in ("listening", "speaking", "attending")
    avatar_class = "ai-avatar ai-avatar-listening" if is_active else "ai-avatar"
    
    if status == "listening":
        status_pill = '<span class="status-pill pill-active"><span class="pulsing-dot" style="background:#10b981"></span> LISTENING (SPEAK NOW)</span>'
    elif status == "speaking":
        status_pill = '<span class="status-pill pill-busy"><span class="pulsing-dot" style="background:#fbbf24"></span> SPEAKING (AI RECEPTIONIST)</span>'
    elif status == "attending":
        status_pill = '<span class="status-pill pill-active"><span class="pulsing-dot" style="background:#06b6d4"></span> CALL CONNECTED</span>'
    else:
        status_pill = '<span class="status-pill pill-idle"><span class="pulsing-dot" style="background:#94a3b8"></span> READY ON STANDBY</span>'

    soundwave_html = ""
    if is_active:
        soundwave_html = """
<div class="soundwave">
<div class="wave-bar"></div>
<div class="wave-bar"></div>
<div class="wave-bar"></div>
<div class="wave-bar"></div>
<div class="wave-bar"></div>
</div>
        """

    html = textwrap.dedent(f"""
<div class="voice-hero">
<div class="{avatar_class}">🎙️</div>
<h2 style="margin:0;font-size:1.75rem;font-weight:800;letter-spacing:-0.03em">{ai_name}</h2>
<div style="font-size:0.85rem;color:var(--text-muted);margin:4px 0 16px 0">{biz_name} · Multilingual AI Receptionist</div>
<div style="display:flex;align-items:center;justify-content:center;gap:12px;margin-bottom:8px">
{status_pill}
</div>
{soundwave_html}
</div>
    """).strip()
    st.markdown(html, unsafe_allow_html=True)


def empty_state(message: str, icon: str = "✨"):
    """Render a clean empty state without raw unescaped code blocks."""
    html = textwrap.dedent(f"""
<div style="text-align:center;padding:3rem 1.5rem;background:rgba(255,255,255,0.02);border:1px dashed var(--border-medium);border-radius:var(--radius-lg);margin:1rem 0;">
<div style="font-size:2rem;margin-bottom:8px;opacity:0.6">{icon}</div>
<div style="color:var(--text-secondary);font-size:0.9rem;max-width:420px;margin:0 auto">{message}</div>
</div>
    """).strip()
    st.markdown(html, unsafe_allow_html=True)


def section_header(title: str, description: str = ""):
    """Render a clean section header inside cards."""
    desc_html = f'<div style="color:var(--text-muted);font-size:0.8rem;margin-top:2px">{description}</div>' if description else ''
    html = textwrap.dedent(f"""
<div style="margin-bottom:14px;margin-top:6px">
<h3 style="margin:0;font-size:1.15rem;font-weight:700">{title}</h3>
{desc_html}
</div>
    """).strip()
    st.markdown(html, unsafe_allow_html=True)


def divider():
    """Render a subtle divider."""
    st.markdown('<hr style="border:none;border-top:1px solid var(--border-subtle);margin:1.5rem 0;">', unsafe_allow_html=True)
