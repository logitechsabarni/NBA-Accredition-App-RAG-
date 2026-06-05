import os
import time
import json
import hashlib
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


def format_timestamp(dt: Optional[datetime] = None) -> str:
    """Format a datetime to a readable string."""
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def file_hash(content: bytes) -> str:
    """Generate SHA-256 hash for file deduplication."""
    return hashlib.sha256(content).hexdigest()[:12]


def format_file_size(size_bytes: int) -> str:
    """Human-readable file size."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def log_query(query: str, response_length: int, source: str = "chat"):
    """Log AI queries for analytics."""
    try:
        log_file = LOG_DIR / "queries.jsonl"
        entry = {
            "timestamp": format_timestamp(),
            "query": query[:200],
            "response_length": response_length,
            "source": source,
        }
        with open(log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        logger.error(f"Query log error: {e}")


def load_query_logs() -> List[Dict]:
    """Load query logs."""
    log_file = LOG_DIR / "queries.jsonl"
    if not log_file.exists():
        return []
    try:
        logs = []
        with open(log_file) as f:
            for line in f:
                try:
                    logs.append(json.loads(line.strip()))
                except Exception:
                    pass
        return logs
    except Exception:
        return []


def save_json(data: Any, path: str):
    """Save data as JSON."""
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


def load_json(path: str) -> Optional[Any]:
    """Load JSON from file."""
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None


def sanitize_filename(name: str) -> str:
    """Make a string safe for use as filename."""
    import re
    return re.sub(r"[^\w\-_\. ]", "_", name).strip()


def retry(func, retries: int = 3, delay: float = 1.0):
    """Retry a function on failure."""
    last_error = None
    for attempt in range(retries):
        try:
            return func()
        except Exception as e:
            last_error = e
            if attempt < retries - 1:
                time.sleep(delay * (attempt + 1))
    raise last_error


def color_for_attainment(value: float, target: float = 60.0) -> str:
    """Return a color hex for attainment visualization."""
    if value >= target + 15:
        return "#22c55e"   # Green
    elif value >= target:
        return "#84cc16"   # Light green
    elif value >= target - 10:
        return "#f59e0b"   # Amber
    elif value >= target - 20:
        return "#f97316"   # Orange
    else:
        return "#ef4444"   # Red


def attainment_emoji(value: float, target: float = 60.0) -> str:
    if value >= target:
        return "✅"
    elif value >= target - 10:
        return "⚠️"
    else:
        return "❌"


def department_benchmarks() -> Dict[str, float]:
    """Synthetic department benchmark data for demo."""
    return {
        "Computer Science": 74.2,
        "Electronics": 68.5,
        "Mechanical": 65.1,
        "Civil": 61.8,
        "Electrical": 70.3,
        "Chemical": 63.4,
        "Information Technology": 72.1,
        "Biotechnology": 58.9,
    }


def generate_sar_sections() -> List[Dict[str, Any]]:
    """Return NBA SAR section definitions."""
    return [
        {"id": "1", "title": "Departmental Overview", "weight": 5, "subsections": ["Vision & Mission", "PEOs", "Program Objectives"]},
        {"id": "2", "title": "Program Curriculum", "weight": 15, "subsections": ["Curriculum Design", "CO-PO Mapping", "Syllabus"]},
        {"id": "3", "title": "Course Outcomes Attainment", "weight": 20, "subsections": ["CO Definition", "Assessment Methods", "Attainment Results"]},
        {"id": "4", "title": "PO/PSO Attainment", "weight": 20, "subsections": ["PO Mapping", "PO Attainment", "PSO Attainment"]},
        {"id": "5", "title": "Faculty Information", "weight": 10, "subsections": ["Faculty Qualifications", "Research Output", "Training"]},
        {"id": "6", "title": "Infrastructure", "weight": 10, "subsections": ["Classrooms", "Labs", "Library"]},
        {"id": "7", "title": "Student Performance", "weight": 10, "subsections": ["Results Analysis", "Placements", "Higher Studies"]},
        {"id": "8", "title": "Continuous Improvement", "weight": 10, "subsections": ["CQI Process", "Action Plans", "Feedback"]},
    ]
