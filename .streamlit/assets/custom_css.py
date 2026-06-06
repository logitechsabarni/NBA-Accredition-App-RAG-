"""
assets/custom_css.py
IBM Watsonx-branded enterprise dark theme with glassmorphism.
Inject via st.markdown(get_css(), unsafe_allow_html=True) in app.py.
"""

from __future__ import annotations


def get_css() -> str:
    return """
<style>
/* ═══════════════════════════════════════════════════════════════
   FONTS
═══════════════════════════════════════════════════════════════ */
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600&family=IBM+Plex+Sans:wght@300;400;500;600;700&family=IBM+Plex+Serif:wght@400;500&display=swap');

/* ═══════════════════════════════════════════════════════════════
   CSS VARIABLES – IBM CARBON DARK + WATSONX ACCENT
═══════════════════════════════════════════════════════════════ */
:root {
  /* Carbon Dark surfaces */
  --bg-base:       #0f1117;
  --bg-layer-01:   #161b22;
  --bg-layer-02:   #1c2333;
  --bg-layer-03:   #21283a;
  --bg-overlay:    rgba(15,17,23,0.85);

  /* Watsonx brand */
  --wx-blue:       #0f62fe;
  --wx-blue-hover: #0353e9;
  --wx-blue-light: #4589ff;
  --wx-cyan:       #33b1ff;
  --wx-purple:     #be95ff;
  --wx-teal:       #3ddbd9;
  --wx-green:      #42be65;
  --wx-yellow:     #f1c21b;
  --wx-red:        #fa4d56;
  --wx-orange:     #ff832b;

  /* Text hierarchy */
  --text-primary:   #f4f4f4;
  --text-secondary: #c6c6c6;
  --text-helper:    #8d8d8d;
  --text-disabled:  #525252;
  --text-inverse:   #161616;

  /* Borders */
  --border-subtle:   rgba(255,255,255,0.06);
  --border-strong:   rgba(255,255,255,0.12);
  --border-focus:    #0f62fe;
  --border-inverse:  rgba(255,255,255,0.20);

  /* Glass */
  --glass-bg:     rgba(28, 35, 51, 0.60);
  --glass-border: rgba(255, 255, 255, 0.08);
  --glass-blur:   blur(16px);
  --glass-shadow: 0 8px 32px rgba(0,0,0,0.45);

  /* Gradients */
  --grad-blue:    linear-gradient(135deg, #0f62fe 0%, #4589ff 100%);
  --grad-cyan:    linear-gradient(135deg, #33b1ff 0%, #3ddbd9 100%);
  --grad-purple:  linear-gradient(135deg, #8a3ffc 0%, #be95ff 100%);
  --grad-green:   linear-gradient(135deg, #198038 0%, #42be65 100%);
  --grad-dark:    linear-gradient(180deg, #161b22 0%, #0f1117 100%);

  /* Typography */
  --font-sans:  'IBM Plex Sans', sans-serif;
  --font-mono:  'IBM Plex Mono', monospace;
  --font-serif: 'IBM Plex Serif', serif;

  /* Sizing */
  --radius-sm:  4px;
  --radius-md:  8px;
  --radius-lg:  12px;
  --radius-xl:  16px;
  --radius-2xl: 24px;

  /* Animation */
  --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
  --ease-smooth: cubic-bezier(0.4, 0, 0.2, 1);
  --dur-fast:  150ms;
  --dur-base:  250ms;
  --dur-slow:  400ms;
}

/* ═══════════════════════════════════════════════════════════════
   GLOBAL RESET & BASE
═══════════════════════════════════════════════════════════════ */
*, *::before, *::after { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"],
[data-testid="stApp"] {
  background-color: var(--bg-base) !important;
  color: var(--text-primary) !important;
  font-family: var(--font-sans) !important;
  -webkit-font-smoothing: antialiased;
}

/* Noise texture overlay */
[data-testid="stApp"]::before {
  content: '';
  position: fixed;
  inset: 0;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.03'/%3E%3C/svg%3E");
  pointer-events: none;
  z-index: 9999;
  opacity: 0.4;
}

/* Ambient glow top-left */
[data-testid="stApp"]::after {
  content: '';
  position: fixed;
  top: -200px; left: -200px;
  width: 600px; height: 600px;
  background: radial-gradient(circle, rgba(15,98,254,0.12) 0%, transparent 70%);
  pointer-events: none;
  z-index: 0;
}

/* ═══════════════════════════════════════════════════════════════
   STREAMLIT CHROME CLEANUP
═══════════════════════════════════════════════════════════════ */
#MainMenu, footer, header { visibility: hidden !important; }
[data-testid="stToolbar"] { display: none !important; }
[data-testid="stSidebar"] > div:first-child { padding-top: 0 !important; }
.block-container {
  padding: 0 !important;
  max-width: 100% !important;
}
section[data-testid="stSidebar"] {
  background: var(--bg-layer-01) !important;
  border-right: 1px solid var(--border-subtle) !important;
  width: 260px !important;
}

/* ═══════════════════════════════════════════════════════════════
   TYPOGRAPHY
═══════════════════════════════════════════════════════════════ */
h1 { font-size: 2rem; font-weight: 600; letter-spacing: -0.02em; line-height: 1.2; color: var(--text-primary); }
h2 { font-size: 1.5rem; font-weight: 600; letter-spacing: -0.01em; color: var(--text-primary); }
h3 { font-size: 1.125rem; font-weight: 500; color: var(--text-primary); }
p, li { font-size: 0.9375rem; line-height: 1.6; color: var(--text-secondary); }
code, pre { font-family: var(--font-mono) !important; }

/* ═══════════════════════════════════════════════════════════════
   GLASS CARD BASE
═══════════════════════════════════════════════════════════════ */
.glass-card {
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--glass-shadow);
  transition: border-color var(--dur-base) var(--ease-smooth),
              box-shadow var(--dur-base) var(--ease-smooth),
              transform var(--dur-base) var(--ease-smooth);
}
.glass-card:hover {
  border-color: rgba(255,255,255,0.15);
  box-shadow: 0 12px 40px rgba(0,0,0,0.55);
  transform: translateY(-1px);
}

/* ═══════════════════════════════════════════════════════════════
   KPI / METRIC CARDS
═══════════════════════════════════════════════════════════════ */
.kpi-card {
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-lg);
  padding: 1.25rem 1.5rem;
  position: relative;
  overflow: hidden;
  transition: all var(--dur-base) var(--ease-smooth);
}
.kpi-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 3px;
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
}
.kpi-card.blue::before   { background: var(--grad-blue); }
.kpi-card.cyan::before   { background: var(--grad-cyan); }
.kpi-card.purple::before { background: var(--grad-purple); }
.kpi-card.green::before  { background: var(--grad-green); }
.kpi-card.yellow::before { background: linear-gradient(90deg, #f1c21b, #ff832b); }
.kpi-card.red::before    { background: linear-gradient(90deg, #fa4d56, #ff832b); }

.kpi-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 16px 48px rgba(0,0,0,0.5);
  border-color: rgba(255,255,255,0.14);
}
.kpi-label {
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-helper);
  margin-bottom: 0.5rem;
}
.kpi-value {
  font-size: 2.25rem;
  font-weight: 600;
  line-height: 1;
  color: var(--text-primary);
  font-variant-numeric: tabular-nums;
}
.kpi-delta {
  font-size: 0.8125rem;
  font-weight: 500;
  margin-top: 0.375rem;
  font-family: var(--font-mono);
}
.kpi-delta.positive { color: var(--wx-green); }
.kpi-delta.negative { color: var(--wx-red); }
.kpi-delta.neutral  { color: var(--text-helper); }
.kpi-icon {
  position: absolute;
  top: 1.25rem; right: 1.25rem;
  width: 36px; height: 36px;
  border-radius: var(--radius-md);
  display: flex; align-items: center; justify-content: center;
  font-size: 1.125rem;
}

/* Shimmer animation for loading */
@keyframes shimmer {
  0%   { background-position: -200% 0; }
  100% { background-position:  200% 0; }
}
.kpi-skeleton {
  background: linear-gradient(90deg,
    var(--bg-layer-02) 25%,
    var(--bg-layer-03) 50%,
    var(--bg-layer-02) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: var(--radius-lg);
  height: 110px;
}

/* Number count-up animation */
@keyframes countUp {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}
.kpi-value { animation: countUp var(--dur-slow) var(--ease-spring) both; }

/* ═══════════════════════════════════════════════════════════════
   SIDEBAR NAVIGATION
═══════════════════════════════════════════════════════════════ */
.sidebar-logo {
  padding: 1.5rem 1.25rem 1rem;
  border-bottom: 1px solid var(--border-subtle);
  margin-bottom: 0.75rem;
}
.sidebar-logo-text {
  font-size: 1.125rem;
  font-weight: 700;
  letter-spacing: -0.01em;
  color: var(--text-primary);
}
.sidebar-logo-sub {
  font-size: 0.6875rem;
  font-family: var(--font-mono);
  color: var(--wx-blue-light);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  margin-top: 2px;
}

.sidebar-section-label {
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--text-disabled);
  padding: 0.75rem 1.25rem 0.25rem;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  padding: 0.5625rem 1.25rem;
  margin: 1px 0.5rem;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--dur-fast) var(--ease-smooth);
  font-size: 0.875rem;
  font-weight: 400;
  color: var(--text-secondary);
  text-decoration: none;
  border: 1px solid transparent;
}
.nav-item:hover {
  background: rgba(255,255,255,0.05);
  color: var(--text-primary);
}
.nav-item.active {
  background: rgba(15,98,254,0.15);
  border-color: rgba(15,98,254,0.30);
  color: var(--wx-blue-light);
  font-weight: 500;
}
.nav-item.active .nav-icon { color: var(--wx-blue); }
.nav-icon { font-size: 1rem; width: 1.125rem; text-align: center; }

.sidebar-footer {
  padding: 1rem 1.25rem;
  border-top: 1px solid var(--border-subtle);
  margin-top: auto;
}
.sidebar-status-dot {
  display: inline-block;
  width: 7px; height: 7px;
  border-radius: 50%;
  margin-right: 6px;
}
.sidebar-status-dot.online  { background: var(--wx-green); box-shadow: 0 0 6px var(--wx-green); }
.sidebar-status-dot.offline { background: var(--wx-red); }
.sidebar-status-dot.warning { background: var(--wx-yellow); }

/* ═══════════════════════════════════════════════════════════════
   TOP NAVBAR
═══════════════════════════════════════════════════════════════ */
.top-navbar {
  background: rgba(22, 27, 34, 0.90);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--border-subtle);
  padding: 0.75rem 1.75rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: sticky;
  top: 0;
  z-index: 100;
}
.navbar-breadcrumb {
  font-size: 0.8125rem;
  color: var(--text-helper);
  font-family: var(--font-mono);
}
.navbar-breadcrumb span { color: var(--text-primary); font-weight: 500; }
.navbar-actions { display: flex; align-items: center; gap: 0.75rem; }

.badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 99px;
  font-size: 0.6875rem;
  font-weight: 600;
  font-family: var(--font-mono);
  letter-spacing: 0.03em;
}
.badge-blue   { background: rgba(15,98,254,0.18);  color: var(--wx-blue-light); border: 1px solid rgba(15,98,254,0.35); }
.badge-green  { background: rgba(66,190,101,0.15); color: var(--wx-green);      border: 1px solid rgba(66,190,101,0.30); }
.badge-red    { background: rgba(250,77,86,0.15);  color: var(--wx-red);        border: 1px solid rgba(250,77,86,0.30); }
.badge-yellow { background: rgba(241,194,27,0.15); color: var(--wx-yellow);     border: 1px solid rgba(241,194,27,0.30); }
.badge-purple { background: rgba(190,149,255,0.12);color: var(--wx-purple);     border: 1px solid rgba(190,149,255,0.25); }
.badge-cyan   { background: rgba(51,177,255,0.12); color: var(--wx-cyan);       border: 1px solid rgba(51,177,255,0.25); }

/* ═══════════════════════════════════════════════════════════════
   CHAT INTERFACE
═══════════════════════════════════════════════════════════════ */
.chat-container {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 180px);
  background: transparent;
}
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  scroll-behavior: smooth;
}
.chat-messages::-webkit-scrollbar { width: 4px; }
.chat-messages::-webkit-scrollbar-track { background: transparent; }
.chat-messages::-webkit-scrollbar-thumb {
  background: var(--border-strong);
  border-radius: 99px;
}

.message-row {
  display: flex;
  gap: 0.875rem;
  align-items: flex-start;
  animation: messageIn var(--dur-slow) var(--ease-spring) both;
}
@keyframes messageIn {
  from { opacity: 0; transform: translateY(10px) scale(0.98); }
  to   { opacity: 1; transform: translateY(0) scale(1); }
}
.message-row.user { flex-direction: row-reverse; }

.avatar {
  width: 32px; height: 32px;
  border-radius: var(--radius-md);
  flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.875rem; font-weight: 600;
}
.avatar-user { background: var(--grad-blue); color: white; }
.avatar-ai   { background: linear-gradient(135deg, #8a3ffc, #33b1ff); color: white; }

.message-bubble {
  max-width: 75%;
  padding: 0.875rem 1.125rem;
  border-radius: var(--radius-lg);
  line-height: 1.65;
  font-size: 0.9375rem;
  position: relative;
}
.message-bubble.user {
  background: rgba(15,98,254,0.20);
  border: 1px solid rgba(15,98,254,0.30);
  color: var(--text-primary);
  border-bottom-right-radius: var(--radius-sm);
}
.message-bubble.ai {
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  color: var(--text-primary);
  border-bottom-left-radius: var(--radius-sm);
  backdrop-filter: var(--glass-blur);
}
.message-timestamp {
  font-size: 0.6875rem;
  color: var(--text-disabled);
  margin-top: 0.25rem;
  font-family: var(--font-mono);
}
.message-sources {
  margin-top: 0.75rem;
  padding: 0.625rem 0.875rem;
  background: rgba(255,255,255,0.03);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  font-size: 0.8125rem;
}
.source-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 4px;
  background: rgba(51,177,255,0.10);
  border: 1px solid rgba(51,177,255,0.20);
  color: var(--wx-cyan);
  font-size: 0.6875rem;
  font-family: var(--font-mono);
  margin: 2px;
}

/* Streaming cursor */
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }
.cursor-blink {
  display: inline-block;
  width: 2px; height: 1em;
  background: var(--wx-blue-light);
  animation: blink 1s step-end infinite;
  vertical-align: text-bottom;
  margin-left: 2px;
}

.chat-input-area {
  padding: 1rem 1.5rem 1.25rem;
  border-top: 1px solid var(--border-subtle);
  background: rgba(15,17,23,0.8);
  backdrop-filter: blur(20px);
}
.chat-input-wrapper {
  background: var(--bg-layer-02);
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-xl);
  transition: border-color var(--dur-fast) var(--ease-smooth),
              box-shadow var(--dur-fast) var(--ease-smooth);
  overflow: hidden;
}
.chat-input-wrapper:focus-within {
  border-color: var(--wx-blue);
  box-shadow: 0 0 0 3px rgba(15,98,254,0.15);
}

/* ═══════════════════════════════════════════════════════════════
   WORKFLOW VISUALIZER
═══════════════════════════════════════════════════════════════ */
.workflow-container {
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-xl);
  padding: 2rem;
  backdrop-filter: var(--glass-blur);
}
.workflow-title {
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--text-helper);
  margin-bottom: 1.5rem;
  font-family: var(--font-mono);
}

.wf-node {
  display: flex;
  align-items: center;
  gap: 0.875rem;
  padding: 0.875rem 1.125rem;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-subtle);
  background: var(--bg-layer-02);
  position: relative;
  transition: all var(--dur-base) var(--ease-smooth);
}
.wf-node.active {
  border-color: var(--wx-blue);
  background: rgba(15,98,254,0.08);
  box-shadow: 0 0 0 1px rgba(15,98,254,0.20), 0 4px 20px rgba(15,98,254,0.15);
}
.wf-node.completed {
  border-color: rgba(66,190,101,0.30);
  background: rgba(66,190,101,0.06);
}
.wf-node.failed {
  border-color: rgba(250,77,86,0.30);
  background: rgba(250,77,86,0.06);
}
.wf-node.pending {
  opacity: 0.5;
}

.wf-node-icon {
  width: 36px; height: 36px;
  border-radius: var(--radius-md);
  display: flex; align-items: center; justify-content: center;
  font-size: 1rem;
  flex-shrink: 0;
}
.wf-node-icon.blue   { background: rgba(15,98,254,0.15); }
.wf-node-icon.green  { background: rgba(66,190,101,0.15); }
.wf-node-icon.purple { background: rgba(190,149,255,0.15); }
.wf-node-icon.cyan   { background: rgba(51,177,255,0.15); }
.wf-node-icon.yellow { background: rgba(241,194,27,0.15); }
.wf-node-icon.red    { background: rgba(250,77,86,0.15); }

.wf-node-content { flex: 1; min-width: 0; }
.wf-node-name {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.wf-node-desc {
  font-size: 0.75rem;
  color: var(--text-helper);
  margin-top: 1px;
  font-family: var(--font-mono);
}

.wf-status-pill {
  font-size: 0.6875rem;
  font-weight: 600;
  font-family: var(--font-mono);
  padding: 2px 8px;
  border-radius: 99px;
}
.wf-status-pill.running  {
  background: rgba(15,98,254,0.20);
  color: var(--wx-blue-light);
  animation: pulse-blue 1.5s ease-in-out infinite;
}
.wf-status-pill.done     { background: rgba(66,190,101,0.15);  color: var(--wx-green); }
.wf-status-pill.error    { background: rgba(250,77,86,0.15);   color: var(--wx-red); }
.wf-status-pill.waiting  { background: rgba(255,255,255,0.06); color: var(--text-helper); }

@keyframes pulse-blue {
  0%,100% { box-shadow: 0 0 0 0 rgba(15,98,254,0.4); }
  50%      { box-shadow: 0 0 0 4px rgba(15,98,254,0); }
}

.wf-connector {
  display: flex;
  align-items: center;
  padding: 0 1.125rem;
  height: 28px;
  color: var(--text-disabled);
  font-size: 0.75rem;
  gap: 0.5rem;
  font-family: var(--font-mono);
}
.wf-connector-line {
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, var(--border-subtle), var(--border-strong), var(--border-subtle));
}

/* Execution pulse */
@keyframes executionPulse {
  0%   { transform: scale(1); opacity: 1; }
  50%  { transform: scale(1.05); opacity: 0.8; }
  100% { transform: scale(1); opacity: 1; }
}
.wf-node.active { animation: executionPulse 2s ease-in-out infinite; }

/* ═══════════════════════════════════════════════════════════════
   TIMELINE
═══════════════════════════════════════════════════════════════ */
.timeline {
  position: relative;
  padding-left: 1.5rem;
}
.timeline::before {
  content: '';
  position: absolute;
  left: 0; top: 0; bottom: 0;
  width: 2px;
  background: linear-gradient(180deg, var(--wx-blue) 0%, transparent 100%);
}
.timeline-item {
  position: relative;
  padding-bottom: 1.25rem;
  padding-left: 1.25rem;
}
.timeline-item::before {
  content: '';
  position: absolute;
  left: -1.6rem; top: 5px;
  width: 10px; height: 10px;
  border-radius: 50%;
  border: 2px solid var(--bg-layer-01);
}
.timeline-item.completed::before { background: var(--wx-green); }
.timeline-item.running::before   { background: var(--wx-blue); animation: pulse-blue 1.5s infinite; }
.timeline-item.pending::before   { background: var(--border-strong); }
.timeline-item.failed::before    { background: var(--wx-red); }

.timeline-time {
  font-size: 0.6875rem;
  color: var(--text-helper);
  font-family: var(--font-mono);
  margin-bottom: 2px;
}
.timeline-event {
  font-size: 0.875rem;
  color: var(--text-primary);
  font-weight: 500;
}
.timeline-detail {
  font-size: 0.8125rem;
  color: var(--text-secondary);
  margin-top: 2px;
}

/* ═══════════════════════════════════════════════════════════════
   AGENT CARDS
═══════════════════════════════════════════════════════════════ */
.agent-card {
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-lg);
  padding: 1.25rem;
  transition: all var(--dur-base) var(--ease-smooth);
  cursor: pointer;
  position: relative;
  overflow: hidden;
}
.agent-card::after {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at top right, rgba(15,98,254,0.05), transparent 60%);
  pointer-events: none;
}
.agent-card:hover {
  border-color: rgba(15,98,254,0.30);
  box-shadow: 0 8px 32px rgba(0,0,0,0.4), 0 0 0 1px rgba(15,98,254,0.15);
  transform: translateY(-2px);
}
.agent-card-header {
  display: flex; align-items: center; gap: 0.75rem;
  margin-bottom: 0.875rem;
}
.agent-avatar {
  width: 40px; height: 40px;
  border-radius: var(--radius-md);
  display: flex; align-items: center; justify-content: center;
  font-size: 1.25rem;
}
.agent-name {
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--text-primary);
}
.agent-id {
  font-size: 0.6875rem;
  color: var(--text-helper);
  font-family: var(--font-mono);
}
.agent-description {
  font-size: 0.8125rem;
  color: var(--text-secondary);
  line-height: 1.5;
  margin-bottom: 0.875rem;
}
.agent-capabilities {
  display: flex; flex-wrap: wrap; gap: 4px;
}

/* ═══════════════════════════════════════════════════════════════
   CHARTS
═══════════════════════════════════════════════════════════════ */
.chart-wrapper {
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-lg);
  padding: 1.25rem 1.5rem;
}
.chart-title {
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 0.25rem;
}
.chart-subtitle {
  font-size: 0.8125rem;
  color: var(--text-helper);
  font-family: var(--font-mono);
  margin-bottom: 1rem;
}

/* ═══════════════════════════════════════════════════════════════
   UPLOAD WIDGET
═══════════════════════════════════════════════════════════════ */
.upload-zone {
  border: 2px dashed var(--border-strong);
  border-radius: var(--radius-xl);
  padding: 2.5rem;
  text-align: center;
  cursor: pointer;
  transition: all var(--dur-base) var(--ease-smooth);
  background: rgba(255,255,255,0.01);
  position: relative;
  overflow: hidden;
}
.upload-zone:hover, .upload-zone.drag-over {
  border-color: var(--wx-blue);
  background: rgba(15,98,254,0.04);
  box-shadow: inset 0 0 0 1px rgba(15,98,254,0.15);
}
.upload-icon {
  font-size: 2.5rem;
  margin-bottom: 0.75rem;
  display: block;
}
.upload-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 0.25rem;
}
.upload-subtitle {
  font-size: 0.8125rem;
  color: var(--text-helper);
}
.upload-formats {
  margin-top: 0.75rem;
  font-size: 0.75rem;
  font-family: var(--font-mono);
  color: var(--text-disabled);
}
.upload-progress {
  margin-top: 1rem;
  height: 4px;
  border-radius: 99px;
  background: var(--border-subtle);
  overflow: hidden;
}
.upload-progress-bar {
  height: 100%;
  background: var(--grad-blue);
  border-radius: 99px;
  transition: width 0.3s ease;
}
.uploaded-file-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem 0.875rem;
  border-radius: var(--radius-md);
  background: var(--bg-layer-02);
  border: 1px solid var(--border-subtle);
  margin-bottom: 0.5rem;
  animation: messageIn var(--dur-base) var(--ease-spring) both;
}
.file-icon { font-size: 1.125rem; }
.file-name {
  flex: 1;
  font-size: 0.875rem;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.file-size {
  font-size: 0.75rem;
  font-family: var(--font-mono);
  color: var(--text-helper);
}

/* ═══════════════════════════════════════════════════════════════
   STREAMLIT COMPONENT OVERRIDES
═══════════════════════════════════════════════════════════════ */

/* Inputs */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div > div {
  background: var(--bg-layer-02) !important;
  border: 1px solid var(--border-strong) !important;
  border-radius: var(--radius-md) !important;
  color: var(--text-primary) !important;
  font-family: var(--font-sans) !important;
  font-size: 0.9375rem !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
  border-color: var(--wx-blue) !important;
  box-shadow: 0 0 0 3px rgba(15,98,254,0.15) !important;
  outline: none !important;
}

/* Labels */
.stTextInput label, .stTextArea label,
.stSelectbox label, .stSlider label,
.stNumberInput label {
  color: var(--text-secondary) !important;
  font-size: 0.8125rem !important;
  font-weight: 500 !important;
}

/* Buttons */
.stButton > button {
  background: var(--wx-blue) !important;
  color: white !important;
  border: none !important;
  border-radius: var(--radius-md) !important;
  font-family: var(--font-sans) !important;
  font-size: 0.875rem !important;
  font-weight: 500 !important;
  padding: 0.5rem 1.25rem !important;
  transition: all var(--dur-fast) var(--ease-smooth) !important;
}
.stButton > button:hover {
  background: var(--wx-blue-hover) !important;
  box-shadow: 0 4px 14px rgba(15,98,254,0.40) !important;
  transform: translateY(-1px) !important;
}
.stButton > button:active { transform: translateY(0) !important; }

/* Secondary button override via class trick */
.stButton[data-secondary="true"] > button {
  background: transparent !important;
  border: 1px solid var(--border-strong) !important;
  color: var(--text-primary) !important;
}
.stButton[data-secondary="true"] > button:hover {
  background: rgba(255,255,255,0.05) !important;
  box-shadow: none !important;
}

/* Slider */
.stSlider > div > div > div > div {
  background: var(--wx-blue) !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
  background: transparent !important;
  border-bottom: 1px solid var(--border-subtle) !important;
  gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
  background: transparent !important;
  color: var(--text-helper) !important;
  font-size: 0.875rem !important;
  font-weight: 500 !important;
  padding: 0.625rem 1.25rem !important;
  border-radius: 0 !important;
  border-bottom: 2px solid transparent !important;
  transition: all var(--dur-fast) !important;
}
.stTabs [data-baseweb="tab"]:hover { color: var(--text-primary) !important; }
.stTabs [aria-selected="true"] {
  color: var(--wx-blue-light) !important;
  border-bottom-color: var(--wx-blue) !important;
}
[data-baseweb="tab-panel"] {
  padding: 1.25rem 0 0 !important;
  background: transparent !important;
}

/* Expander */
.streamlit-expanderHeader {
  background: var(--bg-layer-02) !important;
  border: 1px solid var(--border-subtle) !important;
  border-radius: var(--radius-md) !important;
  color: var(--text-primary) !important;
  font-size: 0.9375rem !important;
}
.streamlit-expanderContent {
  background: var(--bg-layer-01) !important;
  border: 1px solid var(--border-subtle) !important;
  border-top: none !important;
  border-radius: 0 0 var(--radius-md) var(--radius-md) !important;
}

/* Metrics */
[data-testid="stMetric"] {
  background: var(--glass-bg) !important;
  border: 1px solid var(--glass-border) !important;
  border-radius: var(--radius-lg) !important;
  padding: 1rem 1.25rem !important;
  backdrop-filter: var(--glass-blur) !important;
}
[data-testid="stMetricLabel"] { color: var(--text-helper) !important; font-size: 0.75rem !important; text-transform: uppercase; letter-spacing: 0.06em; }
[data-testid="stMetricValue"] { color: var(--text-primary) !important; font-size: 2rem !important; font-weight: 600 !important; }
[data-testid="stMetricDelta"] > div { font-family: var(--font-mono) !important; font-size: 0.8125rem !important; }

/* Info / Warning / Error / Success boxes */
.stAlert {
  border-radius: var(--radius-md) !important;
  border-left-width: 3px !important;
  font-size: 0.875rem !important;
}

/* Dataframe */
[data-testid="stDataFrame"] {
  border-radius: var(--radius-lg) !important;
  overflow: hidden !important;
  border: 1px solid var(--border-subtle) !important;
}

/* Progress bar */
.stProgress > div > div {
  background: var(--border-subtle) !important;
  border-radius: 99px !important;
}
.stProgress > div > div > div {
  background: var(--grad-blue) !important;
  border-radius: 99px !important;
  transition: width 0.5s ease !important;
}

/* Spinner */
.stSpinner > div { border-top-color: var(--wx-blue) !important; }

/* Divider */
hr { border-color: var(--border-subtle) !important; }

/* Scrollbar global */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border-strong); border-radius: 99px; }
::-webkit-scrollbar-thumb:hover { background: var(--border-inverse); }

/* ═══════════════════════════════════════════════════════════════
   UTILITY CLASSES
═══════════════════════════════════════════════════════════════ */
.flex          { display: flex; }
.flex-col      { flex-direction: column; }
.items-center  { align-items: center; }
.justify-between { justify-content: space-between; }
.gap-1 { gap: 0.25rem; }
.gap-2 { gap: 0.5rem; }
.gap-3 { gap: 0.75rem; }
.gap-4 { gap: 1rem; }

.text-mono  { font-family: var(--font-mono); }
.text-xs    { font-size: 0.75rem; }
.text-sm    { font-size: 0.875rem; }
.text-base  { font-size: 0.9375rem; }
.text-lg    { font-size: 1.125rem; }
.text-xl    { font-size: 1.25rem; }
.text-2xl   { font-size: 1.5rem; }

.text-primary   { color: var(--text-primary); }
.text-secondary { color: var(--text-secondary); }
.text-helper    { color: var(--text-helper); }
.text-disabled  { color: var(--text-disabled); }
.text-blue      { color: var(--wx-blue-light); }
.text-green     { color: var(--wx-green); }
.text-red       { color: var(--wx-red); }
.text-yellow    { color: var(--wx-yellow); }
.text-cyan      { color: var(--wx-cyan); }
.text-purple    { color: var(--wx-purple); }

.font-medium { font-weight: 500; }
.font-bold   { font-weight: 600; }

.mt-1 { margin-top: 0.25rem; }
.mt-2 { margin-top: 0.5rem; }
.mt-3 { margin-top: 0.75rem; }
.mt-4 { margin-top: 1rem; }
.mb-1 { margin-bottom: 0.25rem; }
.mb-2 { margin-bottom: 0.5rem; }
.mb-3 { margin-bottom: 0.75rem; }
.mb-4 { margin-bottom: 1rem; }
.p-2  { padding: 0.5rem; }
.p-3  { padding: 0.75rem; }
.p-4  { padding: 1rem; }

.rounded-sm { border-radius: var(--radius-sm); }
.rounded-md { border-radius: var(--radius-md); }
.rounded-lg { border-radius: var(--radius-lg); }
.rounded-xl { border-radius: var(--radius-xl); }

.border         { border: 1px solid var(--border-subtle); }
.border-strong  { border: 1px solid var(--border-strong); }
.bg-layer-01    { background: var(--bg-layer-01); }
.bg-layer-02    { background: var(--bg-layer-02); }
.bg-layer-03    { background: var(--bg-layer-03); }

/* Fade-in page animation */
@keyframes pageFadeIn {
  from { opacity: 0; transform: translateY(6px); }
  to   { opacity: 1; transform: translateY(0); }
}
.page-content {
  animation: pageFadeIn var(--dur-slow) var(--ease-smooth) both;
}

/* Glow effects */
.glow-blue   { box-shadow: 0 0 20px rgba(15,98,254,0.25); }
.glow-green  { box-shadow: 0 0 20px rgba(66,190,101,0.25); }
.glow-red    { box-shadow: 0 0 20px rgba(250,77,86,0.25); }
.glow-purple { box-shadow: 0 0 20px rgba(190,149,255,0.25); }

/* Truncate */
.truncate { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

/* Loading dots */
@keyframes loadDots {
  0%,80%,100% { transform: scale(0); opacity: 0.5; }
  40%          { transform: scale(1); opacity: 1; }
}
.loading-dot {
  display: inline-block;
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--wx-blue-light);
  animation: loadDots 1.4s infinite ease-in-out;
  margin: 0 2px;
}
.loading-dot:nth-child(2) { animation-delay: 0.16s; }
.loading-dot:nth-child(3) { animation-delay: 0.32s; }

/* ═══════════════════════════════════════════════════════════════
   SECTION HEADERS
═══════════════════════════════════════════════════════════════ */
.section-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1.25rem;
}
.section-header-line {
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, var(--border-strong), transparent);
}
.section-title {
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--text-helper);
  font-family: var(--font-mono);
  white-space: nowrap;
}

/* ═══════════════════════════════════════════════════════════════
   STATUS INDICATORS
═══════════════════════════════════════════════════════════════ */
.status-indicator {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.75rem;
  font-family: var(--font-mono);
  font-weight: 500;
}
.status-dot {
  width: 7px; height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}
.status-dot.online  { background: var(--wx-green);  box-shadow: 0 0 6px var(--wx-green); animation: pulse-green 2s infinite; }
.status-dot.offline { background: var(--wx-red); }
.status-dot.warning { background: var(--wx-yellow); animation: pulse-yellow 2s infinite; }
.status-dot.idle    { background: var(--text-disabled); }
@keyframes pulse-green  { 0%,100%{box-shadow:0 0 0 0 rgba(66,190,101,0.5)} 50%{box-shadow:0 0 0 4px rgba(66,190,101,0)} }
@keyframes pulse-yellow { 0%,100%{box-shadow:0 0 0 0 rgba(241,194,27,0.5)} 50%{box-shadow:0 0 0 4px rgba(241,194,27,0)} }

/* ═══════════════════════════════════════════════════════════════
   WATSONX BRANDING ELEMENTS
═══════════════════════════════════════════════════════════════ */
.watsonx-logo-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 4px;
  background: linear-gradient(135deg, rgba(15,98,254,0.15), rgba(51,177,255,0.10));
  border: 1px solid rgba(15,98,254,0.25);
  font-size: 0.75rem;
  font-weight: 600;
  font-family: var(--font-mono);
  letter-spacing: 0.05em;
  color: var(--wx-blue-light);
}
.watsonx-logo-badge::before {
  content: '◆';
  color: var(--wx-blue);
}

/* IBM Carbon Design System inspired data table */
.carbon-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  font-size: 0.875rem;
}
.carbon-table thead tr { background: var(--bg-layer-02); }
.carbon-table th {
  padding: 0.75rem 1rem;
  text-align: left;
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-helper);
  border-bottom: 1px solid var(--border-strong);
}
.carbon-table td {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--border-subtle);
  color: var(--text-secondary);
}
.carbon-table tbody tr {
  transition: background var(--dur-fast);
}
.carbon-table tbody tr:hover { background: rgba(255,255,255,0.03); }
.carbon-table tbody tr:last-child td { border-bottom: none; }
</style>
"""


