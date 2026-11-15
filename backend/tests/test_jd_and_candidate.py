import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume import Resume, ResumeItem, ResumeSection
from app.modules.jd_engine.extractor import jd_extractor
from app.modules.ontology.normalizer import skill_normalizer

SAMPLE_JD_TEXT = """
Job Title: Senior Backend Engineer
Company: Acme AI Labs
Location: San Francisco, CA (Remote)
Salary: $160,000 - $190,000 per year

About the Role:
We are looking for a Senior Backend Engineer to build high-scale distributed systems and APIs.

Minimum Qualifications:
- 5+ years of experience building production backend systems with Python and Go.
- Strong hands-on proficiency with PostgreSQL, Redis, and database query optimization.
- Proven experience deploying containerized applications with Docker and Kubernetes on AWS.
- Bachelor's degree in Computer Science or equivalent practical experience.

Preferred Qualifications:
- 2+ years of experience with Kafka and event-driven architectures.
- Experience with GraphQL APIs and TypeScript.
- Contributions to open-source software.

Responsibilities:
- Design and scale distributed microservices handling millions of daily requests.
- Collaborate closely with product managers and frontend engineers.
"""


def test_skill_normalizer_aliases_and_extraction():
    # Canonical mappings
    assert skill_normalizer.normalize("python3") == ("Python", "Programming Languages")
    assert skill_normalizer.normalize("golang") == ("Go", "Programming Languages")
    assert skill_normalizer.normalize("k8s") == ("Kubernetes", "Cloud & Infrastructure")
    assert skill_normalizer.normalize("aws") == ("AWS", "Cloud & Infrastructure")
    assert skill_normalizer.normalize("POSTGRES") == ("PostgreSQL", "Databases & Storage")

    # Text extraction
    text = "Architected low-latency microservices with Python, FastAPI, and Docker on AWS."
    skills = skill_normalizer.extract_skills_from_text(text)
    canonical_names = {s["canonical_name"] for s in skills}
    assert "Python" in canonical_names
    assert "FastAPI" in canonical_names
    assert "Docker" in canonical_names
    assert "AWS" in canonical_names


@pytest.mark.asyncio
async def test_jd_extractor_rule_based_decomposition():
    decomposed = await jd_extractor.extract(SAMPLE_JD_TEXT)

    assert "Senior Backend Engineer" in decomposed.job_title
    assert decomposed.seniority_level == "Senior"
    assert decomposed.work_mode == "Remote"
    assert "$160,000" in (decomposed.salary_range or "")
    assert len(decomposed.requirements) >= 5

    # Check mandatory vs preferred classification
    mandatory_reqs = [r for r in decomposed.requirements if r.is_mandatory]
    preferred_reqs = [r for r in decomposed.requirements if not r.is_mandatory]

    assert len(mandatory_reqs) >= 3
    assert len(preferred_reqs) >= 2

    # Check experience extraction (e.g. 5+ years)
    python_req = next(
        (
            r
            for r in mandatory_reqs
            if "Python" in (r.canonical_skill_name or "") or "Python" in r.requirement_text
        ),
        None,
    )
    assert python_req is not None
    assert python_req.min_years_experience == 5.0
    assert python_req.importance_weight == 1.0

    # Preferred req should have lower importance weight
    kafka_req = next(
        (
            r
            for r in preferred_reqs
            if "Kafka" in (r.canonical_skill_name or "") or "Kafka" in r.requirement_text
        ),
        None,
    )
    assert kafka_req is not None
    assert kafka_req.is_mandatory is False
    assert kafka_req.importance_weight == 0.6


@pytest.mark.asyncio
async def test_jd_extractor_narrative_paragraph_decomposition():
    narrative_jd = """
    Job Title: Staff Infrastructure Architect
    Acme Corp is looking for a Staff Infrastructure Architect. You will be responsible for leading our distributed systems migration on AWS and Kubernetes.
    The ideal candidate must have at least 7 years of hands-on experience designing fault-tolerant cloud backends in Go and Python.
    You will lead technical architecture reviews and mentor junior engineers across engineering.
    Experience with Apache Kafka and Redis is a plus.
    """
    decomposed = await jd_extractor.extract(narrative_jd)

    assert "Staff Infrastructure Architect" in decomposed.job_title
    assert len(decomposed.requirements) >= 3

    # Ensure requirements are extracted verbatim from paragraphs rather than synthetic generic phrases
    req_texts = [r.requirement_text for r in decomposed.requirements]
    assert any("7 years" in t or "hands-on experience" in t for t in req_texts)
    assert any("Kafka" in t or "Redis" in t for t in req_texts)

    # Check that "is a plus" was classified as preferred
    kafka_req = next((r for r in decomposed.requirements if "Kafka" in r.requirement_text), None)
    if kafka_req:
        assert kafka_req.is_mandatory is False


