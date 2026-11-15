import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate import CandidateSkill
from app.models.jd import JDRequirement, JobDescription
from app.models.resume import Resume, ResumeItem, ResumeSection
from app.modules.matching.bm25 import BM25Index
from app.modules.matching.dense import cosine_similarity, dense_matcher
from app.modules.matching.scorer import hybrid_matching_engine


def test_bm25_indexing_and_scoring():
    corpus = [
        "Architected distributed microservices in Go and Python on AWS ECS.",
        "Built responsive frontend user interfaces using React, Next.js, and Tailwind CSS.",
        "Managed database migrations, indexing, and query tuning in PostgreSQL and Redis.",
    ]
    bm25 = BM25Index()
    bm25.fit(corpus)

    # Query matching doc 0
    score_python = bm25.score_query_across_corpus("Python microservices AWS")
    assert score_python > 0.5

    # Query matching doc 1
    score_react = bm25.score_query_across_corpus("React frontend Next.js")
    assert score_react > 0.5

    # Overall lexical alignment
    requirements = [
        "5+ years of experience with Python and microservices",
        "Proficiency with PostgreSQL query optimization",
    ]
    lex_score = bm25.compute_overall_lexical_alignment(requirements)
    assert 40.0 <= lex_score <= 100.0


@pytest.mark.asyncio
async def test_dense_matcher_cosine_similarity():
    # Identical vectors
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    assert cosine_similarity(v1, v2) == 1.0

    # Orthogonal
    v3 = [0.0, 1.0, 0.0]
    assert cosine_similarity(v1, v3) == 0.0

    # Best evidence match
    snippets = [
        "Led backend infrastructure team at Fintech Corp.",
        "Designed and implemented high-throughput Kafka streaming pipelines.",
        "Created design systems and UI component libraries in Figma and CSS.",
    ]
    sim, best = await dense_matcher.find_best_evidence_match("Kafka event streaming", snippets)
    assert sim > 0.4
    assert best == snippets[1]


@pytest.mark.asyncio
async def test_hybrid_scoring_engine_calculation():
    # Prepare mock objects
    resume = Resume(
        user_id=uuid.uuid4(),
        file_name="resume.pdf",
        file_key="resumes/resume.pdf",
        file_format="pdf",
        file_size_bytes=1000,
        raw_text="Experienced engineer in Python, Docker, and PostgreSQL.",
        is_master=True,
    )
    sec = ResumeSection(
        resume_id=resume.id,
        section_type="EXPERIENCE",
        heading="Work Experience",
        raw_content="Senior Backend Dev at Acme",
        display_order=1,
    )
    sec.items = [
        ResumeItem(
            section_id=sec.id,
            item_type="EXPERIENCE",
            title="Senior Backend Dev",
            organization="Acme",
            bullets=[
                "Built production backend APIs in Python and FastAPI.",
                "Administered PostgreSQL database clusters and optimized SQL queries.",
            ],
        )
    ]
    resume.sections = [sec]

    jd = JobDescription(
        user_id=resume.user_id,
        job_title="Senior Python Backend Engineer",
        raw_text="We need Python, PostgreSQL, and Kubernetes.",
        seniority_level="Senior",
    )
    jd.requirements = [
        JDRequirement(
            jd_id=jd.id,
            requirement_text="5+ years of Python microservices experience.",
            category="technical_skill",
            is_mandatory=True,
            importance_weight=1.0,
            canonical_skill_name="Python",
        ),
        JDRequirement(
            jd_id=jd.id,
            requirement_text="Strong relational database query tuning in PostgreSQL.",
            category="technical_skill",
            is_mandatory=True,
            importance_weight=1.0,
            canonical_skill_name="PostgreSQL",
        ),
        JDRequirement(
            jd_id=jd.id,
            requirement_text="Experience with Kubernetes container orchestration.",
            category="technical_skill",
            is_mandatory=False,
            importance_weight=0.6,
            canonical_skill_name="Kubernetes",
        ),
    ]

    cand_skills = [
        CandidateSkill(
            user_id=resume.user_id,
            skill_name="Python",
            normalized_name="Python",
            category="Programming Languages",
            proficiency_level="advanced",
            evidence_text="Built production backend APIs in Python and FastAPI.",
            is_user_verified=True,
        ),
        CandidateSkill(
            user_id=resume.user_id,
            skill_name="PostgreSQL",
            normalized_name="PostgreSQL",
            category="Databases & Storage",
            proficiency_level="proficient",
            evidence_text="Administered PostgreSQL database clusters and optimized SQL queries.",
            is_user_verified=False,
        ),
    ]

    result = await hybrid_matching_engine.evaluate(
        resume=resume,
        jd=jd,
        candidate_skills=cand_skills,
    )

    assert result.overall_score >= 60.0
    assert result.skill_match_score >= 65.0
    assert result.lexical_score > 0.0
    assert result.experience_score >= 60.0
    assert result.domain_score >= 50.0
    assert len(result.gap_evaluations) == 3

    # Python should be DEMONSTRATED
    py_gap = next(g for g in result.gap_evaluations if "Python" in g["requirement_text"])
    assert py_gap["status"] == "DEMONSTRATED"
    assert py_gap["evidence_snippet"] is not None

    # Kubernetes is not in resume -> should be NOT_DEMONSTRATED or PARTIAL
    k8s_gap = next(g for g in result.gap_evaluations if "Kubernetes" in g["requirement_text"])
    assert k8s_gap["status"] in ["NOT_DEMONSTRATED", "PARTIAL"]


