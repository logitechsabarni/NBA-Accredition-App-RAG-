"""
NBA Enterprise AI Platform — Models Package
All ORM models are imported here so that Alembic's env.py
can discover them via `import models` and populate Base.metadata.

Import order respects foreign key dependency graph:
  User (no FK to domain models)
  Department → User (HOD FK)
  Program → Department
  Course → Program
  CO → Course
  PO → Program
  COPOMap → CO, PO, Program
  AttainmentRecord → Program, Course, CO
  SARDocument → Program
  AuditLog → User
"""

from models.user import User, UserRole, UserStatus
from models.department import Department
from models.program import Program, ProgramLevel, ProgramStatus
from models.course import Course, CourseType, CourseCategory
from models.co import CO, BloomsTaxonomyLevel, COStatus
from models.po import PO, POType, POStatus
from models.copo_map import COPOMap, MappingMethod, CorrelationLevel
from models.attainment_record import (
    AttainmentRecord,
    AttainmentType,
    AttainmentMethod,
    AttainmentStatus,
)
from models.sar_document import SARDocument, SARStatus, SARVersion
from models.audit_log import AuditLog, AuditAction, AuditResourceType, AuditStatus

__all__ = [
    # User
    "User",
    "UserRole",
    "UserStatus",
    # Department
    "Department",
    # Program
    "Program",
    "ProgramLevel",
    "ProgramStatus",
    # Course
    "Course",
    "CourseType",
    "CourseCategory",
    # CO
    "CO",
    "BloomsTaxonomyLevel",
    "COStatus",
    # PO
    "PO",
    "POType",
    "POStatus",
    # CO-PO Map
    "COPOMap",
    "MappingMethod",
    "CorrelationLevel",
    # Attainment
    "AttainmentRecord",
    "AttainmentType",
    "AttainmentMethod",
    "AttainmentStatus",
    # SAR
    "SARDocument",
    "SARStatus",
    "SARVersion",
    # Audit
    "AuditLog",
    "AuditAction",
    "AuditResourceType",
    "AuditStatus",
]
