"""
services/auth_service.py
Enterprise authentication service with JWT validation, session management,
role-based access control, and Streamlit session state integration.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import streamlit as st

import structlog

log = structlog.get_logger(__name__)


# ─────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────

JWT_SECRET          = "nba-enterprise-ai-platform-jwt-secret-2025"  # In prod: load from env
JWT_ALGORITHM       = "HS256"
ACCESS_TOKEN_TTL    = 3600          # 1 hour (seconds)
REFRESH_TOKEN_TTL   = 86400 * 7    # 7 days
SESSION_TIMEOUT     = 3600          # 1 hour idle timeout
MAX_LOGIN_ATTEMPTS  = 5
LOCKOUT_DURATION    = 900           # 15 minutes


# ─────────────────────────────────────────────────────────────
# Roles & Permissions
# ─────────────────────────────────────────────────────────────

class Role(str, Enum):
    ADMIN                   = "admin"
    FACULTY                 = "faculty"
    ACCREDITATION_COORDINATOR = "accreditation_coordinator"
    AUDITOR                 = "auditor"
    VIEWER                  = "viewer"


class Permission(str, Enum):
    # Dashboard
    VIEW_DASHBOARD          = "view_dashboard"
    # AI Chat
    USE_AI_CHAT             = "use_ai_chat"
    # CO-PO
    VIEW_COPO               = "view_copo"
    EDIT_COPO               = "edit_copo"
    GENERATE_COPO           = "generate_copo"
    # Attainment
    VIEW_ATTAINMENT         = "view_attainment"
    COMPUTE_ATTAINMENT      = "compute_attainment"
    # SAR
    VIEW_SAR                = "view_sar"
    GENERATE_SAR            = "generate_sar"
    EXPORT_SAR              = "export_sar"
    # Analytics
    VIEW_ANALYTICS          = "view_analytics"
    EXPORT_ANALYTICS        = "export_analytics"
    # Knowledge Base
    VIEW_KB                 = "view_kb"
    UPLOAD_KB               = "upload_kb"
    DELETE_KB               = "delete_kb"
    # Workflow
    VIEW_WORKFLOW           = "view_workflow"
    RUN_WORKFLOW            = "run_workflow"
    # Admin
    VIEW_ADMIN              = "view_admin"
    MANAGE_USERS            = "manage_users"
    VIEW_AUDIT_LOGS         = "view_audit_logs"
    MANAGE_SETTINGS         = "manage_settings"
    SYSTEM_HEALTH           = "system_health"


# Role → Permission mapping
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.ADMIN: set(Permission),  # All permissions

    Role.ACCREDITATION_COORDINATOR: {
        Permission.VIEW_DASHBOARD,
        Permission.USE_AI_CHAT,
        Permission.VIEW_COPO,   Permission.EDIT_COPO,   Permission.GENERATE_COPO,
        Permission.VIEW_ATTAINMENT, Permission.COMPUTE_ATTAINMENT,
        Permission.VIEW_SAR,    Permission.GENERATE_SAR, Permission.EXPORT_SAR,
        Permission.VIEW_ANALYTICS, Permission.EXPORT_ANALYTICS,
        Permission.VIEW_KB,     Permission.UPLOAD_KB,
        Permission.VIEW_WORKFLOW, Permission.RUN_WORKFLOW,
        Permission.VIEW_AUDIT_LOGS,
    },

    Role.FACULTY: {
        Permission.VIEW_DASHBOARD,
        Permission.USE_AI_CHAT,
        Permission.VIEW_COPO,   Permission.EDIT_COPO,
        Permission.VIEW_ATTAINMENT, Permission.COMPUTE_ATTAINMENT,
        Permission.VIEW_SAR,
        Permission.VIEW_ANALYTICS,
        Permission.VIEW_KB,     Permission.UPLOAD_KB,
        Permission.VIEW_WORKFLOW,
    },

    Role.AUDITOR: {
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_COPO,
        Permission.VIEW_ATTAINMENT,
        Permission.VIEW_SAR,
        Permission.VIEW_ANALYTICS, Permission.EXPORT_ANALYTICS,
        Permission.VIEW_KB,
        Permission.VIEW_WORKFLOW,
        Permission.VIEW_AUDIT_LOGS,
    },

    Role.VIEWER: {
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_COPO,
        Permission.VIEW_ATTAINMENT,
        Permission.VIEW_SAR,
        Permission.VIEW_ANALYTICS,
        Permission.VIEW_KB,
    },
}


# ─────────────────────────────────────────────────────────────
# Demo user store (replace with DB calls in production)
# ─────────────────────────────────────────────────────────────

def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


_DEMO_USERS: Dict[str, Dict[str, Any]] = {
    "admin": {
        "user_id":      "usr-0001",
        "username":     "admin",
        "display_name": "System Administrator",
        "email":        "admin@nba-platform.edu",
        "role":         Role.ADMIN,
        "password_hash": _hash_password("admin123"),
        "department":   "Administration",
        "active":       True,
        "created_at":   "2025-01-01T00:00:00Z",
        "last_login":   None,
    },
    "coordinator": {
        "user_id":      "usr-0002",
        "username":     "coordinator",
        "display_name": "NBA Coordinator",
        "email":        "coordinator@nba-platform.edu",
        "role":         Role.ACCREDITATION_COORDINATOR,
        "password_hash": _hash_password("coord123"),
        "department":   "Quality Assurance",
        "active":       True,
        "created_at":   "2025-01-01T00:00:00Z",
        "last_login":   None,
    },
    "faculty": {
        "user_id":      "usr-0003",
        "username":     "faculty",
        "display_name": "Dr. Faculty Member",
        "email":        "faculty@nba-platform.edu",
        "role":         Role.FACULTY,
        "password_hash": _hash_password("faculty123"),
        "department":   "Computer Science & Engineering",
        "active":       True,
        "created_at":   "2025-01-01T00:00:00Z",
        "last_login":   None,
    },
    "auditor": {
        "user_id":      "usr-0004",
        "username":     "auditor",
        "display_name": "External Auditor",
        "email":        "auditor@nba-platform.edu",
        "role":         Role.AUDITOR,
        "password_hash": _hash_password("audit123"),
        "department":   "External",
        "active":       True,
        "created_at":   "2025-01-01T00:00:00Z",
        "last_login":   None,
    },
}

# Failed attempts tracker (in-memory; use Redis in prod)
_failed_attempts: Dict[str, Tuple[int, float]] = {}  # username → (count, first_fail_ts)


# ─────────────────────────────────────────────────────────────
# Data structures
# ─────────────────────────────────────────────────────────────

@dataclass
class UserSession:
    user_id:      str
    username:     str
    display_name: str
    email:        str
    role:         Role
    department:   str
    permissions:  Set[Permission]
    access_token: str
    refresh_token: str
    access_token_exp:  float   # unix timestamp
    refresh_token_exp: float
    session_id:   str  = field(default_factory=lambda: str(uuid.uuid4()))
    login_at:     float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    ip_address:   Optional[str] = None

    @property
    def is_access_token_valid(self) -> bool:
        return time.time() < self.access_token_exp

    @property
    def is_refresh_token_valid(self) -> bool:
        return time.time() < self.refresh_token_exp

    @property
    def is_session_active(self) -> bool:
        return time.time() - self.last_activity < SESSION_TIMEOUT

    def touch(self) -> None:
        self.last_activity = time.time()

    def has_permission(self, perm: Permission) -> bool:
        return perm in self.permissions

    def has_any_permission(self, *perms: Permission) -> bool:
        return any(p in self.permissions for p in perms)

    def has_all_permissions(self, *perms: Permission) -> bool:
        return all(p in self.permissions for p in perms)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id":      self.user_id,
            "username":     self.username,
            "display_name": self.display_name,
            "email":        self.email,
            "role":         self.role.value,
            "department":   self.department,
        }


@dataclass
class AuditLogEntry:
    log_id:     str  = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp:  float = field(default_factory=time.time)
    username:   str  = ""
    action:     str  = ""
    resource:   str  = ""
    ip_address: Optional[str] = None
    status:     str  = "success"   # success | failure
    detail:     str  = ""


# ─────────────────────────────────────────────────────────────
# Minimal JWT implementation (no PyJWT dep)
# ─────────────────────────────────────────────────────────────

import base64


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    padding = 4 - len(s) % 4
    return base64.urlsafe_b64decode(s + "=" * padding)


def _jwt_create(payload: Dict[str, Any], secret: str = JWT_SECRET) -> str:
    header  = _b64url_encode(json.dumps({"alg": JWT_ALGORITHM, "typ": "JWT"}).encode())
    body    = _b64url_encode(json.dumps(payload).encode())
    sig_input = f"{header}.{body}".encode()
    sig     = hmac.new(secret.encode(), sig_input, hashlib.sha256).digest()
    return f"{header}.{body}.{_b64url_encode(sig)}"


def _jwt_verify(token: str, secret: str = JWT_SECRET) -> Optional[Dict[str, Any]]:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header_b, body_b, sig_b = parts
        expected_sig = hmac.new(
            secret.encode(),
            f"{header_b}.{body_b}".encode(),
            hashlib.sha256,
        ).digest()
        actual_sig = _b64url_decode(sig_b)
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None
        payload = json.loads(_b64url_decode(body_b))
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None


def _create_access_token(user_data: Dict[str, Any]) -> Tuple[str, float]:
    exp = time.time() + ACCESS_TOKEN_TTL
    payload = {
        "sub":  user_data["user_id"],
        "usr":  user_data["username"],
        "role": user_data["role"].value,
        "jti":  str(uuid.uuid4()),
        "iat":  time.time(),
        "exp":  exp,
        "typ":  "access",
    }
    return _jwt_create(payload), exp


def _create_refresh_token(user_data: Dict[str, Any]) -> Tuple[str, float]:
    exp = time.time() + REFRESH_TOKEN_TTL
    payload = {
        "sub":  user_data["user_id"],
        "usr":  user_data["username"],
        "jti":  str(uuid.uuid4()),
        "iat":  time.time(),
        "exp":  exp,
        "typ":  "refresh",
    }
    return _jwt_create(payload), exp


# ─────────────────────────────────────────────────────────────
# Lockout management
# ─────────────────────────────────────────────────────────────

def _is_locked_out(username: str) -> bool:
    if username not in _failed_attempts:
        return False
    count, first_ts = _failed_attempts[username]
    if time.time() - first_ts > LOCKOUT_DURATION:
        del _failed_attempts[username]
        return False
    return count >= MAX_LOGIN_ATTEMPTS


def _record_failed_attempt(username: str) -> int:
    now = time.time()
    if username in _failed_attempts:
        count, first_ts = _failed_attempts[username]
        if now - first_ts > LOCKOUT_DURATION:
            _failed_attempts[username] = (1, now)
            return 1
        new_count = count + 1
        _failed_attempts[username] = (new_count, first_ts)
        return new_count
    _failed_attempts[username] = (1, now)
    return 1


def _clear_failed_attempts(username: str) -> None:
    _failed_attempts.pop(username, None)


# ─────────────────────────────────────────────────────────────
# Session state management
# ─────────────────────────────────────────────────────────────

_SESSION_KEY = "auth_session"
_AUDIT_KEY   = "auth_audit_log"


def _init_auth_state() -> None:
    if _SESSION_KEY not in st.session_state:
        st.session_state[_SESSION_KEY] = None
    if _AUDIT_KEY not in st.session_state:
        st.session_state[_AUDIT_KEY] = []


def _write_audit_log(entry: AuditLogEntry) -> None:
    _init_auth_state()
    log_list: List[AuditLogEntry] = st.session_state[_AUDIT_KEY]
    log_list.insert(0, entry)
    st.session_state[_AUDIT_KEY] = log_list[:200]  # keep last 200


# ─────────────────────────────────────────────────────────────
# Core Auth Service
# ─────────────────────────────────────────────────────────────

class AuthService:
    """
    Stateless authentication service.
    All state is stored in st.session_state.
    """

    # ── Login ─────────────────────────────────────────────────

    @staticmethod
    def login(username: str, password: str) -> Tuple[bool, str, Optional[UserSession]]:
        """
        Authenticate user with username/password.

        Returns: (success, message, session_or_None)
        """
        _init_auth_state()

        username = username.strip().lower()

        if _is_locked_out(username):
            remaining = int(LOCKOUT_DURATION - (time.time() - _failed_attempts.get(username, (0, time.time()))[1]))
            msg = f"Account locked. Try again in {remaining // 60}m {remaining % 60}s."
            log.warning("auth.login.locked", username=username)
            return False, msg, None

        user = _DEMO_USERS.get(username)
        if not user:
            attempts = _record_failed_attempt(username)
            log.warning("auth.login.user_not_found", username=username)
            return False, "Invalid username or password.", None

        if not user.get("active", False):
            return False, "Account is disabled. Contact your administrator.", None

        if user["password_hash"] != _hash_password(password):
            attempts = _record_failed_attempt(username)
            remaining = MAX_LOGIN_ATTEMPTS - attempts
            msg = (
                f"Invalid password. {remaining} attempt(s) remaining."
                if remaining > 0
                else "Account locked due to too many failed attempts."
            )
            log.warning("auth.login.wrong_password", username=username, attempts=attempts)
            return False, msg, None

        _clear_failed_attempts(username)

        role        = user["role"]
        permissions = ROLE_PERMISSIONS.get(role, set())
        access_tok, access_exp   = _create_access_token(user)
        refresh_tok, refresh_exp = _create_refresh_token(user)

        session = UserSession(
            user_id=user["user_id"],
            username=user["username"],
            display_name=user["display_name"],
            email=user["email"],
            role=role,
            department=user["department"],
            permissions=permissions,
            access_token=access_tok,
            refresh_token=refresh_tok,
            access_token_exp=access_exp,
            refresh_token_exp=refresh_exp,
        )

        st.session_state[_SESSION_KEY] = session

        # Audit
        _write_audit_log(AuditLogEntry(
            username=username,
            action="LOGIN",
            resource="auth",
            status="success",
            detail=f"Role: {role.value}",
        ))
        log.info("auth.login.success", username=username, role=role.value)
        return True, f"Welcome back, {user['display_name']}!", session

    # ── Logout ────────────────────────────────────────────────

    @staticmethod
    def logout() -> None:
        """Terminate current session."""
        _init_auth_state()
        sess: Optional[UserSession] = st.session_state.get(_SESSION_KEY)
        if sess:
            _write_audit_log(AuditLogEntry(
                username=sess.username,
                action="LOGOUT",
                resource="auth",
                status="success",
            ))
            log.info("auth.logout", username=sess.username)
        st.session_state[_SESSION_KEY] = None

    # ── Session retrieval ─────────────────────────────────────

    @staticmethod
    def get_session() -> Optional[UserSession]:
        """Return the active UserSession or None."""
        _init_auth_state()
        sess: Optional[UserSession] = st.session_state.get(_SESSION_KEY)
        if sess is None:
            return None
        if not sess.is_session_active:
            log.info("auth.session.timeout", username=sess.username)
            st.session_state[_SESSION_KEY] = None
            return None
        sess.touch()
        return sess

    @staticmethod
    def is_authenticated() -> bool:
        return AuthService.get_session() is not None

    # ── Token refresh ─────────────────────────────────────────

    @staticmethod
    def refresh_access_token() -> bool:
        """Refresh the access token using the refresh token."""
        _init_auth_state()
        sess: Optional[UserSession] = st.session_state.get(_SESSION_KEY)
        if sess is None or not sess.is_refresh_token_valid:
            return False

        user = _DEMO_USERS.get(sess.username)
        if not user:
            return False

        new_tok, new_exp = _create_access_token(user)
        sess.access_token     = new_tok
        sess.access_token_exp = new_exp
        sess.touch()
        log.info("auth.token.refreshed", username=sess.username)
        return True

    # ── JWT validation ────────────────────────────────────────

    @staticmethod
    def validate_token(token: str) -> Optional[Dict[str, Any]]:
        """Validate a JWT and return its payload, or None if invalid."""
        return _jwt_verify(token)

    # ── Permission checks ─────────────────────────────────────

    @staticmethod
    def check_permission(perm: Permission) -> bool:
        """Return True if the current user has the given permission."""
        sess = AuthService.get_session()
        if sess is None:
            return False
        return sess.has_permission(perm)

    @staticmethod
    def require_permission(perm: Permission) -> bool:
        """
        Assert permission; shows error and returns False if denied.
        Use in page guards: if not auth_service.require_permission(Permission.VIEW_SAR): return
        """
        if not AuthService.check_permission(perm):
            st.error(
                f"🔒 Access Denied. You don't have permission: `{perm.value}`. "
                f"Contact your administrator."
            )
            return False
        return True

    @staticmethod
    def require_role(*roles: Role) -> bool:
        """Assert one of the given roles; shows error and returns False if denied."""
        sess = AuthService.get_session()
        if sess is None or sess.role not in roles:
            st.error("🔒 Insufficient role for this action.")
            return False
        return True

    # ── Audit log ─────────────────────────────────────────────

    @staticmethod
    def audit(action: str, resource: str, status: str = "success", detail: str = "") -> None:
        """Write an audit log entry for the current user."""
        sess = AuthService.get_session()
        username = sess.username if sess else "anonymous"
        _write_audit_log(AuditLogEntry(
            username=username,
            action=action.upper(),
            resource=resource,
            status=status,
            detail=detail,
        ))

    @staticmethod
    def get_audit_log() -> List[AuditLogEntry]:
        """Return the in-session audit log."""
        _init_auth_state()
        return st.session_state.get(_AUDIT_KEY, [])

    # ── User management (admin only) ──────────────────────────

    @staticmethod
    def list_users() -> List[Dict[str, Any]]:
        """Return sanitised user list (no password hashes)."""
        return [
            {k: v for k, v in u.items() if k != "password_hash"}
            for u in _DEMO_USERS.values()
        ]

    @staticmethod
    def get_role_summary() -> Dict[str, int]:
        """Count users per role."""
        summary: Dict[str, int] = {}
        for u in _DEMO_USERS.values():
            r = u["role"].value if isinstance(u["role"], Role) else str(u["role"])
            summary[r] = summary.get(r, 0) + 1
        return summary


# ─────────────────────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────────────────────

auth_service = AuthService()


# ─────────────────────────────────────────────────────────────
# Streamlit login UI
# ─────────────────────────────────────────────────────────────

def render_login_page() -> bool:
    """
    Render the full login page.
    Returns True if user successfully logged in during this render.
    """
    st.markdown(
        """
        <div style="min-height:100vh;display:flex;align-items:center;
                    justify-content:center;padding:2rem;
                    background:var(--bg-base);">
        """,
        unsafe_allow_html=True,
    )

    col_l, col_c, col_r = st.columns([1, 1.4, 1])
    with col_c:
        # Logo block
        st.markdown(
            """
            <div style="text-align:center;margin-bottom:2rem;">
              <div style="width:56px;height:56px;border-radius:14px;
                          background:linear-gradient(135deg,#0f62fe,#33b1ff);
                          display:flex;align-items:center;justify-content:center;
                          font-size:1.5rem;font-weight:700;color:white;
                          margin:0 auto 1rem;
                          box-shadow:0 4px 24px rgba(15,98,254,0.40);">N</div>
              <div style="font-size:1.5rem;font-weight:700;color:var(--text-primary);
                          letter-spacing:-0.02em;">NBA Accreditation Platform</div>
              <div style="font-size:0.875rem;color:var(--text-helper);margin-top:4px;
                          font-family:var(--font-mono);">Enterprise AI · IBM Watsonx</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Card
        with st.container():
            st.markdown(
                '<div class="glass-card" style="padding:2rem;">',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<div style="font-size:1.125rem;font-weight:600;color:var(--text-primary);'
                'margin-bottom:1.25rem;">Sign In</div>',
                unsafe_allow_html=True,
            )

            username = st.text_input(
                "Username",
                placeholder="Enter your username",
                key="login_username",
            )
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
                key="login_password",
            )

            st.markdown("<br>", unsafe_allow_html=True)
            login_btn = st.button("Sign In →", use_container_width=True, key="login_btn")

            if login_btn:
                if not username or not password:
                    st.error("Please enter both username and password.")
                else:
                    with st.spinner("Authenticating…"):
                        success, msg, _ = auth_service.login(username, password)
                    if success:
                        st.success(msg)
                        time.sleep(0.4)
                        st.rerun()
                        return True
                    else:
                        st.error(msg)

            st.markdown("</div>", unsafe_allow_html=True)

        # Demo credentials hint
        st.markdown(
            """
            <div style="margin-top:1.25rem;padding:0.875rem 1rem;
                        background:rgba(15,98,254,0.06);
                        border:1px solid rgba(15,98,254,0.15);
                        border-radius:var(--radius-md);">
              <div style="font-size:0.6875rem;font-weight:600;letter-spacing:0.08em;
                          text-transform:uppercase;color:var(--text-helper);
                          margin-bottom:6px;">Demo Credentials</div>
              <div style="font-size:0.8125rem;color:var(--text-secondary);
                          font-family:var(--font-mono);line-height:1.8;">
                admin / admin123  →  Admin<br>
                coordinator / coord123  →  Coordinator<br>
                faculty / faculty123  →  Faculty<br>
                auditor / audit123  →  Auditor
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)
    return False


# ─────────────────────────────────────────────────────────────
# Decorator: require authentication
# ─────────────────────────────────────────────────────────────

def require_auth(func: Callable) -> Callable:
    """Decorator that redirects to login if user is not authenticated."""
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if not auth_service.is_authenticated():
            render_login_page()
            st.stop()
        return func(*args, **kwargs)
    return wrapper


def require_permission_decorator(perm: Permission) -> Callable:
    """Decorator factory: wraps page functions with permission check."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not auth_service.is_authenticated():
                render_login_page()
                st.stop()
            if not auth_service.require_permission(perm):
                st.stop()
            return func(*args, **kwargs)
        return wrapper
    return decorator
