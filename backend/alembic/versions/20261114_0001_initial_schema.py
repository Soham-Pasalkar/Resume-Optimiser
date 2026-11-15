"""initial schema

Revision ID: 20261114_0001
Revises: 
Create Date: 2026-11-14 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from app.models.base import GUID

# revision identifiers, used by Alembic.
revision: str = "20261114_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users
    op.create_table(
        "users",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True, index=True),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False, default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 2. user_profiles
    op.create_table(
        "user_profiles",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("user_id", GUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True),
        sa.Column("headline", sa.String(length=255), nullable=True),
        sa.Column("target_role_title", sa.String(length=255), nullable=True),
        sa.Column("target_seniority", sa.String(length=50), nullable=True),
        sa.Column("years_of_experience", sa.Float(), nullable=True),
        sa.Column("linkedin_url", sa.String(length=512), nullable=True),
        sa.Column("github_url", sa.String(length=512), nullable=True),
        sa.Column("portfolio_url", sa.String(length=512), nullable=True),
        sa.Column("preferences", sa.JSON(), nullable=False, default=dict),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 3. resumes
    op.create_table(
        "resumes",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("user_id", GUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_key", sa.String(length=512), nullable=False),
        sa.Column("file_format", sa.String(length=10), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("is_master", sa.Boolean(), nullable=False, default=False),
        sa.Column("parsing_status", sa.String(length=50), nullable=False, default="PARSED"),
        sa.Column("ocr_applied", sa.Boolean(), nullable=False, default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 4. resume_sections
    op.create_table(
        "resume_sections",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("resume_id", GUID(), sa.ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("section_type", sa.String(length=50), nullable=False),
        sa.Column("heading", sa.String(length=255), nullable=False),
        sa.Column("raw_content", sa.Text(), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False, default=1),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 5. resume_items
    op.create_table(
        "resume_items",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("section_id", GUID(), sa.ForeignKey("resume_sections.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("item_type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("organization", sa.String(length=255), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("start_date", sa.String(length=50), nullable=True),
        sa.Column("end_date", sa.String(length=50), nullable=True),
        sa.Column("is_current", sa.Boolean(), nullable=False, default=False),
        sa.Column("bullets", sa.JSON(), nullable=False, default=list),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 6. job_descriptions
    op.create_table(
        "job_descriptions",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("user_id", GUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("job_title", sa.String(length=255), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("department", sa.String(length=255), nullable=True),
        sa.Column("seniority_level", sa.String(length=50), nullable=True),
        sa.Column("work_mode", sa.String(length=50), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("salary_range", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 7. jd_requirements
    op.create_table(
        "jd_requirements",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("jd_id", GUID(), sa.ForeignKey("job_descriptions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("requirement_text", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("is_mandatory", sa.Boolean(), nullable=False, default=True),
        sa.Column("importance_weight", sa.Float(), nullable=False, default=1.0),
        sa.Column("min_years_experience", sa.Float(), nullable=True),
        sa.Column("canonical_skill_name", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 8. candidate_skills
    op.create_table(
        "candidate_skills",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("user_id", GUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("skill_name", sa.String(length=255), nullable=False),
        sa.Column("normalized_name", sa.String(length=255), nullable=False, index=True),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("proficiency_level", sa.String(length=50), nullable=True, default="proficient"),
        sa.Column("years_experience", sa.Float(), nullable=True),
        sa.Column("evidence_text", sa.Text(), nullable=True),
        sa.Column("evidence_item_id", sa.String(length=50), nullable=True),
        sa.Column("is_user_verified", sa.Boolean(), nullable=False, default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 9. match_evaluations
    op.create_table(
        "match_evaluations",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("user_id", GUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("resume_id", GUID(), sa.ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("jd_id", GUID(), sa.ForeignKey("job_descriptions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("overall_score", sa.Float(), nullable=False),
        sa.Column("lexical_score", sa.Float(), nullable=False),
        sa.Column("semantic_score", sa.Float(), nullable=False),
        sa.Column("skill_match_score", sa.Float(), nullable=False),
        sa.Column("experience_score", sa.Float(), nullable=False),
        sa.Column("domain_score", sa.Float(), nullable=False),
        sa.Column("scoring_breakdown", sa.JSON(), nullable=False, default=dict),
        sa.Column("summary_analysis", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 10. skill_gap_items
    op.create_table(
        "skill_gap_items",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("match_evaluation_id", GUID(), sa.ForeignKey("match_evaluations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("requirement_id", GUID(), sa.ForeignKey("jd_requirements.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("gap_severity", sa.String(length=20), nullable=False),
        sa.Column("evidence_snippet", sa.Text(), nullable=True),
        sa.Column("similarity_score", sa.Float(), nullable=False, default=0.0),
        sa.Column("suggested_action", sa.Text(), nullable=True),
        sa.Column("is_resolved", sa.Boolean(), nullable=False, default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 11. skill_ontology_nodes
    op.create_table(
        "skill_ontology_nodes",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("canonical_name", sa.String(length=255), nullable=False, unique=True, index=True),
        sa.Column("aliases", sa.JSON(), nullable=False, default=list),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("parent_name", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 12. tailored_resumes
    op.create_table(
        "tailored_resumes",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("user_id", GUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("source_resume_id", GUID(), sa.ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("target_jd_id", GUID(), sa.ForeignKey("job_descriptions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("match_evaluation_id", GUID(), sa.ForeignKey("match_evaluations.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("version_title", sa.String(length=255), nullable=False),
        sa.Column("tailored_content", sa.JSON(), nullable=False, default=dict),
        sa.Column("pdf_export_key", sa.String(length=512), nullable=True),
        sa.Column("docx_export_key", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 13. tailored_bullet_diffs
    op.create_table(
        "tailored_bullet_diffs",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("tailored_resume_id", GUID(), sa.ForeignKey("tailored_resumes.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("section_id", sa.String(length=50), nullable=True),
        sa.Column("item_id", sa.String(length=50), nullable=True),
        sa.Column("bullet_index", sa.Integer(), nullable=False, default=0),
        sa.Column("original_text", sa.Text(), nullable=False),
        sa.Column("optimized_text", sa.Text(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("targeted_requirement_id", GUID(), sa.ForeignKey("jd_requirements.id", ondelete="SET NULL"), nullable=True),
        sa.Column("nli_verification_status", sa.String(length=50), nullable=False, default="ENTAILMENT"),
        sa.Column("status", sa.String(length=20), nullable=False, default="PENDING"),
        sa.Column("edited_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 14. learning_roadmaps
    op.create_table(
        "learning_roadmaps",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("user_id", GUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("match_evaluation_id", GUID(), sa.ForeignKey("match_evaluations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("target_role_title", sa.String(length=255), nullable=False),
        sa.Column("estimated_total_hours", sa.Integer(), nullable=True, default=40),
        sa.Column("status", sa.String(length=50), nullable=False, default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 15. learning_milestones (Baseline columns)
    op.create_table(
        "learning_milestones",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("roadmap_id", GUID(), sa.ForeignKey("learning_roadmaps.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("sequence_order", sa.Integer(), nullable=False, default=1),
        sa.Column("skill_name", sa.String(length=255), nullable=False),
        sa.Column("milestone_title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("curated_resources", sa.JSON(), nullable=False, default=list),
        sa.Column("practical_project_brief", sa.Text(), nullable=True),
        sa.Column("is_completed", sa.Boolean(), nullable=False, default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 16. interview_preps
    op.create_table(
        "interview_preps",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("user_id", GUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("match_evaluation_id", GUID(), sa.ForeignKey("match_evaluations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("target_role_title", sa.String(length=255), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 17. interview_questions
    op.create_table(
        "interview_questions",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("prep_id", GUID(), sa.ForeignKey("interview_preps.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("question_type", sa.String(length=50), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("target_skill_or_gap", sa.String(length=255), nullable=True),
        sa.Column("evaluation_criteria", sa.Text(), nullable=False),
        sa.Column("star_guidelines", sa.JSON(), nullable=False, default=dict),
        sa.Column("practice_response", sa.Text(), nullable=True),
        sa.Column("ai_feedback", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 18. job_applications
    op.create_table(
        "job_applications",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("user_id", GUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("job_description_id", GUID(), sa.ForeignKey("job_descriptions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("tailored_resume_id", GUID(), sa.ForeignKey("tailored_resumes.id", ondelete="SET NULL"), nullable=True),
        sa.Column("match_evaluation_id", GUID(), sa.ForeignKey("match_evaluations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("job_title", sa.String(length=255), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("stage", sa.String(length=50), nullable=False, default="SAVED"),
        sa.Column("priority", sa.String(length=20), nullable=False, default="MEDIUM"),
        sa.Column("salary_range", sa.String(length=100), nullable=True),
        sa.Column("job_url", sa.String(length=500), nullable=True),
        sa.Column("applied_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_archived", sa.Boolean(), nullable=False, default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 19. application_activities
    op.create_table(
        "application_activities",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("application_id", GUID(), sa.ForeignKey("job_applications.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("activity_type", sa.String(length=50), nullable=False),
        sa.Column("from_stage", sa.String(length=50), nullable=True),
        sa.Column("to_stage", sa.String(length=50), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("application_activities")
    op.drop_table("job_applications")
    op.drop_table("interview_questions")
    op.drop_table("interview_preps")
    op.drop_table("learning_milestones")
    op.drop_table("learning_roadmaps")
    op.drop_table("tailored_bullet_diffs")
    op.drop_table("tailored_resumes")
    op.drop_table("skill_ontology_nodes")
    op.drop_table("skill_gap_items")
    op.drop_table("match_evaluations")
    op.drop_table("candidate_skills")
    op.drop_table("jd_requirements")
    op.drop_table("job_descriptions")
    op.drop_table("resume_items")
    op.drop_table("resume_sections")
    op.drop_table("resumes")
    op.drop_table("user_profiles")
    op.drop_table("users")
