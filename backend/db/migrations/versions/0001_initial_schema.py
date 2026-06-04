"""Initial schema — NBA Enterprise AI Platform

Creates all production tables:
  users, departments, programs, courses,
  course_outcomes, program_outcomes, copo_maps,
  attainment_records, sar_documents, audit_logs

Revision ID: 0001_initial_schema
Revises: None
Create Date: 2024-01-01 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # PostgreSQL extensions
    # ------------------------------------------------------------------
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "btree_gin"')

    # ------------------------------------------------------------------
    # ENUM types
    # ------------------------------------------------------------------
    user_role_enum = postgresql.ENUM(
        "super_admin", "institution_admin", "hod",
        "faculty", "nba_coordinator", "viewer",
        name="user_role_enum",
    )
    user_status_enum = postgresql.ENUM(
        "active", "inactive", "suspended", "pending_verification",
        name="user_status_enum",
    )
    program_level_enum = postgresql.ENUM(
        "undergraduate", "postgraduate", "doctoral", "diploma",
        name="program_level_enum",
    )
    program_status_enum = postgresql.ENUM(
        "active", "inactive", "under_review",
        "accreditation_pending", "accredited",
        name="program_status_enum",
    )
    course_type_enum = postgresql.ENUM(
        "theory", "lab", "theory_lab", "project",
        "seminar", "elective", "mandatory", "open_elective",
        name="course_type_enum",
    )
    course_category_enum = postgresql.ENUM(
        "professional_core", "professional_elective", "basic_science",
        "engineering_science", "humanities", "open_elective",
        "project_based", "internship",
        name="course_category_enum",
    )
    blooms_taxonomy_enum = postgresql.ENUM(
        "remember", "understand", "apply",
        "analyze", "evaluate", "create",
        name="blooms_taxonomy_enum",
    )
    co_status_enum = postgresql.ENUM(
        "draft", "active", "archived",
        name="co_status_enum",
    )
    po_type_enum = postgresql.ENUM(
        "po", "pso",
        name="po_type_enum",
    )
    po_status_enum = postgresql.ENUM(
        "draft", "active", "archived",
        name="po_status_enum",
    )
    mapping_method_enum = postgresql.ENUM(
        "manual", "ai_suggested", "ai_approved", "imported",
        name="mapping_method_enum",
    )
    attainment_type_enum = postgresql.ENUM(
        "co", "po", "pso",
        name="attainment_type_enum",
    )
    attainment_method_enum = postgresql.ENUM(
        "direct_cia", "direct_ese", "direct_combined",
        "indirect_survey", "final_weighted", "po_aggregated",
        name="attainment_method_enum",
    )
    attainment_status_enum = postgresql.ENUM(
        "draft", "computed", "verified", "approved", "rejected",
        name="attainment_status_enum",
    )
    sar_status_enum = postgresql.ENUM(
        "draft", "in_progress", "ai_generating", "review",
        "revision_requested", "hod_approved", "principal_approved",
        "submitted", "accepted", "rejected", "archived",
        name="sar_status_enum",
    )
    sar_version_enum = postgresql.ENUM(
        "tier_1", "tier_2",
        name="sar_version_enum",
    )
    audit_action_enum = postgresql.ENUM(
        "login", "logout", "failed_login", "password_change", "token_refresh",
        "user_create", "user_update", "user_delete", "user_suspend", "user_activate",
        "department_create", "department_update",
        "program_create", "program_update",
        "course_create", "course_update",
        "co_create", "co_update", "co_delete",
        "po_create", "po_update",
        "copo_map_create", "copo_map_update", "copo_map_approve", "copo_map_bulk_import",
        "attainment_compute", "attainment_verify", "attainment_approve", "attainment_reject",
        "sar_create", "sar_update", "sar_ai_generate", "sar_hod_approve",
        "sar_principal_approve", "sar_submit", "sar_export_pdf",
        "agent_run", "agent_success", "agent_failure",
        "ci_record_create", "ci_action_complete",
        "data_import", "data_export", "data_delete",
        name="audit_action_enum",
    )
    audit_resource_type_enum = postgresql.ENUM(
        "user", "department", "program", "course", "co", "po",
        "copo_map", "attainment_record", "sar_document", "agent", "system",
        name="audit_resource_type_enum",
    )
    audit_status_enum = postgresql.ENUM(
        "success", "failure", "warning", "partial",
        name="audit_status_enum",
    )

    # Create all enum types
    for enum_type in [
        user_role_enum, user_status_enum, program_level_enum, program_status_enum,
        course_type_enum, course_category_enum, blooms_taxonomy_enum, co_status_enum,
        po_type_enum, po_status_enum, mapping_method_enum,
        attainment_type_enum, attainment_method_enum, attainment_status_enum,
        sar_status_enum, sar_version_enum,
        audit_action_enum, audit_resource_type_enum, audit_status_enum,
    ]:
        enum_type.create(op.get_bind(), checkfirst=True)

    # ------------------------------------------------------------------
    # TABLE: users
    # ------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("username", sa.String(100), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("employee_id", sa.String(50), nullable=True),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("designation", sa.String(150), nullable=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("is_verified", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("is_superuser", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("role", postgresql.ENUM(name="user_role_enum", create_type=False), nullable=False),
        sa.Column("status", postgresql.ENUM(name="user_status_enum", create_type=False), nullable=False),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("password_changed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("refresh_token_hash", sa.String(255), nullable=True),
        sa.Column("avatar_url", sa.String(512), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.UniqueConstraint("username", name="uq_users_username"),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_role", "users", ["role"])
    op.create_index("ix_users_department_id", "users", ["department_id"])
    op.create_index("ix_users_is_active", "users", ["is_active"])

    # ------------------------------------------------------------------
    # TABLE: departments
    # ------------------------------------------------------------------
    op.create_table(
        "departments",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("short_name", sa.String(50), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("institution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("institution_name", sa.String(255), nullable=False),
        sa.Column("hod_name", sa.String(255), nullable=True),
        sa.Column("hod_email", sa.String(255), nullable=True),
        sa.Column("hod_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("nba_accredited", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("nba_accreditation_year", sa.Integer(), nullable=True),
        sa.Column("nba_valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("naac_grade", sa.String(5), nullable=True),
        sa.Column("established_year", sa.Integer(), nullable=True),
        sa.Column("intake_capacity", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("office_phone", sa.String(20), nullable=True),
        sa.Column("office_email", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["hod_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", "institution_id", name="uq_dept_code_institution"),
    )
    op.create_index("ix_departments_code", "departments", ["code"])
    op.create_index("ix_departments_institution_id", "departments", ["institution_id"])
    op.create_index("ix_departments_is_active", "departments", ["is_active"])

    # Add FK from users.department_id → departments.id
    op.create_foreign_key(
        "fk_users_department_id",
        "users", "departments",
        ["department_id"], ["id"],
        ondelete="SET NULL",
    )

    # ------------------------------------------------------------------
    # TABLE: programs
    # ------------------------------------------------------------------
    op.create_table(
        "programs",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("code", sa.String(30), nullable=False),
        sa.Column("short_name", sa.String(50), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("level", postgresql.ENUM(name="program_level_enum", create_type=False), nullable=False),
        sa.Column("duration_years", sa.Integer(), nullable=False),
        sa.Column("total_semesters", sa.Integer(), nullable=False),
        sa.Column("credits_required", sa.Integer(), nullable=True),
        sa.Column("status", postgresql.ENUM(name="program_status_enum", create_type=False), nullable=False),
        sa.Column("nba_tier", sa.Integer(), nullable=True),
        sa.Column("current_accreditation_cycle", sa.String(20), nullable=True),
        sa.Column("accreditation_start_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("accreditation_end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_sar_submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("co_attainment_target", sa.Float(), nullable=False),
        sa.Column("po_attainment_target", sa.Float(), nullable=False),
        sa.Column("direct_attainment_weight", sa.Float(), nullable=False),
        sa.Column("indirect_attainment_weight", sa.Float(), nullable=False),
        sa.Column("intake_year", sa.Integer(), nullable=True),
        sa.Column("regulation_year", sa.Integer(), nullable=True),
        sa.Column("program_educational_objectives", sa.Text(), nullable=True),
        sa.Column("vision", sa.Text(), nullable=True),
        sa.Column("mission", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", "department_id", name="uq_program_code_dept"),
    )
    op.create_index("ix_programs_department_id", "programs", ["department_id"])
    op.create_index("ix_programs_code", "programs", ["code"])
    op.create_index("ix_programs_status", "programs", ["status"])
    op.create_index("ix_programs_is_active", "programs", ["is_active"])

    # ------------------------------------------------------------------
    # TABLE: courses
    # ------------------------------------------------------------------
    op.create_table(
        "courses",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("code", sa.String(30), nullable=False),
        sa.Column("short_name", sa.String(80), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("program_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("faculty_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("semester", sa.Integer(), nullable=False),
        sa.Column("academic_year", sa.String(10), nullable=True),
        sa.Column("batch_year", sa.Integer(), nullable=True),
        sa.Column("course_type", postgresql.ENUM(name="course_type_enum", create_type=False), nullable=False),
        sa.Column("course_category", postgresql.ENUM(name="course_category_enum", create_type=False), nullable=False),
        sa.Column("credits", sa.Float(), nullable=False),
        sa.Column("lecture_hours", sa.Integer(), nullable=True),
        sa.Column("tutorial_hours", sa.Integer(), nullable=True),
        sa.Column("practical_hours", sa.Integer(), nullable=True),
        sa.Column("total_contact_hours", sa.Integer(), nullable=True),
        sa.Column("cia_max_marks", sa.Float(), nullable=False),
        sa.Column("ese_max_marks", sa.Float(), nullable=False),
        sa.Column("cia_weightage_percent", sa.Float(), nullable=False),
        sa.Column("ese_weightage_percent", sa.Float(), nullable=False),
        sa.Column("passing_marks_percent", sa.Float(), nullable=False),
        sa.Column("co_attainment_target_percent", sa.Float(), nullable=False),
        sa.Column("threshold_percentage", sa.Float(), nullable=False),
        sa.Column("assignment_weightage", sa.Float(), nullable=True),
        sa.Column("quiz_weightage", sa.Float(), nullable=True),
        sa.Column("mid_sem_1_weightage", sa.Float(), nullable=True),
        sa.Column("mid_sem_2_weightage", sa.Float(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("is_elective", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("enrolled_students", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["program_id"], ["programs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["faculty_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", "program_id", "semester", name="uq_course_code_program_sem"),
    )
    op.create_index("ix_courses_program_id", "courses", ["program_id"])
    op.create_index("ix_courses_code", "courses", ["code"])
    op.create_index("ix_courses_semester", "courses", ["semester"])
    op.create_index("ix_courses_is_active", "courses", ["is_active"])
    op.create_index("ix_courses_faculty_id", "courses", ["faculty_id"])

    # ------------------------------------------------------------------
    # TABLE: course_outcomes (COs)
    # ------------------------------------------------------------------
    op.create_table(
        "course_outcomes",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("short_description", sa.String(255), nullable=True),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("blooms_level", postgresql.ENUM(name="blooms_taxonomy_enum", create_type=False), nullable=True),
        sa.Column("status", postgresql.ENUM(name="co_status_enum", create_type=False), nullable=False),
        sa.Column("assessment_weightage", postgresql.JSONB(), nullable=True),
        sa.Column("cia1_mapping", postgresql.JSONB(), nullable=True),
        sa.Column("cia2_mapping", postgresql.JSONB(), nullable=True),
        sa.Column("ese_mapping", postgresql.JSONB(), nullable=True),
        sa.Column("cia_attainment_percent", sa.Float(), nullable=True),
        sa.Column("ese_attainment_percent", sa.Float(), nullable=True),
        sa.Column("direct_attainment_percent", sa.Float(), nullable=True),
        sa.Column("indirect_attainment_percent", sa.Float(), nullable=True),
        sa.Column("final_attainment_percent", sa.Float(), nullable=True),
        sa.Column("attainment_target_percent", sa.Float(), nullable=False),
        sa.Column("is_attained", sa.Boolean(), nullable=True),
        sa.Column("ai_suggested", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("ai_confidence_score", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", "course_id", name="uq_co_code_course"),
    )
    op.create_index("ix_cos_course_id", "course_outcomes", ["course_id"])
    op.create_index("ix_cos_code", "course_outcomes", ["code"])
    op.create_index("ix_cos_status", "course_outcomes", ["status"])
    op.create_index("ix_cos_blooms_level", "course_outcomes", ["blooms_level"])

    # ------------------------------------------------------------------
    # TABLE: program_outcomes (POs)
    # ------------------------------------------------------------------
    op.create_table(
        "program_outcomes",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("code", sa.String(10), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("short_description", sa.String(255), nullable=True),
        sa.Column("program_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("po_type", postgresql.ENUM(name="po_type_enum", create_type=False), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("status", postgresql.ENUM(name="po_status_enum", create_type=False), nullable=False),
        sa.Column("is_nba_standard", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("attainment_percent", sa.Float(), nullable=True),
        sa.Column("attainment_target_percent", sa.Float(), nullable=False),
        sa.Column("is_attained", sa.Boolean(), nullable=True),
        sa.Column("gap_percent", sa.Float(), nullable=True),
        sa.Column("previous_attainment_percent", sa.Float(), nullable=True),
        sa.Column("improvement_percent", sa.Float(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["program_id"], ["programs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", "program_id", name="uq_po_code_program"),
    )
    op.create_index("ix_pos_program_id", "program_outcomes", ["program_id"])
    op.create_index("ix_pos_code", "program_outcomes", ["code"])
    op.create_index("ix_pos_po_type", "program_outcomes", ["po_type"])
    op.create_index("ix_pos_is_active", "program_outcomes", ["is_active"])

    # ------------------------------------------------------------------
    # TABLE: copo_maps
    # ------------------------------------------------------------------
    op.create_table(
        "copo_maps",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("co_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("po_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("program_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("correlation_value", sa.Integer(), nullable=False),
        sa.Column("mapping_method", postgresql.ENUM(name="mapping_method_enum", create_type=False), nullable=False),
        sa.Column("justification", sa.Text(), nullable=True),
        sa.Column("ai_confidence_score", sa.Float(), nullable=True),
        sa.Column("ai_reasoning", sa.Text(), nullable=True),
        sa.Column("is_approved", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("academic_year", sa.String(10), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.CheckConstraint("correlation_value IN (0, 1, 2, 3)", name="chk_copo_correlation_value"),
        sa.ForeignKeyConstraint(["co_id"], ["course_outcomes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["po_id"], ["program_outcomes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["program_id"], ["programs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("co_id", "po_id", name="uq_copo_map_co_po"),
    )
    op.create_index("ix_copo_maps_co_id", "copo_maps", ["co_id"])
    op.create_index("ix_copo_maps_po_id", "copo_maps", ["po_id"])
    op.create_index("ix_copo_maps_correlation_value", "copo_maps", ["correlation_value"])
    op.create_index("ix_copo_maps_mapping_method", "copo_maps", ["mapping_method"])
    op.create_index("ix_copo_maps_program_id", "copo_maps", ["program_id"])

    # ------------------------------------------------------------------
    # TABLE: attainment_records
    # ------------------------------------------------------------------
    op.create_table(
        "attainment_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("reference_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reference_code", sa.String(20), nullable=False),
        sa.Column("attainment_type", postgresql.ENUM(name="attainment_type_enum", create_type=False), nullable=False),
        sa.Column("program_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("co_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("academic_year", sa.String(10), nullable=False),
        sa.Column("batch_year", sa.Integer(), nullable=True),
        sa.Column("semester", sa.Integer(), nullable=True),
        sa.Column("total_students", sa.Integer(), nullable=True),
        sa.Column("students_attained", sa.Integer(), nullable=True),
        sa.Column("cia1_data", postgresql.JSONB(), nullable=True),
        sa.Column("cia2_data", postgresql.JSONB(), nullable=True),
        sa.Column("ese_data", postgresql.JSONB(), nullable=True),
        sa.Column("assignment_data", postgresql.JSONB(), nullable=True),
        sa.Column("survey_data", postgresql.JSONB(), nullable=True),
        sa.Column("cia_attainment_percent", sa.Float(), nullable=True),
        sa.Column("ese_attainment_percent", sa.Float(), nullable=True),
        sa.Column("direct_attainment_percent", sa.Float(), nullable=True),
        sa.Column("indirect_attainment_percent", sa.Float(), nullable=True),
        sa.Column("final_attainment_percent", sa.Float(), nullable=True),
        sa.Column("attainment_target_percent", sa.Float(), nullable=False),
        sa.Column("threshold_marks_percent", sa.Float(), nullable=False),
        sa.Column("is_attained", sa.Boolean(), nullable=True),
        sa.Column("gap_percent", sa.Float(), nullable=True),
        sa.Column("calculation_method", postgresql.ENUM(name="attainment_method_enum", create_type=False), nullable=False),
        sa.Column("direct_weight", sa.Float(), nullable=False),
        sa.Column("indirect_weight", sa.Float(), nullable=False),
        sa.Column("calculation_notes", sa.Text(), nullable=True),
        sa.Column("status", postgresql.ENUM(name="attainment_status_enum", create_type=False), nullable=False),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("computed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("verified_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("previous_attainment_percent", sa.Float(), nullable=True),
        sa.Column("improvement_percent", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["program_id"], ["programs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["co_id"], ["course_outcomes.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "reference_id", "attainment_type", "academic_year", "batch_year",
            name="uq_attainment_ref_type_year",
        ),
    )
    op.create_index("ix_attainment_reference_id", "attainment_records", ["reference_id"])
    op.create_index("ix_attainment_program_id", "attainment_records", ["program_id"])
    op.create_index("ix_attainment_course_id", "attainment_records", ["course_id"])
    op.create_index("ix_attainment_co_id", "attainment_records", ["co_id"])
    op.create_index("ix_attainment_type", "attainment_records", ["attainment_type"])
    op.create_index("ix_attainment_academic_year", "attainment_records", ["academic_year"])
    op.create_index("ix_attainment_status", "attainment_records", ["status"])
    op.create_index("ix_attainment_is_attained", "attainment_records", ["is_attained"])

    # ------------------------------------------------------------------
    # TABLE: sar_documents
    # ------------------------------------------------------------------
    op.create_table(
        "sar_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("document_number", sa.String(50), nullable=True),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("program_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("academic_year", sa.String(10), nullable=False),
        sa.Column("accreditation_cycle", sa.String(20), nullable=True),
        sa.Column("sar_version", postgresql.ENUM(name="sar_version_enum", create_type=False), nullable=False),
        sa.Column("status", postgresql.ENUM(name="sar_status_enum", create_type=False), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("section_1_data", postgresql.JSONB(), nullable=True),
        sa.Column("section_2_data", postgresql.JSONB(), nullable=True),
        sa.Column("section_3_data", postgresql.JSONB(), nullable=True),
        sa.Column("section_4_data", postgresql.JSONB(), nullable=True),
        sa.Column("section_5_data", postgresql.JSONB(), nullable=True),
        sa.Column("section_6_data", postgresql.JSONB(), nullable=True),
        sa.Column("section_7_data", postgresql.JSONB(), nullable=True),
        sa.Column("section_8_data", postgresql.JSONB(), nullable=True),
        sa.Column("additional_sections", postgresql.JSONB(), nullable=True),
        sa.Column("total_marks_available", sa.Float(), nullable=True),
        sa.Column("marks_obtained", sa.Float(), nullable=True),
        sa.Column("readiness_score_percent", sa.Float(), nullable=True),
        sa.Column("gap_analysis_summary", postgresql.JSONB(), nullable=True),
        sa.Column("ai_generated", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("ai_model_used", sa.String(100), nullable=True),
        sa.Column("ai_generation_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ai_generation_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ai_tokens_used", sa.Integer(), nullable=True),
        sa.Column("pdf_file_path", sa.String(512), nullable=True),
        sa.Column("pdf_generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("word_file_path", sa.String(512), nullable=True),
        sa.Column("supporting_documents", postgresql.JSONB(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("submission_reference", sa.String(100), nullable=True),
        sa.Column("hod_approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("hod_approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("principal_approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("principal_approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_comments", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["program_id"], ["programs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sar_program_id", "sar_documents", ["program_id"])
    op.create_index("ix_sar_status", "sar_documents", ["status"])
    op.create_index("ix_sar_academic_year", "sar_documents", ["academic_year"])
    op.create_index("ix_sar_is_active", "sar_documents", ["is_active"])
    op.create_index("ix_sar_created_by", "sar_documents", ["created_by"])

    # ------------------------------------------------------------------
    # TABLE: audit_logs
    # ------------------------------------------------------------------
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("user_email", sa.String(255), nullable=True),
        sa.Column("user_role", sa.String(50), nullable=True),
        sa.Column("action", postgresql.ENUM(name="audit_action_enum", create_type=False), nullable=False),
        sa.Column("action_description", sa.Text(), nullable=True),
        sa.Column("resource_type", postgresql.ENUM(name="audit_resource_type_enum", create_type=False), nullable=False),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("resource_code", sa.String(100), nullable=True),
        sa.Column("program_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("session_id", sa.String(128), nullable=True),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.Column("user_agent", sa.String(512), nullable=True),
        sa.Column("request_id", sa.String(128), nullable=True),
        sa.Column("endpoint", sa.String(512), nullable=True),
        sa.Column("http_method", sa.String(10), nullable=True),
        sa.Column("before_state", postgresql.JSONB(), nullable=True),
        sa.Column("after_state", postgresql.JSONB(), nullable=True),
        sa.Column("input_payload", postgresql.JSONB(), nullable=True),
        sa.Column("output_summary", sa.Text(), nullable=True),
        sa.Column("status", postgresql.ENUM(name="audit_status_enum", create_type=False), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("error_code", sa.String(50), nullable=True),
        sa.Column("duration_ms", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_action", "audit_logs", ["action"])
    op.create_index("ix_audit_resource_type", "audit_logs", ["resource_type"])
    op.create_index("ix_audit_resource_id", "audit_logs", ["resource_id"])
    op.create_index("ix_audit_status", "audit_logs", ["status"])
    op.create_index("ix_audit_created_at", "audit_logs", ["created_at"])
    op.create_index("ix_audit_program_id", "audit_logs", ["program_id"])
    op.create_index("ix_audit_session_id", "audit_logs", ["session_id"])

    # ------------------------------------------------------------------
    # Trigger: auto-update updated_at columns
    # ------------------------------------------------------------------
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)

    for table in [
        "users", "departments", "programs", "courses",
        "course_outcomes", "program_outcomes", "copo_maps",
        "attainment_records", "sar_documents",
    ]:
        op.execute(f"""
            CREATE TRIGGER trg_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """)


def downgrade() -> None:
    # Drop triggers first
    for table in [
        "users", "departments", "programs", "courses",
        "course_outcomes", "program_outcomes", "copo_maps",
        "attainment_records", "sar_documents",
    ]:
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_updated_at ON {table};")

    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column();")

    # Drop tables in reverse FK order
    op.drop_table("audit_logs")
    op.drop_table("sar_documents")
    op.drop_table("attainment_records")
    op.drop_table("copo_maps")
    op.drop_table("program_outcomes")
    op.drop_table("course_outcomes")
    op.drop_table("courses")
    op.drop_table("programs")

    # Remove the cross-reference FK before dropping departments
    op.drop_constraint("fk_users_department_id", "users", type_="foreignkey")
    op.drop_table("departments")
    op.drop_table("users")

    # Drop enums
    for enum_name in [
        "audit_status_enum", "audit_resource_type_enum", "audit_action_enum",
        "sar_version_enum", "sar_status_enum",
        "attainment_status_enum", "attainment_method_enum", "attainment_type_enum",
        "mapping_method_enum", "po_status_enum", "po_type_enum",
        "co_status_enum", "blooms_taxonomy_enum",
        "course_category_enum", "course_type_enum",
        "program_status_enum", "program_level_enum",
        "user_status_enum", "user_role_enum",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name};")
