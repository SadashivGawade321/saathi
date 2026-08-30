"""
SAATHI ONE — Luxury Dark Executive Design System
Ultra-Clean, High-Tech Glassmorphism with Futuristic Intro Loader & Live Phone Animation.
"""


def get_main_css() -> str:
    """Return the complete CSS design system with intro animation & phone styles."""
    return """
<style>
/* ═══════════════════════════════════════════════════════════════
   SAATHI ONE — LUXURY EXECUTIVE DESIGN SYSTEM
   ═══════════════════════════════════════════════════════════════ */

@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

:root {
    --bg-base: #05050a;
    --bg-surface: #0c0c16;
    --bg-elevated: #131322;
    --bg-glass: rgba(18, 18, 32, 0.7);
    --bg-glass-hover: rgba(26, 26, 44, 0.85);

    --text-primary: #f8fafc;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;

    --brand-violet: #8b5cf6;
    --brand-indigo: #6366f1;
    --brand-cyan: #06b6d4;
    --brand-emerald: #10b981;
    --brand-rose: #f43f5e;
    --brand-amber: #f59e0b;

    --border-subtle: rgba(255, 255, 255, 0.08);
    --border-medium: rgba(255, 255, 255, 0.16);
    --border-glow: rgba(139, 92, 246, 0.4);

    --radius-sm: 6px;
    --radius-md: 10px;
    --radius-lg: 16px;
    --radius-xl: 24px;
    --radius-full: 9999px;
}

/* Global App */
.stApp {
    background: radial-gradient(circle at 50% 0%, #15102a 0%, #06060c 60%, #030307 100%) !important;
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    color: var(--text-primary) !important;
}

#MainMenu, footer, header, [data-testid="stDecoration"] {
    display: none !important;
}

.block-container {
    padding: 1.5rem 2rem !important;
    max-width: 1360px !important;
}

/* Typography */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    color: var(--text-primary) !important;
    letter-spacing: -0.03em !important;
    font-weight: 700 !important;
}

/* Brand Badge */
.brand-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 10px;
    background: rgba(139, 92, 246, 0.2);
    border: 1px solid rgba(139, 92, 246, 0.4);
    border-radius: var(--radius-full);
    font-size: 0.7rem;
    font-weight: 700;
    color: #c4b5fd;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

/* Metrics Box */
.metric-box {
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-md);
    padding: 1rem 1.25rem;
    text-align: left;
    transition: all 0.2s ease;
}

.metric-box:hover {
    border-color: var(--brand-violet);
    background: rgba(139, 92, 246, 0.04);
}

.metric-num {
    font-size: 1.85rem;
    font-weight: 800;
    font-family: 'JetBrains Mono', monospace;
    color: #fff;
    line-height: 1.1;
}

.metric-label {
    font-size: 0.72rem;
    color: var(--text-muted);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

/* Status Badges */
.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 3px 10px;
    border-radius: var(--radius-full);
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    font-family: 'JetBrains Mono', monospace;
}

.pill-active {
    background: rgba(16, 185, 129, 0.12);
    color: #34d399;
    border: 1px solid rgba(16, 185, 129, 0.3);
}

.pill-busy {
    background: rgba(245, 158, 11, 0.12);
    color: #fbbf24;
    border: 1px solid rgba(245, 158, 11, 0.3);
}

.pill-idle {
    background: rgba(148, 163, 184, 0.12);
    color: #cbd5e1;
    border: 1px solid rgba(148, 163, 184, 0.25);
}

.pill-cancelled {
    background: rgba(244, 63, 94, 0.12);
    color: #fb7185;
    border: 1px solid rgba(244, 63, 94, 0.3);
}

.pulsing-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    display: inline-block;
    animation: radar 1.6s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes radar {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.3; transform: scale(1.4); }
}

/* Animated Soundwave */
.soundwave {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 4px;
    height: 28px;
    margin: 8px 0;
}

.wave-bar {
    width: 4px;
    height: 8px;
    background: var(--brand-violet);
    border-radius: 2px;
    animation: sound 1.1s ease-in-out infinite alternate;
}

.wave-bar:nth-child(1) { animation-delay: 0.1s; height: 14px; }
.wave-bar:nth-child(2) { animation-delay: 0.3s; height: 24px; background: var(--brand-cyan); }
.wave-bar:nth-child(3) { animation-delay: 0.2s; height: 32px; }
.wave-bar:nth-child(4) { animation-delay: 0.4s; height: 20px; background: var(--brand-cyan); }
.wave-bar:nth-child(5) { animation-delay: 0.15s; height: 12px; }

@keyframes sound {
    0% { transform: scaleY(0.3); }
    100% { transform: scaleY(1); }
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #7c3aed 0%, #6366f1 100%) !important;
    color: #fff !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    border-radius: var(--radius-md) !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    padding: 0.55rem 1.25rem !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 14px rgba(124, 58, 237, 0.3) !important;
}

.stButton > button:hover {
    background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%) !important;
    box-shadow: 0 6px 22px rgba(124, 58, 237, 0.5) !important;
    transform: translateY(-1px) !important;
}

/* Input Fields */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div,
.stNumberInput > div > div > input {
    background: rgba(14, 14, 24, 0.9) !important;
    color: #fff !important;
    border: 1px solid var(--border-medium) !important;
    border-radius: var(--radius-md) !important;
    padding: 0.55rem 0.8rem !important;
    font-size: 0.88rem !important;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--brand-violet) !important;
    box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.25) !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    border-bottom: 1px solid var(--border-subtle);
    padding-bottom: 4px;
    margin-bottom: 1.25rem;
}

.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--text-muted) !important;
    font-weight: 600 !important;
    font-size: 0.86rem !important;
    padding: 6px 16px !important;
    border-radius: var(--radius-md) !important;
    border: none !important;
}

.stTabs [aria-selected="true"] {
    color: #fff !important;
    background: rgba(139, 92, 246, 0.15) !important;
    border: 1px solid rgba(139, 92, 246, 0.3) !important;
}

/* ═══════════════════════════════════════════════════════════════
   FUTURISTIC SPLASH / INTRO SCREEN ANIMATION
   ═══════════════════════════════════════════════════════════════ */
.intro-splash-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 60px 20px 40px 20px;
    text-align: center;
    position: relative;
}

.hologram-orb {
    width: 100px;
    height: 100px;
    border-radius: 50%;
    background: radial-gradient(circle at 35% 35%, #06b6d4 0%, #7c3aed 60%, #0c0c16 100%);
    box-shadow: 0 0 50px rgba(124, 58, 237, 0.6), 0 0 100px rgba(6, 182, 212, 0.4);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2.5rem;
    margin-bottom: 24px;
    animation: orb-float 3s ease-in-out infinite alternate, orb-glow 2s ease-in-out infinite alternate;
    position: relative;
}

.hologram-ring {
    position: absolute;
    width: 130px;
    height: 130px;
    border-radius: 50%;
    border: 2px dashed rgba(6, 182, 212, 0.5);
    animation: ring-spin 8s linear infinite;
}

.hologram-ring-2 {
    position: absolute;
    width: 155px;
    height: 155px;
    border-radius: 50%;
    border: 1px solid rgba(139, 92, 246, 0.3);
    animation: ring-spin-reverse 12s linear infinite;
}

@keyframes orb-float {
    0% { transform: translateY(0px) scale(1); }
    100% { transform: translateY(-10px) scale(1.05); }
}

@keyframes orb-glow {
    0% { box-shadow: 0 0 35px rgba(124, 58, 237, 0.5), 0 0 60px rgba(6, 182, 212, 0.3); }
    100% { box-shadow: 0 0 65px rgba(124, 58, 237, 0.8), 0 0 110px rgba(6, 182, 212, 0.6); }
}

@keyframes ring-spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

@keyframes ring-spin-reverse {
    from { transform: rotate(360deg); }
    to { transform: rotate(0deg); }
}

.shimmer-title {
    font-size: 2.6rem;
    font-weight: 800;
    letter-spacing: -0.04em;
    background: linear-gradient(90deg, #fff 0%, #c4b5fd 40%, #67e8f9 70%, #fff 100%);
    background-size: 200% auto;
    color: transparent;
    -webkit-background-clip: text;
    animation: shimmer-text 3.5s linear infinite;
    margin: 8px 0 6px 0;
}

@keyframes shimmer-text {
    0% { background-position: 0% 50%; }
    100% { background-position: 200% 50%; }
}

.pulse-subtitle {
    color: var(--text-secondary);
    font-size: 0.95rem;
    letter-spacing: 0.02em;
    max-width: 500px;
    margin: 0 auto 16px auto;
}

.loader-bar-wrap {
    width: 260px;
    height: 4px;
    background: rgba(255, 255, 255, 0.08);
    border-radius: 2px;
    overflow: hidden;
    margin: 12px auto;
}

.loader-bar-fill {
    height: 100%;
    width: 40%;
    background: linear-gradient(90deg, #7c3aed, #06b6d4);
    border-radius: 2px;
    animation: loader-slide 1.8s ease-in-out infinite;
}

@keyframes loader-slide {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(350%); }
}
</style>
"""
