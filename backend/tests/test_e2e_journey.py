import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume import Resume, ResumeItem, ResumeSection


@pytest.mark.asyncio
async def test_full_careerpilot_e2e_journey(
    async_client: AsyncClient,
    db_session: AsyncSession,
):
    """Unified End-to-End (E2E) test exercising the entire CareerPilot pipeline across all 10 functional modules."""

    # =========================================================================
    # STEP 1: MODULE 1 — Authentication & User Registration
    # =========================================================================
    user_email = f"e2e_architect_{uuid.uuid4().hex[:6]}@example.com"
    reg_resp = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": user_email,
            "password": "ProductionPassword123!",
            "full_name": "Devin Principal Architect",
        },
    )
    assert reg_resp.status_code == 201
    auth_data = reg_resp.json()
    token = auth_data["access_token"]
    user_id = uuid.UUID(auth_data["user"]["id"])
    headers = {"Authorization": f"Bearer {token}"}

    # Verify user profile endpoint
    me_resp = await async_client.get("/api/v1/users/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == user_email

    # =========================================================================
    # STEP 2: MODULE 2 — Resume Ingestion & Section Segmentation
    # =========================================================================
    resume = Resume(
        user_id=user_id,
        file_name="devin_resume.pdf",
        file_key="resumes/devin_resume.pdf",
        file_format="pdf",
        file_size_bytes=2048,
        raw_text="Experienced Cloud Infrastructure and Backend Engineer proficient in Python, Go, Docker, and PostgreSQL.",
        is_master=True,
    )
    db_session.add(resume)
    await db_session.flush()

    sec_exp = ResumeSection(
        resume_id=resume.id,
        section_type="EXPERIENCE",
        heading="Professional Experience",
        raw_content="Lead Backend Engineer",
        display_order=1,
    )
    db_session.add(sec_exp)
    await db_session.flush()

    item_exp = ResumeItem(
        section_id=sec_exp.id,
        item_type="EXPERIENCE",
        title="Lead Platform Engineer",
        organization="CloudScale Global",
        bullets=[
            "Architected high-throughput microservices using Python and Go, handling 50k requests per second.",
            "Optimized PostgreSQL connection pooling and indexing, reducing p99 database latency by 45%.",
            "Deployed containerized services using Docker and managed CI/CD deployment automation.",
        ],
    )
    db_session.add(item_exp)

    sec_skills = ResumeSection(
        resume_id=resume.id,
        section_type="SKILLS",
        heading="Technical Skills",
        raw_content="Python, Go, PostgreSQL, Docker, Redis, Git, Linux",
        display_order=2,
    )
    db_session.add(sec_skills)
    await db_session.commit()

    # List resumes via API
    resumes_list_resp = await async_client.get("/api/v1/resumes", headers=headers)
    assert resumes_list_resp.status_code == 200
    assert len(resumes_list_resp.json()) == 1
    assert resumes_list_resp.json()[0]["id"] == str(resume.id)

    # =========================================================================
    # STEP 3: MODULE 4 — Candidate Intelligence & Profile Building
    # =========================================================================
    profile_resp = await async_client.post(
        "/api/v1/candidate/build-profile",
        headers=headers,
        json={"resume_id": str(resume.id)},
    )
    assert profile_resp.status_code == 200
    candidate_skills = profile_resp.json()
    assert len(candidate_skills) > 0
    skill_names = [s["normalized_name"] for s in candidate_skills]
    assert "Python" in skill_names
    assert "Docker" in skill_names

    # =========================================================================
    # STEP 4: MODULE 3 — JD Intelligence Engine (Requirement Decomposition)
    # =========================================================================
    jd_payload = {
        "job_title": "Principal Staff Infrastructure Engineer",
        "company_name": "Datadog",
        "raw_text": (
            "Job Title: Principal Staff Infrastructure Engineer\n"
            "Company: Datadog\n"
            "Requirements:\n"
            "- 7+ years of experience with Python or Go backend systems.\n"
            "- Deep expertise in Docker containerization and Kubernetes cluster management.\n"
            "- Production experience with Kafka distributed streaming architectures.\n"
            "- Relational database tuning with PostgreSQL.\n"
        ),
    }
    jd_resp = await async_client.post(
        "/api/v1/jobs/analyze",
        headers=headers,
        json=jd_payload,
    )
    assert jd_resp.status_code == 201
    jd_data = jd_resp.json()
    jd_id = jd_data["id"]
    assert jd_data["job_title"] == "Principal Staff Infrastructure Engineer"
    assert len(jd_data["requirements"]) >= 3

    # =========================================================================
    # STEP 5: MODULE 5 & 6 — Hybrid Matching & 4-Tier Skill Gap Analysis
    # =========================================================================
    match_resp = await async_client.post(
        "/api/v1/matches/evaluate",
        headers=headers,
        json={"resume_id": str(resume.id), "jd_id": jd_id},
    )
    assert match_resp.status_code == 201
    match_data = match_resp.json()
    match_id = match_data["id"]
    assert match_data["overall_score"] > 0
    assert len(match_data["gap_items"]) > 0

    # Find an unverified or missing gap
    gap_items = match_data["gap_items"]
    unresolved_gap = next((g for g in gap_items if g["status"] != "DEMONSTRATED"), gap_items[0])
    gap_id = unresolved_gap["id"]

    # STEP 6: Verify a gap with user explanation
    verify_resp = await async_client.post(
        f"/api/v1/matches/{match_id}/gaps/verify",
        headers=headers,
        json={
            "gap_item_id": gap_id,
            "has_experience": True,
            "verification_evidence": "Extensively deployed stateful Kafka and Kubernetes topologies in private cloud environments.",
        },
    )
    assert verify_resp.status_code == 200

    # =========================================================================
    # STEP 7: MODULE 7 — AI Resume Optimizer & Factual Preservation Guardrails
    # =========================================================================
    tailor_resp = await async_client.post(
        "/api/v1/optimizer/tailor",
        headers=headers,
        json={"resume_id": str(resume.id), "jd_id": jd_id},
    )
    assert tailor_resp.status_code == 201
    tailored = tailor_resp.json()
    tailored_id = tailored["id"]
    assert tailored["id"] is not None
    assert tailored["tailored_content"]["candidate_name"] == "Devin Principal Architect"
    assert len(tailored["diffs"]) > 0

    # Accept first diff and verify NLI verification status
    diff_0 = tailored["diffs"][0]
    diff_id = diff_0["id"]
    assert diff_0["nli_verification_status"] in ("ENTAILMENT", "FLAGGED", "NEUTRAL")

    diff_update_resp = await async_client.put(
        f"/api/v1/optimizer/diffs/{diff_id}",
        headers=headers,
        json={"status": "ACCEPTED"},
    )
    assert diff_update_resp.status_code == 200
    assert diff_update_resp.json()["status"] == "ACCEPTED"

    # Export ATS Single-Column PDF
    pdf_resp = await async_client.post(
        f"/api/v1/optimizer/tailored-resumes/{tailored_id}/export-pdf",
        headers=headers,
    )
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert pdf_resp.content.startswith(b"%PDF")

    # Export ATS DOCX
    docx_resp = await async_client.post(
        f"/api/v1/optimizer/tailored-resumes/{tailored_id}/export-docx",
        headers=headers,
    )
    assert docx_resp.status_code == 200
    assert "wordprocessingml" in docx_resp.headers["content-type"]

    # =========================================================================
    # STEP 8: MODULE 8 — Personalized Learning Roadmaps
    # =========================================================================
    roadmap_resp = await async_client.post(
        "/api/v1/learning/generate",
        headers=headers,
        json={"match_evaluation_id": match_id},
    )
    assert roadmap_resp.status_code == 201
    roadmap = roadmap_resp.json()
    assert roadmap["id"] is not None
    assert roadmap["total_milestones"] > 0
    assert roadmap["estimated_total_hours"] > 0

    # Complete a learning milestone
    milestone_id = roadmap["milestones"][0]["id"]
    toggle_resp = await async_client.put(
        f"/api/v1/learning/milestones/{milestone_id}",
        headers=headers,
        json={"is_completed": True},
    )
    assert toggle_resp.status_code == 200
    assert toggle_resp.json()["is_completed"] is True

    # =========================================================================
    # STEP 9: MODULE 9 — Interview Intelligence & Rubric Practice Terminal
    # =========================================================================
    interview_resp = await async_client.post(
        "/api/v1/interview/generate",
        headers=headers,
        json={"match_evaluation_id": match_id},
    )
    assert interview_resp.status_code == 201
    interview_prep = interview_resp.json()
    assert interview_prep["questions_count"] == 10
    assert len(interview_prep["questions"]) == 10

    # Practice and evaluate response on question 0
    question_0 = interview_prep["questions"][0]
    eval_resp = await async_client.post(
        f"/api/v1/interview/questions/{question_0['id']}/evaluate",
        headers=headers,
        json={
            "practice_response": (
                "When scaling our Python microservices cluster under high concurrency spikes, "
                "we implemented asynchronous event decoupling with Redis streams and automated Horizontal Pod Autoscaling. "
                "This reduced p99 latency by 38% and maintained 99.99% availability during peak traffic."
            )
        },
    )
    assert eval_resp.status_code == 200
    eval_feedback = eval_resp.json()["ai_feedback"]
    assert eval_feedback is not None
    assert eval_feedback["score"] > 60.0
    assert len(eval_feedback["strengths"]) > 0

    # =========================================================================
    # STEP 10: MODULE 10 — Job Application Pipeline & Opportunity Comparison
    # =========================================================================
    app_1_resp = await async_client.post(
        "/api/v1/applications",
        headers=headers,
        json={
            "company_name": "Datadog",
            "job_title": "Principal Staff Infrastructure Engineer",
            "job_description_id": jd_id,
            "tailored_resume_id": tailored_id,
            "match_evaluation_id": match_id,
            "stage": "WISHLIST",
            "priority": "HIGH",
            "salary_range": "$240k - $290k",
            "location": "New York, NY (Remote)",
        },
    )
    assert app_1_resp.status_code == 201
    app_1 = app_1_resp.json()
    app_1_id = app_1["id"]

    # Advance stage to APPLIED
    stage_resp = await async_client.patch(
        f"/api/v1/applications/{app_1_id}/stage",
        headers=headers,
        json={"stage": "APPLIED", "note": "Applied with tailored ATS PDF resume."},
    )
    assert stage_resp.status_code == 200
    assert stage_resp.json()["stage"] == "APPLIED"

    # Create a 2nd application to compare
    app_2_resp = await async_client.post(
        "/api/v1/applications",
        headers=headers,
        json={
            "company_name": "Cloudflare",
            "job_title": "Senior Systems Engineer",
            "stage": "SCREENING",
            "priority": "HIGH",
            "salary_range": "$220k - $260k",
            "location": "Austin, TX",
        },
    )
    assert app_2_resp.status_code == 201
    app_2_id = app_2_resp.json()["id"]

    # Compare opportunities side-by-side
    comp_resp = await async_client.post(
        "/api/v1/applications/compare",
        headers=headers,
        json={"application_ids": [app_1_id, app_2_id]},
    )
    assert comp_resp.status_code == 200
    assert len(comp_resp.json()["opportunities"]) == 2

    # =========================================================================
    # STEP 11: MODULE 1 — GDPR Account Purge & Cascading Cleanup
    # =========================================================================
    del_account_resp = await async_client.delete(
        "/api/v1/users/me",
        headers=headers,
    )
    assert del_account_resp.status_code == 200
    assert del_account_resp.json()["status"] == "deleted"

    # Confirm user is completely gone
    login_attempt = await async_client.post(
        "/api/v1/auth/login",
        json={"email": user_email, "password": "ProductionPassword123!"},
    )
    assert login_attempt.status_code == 401