@pytest.mark.asyncio
async def test_match_evaluation_api_lifecycle_and_tenancy(
    async_client: AsyncClient,
    db_session: AsyncSession,
):
    # 1. Register User A
    user_a_email = f"matcher_a_{uuid.uuid4().hex[:6]}@example.com"
    reg_a = await async_client.post(
        "/api/v1/auth/register",
        json={"email": user_a_email, "password": "Password123!", "full_name": "Candidate Alpha"},
    )
    assert reg_a.status_code == 201
    token_a = reg_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}
    user_a_id = uuid.UUID(reg_a.json()["user"]["id"])

    # 2. Seed Resume for User A
    resume_a = Resume(
        user_id=user_a_id,
        file_name="alpha_resume.pdf",
        file_key="resumes/alpha_resume.pdf",
        file_format="pdf",
        file_size_bytes=1024,
        raw_text="Alpha Resume Text with Go and Docker",
        is_master=True,
    )
    db_session.add(resume_a)
    await db_session.flush()

    sec_a = ResumeSection(
        resume_id=resume_a.id,
        section_type="EXPERIENCE",
        heading="Experience",
        raw_content="Cloud Architect",
        display_order=1,
    )
    db_session.add(sec_a)
    await db_session.flush()

    item_a = ResumeItem(
        section_id=sec_a.id,
        item_type="EXPERIENCE",
        title="Cloud Architect",
        bullets=["Deployed distributed Go microservices with Docker on AWS."],
    )
    db_session.add(item_a)
    await db_session.commit()

    # 3. Analyze JD for User A
    jd_resp = await async_client.post(
        "/api/v1/jobs/analyze",
        headers=headers_a,
        json={
            "job_title": "Cloud Infrastructure Engineer",
            "company_name": "CloudWorks",
            "raw_text": (
                "Job Title: Cloud Infrastructure Engineer\n"
                "Minimum Qualifications:\n"
                "- 3+ years of experience with Go and Docker.\n"
                "- Experience with Terraform infrastructure as code.\n"
                "Preferred Qualifications:\n"
                "- Kubernetes cluster operations.\n"
            ),
        },
    )
    assert jd_resp.status_code == 201
    jd_a_id = jd_resp.json()["id"]

    # 4. Trigger Match Evaluation
    match_resp = await async_client.post(
        "/api/v1/matches/evaluate",
        headers=headers_a,
        json={
            "resume_id": str(resume_a.id),
            "jd_id": jd_a_id,
        },
    )
    assert match_resp.status_code == 201
    match_data = match_resp.json()
    match_id = match_data["id"]
    assert match_data["overall_score"] > 0
    assert "sub_scores" in match_data
    assert len(match_data["gap_items"]) >= 2

    # 5. List Matches
    list_resp = await async_client.get("/api/v1/matches", headers=headers_a)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1
    assert list_resp.json()[0]["id"] == match_id

    # 6. Get Match Detail
    detail_resp = await async_client.get(f"/api/v1/matches/{match_id}", headers=headers_a)
    assert detail_resp.status_code == 200
    assert detail_resp.json()["id"] == match_id

    # 7. Get Gaps directly
    gaps_resp = await async_client.get(f"/api/v1/matches/{match_id}/gaps", headers=headers_a)
    assert gaps_resp.status_code == 200
    gaps = gaps_resp.json()
    assert len(gaps) >= 2

    # 8. Verify a gap item (e.g. Terraform)
    unresolved_gap = next((g for g in gaps if not g["is_resolved"]), None)
    assert unresolved_gap is not None
    gap_id = unresolved_gap["id"]

    verify_resp = await async_client.post(
        f"/api/v1/matches/{match_id}/gaps/verify",
        headers=headers_a,
        json={
            "gap_item_id": gap_id,
            "has_experience": True,
            "verification_evidence": "Wrote reusable Terraform modules for AWS VPC and RDS.",
        },
    )
    assert verify_resp.status_code == 200
    updated_data = verify_resp.json()
    updated_gap = next(g for g in updated_data["gap_items"] if g["id"] == gap_id)
    assert updated_gap["status"] == "DEMONSTRATED"
    assert updated_gap["is_resolved"] is True
    assert "Terraform" in (updated_gap["evidence_snippet"] or "")

    # 9. Register User B and verify tenant boundary
    user_b_email = f"matcher_b_{uuid.uuid4().hex[:6]}@example.com"
    reg_b = await async_client.post(
        "/api/v1/auth/register",
        json={"email": user_b_email, "password": "Password123!", "full_name": "Candidate Beta"},
    )
    token_b = reg_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User B should not see User A's match
    b_list = await async_client.get("/api/v1/matches", headers=headers_b)
    assert len(b_list.json()) == 0

    # User B attempting to get User A's match returns 404
    b_get = await async_client.get(f"/api/v1/matches/{match_id}", headers=headers_b)
    assert b_get.status_code == 404

    # User B attempting to delete User A's match returns 404
    b_del = await async_client.delete(f"/api/v1/matches/{match_id}", headers=headers_b)
    assert b_del.status_code == 404

    # 10. User A deletes Match Evaluation
    del_resp = await async_client.delete(f"/api/v1/matches/{match_id}", headers=headers_a)
    assert del_resp.status_code == 204

    # Subsequent GET returns 404
    after_del = await async_client.get(f"/api/v1/matches/{match_id}", headers=headers_a)
    assert after_del.status_code == 404
