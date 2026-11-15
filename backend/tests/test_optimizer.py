import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate import CandidateSkill
from app.models.jd import JDRequirement, JobDescription
from app.models.resume import Resume, ResumeItem, ResumeSection
from app.modules.optimizer.exporter import resume_exporter
from app.modules.optimizer.nli_guardrail import nli_guardrail
from app.modules.optimizer.rewriter import bullet_rewriter


def test_nli_guardrail_factual_preservation():
    cand_skills = [
        CandidateSkill(
            user_id=uuid.uuid4(),
            skill_name="Python",
            normalized_name="Python",
            category="Programming Languages",
            proficiency_level="advanced",
            is_user_verified=True,
        ),
        CandidateSkill(
            user_id=uuid.uuid4(),
            skill_name="PostgreSQL",
            normalized_name="PostgreSQL",
            category="Databases & Storage",
            proficiency_level="proficient",
            is_user_verified=True,
        ),
    ]

    orig = "Worked on backend microservices and database queries using Python and PostgreSQL."

    # 1. Valid rephrasing (ENTAILMENT)
    valid_opt = "Architected backend microservices and optimized database queries using Python and PostgreSQL."
    status, rationale = nli_guardrail.verify_bullet(orig, valid_opt, cand_skills)
    assert status == "ENTAILMENT"

    # 2. Hallucinating an ungrounded technology not in source or candidate profile (FLAGGED)
    hallucinated_tech = "Architected Kubernetes microservices deployed using Rust and Docker."
    status, rationale = nli_guardrail.verify_bullet(orig, hallucinated_tech, cand_skills)
    assert status == "FLAGGED"
    assert "unverified technologies" in rationale

    # 3. Fabricating a numerical metric not in source (FLAGGED)
    hallucinated_metric = "Architected Python backend microservices, increasing throughput by 85% and saving $2M annually."
    status, rationale = nli_guardrail.verify_bullet(orig, hallucinated_metric, cand_skills)
    assert status == "FLAGGED"
    assert "fabricated quantitative metrics" in rationale


@pytest.mark.asyncio
async def test_bullet_rewriter_google_xyz_formula():
    jd = JobDescription(
        user_id=uuid.uuid4(),
        job_title="Lead Backend Engineer",
        raw_text="Looking for a Lead Engineer with Python and PostgreSQL.",
    )
    req = JDRequirement(
        jd_id=jd.id,
        requirement_text="Demonstrated microservices optimization in Python.",
        category="technical_skill",
        canonical_skill_name="Python",
    )
    cand_skills = [
        CandidateSkill(
            user_id=jd.user_id,
            skill_name="Python",
            normalized_name="Python",
            category="Programming Languages",
        )
    ]

    orig = "helped with backend APIs and fixed database queries in Python."
    result = await bullet_rewriter.rewrite_bullet(
        original_text=orig,
        jd=jd,
        candidate_skills=cand_skills,
        target_requirement=req,
    )

    assert result["original_text"] == orig
    assert "helped with" not in result["optimized_text"]
    assert (
        "Collaborated to engineer" in result["optimized_text"]
        or "Architected" in result["optimized_text"]
    )
    assert result["nli_verification_status"] == "ENTAILMENT"


def test_resume_export_pdf_and_docx():
    content = {
        "candidate_name": "Marcus Vance",
        "contact_info": "marcus@example.com | San Francisco, CA",
        "sections": [
            {
                "heading": "Experience",
                "section_type": "EXPERIENCE",
                "items": [
                    {
                        "title": "Lead Backend Engineer",
                        "organization": "Acme Tech",
                        "location": "San Francisco",
                        "start_date": "2021",
                        "end_date": "Present",
                        "bullets": [
                            "Architected distributed microservices in Go and Python.",
                            "Optimized PostgreSQL queries reducing latency by 35%.",
                        ],
                    }
                ],
            },
            {
                "heading": "Technical Skills",
                "section_type": "SKILLS",
                "raw_content": "Python, Go, PostgreSQL, Docker, AWS",
            },
        ],
    }

    # 1. PDF Export
    pdf_bytes = resume_exporter.generate_pdf(content)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 500
    assert pdf_bytes.startswith(b"%PDF")

    # 2. DOCX Export
    docx_bytes = resume_exporter.generate_docx(content)
    assert isinstance(docx_bytes, bytes)
    assert len(docx_bytes) > 500
    assert docx_bytes.startswith(b"PK\x03\x04")  # Standard Zip/DOCX header


