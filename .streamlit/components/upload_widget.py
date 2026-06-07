"""
components/upload_widget.py
Enterprise drag-and-drop file upload widget with validation,
progress tracking, statistics, and upload history.
IBM Watsonx themed, Streamlit-compatible.
"""

from __future__ import annotations

import hashlib
import io
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple

import streamlit as st


# ─────────────────────────────────────────────────────────────
# Constants & configuration
# ─────────────────────────────────────────────────────────────

MAX_FILE_SIZE_MB = 50

ALLOWED_TYPES: Dict[str, Dict[str, Any]] = {
    "pdf": {
        "mime":        ["application/pdf"],
        "icon":        "📄",
        "color":       "red",
        "description": "NBA accreditation documents, SAR reports",
        "max_mb":      50,
    },
    "csv": {
        "mime":        ["text/csv", "application/csv"],
        "icon":        "📊",
        "color":       "green",
        "description": "Attainment data, student performance, marks",
        "max_mb":      25,
    },
    "docx": {
        "mime":        [
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword",
        ],
        "icon":        "📝",
        "color":       "blue",
        "description": "Course files, syllabi, faculty documents",
        "max_mb":      25,
    },
    "xlsx": {
        "mime":        [
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-excel",
        ],
        "icon":        "📈",
        "color":       "cyan",
        "description": "Attainment matrices, CO-PO spreadsheets",
        "max_mb":      25,
    },
    "txt": {
        "mime":        ["text/plain"],
        "icon":        "📃",
        "color":       "purple",
        "description": "Plain text notes, agendas",
        "max_mb":      5,
    },
}

_EXT_TO_TYPE: Dict[str, str] = {
    "pdf":  "pdf",
    "csv":  "csv",
    "docx": "docx",
    "doc":  "docx",
    "xlsx": "xlsx",
    "xls":  "xlsx",
    "txt":  "txt",
}


# ─────────────────────────────────────────────────────────────
# Data structures
# ─────────────────────────────────────────────────────────────

@dataclass
class UploadedFileRecord:
    file_id:      str
    filename:     str
    file_type:    str          # "pdf" | "csv" | "docx" | "xlsx" | "txt"
    size_bytes:   int
    uploaded_at:  datetime
    status:       str          # "success" | "error" | "processing"
    error_msg:    Optional[str] = None
    sha256:       Optional[str] = None
    page_count:   Optional[int] = None
    row_count:    Optional[int] = None
    tags:         List[str]    = field(default_factory=list)
    metadata:     Dict[str, Any] = field(default_factory=dict)

    @property
    def size_display(self) -> str:
        if self.size_bytes >= 1_048_576:
            return f"{self.size_bytes / 1_048_576:.1f} MB"
        if self.size_bytes >= 1_024:
            return f"{self.size_bytes / 1_024:.1f} KB"
        return f"{self.size_bytes} B"

    @property
    def type_icon(self) -> str:
        return ALLOWED_TYPES.get(self.file_type, {}).get("icon", "📎")

    @property
    def age_display(self) -> str:
        delta = datetime.now(timezone.utc) - self.uploaded_at
        s = int(delta.total_seconds())
        if s < 60:
            return f"{s}s ago"
        if s < 3600:
            return f"{s // 60}m ago"
        return f"{s // 3600}h ago"


# ─────────────────────────────────────────────────────────────
# Session state management
# ─────────────────────────────────────────────────────────────

def _init_upload_session(session_key: str) -> None:
    sk = f"upload_{session_key}"
    if sk not in st.session_state:
        st.session_state[sk] = {
            "history":      [],   # List[UploadedFileRecord]
            "total_bytes":  0,
            "success_count": 0,
            "error_count":  0,
        }


def _get_session(session_key: str) -> Dict[str, Any]:
    return st.session_state[f"upload_{session_key}"]


def _add_record(session_key: str, record: UploadedFileRecord) -> None:
    s = _get_session(session_key)
    s["history"].insert(0, record)
    if record.status == "success":
        s["success_count"] += 1
        s["total_bytes"]   += record.size_bytes
    else:
        s["error_count"] += 1
    # Keep last 50 records
    s["history"] = s["history"][:50]


