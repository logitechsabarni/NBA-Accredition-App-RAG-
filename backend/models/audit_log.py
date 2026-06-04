"""
NBA Enterprise AI Platform — Audit Log ORM Model
Immutable structured audit trail for all platform actions.
Compliant with NBA accreditation audit requirements.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from db.postgres import Base

if TYPE_CHECKING:
    from models.user import User


class AuditAction(str, PyEnum):
    """Enumeration of auditable platform actions."""
    # Auth
    LOGIN = "login"
    LOGOUT = "logout"
    FAILED_LOGIN = "failed_login"
    PASSWORD_CHANGE = "password_change"
    TOKEN_REFRESH = "token_refresh"

    # User management
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    USER_SUSPEND = "user_suspend"
    USER_ACTIVATE = "user_activate"

    # Department / Program
    DEPARTMENT_CREATE = "department_create"
    DEPARTMENT_UPDATE = "department_update"
    PROGRAM_CREATE = "program_create"
    PROGRAM_UPDATE = "program_update"

    # Course & CO
    COURSE_CREATE = "course_create"
    COURSE_UPDATE = "course_update"
    CO_CREATE = "co_create"
    CO_UPDATE = "co_update"
    CO_DELETE = "co_delete"

    # PO
    PO_CREATE = "po_create"
    PO_UPDATE = "po_update"

    # CO-PO Mapping
    COPO_MAP_CREATE = "copo_map_create"
    COPO_MAP_UPDATE = "copo_map_update"
    COPO_MAP_APPROVE = "copo_map_approve"
    COPO_MAP_BULK_IMPORT = "copo_map_bulk_import"

    # Attainment
    ATTAINMENT_COMPUTE = "attainment_compute"
    ATTAINMENT_VERIFY = "attainment_verify"
    ATTAINMENT_APPROVE = "attainment_approve"
    ATTAINMENT_REJECT = "attainment_reject"

    # SAR
    SAR_CREATE = "sar_create"
    SAR_UPDATE = "sar_update"
    SAR_AI_GENERATE = "sar_ai_generate"
    SAR_HOD_APPROVE = "sar_hod_approve"
    SAR_PRINCIPAL_APPROVE = "sar_principal_approve"
    SAR_SUBMIT = "sar_submit"
    SAR_EXPORT_PDF = "sar_export_pdf"

    # AI Agents
    AGENT_RUN = "agent_run"
    AGENT_SUCCESS = "agent_success"
    AGENT_FAILURE = "agent_failure"

    # CI
    CI_RECORD_CREATE = "ci_record_create"
    CI_ACTION_COMPLETE = "ci_action_complete"

    # Data
    DATA_IMPORT = "data_import"
    DATA_EXPORT = "data_export"
    DATA_DELETE = "data_delete"


class AuditResourceType(str, PyEnum):
    USER = "user"
    DEPARTMENT = "department"
    PROGRAM = "program"
    COURSE = "course"
    CO = "co"
    PO = "po"
    COPO_MAP = "copo_map"
    ATTAINMENT_RECORD = "attainment_record"
    SAR_DOCUMENT = "sar_document"
    AGENT = "agent"
    SYSTEM = "system"


class AuditStatus(str, PyEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    WARNING = "warning"
    PARTIAL = "partial"


class AuditLog(Base):
    """
    Immutable audit log entry.
    Records every significant platform action for compliance auditing.
    Designed to be append-only — records should never be updated or deleted.
    """

    __tablename__ = "audit_logs"

    __table_args__ = (
        Index("ix_audit_user_id", "user_id"),
        Index("ix_audit_action", "action"),
        Index("ix_audit_resource_type", "resource_type"),
        Index("ix_audit_resource_id", "resource_id"),
        Index("ix_audit_status", "status"),
        Index("ix_audit_created_at", "created_at"),
        Index("ix_audit_program_id", "program_id"),
        Index("ix_audit_session_id", "session_id"),
    )

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )

    # Actor
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who performed the action (null for system actions)",
    )
    user_email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Denormalised email for audit trail readability",
    )
    user_role: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Role of the user at the time of the action",
    )

    # Action
    action: Mapped[AuditAction] = mapped_column(
        Enum(AuditAction, name="audit_action_enum", create_type=True),
        nullable=False,
        comment="Categorised action code",
    )
    action_description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Human-readable description of the action",
    )

    # Resource
    resource_type: Mapped[AuditResourceType] = mapped_column(
        Enum(AuditResourceType, name="audit_resource_type_enum", create_type=True),
        nullable=False,
        comment="Type of resource acted upon",
    )
    resource_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="UUID of the resource acted upon",
    )
    resource_code: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Human-readable resource identifier e.g. CO1, PO3",
    )

    # Context
    program_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Program context for multi-tenancy queries",
    )
    department_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Department context",
    )
    session_id: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        comment="User session ID for grouping related actions",
    )

    # Request metadata
    ip_address: Mapped[Optional[str]] = mapped_column(
        INET,
        nullable=True,
        comment="Client IP address",
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
        comment="Client user agent string",
    )
    request_id: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        comment="HTTP request UUID for log correlation",
    )
    endpoint: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
        comment="API endpoint path",
    )
    http_method: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="HTTP method GET, POST, PUT, DELETE, PATCH",
    )

    # Payload (before/after for change tracking)
    before_state: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Resource state before the action (for updates)",
    )
    after_state: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Resource state after the action",
    )
    input_payload: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Sanitised request payload (sensitive fields redacted)",
    )
    output_summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Summary of the action result",
    )

    # Status
    status: Mapped[AuditStatus] = mapped_column(
        Enum(AuditStatus, name="audit_status_enum", create_type=True),
        nullable=False,
        default=AuditStatus.SUCCESS,
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Error message if status is FAILURE",
    )
    error_code: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Error code for programmatic handling",
    )

    # Duration
    duration_ms: Mapped[Optional[float]] = mapped_column(
        nullable=True,
        comment="Time taken to complete the action in milliseconds",
    )

    # Immutable timestamp — no onupdate
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Immutable creation timestamp",
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="audit_logs",
        lazy="select",
    )

    def __repr__(self) -> str:
        return (
            f"<AuditLog id={self.id} action={self.action} "
            f"user_id={self.user_id} status={self.status}>"
        )
