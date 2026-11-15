import os
import tempfile
import pytest
from alembic.config import Config
from alembic import command
import sqlalchemy as sa


def test_alembic_migrations_lifecycle():
    """Test full migration lifecycle:
    1. Fresh database upgrade to 20261114_0001 (baseline schema)
    2. Insert baseline records into learning_milestones and verify
    3. Upgrade to 20261116_0002 (new milestone fields)
    4. Verify all new fields exist with correct default values and existing records remain valid
    5. Test downgrade to 20261114_0001
    6. Verify new columns dropped and baseline records preserved
    7. Re-upgrade to head
    8. Downgrade to base (clean schema drop)
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        db_url = f"sqlite:///{db_path}"
        alembic_ini_path = os.path.join(os.path.dirname(__file__), "..", "alembic.ini")
        alembic_cfg = Config(alembic_ini_path)
        alembic_cfg.set_main_option("sqlalchemy.url", db_url)
        alembic_cfg.set_main_option("script_location", os.path.join(os.path.dirname(__file__), "..", "alembic"))

        # Step 1: Upgrade to baseline revision (20261114_0001)
        command.upgrade(alembic_cfg, "20261114_0001")

        engine = sa.create_engine(db_url)
        with engine.connect() as conn:
            # Check baseline tables exist
            inspector = sa.inspect(conn)
            tables = inspector.get_table_names()
            assert "users" in tables
            assert "learning_roadmaps" in tables
            assert "learning_milestones" in tables

            # Verify baseline columns in learning_milestones
            cols = {c["name"] for c in inspector.get_columns("learning_milestones")}
            assert "sequence_order" in cols
            assert "skill_name" in cols
            assert "why_it_matters" not in cols
            assert "verification_status" not in cols

            # Step 2: Seed baseline user, roadmap, and milestone
            conn.execute(sa.text("""
                INSERT INTO users (id, email, hashed_password, full_name, is_active, is_verified, created_at, updated_at)
                VALUES ('user-1', 'test@careerpilot.io', 'hash', 'Test User', 1, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """))
            conn.execute(sa.text("""
                INSERT INTO resumes (id, user_id, file_name, file_key, file_format, file_size_bytes, raw_text, is_master, parsing_status, ocr_applied, created_at, updated_at)
                VALUES ('res-1', 'user-1', 'res.pdf', 'k', 'pdf', 100, 'text', 1, 'PARSED', 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """))
            conn.execute(sa.text("""
                INSERT INTO job_descriptions (id, user_id, job_title, raw_text, created_at, updated_at)
                VALUES ('jd-1', 'user-1', 'Data Engineer', 'text', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """))
            conn.execute(sa.text("""
                INSERT INTO match_evaluations (id, user_id, resume_id, jd_id, overall_score, lexical_score, semantic_score, skill_match_score, experience_score, domain_score, scoring_breakdown, created_at, updated_at)
                VALUES ('me-1', 'user-1', 'res-1', 'jd-1', 80.0, 80.0, 80.0, 80.0, 80.0, 80.0, '{}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """))
            conn.execute(sa.text("""
                INSERT INTO learning_roadmaps (id, user_id, match_evaluation_id, target_role_title, estimated_total_hours, status, created_at, updated_at)
                VALUES ('rm-1', 'user-1', 'me-1', 'Data Engineer', 40, 'ACTIVE', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """))
            conn.execute(sa.text("""
                INSERT INTO learning_milestones (id, roadmap_id, sequence_order, skill_name, milestone_title, description, curated_resources, practical_project_brief, is_completed, created_at, updated_at)
                VALUES ('ms-1', 'rm-1', 1, 'PySpark', 'Master PySpark', 'Learn distributed data frames', '[]', 'Build pipeline', 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """))
            conn.commit()

        # Step 3: Upgrade to head (20261116_0002)
        command.upgrade(alembic_cfg, "head")

        with engine.connect() as conn:
            inspector = sa.inspect(conn)
            cols = {c["name"] for c in inspector.get_columns("learning_milestones")}
            # All 10 fields must be present
            expected_fields = [
                "why_it_matters", "prerequisites", "learning_objectives",
                "practical_exercises", "expected_deliverables", "verification_criteria",
                "estimated_hours", "completed_evidence", "evidence_verified",
                "verification_status"
            ]
            for f in expected_fields:
                assert f in cols, f"Field {f} missing after upgrade"

            # Step 4: Verify existing record retained its data and acquired default values
            result = conn.execute(sa.text("SELECT skill_name, verification_status, estimated_hours, evidence_verified FROM learning_milestones WHERE id = 'ms-1'")).fetchone()
            assert result[0] == "PySpark"
            assert result[1] == "UNSUBMITTED"
            assert result[2] == 10
            assert result[3] == 0 or result[3] is False

        # Step 5: Downgrade back to baseline (20261114_0001)
        command.downgrade(alembic_cfg, "20261114_0001")

        with engine.connect() as conn:
            inspector = sa.inspect(conn)
            cols = {c["name"] for c in inspector.get_columns("learning_milestones")}
            assert "why_it_matters" not in cols
            assert "verification_status" not in cols
            # Existing baseline record still present
            result = conn.execute(sa.text("SELECT skill_name FROM learning_milestones WHERE id = 'ms-1'")).fetchone()
            assert result[0] == "PySpark"

        # Step 6: Re-upgrade to head
        command.upgrade(alembic_cfg, "head")
        with engine.connect() as conn:
            inspector = sa.inspect(conn)
            cols = {c["name"] for c in inspector.get_columns("learning_milestones")}
            assert "verification_status" in cols

        # Step 7: Downgrade to base (clean teardown)
        command.downgrade(alembic_cfg, "base")
        with engine.connect() as conn:
            inspector = sa.inspect(conn)
            tables = inspector.get_table_names()
            assert "learning_milestones" not in tables
            assert "users" not in tables

    finally:
        if os.path.exists(db_path):
            os.remove(db_path)