@pytest.mark.asyncio
async def test_job_description_crud_and_tenancy(async_client: AsyncClient):
    # 1. Register User A
    user_a_email = f"user_a_{uuid.uuid4().hex[:6]}@example.com"
    reg_a = await async_client.post(
        "/api/v1/auth/register",
        json={"email": user_a_email, "password": "Password123!", "full_name": "User Alpha"},
    )
    assert reg_a.status_code == 201
    token_a = reg_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. User A analyzes JD
    analyze_resp = await async_client.post(
        "/api/v1/jobs/analyze",
        headers=headers_a,
        json={
            "raw_text": SAMPLE_JD_TEXT,
            "job_title": "Custom Senior Engineer",
            "company_name": "Acme AI",
        },
    )
    assert analyze_resp.status_code == 201
    jd_data = analyze_resp.json()
    jd_id = jd_data["id"]
    assert jd_data["job_title"] == "Custom Senior Engineer"
    assert jd_data["company_name"] == "Acme AI"
    assert len(jd_data["requirements"]) >= 5

    # 3. User A lists JDs
    list_resp = await async_client.get("/api/v1/jobs", headers=headers_a)
    assert list_resp.status_code == 200
    jds = list_resp.json()
    assert len(jds) == 1
    assert jds[0]["id"] == jd_id
    assert jds[0]["requirements_count"] >= 5

    # 4. User A gets JD detail
    detail_resp = await async_client.get(f"/api/v1/jobs/{jd_id}", headers=headers_a)
    assert detail_resp.status_code == 200
    assert detail_resp.json()["id"] == jd_id

    # 5. Register User B and verify tenant isolation
    user_b_email = f"user_b_{uuid.uuid4().hex[:6]}@example.com"
    reg_b = await async_client.post(
        "/api/v1/auth/register",
        json={"email": user_b_email, "password": "Password123!", "full_name": "User Beta"},
    )
    assert reg_b.status_code == 201
    token_b = reg_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User B should not see User A's JD
    b_list_resp = await async_client.get("/api/v1/jobs", headers=headers_b)
    assert b_list_resp.status_code == 200
    assert len(b_list_resp.json()) == 0

    # User B attempting to get User A's JD should receive 404
    b_get_resp = await async_client.get(f"/api/v1/jobs/{jd_id}", headers=headers_b)
    assert b_get_resp.status_code == 404

    # User B attempting to delete User A's JD should receive 404
    b_del_resp = await async_client.delete(f"/api/v1/jobs/{jd_id}", headers=headers_b)
    assert b_del_resp.status_code == 404

    # 6. User A deletes JD
    del_resp = await async_client.delete(f"/api/v1/jobs/{jd_id}", headers=headers_a)
    assert del_resp.status_code == 204

    get_after_del = await async_client.get(f"/api/v1/jobs/{jd_id}", headers=headers_a)
    assert get_after_del.status_code == 404


@pytest.mark.asyncio
async def test_candidate_profile_evidence_anchoring_and_verification(
    async_client: AsyncClient,
    db_session: AsyncSession,
):
    # 1. Register candidate
    email = f"candidate_{uuid.uuid4().hex[:6]}@example.com"
    reg = await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!", "full_name": "Jane Candidate"},
    )
    assert reg.status_code == 201
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    user_id = uuid.UUID(reg.json()["user"]["id"])

    # 2. Seed a parsed resume with work experience bullets
    resume = Resume(
        user_id=user_id,
        file_name="jane_resume.pdf",
        file_key="resumes/jane_resume.pdf",
        file_format="pdf",
        file_size_bytes=1024,
        raw_text="Jane Candidate Resume Text",
        is_master=True,
        parsing_status="PARSED",
    )
    db_session.add(resume)
    await db_session.flush()

    sec_exp = ResumeSection(
        resume_id=resume.id,
        section_type="EXPERIENCE",
        heading="Professional Experience",
        raw_content="Acme Tech - Lead Backend Engineer",
        display_order=1,
    )
    db_session.add(sec_exp)
    await db_session.flush()

    item_exp = ResumeItem(
        section_id=sec_exp.id,
        item_type="EXPERIENCE",
        title="Lead Backend Engineer",
        organization="Acme Tech",
        start_date="2021",
        end_date="Present",
        is_current=True,
        bullets=[
            "Built distributed microservices in Go and Python serving 5M daily active users.",
            "Optimized PostgreSQL query latency by 45% and provisioned Redis caching clusters.",
            "Orchestrated Kubernetes deployments with Docker on AWS EKS.",
        ],
    )
    db_session.add(item_exp)
    await db_session.commit()

    # 3. Call build-profile endpoint
    build_resp = await async_client.post(
        "/api/v1/candidate/build-profile",
        headers=headers,
        json={"resume_id": str(resume.id)},
    )
    assert build_resp.status_code == 200
    skills = build_resp.json()
    assert len(skills) >= 4

    canonical_names = {s["normalized_name"] for s in skills}
    assert "Python" in canonical_names
    assert "Go" in canonical_names
    assert "PostgreSQL" in canonical_names
    assert "Kubernetes" in canonical_names

    # Verify evidence anchoring
    python_skill = next(s for s in skills if s["normalized_name"] == "Python")
    assert python_skill["evidence_text"] is not None
    assert "Go and Python" in python_skill["evidence_text"]
    assert python_skill["evidence_item_id"] == str(item_exp.id)
    assert python_skill["is_user_verified"] is False

    # 4. Toggle verification
    verify_resp = await async_client.post(
        "/api/v1/candidate/verify-skill",
        headers=headers,
        json={"skill_id": python_skill["id"], "is_verified": True},
    )
    assert verify_resp.status_code == 200
    assert verify_resp.json()["is_user_verified"] is True

    # 5. Add custom skill
    add_resp = await async_client.post(
        "/api/v1/candidate/skills",
        headers=headers,
        json={
            "skill_name": "FastAPI",
            "proficiency_level": "advanced",
            "evidence_text": "Built asynchronous REST APIs using FastAPI.",
        },
    )
    assert add_resp.status_code == 201
    custom_skill = add_resp.json()
    assert custom_skill["normalized_name"] == "FastAPI"
    assert custom_skill["is_user_verified"] is True

    # 6. Delete custom skill
    del_resp = await async_client.delete(
        f"/api/v1/candidate/skills/{custom_skill['id']}",
        headers=headers,
    )
    assert del_resp.status_code == 204
