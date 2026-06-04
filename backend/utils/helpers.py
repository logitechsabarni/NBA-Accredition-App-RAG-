from typing import Any, Dict
import json


def safe_json_loads(data: str) -> Dict[str, Any]:
    try:
        return json.loads(data)
    except Exception:
        return {}


def truncate_text(text: str, max_length: int = 500) -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."
