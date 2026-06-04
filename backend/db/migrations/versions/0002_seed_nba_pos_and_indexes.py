"""Seed NBA standard PO definitions and add GIN indexes

Revision ID: 0002_seed_nba_pos_and_indexes
Revises: 0001_initial_schema
Create Date: 2024-01-02 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_seed_nba_pos_and_indexes"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ---------------------------------------------------------------------------
# NBA Standard PO Descriptions (PO1–PO12)
# These are seeded into a reference table; actual PO records per program
# are created programmatically at program-creation time.
# ---------------------------------------------------------------------------
NBA_STANDARD_PO_SEED = """
CREATE TABLE IF NOT EXISTS nba_standard_pos (
    code        VARCHAR(10)  PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    description TEXT         NOT NULL,
    sequence    INTEGER      NOT NULL,
    is_active   BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

INSERT INTO nba_standard_pos (code, name, description, sequence) VALUES
('PO1',  'Engineering Knowledge',
 'Apply knowledge of mathematics, science, engineering fundamentals, and engineering specialization to the solution of complex engineering problems.',
 1),
('PO2',  'Problem Analysis',
 'Identify, formulate, review research literature, and analyze complex engineering problems reaching substantiated conclusions using first principles of mathematics, natural sciences, and engineering sciences.',
 2),
('PO3',  'Design/Development of Solutions',
 'Design solutions for complex engineering problems and design system components or processes that meet the specified needs with appropriate consideration for the public health and safety, and the cultural, societal, and environmental considerations.',
 3),
('PO4',  'Conduct Investigations of Complex Problems',
 'Use research-based knowledge and research methods including design of experiments, analysis and interpretation of data, and synthesis of the information to provide valid conclusions.',
 4),
('PO5',  'Modern Tool Usage',
 'Create, select, and apply appropriate techniques, resources, and modern engineering and IT tools including prediction and modeling to complex engineering activities with an understanding of the limitations.',
 5),
('PO6',  'The Engineer and Society',
 'Apply reasoning informed by the contextual knowledge to assess societal, health, safety, legal and cultural issues and the consequent responsibilities relevant to the professional engineering practice.',
 6),
('PO7',  'Environment and Sustainability',
 'Understand the impact of the professional engineering solutions in societal and environmental contexts, and demonstrate the knowledge of, and need for sustainable development.',
 7),
('PO8',  'Ethics',
 'Apply ethical principles and commit to professional ethics and responsibilities and norms of the engineering practice.',
 8),
('PO9',  'Individual and Team Work',
 'Function effectively as an individual, and as a member or leader in diverse teams, and in multidisciplinary settings.',
 9),
('PO10', 'Communication',
 'Communicate effectively on complex engineering activities with the engineering community and with society at large, such as, being able to comprehend and write effective reports and design documentation, make effective presentations, and give and receive clear instructions.',
 10),
('PO11', 'Project Management and Finance',
 'Demonstrate knowledge and understanding of the engineering and management principles and apply these to one''s own work, as a member and leader in a team, to manage projects and in multidisciplinary environments.',
 11),
('PO12', 'Life-long Learning',
 'Recognize the need for, and have the preparation and ability to engage in independent and life-long learning in the broadest context of technological change.',
 12)
ON CONFLICT (code) DO NOTHING;
"""

NBA_STANDARD_PO_SEED_DOWN = "DROP TABLE IF EXISTS nba_standard_pos;"


def upgrade() -> None:
    # ------------------------------------------------------------------
    # Reference table for NBA standard PO definitions
    # ------------------------------------------------------------------
    op.execute(NBA_STANDARD_PO_SEED)

    # ------------------------------------------------------------------
    # GIN index on JSONB columns for fast key/value queries
    # ------------------------------------------------------------------
    op.execute(
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_co_assessment_weightage_gin "
        "ON course_outcomes USING GIN (assessment_weightage);"
    )
    op.execute(
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_co_cia1_mapping_gin "
        "ON course_outcomes USING GIN (cia1_mapping);"
    )
    op.execute(
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_co_ese_mapping_gin "
        "ON course_outcomes USING GIN (ese_mapping);"
    )
    op.execute(
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_attainment_cia1_data_gin "
        "ON attainment_records USING GIN (cia1_data);"
    )
    op.execute(
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_sar_gap_analysis_gin "
        "ON sar_documents USING GIN (gap_analysis_summary);"
    )
    op.execute(
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_audit_before_state_gin "
        "ON audit_logs USING GIN (before_state);"
    )
    op.execute(
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_audit_after_state_gin "
        "ON audit_logs USING GIN (after_state);"
    )

    # ------------------------------------------------------------------
    # pg_trgm index for fuzzy text search on CO statements
    # ------------------------------------------------------------------
    op.execute(
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_cos_statement_trgm "
        "ON course_outcomes USING GIN (statement gin_trgm_ops);"
    )
    op.execute(
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_pos_description_trgm "
        "ON program_outcomes USING GIN (description gin_trgm_ops);"
    )

    # ------------------------------------------------------------------
    # Composite indexes for common query patterns
    # ------------------------------------------------------------------
    # Attainment lookups by program + year
    op.create_index(
        "ix_attainment_program_year",
        "attainment_records",
        ["program_id", "academic_year"],
    )
    # CO-PO map lookups by program + approval status
    op.create_index(
        "ix_copo_program_approved",
        "copo_maps",
        ["program_id", "is_approved"],
    )
    # Active courses per program per semester
    op.create_index(
        "ix_courses_program_semester_active",
        "courses",
        ["program_id", "semester", "is_active"],
    )
    # Users by department + role
    op.create_index(
        "ix_users_dept_role",
        "users",
        ["department_id", "role"],
    )
    # SAR by program + year + status
    op.create_index(
        "ix_sar_program_year_status",
        "sar_documents",
        ["program_id", "academic_year", "status"],
    )
    # Audit logs by date range
    op.create_index(
        "ix_audit_created_at_brin",
        "audit_logs",
        ["created_at"],
        postgresql_using="brin",
    )


def downgrade() -> None:
    # Drop composite / special indexes
    for idx, tbl in [
        ("ix_audit_created_at_brin", "audit_logs"),
        ("ix_sar_program_year_status", "sar_documents"),
        ("ix_users_dept_role", "users"),
        ("ix_courses_program_semester_active", "courses"),
        ("ix_copo_program_approved", "copo_maps"),
        ("ix_attainment_program_year", "attainment_records"),
    ]:
        op.drop_index(idx, table_name=tbl)

    # Drop GIN / trgm indexes
    for idx in [
        "ix_audit_after_state_gin",
        "ix_audit_before_state_gin",
        "ix_sar_gap_analysis_gin",
        "ix_attainment_cia1_data_gin",
        "ix_co_ese_mapping_gin",
        "ix_co_cia1_mapping_gin",
        "ix_co_assessment_weightage_gin",
        "ix_cos_statement_trgm",
        "ix_pos_description_trgm",
    ]:
        op.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {idx};")

    op.execute(NBA_STANDARD_PO_SEED_DOWN)