@pytest.mark.asyncio
async def test_tailor_resume_api_lifecycle_and_tenancy(
    async_client: AsyncClient,
    db_session: AsyncSession,
):
    # 1. Register User A
    user_a_email = f"tailor_a_{uuid.uuid4().hex[:6]}@example.com"
    reg_a = await async_client.post(
        "/api/v1/auth/register",
        json={"email": user_a_email, "password": "Password123!", "full_name": "Taylor Swift"},
    )
    assert reg_a.status_code == 201
    token_a = reg_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}
    user_a_id = uuid.UUID(reg_a.json()["user"]["id"])

    # 2. Seed Resume for User A
    resume_a = Resume(
        user_id=user_a_id,
        file_name="taylor_resume.pdf",
        file_key="resumes/taylor_resume.pdf",
        file_format="pdf",
        file_size_bytes=1024,
        raw_text="Taylor Resume Text",
        is_master=True,
    )
    db_session.add(resume_a)
    await db_session.flush()

    sec_a = ResumeSection(
        resume_id=resume_a.id,
        section_type="EXPERIENCE",
        heading="Work Experience",
        raw_content="Backend Engineer",
        display_order=1,
    )
    db_session.add(sec_a)
    await db_session.flush()

    item_a = ResumeItem(
        section_id=sec_a.id,
        item_type="EXPERIENCE",
        title="Backend Engineer",
        organization="Fintech Labs",
        bullets=[
            "worked on Python microservices and database query optimization.",
            "built internal APIs used by frontend developers.",
        ],
    )
    db_session.add(item_a)
    await db_session.commit()

    # 3. Create JD for User A
    jd_resp = await async_client.post(
        "/api/v1/jobs/analyze",
        headers=headers_a,
        json={
            "job_title": "Senior Python Engineer",
            "company_name": "NextGen AI",
            "raw_text": (
                "Job Title: Senior Python Engineer\n"
                "Minimum Qualifications:\n"
                "- 5+ years of experience with Python.\n"
                "- Strong PostgreSQL query optimization experience.\n"
            ),
        },
    )
    assert jd_resp.status_code == 201
    jd_id = jd_resp.json()["id"]

    # 4. Request Resume Tailoring
    tailor_resp = await async_client.post(
        "/api/v1/optimizer/tailor",
        headers=headers_a,
        json={
            "resume_id": str(resume_a.id),
            "jd_id": jd_id,
        },
    )
    assert tailor_resp.status_code == 201
    tailored_data = tailor_resp.json()
    tailored_id = tailored_data["id"]
    assert tailored_data["diffs_count"] >= 2
    assert len(tailored_data["diffs"]) >= 2

    # Check NLI status on diffs
    diff_0 = tailored_data["diffs"][0]
    assert diff_0["nli_verification_status"] == "ENTAILMENT"
    assert diff_0["status"] == "PENDING"
    diff_id = diff_0["id"]

    # 5. List Tailored Resumes
    list_resp = await async_client.get("/api/v1/optimizer/tailored-resumes", headers=headers_a)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    # 6. Get Tailored Resume Detail
    detail_resp = await async_client.get(
        f"/api/v1/optimizer/tailored-resumes/{tailored_id}",
        headers=headers_a,
    )
    assert detail_resp.status_code == 200
    assert detail_resp.json()["id"] == tailored_id
    assert detail_resp.json()["tailored_content"]["candidate_name"] == "Taylor Swift"
    assert "Taylor Swift" in detail_resp.json()["tailored_content"]["full_name"]
    assert user_a_email in detail_resp.json()["tailored_content"]["contact_info"]

    # 7. Accept a diff
    accept_resp = await async_client.put(
        f"/api/v1/optimizer/diffs/{diff_id}",
        headers=headers_a,
        json={"status": "ACCEPTED"},
    )
    assert accept_resp.status_code == 200
    assert accept_resp.json()["status"] == "ACCEPTED"

    # Verify that the live snapshot updated to the accepted bullet
    refreshed_detail = await async_client.get(
        f"/api/v1/optimizer/tailored-resumes/{tailored_id}",
        headers=headers_a,
    )
    snapshot = refreshed_detail.json()["tailored_content"]
    exp_bullets = snapshot["sections"][0]["items"][0]["bullets"]
    assert exp_bullets[0] == diff_0["optimized_text"]

    # 8. Edit a diff
    custom_bullet = (
        "Architected mission-critical Python microservices with verified sub-10ms latency."
    )
    edit_resp = await async_client.put(
        f"/api/v1/optimizer/diffs/{diff_id}",
        headers=headers_a,
        json={"status": "EDITED", "edited_text": custom_bullet},
    )
    assert edit_resp.status_code == 200
    assert edit_resp.json()["status"] == "EDITED"
    assert edit_resp.json()["edited_text"] == custom_bullet

    # Verify snapshot updated to custom edited text
    refreshed_detail2 = await async_client.get(
        f"/api/v1/optimizer/tailored-resumes/{tailored_id}",
        headers=headers_a,
    )
    exp_bullets2 = refreshed_detail2.json()["tailored_content"]["sections"][0]["items"][0][
        "bullets"
    ]
    assert exp_bullets2[0] == custom_bullet

    # 9. Export PDF
    pdf_resp = await async_client.post(
        f"/api/v1/optimizer/tailored-resumes/{tailored_id}/export-pdf",
        headers=headers_a,
    )
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert len(pdf_resp.content) > 500
    assert pdf_resp.content.startswith(b"%PDF")

    # 10. Export DOCX
    docx_resp = await async_client.post(
        f"/api/v1/optimizer/tailored-resumes/{tailored_id}/export-docx",
        headers=headers_a,
    )
    assert docx_resp.status_code == 200
    assert "wordprocessingml" in docx_resp.headers["content-type"]
    assert len(docx_resp.content) > 500

    # 11. Multi-tenant boundary check with User B
    user_b_email = f"tailor_b_{uuid.uuid4().hex[:6]}@example.com"
    reg_b = await async_client.post(
        "/api/v1/auth/register",
        json={"email": user_b_email, "password": "Password123!", "full_name": "User Bravo"},
    )
    token_b = reg_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User B list should be empty
    b_list = await async_client.get("/api/v1/optimizer/tailored-resumes", headers=headers_b)
    assert len(b_list.json()) == 0

    # User B cannot access User A's tailored resume
    b_get = await async_client.get(
        f"/api/v1/optimizer/tailored-resumes/{tailored_id}",
        headers=headers_b,
    )
    assert b_get.status_code == 404

    # User B cannot edit User A's diff
    b_edit = await async_client.put(
        f"/api/v1/optimizer/diffs/{diff_id}",
        headers=headers_b,
        json={"status": "REJECTED"},
    )
    assert b_edit.status_code == 404

    # 12. User A deletes tailored resume
    del_resp = await async_client.delete(
        f"/api/v1/optimizer/tailored-resumes/{tailored_id}",
        headers=headers_a,
    )
    assert del_resp.status_code == 204

    # Subsequent GET returns 404
    after_del = await async_client.get(
        f"/api/v1/optimizer/tailored-resumes/{tailored_id}",
        headers=headers_a,
    )
    assert after_del.status_code == 404