# ─────────────────────────────────────────────────────────────
# Validation
# ─────────────────────────────────────────────────────────────

def _detect_type(filename: str) -> Optional[str]:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return _EXT_TO_TYPE.get(ext)


def _validate_file(
    uploaded_file: Any,
    allowed_types: Optional[List[str]] = None,
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validate an uploaded file object (from st.file_uploader).

    Returns: (is_valid, file_type, error_message)
    """
    name = uploaded_file.name
    size = len(uploaded_file.getvalue())
    ftype = _detect_type(name)

    if ftype is None:
        ext = name.rsplit(".", 1)[-1] if "." in name else "unknown"
        return False, None, f"Unsupported file type '.{ext}'. Allowed: PDF, CSV, DOCX, XLSX, TXT"

    if allowed_types and ftype not in allowed_types:
        return False, ftype, f"File type '{ftype.upper()}' not permitted for this upload area"

    cfg = ALLOWED_TYPES[ftype]
    max_bytes = cfg["max_mb"] * 1_048_576
    if size > max_bytes:
        return False, ftype, f"File exceeds {cfg['max_mb']} MB limit (current: {size/1_048_576:.1f} MB)"

    if size == 0:
        return False, ftype, "File is empty"

    return True, ftype, None


def _compute_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:16]


def _extract_stats(
    uploaded_file: Any,
    ftype: str,
) -> Dict[str, Any]:
    """Extract basic file statistics (row count for CSV, etc.)."""
    stats: Dict[str, Any] = {}
    try:
        data = uploaded_file.getvalue()
        if ftype == "csv":
            text = data.decode("utf-8", errors="ignore")
            rows = text.count("\n")
            stats["row_count"] = max(0, rows - 1)  # exclude header
        elif ftype == "pdf":
            # Basic page count via byte scanning (no extra deps)
            page_count = data.count(b"/Page")
            stats["page_count"] = max(1, page_count // 2)
    except Exception:
        pass
    return stats


# ─────────────────────────────────────────────────────────────
# HTML helpers
# ─────────────────────────────────────────────────────────────

def _color_var(color: str) -> str:
    m = {
        "red":    "var(--wx-red)",
        "blue":   "var(--wx-blue-light)",
        "green":  "var(--wx-green)",
        "cyan":   "var(--wx-cyan)",
        "purple": "var(--wx-purple)",
        "yellow": "var(--wx-yellow)",
    }
    return m.get(color, "var(--wx-blue-light)")


def _badge(text: str, color: str = "blue") -> str:
    return (
        f'<span class="badge badge-{color}" '
        f'style="font-size:0.6rem;padding:1px 6px;">{text}</span>'
    )


def _status_chip(status: str) -> str:
    cfg = {
        "success":    ("green",  "✓ Uploaded"),
        "error":      ("red",    "✗ Failed"),
        "processing": ("yellow", "⟳ Processing"),
    }.get(status, ("blue", status))
    color, label = cfg
    return _badge(label, color)


def _file_row_html(rec: UploadedFileRecord) -> str:
    extra = ""
    if rec.row_count is not None:
        extra = f'<span style="color:var(--text-disabled);font-size:0.6875rem;margin-left:6px;">{rec.row_count:,} rows</span>'
    elif rec.page_count is not None:
        extra = f'<span style="color:var(--text-disabled);font-size:0.6875rem;margin-left:6px;">{rec.page_count} pages</span>'
    err_html = ""
    if rec.error_msg:
        err_html = (
            f'<div style="font-size:0.6875rem;color:var(--wx-red);'
            f'margin-top:2px;font-family:var(--font-mono);">{rec.error_msg}</div>'
        )
    sha_html = (
        f'<span style="font-size:0.625rem;font-family:var(--font-mono);'
        f'color:var(--text-disabled);">#{rec.sha256}</span>'
        if rec.sha256 else ""
    )
    return f"""
    <div class="uploaded-file-item">
      <span class="file-icon">{rec.type_icon}</span>
      <div style="flex:1;min-width:0;">
        <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;">
          <span class="file-name">{rec.filename}</span>
          {_status_chip(rec.status)}
          {extra}
        </div>
        {err_html}
        <div style="display:flex;gap:8px;align-items:center;margin-top:2px;">
          <span class="file-size">{rec.size_display}</span>
          <span style="font-size:0.6875rem;color:var(--text-disabled);">{rec.age_display}</span>
          {sha_html}
        </div>
      </div>
    </div>
    """


# ─────────────────────────────────────────────────────────────
# Upload zone header
# ─────────────────────────────────────────────────────────────

def _render_upload_zone_header(
    allowed_types: Optional[List[str]],
    title: str,
    subtitle: str,
) -> None:
    types = allowed_types or list(ALLOWED_TYPES.keys())
    type_badges = " ".join(
        f'<span class="badge badge-{ALLOWED_TYPES[t]["color"]}">'
        f'{ALLOWED_TYPES[t]["icon"]} {t.upper()}</span>'
        for t in types
        if t in ALLOWED_TYPES
    )
    st.markdown(
        f"""
        <div class="upload-zone" style="margin-bottom:1rem;">
          <span class="upload-icon">☁</span>
          <div class="upload-title">{title}</div>
          <div class="upload-subtitle">{subtitle}</div>
          <div class="upload-formats" style="margin-top:0.75rem;">
            {type_badges}
          </div>
          <div style="font-size:0.6875rem;color:var(--text-disabled);margin-top:8px;
                      font-family:var(--font-mono);">
            Max: PDF 50 MB · CSV/DOCX/XLSX 25 MB · TXT 5 MB
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────
# Progress simulation
# ─────────────────────────────────────────────────────────────

def _simulate_progress(filename: str, size_bytes: int) -> None:
    """Show a brief animated progress bar during processing."""
    steps = 5
    bar   = st.progress(0, text=f"Processing {filename}…")
    delay = min(0.08, max(0.02, size_bytes / 5_000_000))
    for i in range(1, steps + 1):
        time.sleep(delay)
        bar.progress(i / steps, text=f"Processing {filename}… {i * 100 // steps}%")
    bar.empty()


# ─────────────────────────────────────────────────────────────
# Session statistics panel
# ─────────────────────────────────────────────────────────────

def render_upload_stats(session_key: str = "default") -> None:
    """Render compact upload statistics for the current session."""
    _init_upload_session(session_key)
    s = _get_session(session_key)
    total    = s["success_count"] + s["error_count"]
    success  = s["success_count"]
    errors   = s["error_count"]
    total_mb = s["total_bytes"] / 1_048_576

    if total == 0:
        return

    st.markdown(
        f"""
        <div style="display:flex;gap:0;background:var(--bg-layer-02);
                    border:1px solid var(--border-subtle);border-radius:var(--radius-md);
                    overflow:hidden;margin-bottom:0.75rem;">
          <div style="flex:1;padding:0.5rem 0.875rem;text-align:center;
                      border-right:1px solid var(--border-subtle);">
            <div style="font-size:1.125rem;font-weight:600;color:var(--text-primary);
                        font-variant-numeric:tabular-nums;">{total}</div>
            <div style="font-size:0.625rem;color:var(--text-disabled);
                        text-transform:uppercase;letter-spacing:0.08em;">Total</div>
          </div>
          <div style="flex:1;padding:0.5rem 0.875rem;text-align:center;
                      border-right:1px solid var(--border-subtle);">
            <div style="font-size:1.125rem;font-weight:600;color:var(--wx-green);
                        font-variant-numeric:tabular-nums;">{success}</div>
            <div style="font-size:0.625rem;color:var(--text-disabled);
                        text-transform:uppercase;letter-spacing:0.08em;">Success</div>
          </div>
          <div style="flex:1;padding:0.5rem 0.875rem;text-align:center;
                      border-right:1px solid var(--border-subtle);">
            <div style="font-size:1.125rem;font-weight:600;color:var(--wx-red);
                        font-variant-numeric:tabular-nums;">{errors}</div>
            <div style="font-size:0.625rem;color:var(--text-disabled);
                        text-transform:uppercase;letter-spacing:0.08em;">Errors</div>
          </div>
          <div style="flex:1;padding:0.5rem 0.875rem;text-align:center;">
            <div style="font-size:1.125rem;font-weight:600;color:var(--wx-cyan);
                        font-variant-numeric:tabular-nums;">{total_mb:.1f}</div>
            <div style="font-size:0.625rem;color:var(--text-disabled);
                        text-transform:uppercase;letter-spacing:0.08em;">MB</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────
# Upload history panel
# ─────────────────────────────────────────────────────────────

def render_upload_history(
    session_key: str = "default",
    max_items: int = 10,
) -> None:
    """Render the upload history list for the current session."""
    _init_upload_session(session_key)
    history: List[UploadedFileRecord] = _get_session(session_key)["history"]

    if not history:
        st.markdown(
            '<div style="text-align:center;padding:1.5rem;color:var(--text-disabled);'
            'font-size:0.875rem;">No files uploaded yet.</div>',
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        '<div style="font-size:0.75rem;font-weight:600;letter-spacing:0.08em;'
        'text-transform:uppercase;color:var(--text-helper);margin-bottom:8px;">'
        'Upload History</div>',
        unsafe_allow_html=True,
    )
    for rec in history[:max_items]:
        st.markdown(_file_row_html(rec), unsafe_allow_html=True)

    if len(history) > max_items:
        st.markdown(
            f'<div style="font-size:0.75rem;color:var(--text-disabled);'
            f'text-align:center;padding:4px;">'
            f'+{len(history) - max_items} more files</div>',
            unsafe_allow_html=True,
        )


# ─────────────────────────────────────────────────────────────
# Core upload widget
# ─────────────────────────────────────────────────────────────

def render_upload_widget(
    label: str = "Upload Accreditation Documents",
    subtitle: str = "Drag and drop or click to browse",
    allowed_types: Optional[List[str]] = None,
    accept_multiple: bool = True,
    session_key: str = "default",
    on_upload: Optional[Callable[[UploadedFileRecord, bytes], None]] = None,
    show_stats: bool = True,
    show_history: bool = True,
    key: str = "main_uploader",
) -> List[UploadedFileRecord]:
    """
    Render the complete enterprise upload widget.

    Args:
        label:           Upload zone title.
        subtitle:        Upload zone subtitle.
        allowed_types:   Restrict to these types (None = all).
        accept_multiple: Allow multiple file uploads.
        session_key:     Namespace for session state (use unique keys per page).
        on_upload:       Callback(record, raw_bytes) called for each valid upload.
        show_stats:      Show session statistics bar.
        show_history:    Show upload history list.
        key:             Streamlit widget key prefix.

    Returns:
        List of UploadedFileRecord for successfully uploaded files in this call.
    """
    _init_upload_session(session_key)
    types = allowed_types or list(ALLOWED_TYPES.keys())

    # Build st.file_uploader accepted types list
    st_types: List[str] = []
    for t in types:
        if t in ALLOWED_TYPES:
            st_types.extend(ALLOWED_TYPES[t]["mime"])
    st_types = list(dict.fromkeys(st_types))  # deduplicate

    # Visual upload zone header
    _render_upload_zone_header(types, label, subtitle)

    # Stats bar
    if show_stats:
        render_upload_stats(session_key)

    # Streamlit file uploader
    uploaded_files = st.file_uploader(
        label,
        type=[t for t in types],  # file extensions
        accept_multiple_files=accept_multiple,
        key=key,
        label_visibility="collapsed",
    )

    if uploaded_files is None:
        uploaded_files = []
    elif not isinstance(uploaded_files, list):
        uploaded_files = [uploaded_files]

    results: List[UploadedFileRecord] = []

    for uf in uploaded_files:
        file_id = f"{uf.name}_{len(uf.getvalue())}"

        # Skip already-processed files
        history = _get_session(session_key)["history"]
        already = any(
            r.filename == uf.name and r.size_bytes == len(uf.getvalue())
            for r in history
        )
        if already:
            continue

        # Validate
        is_valid, ftype, error_msg = _validate_file(uf, allowed_types)
        raw_bytes = uf.getvalue()

        if not is_valid or ftype is None:
            rec = UploadedFileRecord(
                file_id=file_id,
                filename=uf.name,
                file_type=ftype or "unknown",
                size_bytes=len(raw_bytes),
                uploaded_at=datetime.now(timezone.utc),
                status="error",
                error_msg=error_msg,
            )
            _add_record(session_key, rec)
            st.error(f"❌ **{uf.name}**: {error_msg}")
            continue

        # Show progress
        with st.spinner(f"Processing {uf.name}…"):
            _simulate_progress(uf.name, len(raw_bytes))
            stats = _extract_stats(uf, ftype)
            sha   = _compute_sha256(raw_bytes)

        rec = UploadedFileRecord(
            file_id=file_id,
            filename=uf.name,
            file_type=ftype,
            size_bytes=len(raw_bytes),
            uploaded_at=datetime.now(timezone.utc),
            status="success",
            sha256=sha,
            page_count=stats.get("page_count"),
            row_count=stats.get("row_count"),
        )
        _add_record(session_key, rec)
        results.append(rec)

        # Fire callback
        if on_upload:
            try:
                on_upload(rec, raw_bytes)
            except Exception as exc:
                st.warning(f"Post-upload processing failed for {uf.name}: {exc}")

        # Success toast
        extra = ""
        if rec.row_count is not None:
            extra = f" · {rec.row_count:,} rows"
        elif rec.page_count is not None:
            extra = f" · {rec.page_count} pages"
        st.success(
            f"{rec.type_icon} **{rec.filename}** uploaded successfully "
            f"({rec.size_display}{extra})"
        )

    # History panel
    if show_history:
        with st.expander("📁 Upload History", expanded=bool(results)):
            render_upload_history(session_key)

    return results


# ─────────────────────────────────────────────────────────────
# Specialised single-purpose widgets
# ─────────────────────────────────────────────────────────────

def render_pdf_uploader(
    session_key: str = "pdf",
    on_upload: Optional[Callable[[UploadedFileRecord, bytes], None]] = None,
    key: str = "pdf_uploader",
) -> List[UploadedFileRecord]:
    """Convenience wrapper: PDF-only uploader."""
    return render_upload_widget(
        label="Upload NBA Accreditation Documents (PDF)",
        subtitle="SAR reports, NAAC reports, NBA criteria evidence",
        allowed_types=["pdf"],
        session_key=session_key,
        on_upload=on_upload,
        key=key,
    )


def render_data_uploader(
    session_key: str = "data",
    on_upload: Optional[Callable[[UploadedFileRecord, bytes], None]] = None,
    key: str = "data_uploader",
) -> List[UploadedFileRecord]:
    """Convenience wrapper: CSV / XLSX uploader."""
    return render_upload_widget(
        label="Upload Attainment Data",
        subtitle="Student marks, CO attainment, PO mapping spreadsheets",
        allowed_types=["csv", "xlsx"],
        session_key=session_key,
        on_upload=on_upload,
        key=key,
    )


def render_document_uploader(
    session_key: str = "docs",
    on_upload: Optional[Callable[[UploadedFileRecord, bytes], None]] = None,
    key: str = "doc_uploader",
) -> List[UploadedFileRecord]:
    """Convenience wrapper: DOCX / TXT uploader."""
    return render_upload_widget(
        label="Upload Course Documents",
        subtitle="Syllabi, lesson plans, faculty CVs, committee reports",
        allowed_types=["docx", "txt"],
        session_key=session_key,
        on_upload=on_upload,
        key=key,
    )


def clear_upload_history(session_key: str = "default") -> None:
    """Reset the upload history for a session namespace."""
    sk = f"upload_{session_key}"
    if sk in st.session_state:
        st.session_state[sk] = {
            "history":       [],
            "total_bytes":   0,
            "success_count": 0,
            "error_count":   0,
        }


def get_upload_history(session_key: str = "default") -> List[UploadedFileRecord]:
    """Return the upload history for the given session namespace."""
    _init_upload_session(session_key)
    return _get_session(session_key)["history"]