def get_plotly_theme() -> dict:
    """Return Plotly layout defaults matching the dark IBM theme."""
    return {
        "template": "plotly_dark",
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"family": "IBM Plex Sans, sans-serif", "color": "#c6c6c6", "size": 12},
        "colorway": [
            "#4589ff", "#33b1ff", "#be95ff", "#42be65",
            "#f1c21b", "#ff832b", "#fa4d56", "#3ddbd9",
        ],
        "xaxis": {
            "gridcolor": "rgba(255,255,255,0.06)",
            "linecolor": "rgba(255,255,255,0.12)",
            "tickfont": {"color": "#8d8d8d", "size": 11},
            "title_font": {"color": "#c6c6c6"},
        },
        "yaxis": {
            "gridcolor": "rgba(255,255,255,0.06)",
            "linecolor": "rgba(255,255,255,0.12)",
            "tickfont": {"color": "#8d8d8d", "size": 11},
            "title_font": {"color": "#c6c6c6"},
        },
        "legend": {
            "bgcolor": "rgba(28,35,51,0.6)",
            "bordercolor": "rgba(255,255,255,0.08)",
            "borderwidth": 1,
            "font": {"color": "#c6c6c6", "size": 11},
        },
        "hoverlabel": {
            "bgcolor": "#1c2333",
            "bordercolor": "rgba(255,255,255,0.12)",
            "font": {"family": "IBM Plex Mono, monospace", "color": "#f4f4f4", "size": 12},
        },
        "margin": {"l": 48, "r": 16, "t": 32, "b": 48},
    }
