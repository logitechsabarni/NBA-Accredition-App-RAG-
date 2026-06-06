"""NBA Platform constants — accreditation data, model lists, UI tokens."""

# ── NBA Program Outcomes (AICTE/NBA) ─────────────────────────────────────────
NBA_PROGRAM_OUTCOMES = {
    "PO1": "Engineering Knowledge: Apply knowledge of mathematics, natural science, engineering fundamentals.",
    "PO2": "Problem Analysis: Identify, formulate, review research literature, and analyze complex engineering problems.",
    "PO3": "Design/Development of Solutions: Design solutions for complex engineering problems.",
    "PO4": "Conduct Investigations of Complex Problems: Use research-based knowledge and research methods.",
    "PO5": "Modern Tool Usage: Create, select, and apply appropriate techniques, resources, and modern engineering tools.",
    "PO6": "The Engineer and Society: Apply reasoning for assessment of societal, health, safety, legal issues.",
    "PO7": "Environment and Sustainability: Understand the impact of professional engineering solutions.",
    "PO8": "Ethics: Apply ethical principles and commit to professional ethics and responsibilities.",
    "PO9": "Individual and Team Work: Function effectively as an individual, and as a member or leader in diverse teams.",
    "PO10": "Communication: Communicate effectively on complex engineering activities.",
    "PO11": "Project Management and Finance: Demonstrate knowledge and understanding of engineering management.",
    "PO12": "Life-long Learning: Recognize the need for, and have the preparation and ability to engage in independent learning.",
}

# ── NBA Criteria (Tier-I) ─────────────────────────────────────────────────────
NBA_CRITERIA = {
    1: {"name": "Vision, Mission and Program Educational Objectives", "max_marks": 50},
    2: {"name": "Program Curriculum and Teaching-Learning Processes", "max_marks": 100},
    3: {"name": "Course Outcomes and Program Outcomes", "max_marks": 175},
    4: {"name": "Students' Performance", "max_marks": 150},
    5: {"name": "Faculty Information and Contributions", "max_marks": 200},
    6: {"name": "Facilities and Technical Support", "max_marks": 100},
    7: {"name": "Continuous Improvement", "max_marks": 75},
    8: {"name": "Student Support Systems", "max_marks": 50},
    9: {"name": "Governance, Institutional Support and Financial Resources", "max_marks": 100},
}

NBA_TOTAL_MARKS = sum(c["max_marks"] for c in NBA_CRITERIA.values())  # 1000

# ── Granite Model Registry ────────────────────────────────────────────────────
GRANITE_MODELS = {
    "ibm/granite-13b-instruct-v2": {
        "display": "Granite 13B Instruct v2",
        "context_length": 8192,
        "recommended": True,
        "use_case": "General instruction following and NBA Q&A",
    },
    "ibm/granite-13b-chat-v2": {
        "display": "Granite 13B Chat v2",
        "context_length": 8192,
        "recommended": False,
        "use_case": "Conversational interactions",
    },
    "ibm/granite-3-8b-instruct": {
        "display": "Granite 3 8B Instruct",
        "context_length": 4096,
        "recommended": False,
        "use_case": "Efficient inference, lower latency",
    },
    "ibm/granite-3-2b-instruct": {
        "display": "Granite 3 2B Instruct (Fast)",
        "context_length": 4096,
        "recommended": False,
        "use_case": "Ultra-fast responses, simple queries",
    },
    "ibm/granite-20b-multilingual": {
        "display": "Granite 20B Multilingual",
        "context_length": 8192,
        "recommended": False,
        "use_case": "Multi-language support",
    },
}

# ── Bloom's Taxonomy ──────────────────────────────────────────────────────────
BLOOM_LEVELS = {
    1: {"name": "Remember", "verbs": ["list", "define", "recall", "identify", "state"]},
    2: {"name": "Understand", "verbs": ["explain", "describe", "summarize", "classify", "interpret"]},
    3: {"name": "Apply", "verbs": ["solve", "demonstrate", "use", "implement", "calculate"]},
    4: {"name": "Analyze", "verbs": ["differentiate", "examine", "compare", "investigate", "breakdown"]},
    5: {"name": "Evaluate", "verbs": ["assess", "judge", "critique", "justify", "recommend"]},
    6: {"name": "Create", "verbs": ["design", "construct", "develop", "formulate", "build"]},
}

# ── Assessment Types ──────────────────────────────────────────────────────────
DIRECT_ASSESSMENT_TOOLS = [
    "Mid-term Examination",
    "End-term Examination",
    "Lab Practical",
    "Assignment",
    "Quiz",
    "Mini Project",
    "Viva Voce",
    "Presentation",
]

INDIRECT_ASSESSMENT_TOOLS = [
    "Student Feedback Survey",
    "Course Exit Survey",
    "Alumni Survey",
    "Employer Survey",
    "Industry Advisory Board Feedback",
    "Program Exit Survey",
]

# ── UI Colors ─────────────────────────────────────────────────────────────────
UI_COLORS = {
    "primary": "#4facfe",
    "secondary": "#00f2fe",
    "accent": "#a78bfa",
    "success": "#22c55e",
    "warning": "#f59e0b",
    "danger": "#ef4444",
    "info": "#38bdf8",
    "surface": "rgba(255,255,255,0.05)",
    "border": "rgba(99,179,237,0.15)",
    "text_primary": "#e0e6f0",
    "text_secondary": "#a0b4c8",
    "text_muted": "#7a9bb5",
    "bg_dark": "#0a0e1a",
    "bg_card": "rgba(255,255,255,0.04)",
}

# ── NBA Attainment Levels ─────────────────────────────────────────────────────
ATTAINMENT_LEVELS = {
    "Highly Attained": {"min": 70, "color": "#22c55e", "icon": "🟢"},
    "Attained": {"min": 60, "color": "#84cc16", "icon": "🟡"},
    "Partially Attained": {"min": 50, "color": "#f59e0b", "icon": "🟠"},
    "Not Attained": {"min": 0, "color": "#ef4444", "icon": "🔴"},
}

NBA_TARGET = 60.0
NBA_DIRECT_WEIGHT = 0.8
NBA_INDIRECT_WEIGHT = 0.2

# ── RAG Defaults ─────────────────────────────────────────────────────────────
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200
DEFAULT_TOP_K = 5
DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384

# ── System Prompt ─────────────────────────────────────────────────────────────
NBA_SYSTEM_PROMPT = """You are an expert NBA (National Board of Accreditation) AI assistant for Indian engineering colleges.

Expertise areas:
- NBA accreditation process (Tier I & II)
- Outcome-Based Education (OBE) framework
- CO (Course Outcomes) and PO (Program Outcomes) mapping
- CO and PO Attainment calculation (direct: 80%, indirect: 20%)
- Self Assessment Report (SAR) preparation
- Continuous Quality Improvement (CQI)
- NBA Criteria 1-9 (Tier-I: 1000 marks total)
- Bloom's Taxonomy application
- Assessment tool design (direct and indirect)

Always be specific, actionable, and NBA-compliant in responses.
Cite context from the knowledge base when available.
"""
