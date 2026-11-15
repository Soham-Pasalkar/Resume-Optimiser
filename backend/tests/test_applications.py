import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume import Resume, ResumeItem, ResumeSection


@pytest.mark.asyncio
async def test_application_lifecycle_and_activity_logging(
    async_client: AsyncClient,
    db_session: AsyncSession,
):
    # 1. Register User A
    user_email = f"app_user_{uuid.uuid4().hex[:6]}@example.com"
    reg = await async_client.post(
        "/api/v1/auth/register",
        json={"email": user_email, "password": "Password123!", "full_name": "Applicant Alice"},
    )
    assert reg.status_code == 201
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Application in WISHLIST
    create_payload = {
        "company_name": "Stripe",
        "job_title": "Staff Infrastructure Engineer",
        "location": "San Francisco, CA (Remote)",
        "stage": "WISHLIST",
        "priority": "HIGH",
        "salary_range": "$220,000 - $260,000",
        "job_url": "https://stripe.com/jobs/123",
        "notes": "Referred by former colleague.",
    }
    create_resp = await async_client.post(
        "/api/v1/applications",
        headers=headers,
        json=create_payload,
    )
    assert create_resp.status_code == 201
    app_data = create_resp.json()
    app_id = app_data["id"]
    assert app_data["company_name"] == "Stripe"
    assert app_data["stage"] == "WISHLIST"
    assert app_data["priority"] == "HIGH"
    assert len(app_data["activities"]) == 1
    assert app_data["activities"][0]["activity_type"] == "CREATED"

    # 3. Transition Stage to APPLIED
    stage_resp = await async_client.patch(
        f"/api/v1/applications/{app_id}/stage",
        headers=headers,
        json={"stage": "APPLIED", "note": "Submitted application with tailored ATS resume."},
    )
    assert stage_resp.status_code == 200
    assert stage_resp.json()["stage"] == "APPLIED"

    # 4. Transition Stage to INTERVIEWING
    interview_resp = await async_client.patch(
        f"/api/v1/applications/{app_id}/stage",
        headers=headers,
        json={"stage": "INTERVIEWING", "note": "Passed phone screen. Technical round scheduled."},
    )
    assert interview_resp.status_code == 200
    assert interview_resp.json()["stage"] == "INTERVIEWING"

    # 5. Fetch Full Application Detail and verify activity log
    detail_resp = await async_client.get(f"/api/v1/applications/{app_id}", headers=headers)
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["stage"] == "INTERVIEWING"
    # Should have 3 activities: CREATED, STAGE_CHANGE (APPLIED), STAGE_CHANGE (INTERVIEWING)
    assert len(detail["activities"]) == 3
    act_types = [a["activity_type"] for a in detail["activities"]]
    assert "CREATED" in act_types
    assert "STAGE_CHANGE" in act_types

    # 6. Update Application Details
    update_resp = await async_client.put(
        f"/api/v1/applications/{app_id}",
        headers=headers,
        json={"salary_range": "$235,000 - $275,000", "notes": "Offer negotiation stage prep."},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["salary_range"] == "$235,000 - $275,000"

    # 7. List Applications with stage filter
    list_applied = await async_client.get(
        "/api/v1/applications?stage=INTERVIEWING", headers=headers
    )
    assert list_applied.status_code == 200
    assert len(list_applied.json()) == 1

    list_wishlist = await async_client.get("/api/v1/applications?stage=WISHLIST", headers=headers)
    assert list_wishlist.status_code == 200
    assert len(list_wishlist.json()) == 0

    # 8. Delete Application
    del_resp = await async_client.delete(f"/api/v1/applications/{app_id}", headers=headers)
    assert del_resp.status_code == 204

    get_deleted = await async_client.get(f"/api/v1/applications/{app_id}", headers=headers)
    assert get_deleted.status_code == 404


@pytest.mark.asyncio
async def test_opportunity_comparison_and_multi_tenancy(
    async_client: AsyncClient,
    db_session: AsyncSession,
):
    # 1. Register User A
    user_a_email = f"user_comp_a_{uuid.uuid4().hex[:6]}@example.com"
    reg_a = await async_client.post(
        "/api/v1/auth/register",
        json={"email": user_a_email, "password": "Password123!", "full_name": "Candidate Alice"},
    )
    assert reg_a.status_code == 201
    token_a = reg_a.json()["access_token"]
    user_a_id = uuid.UUID(reg_a.json()["user"]["id"])
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. Register User B
    user_b_email = f"user_comp_b_{uuid.uuid4().hex[:6]}@example.com"
    reg_b = await async_client.post(
        "/api/v1/auth/register",
        json={"email": user_b_email, "password": "Password123!", "full_name": "Candidate Bob"},
    )
    assert reg_b.status_code == 201
    token_b = reg_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 3. Create Resume for User A
    resume = Resume(
        user_id=user_a_id,
        file_name="comp_resume.pdf",
        file_key="resumes/comp_resume.pdf",
        file_format="pdf",
        file_size_bytes=1024,
        raw_text="Experienced Cloud and Backend Engineer with Go, Python, and Docker.",
        is_master=True,
    )
    db_session.add(resume)
    await db_session.flush()

    sec = ResumeSection(
        resume_id=resume.id,
        section_type="EXPERIENCE",
        heading="Experience",
        raw_content="Backend Engineer",
        display_order=1,
    )
    db_session.add(sec)
    await db_session.flush()

    item = ResumeItem(
        section_id=sec.id,
        item_type="EXPERIENCE",
        title="Backend Engineer",
        organization="CloudScale",
        bullets=["Architected backend services in Go and Python."],
    )
    db_session.add(item)
    await db_session.commit()

    # 4. Create Opportunity 1 (Google) with JD & Match Evaluation
    jd_1_resp = await async_client.post(
        "/api/v1/jobs/analyze",
        headers=headers_a,
        json={
            "job_title": "Site Reliability Engineer",
            "company_name": "Google",
            "raw_text": "Requirements:\n- Strong Go and Python programming.\n- Kubernetes cluster scaling.",
        },
    )
    assert jd_1_resp.status_code == 201
    jd_1_id = jd_1_resp.json()["id"]

    match_1_resp = await async_client.post(
        "/api/v1/matches/evaluate",
        headers=headers_a,
        json={"resume_id": str(resume.id), "jd_id": jd_1_id},
    )
    assert match_1_resp.status_code == 201
    match_1_id = match_1_resp.json()["id"]

    app_1_resp = await async_client.post(
        "/api/v1/applications",
        headers=headers_a,
        json={
            "company_name": "Google",
            "job_title": "Site Reliability Engineer",
            "job_description_id": jd_1_id,
            "match_evaluation_id": match_1_id,
            "stage": "APPLIED",
            "priority": "HIGH",
            "salary_range": "$190k - $240k",
        },
    )
    assert app_1_resp.status_code == 201
    app_1_id = app_1_resp.json()["id"]

    # 5. Create Opportunity 2 (Netflix) with JD & Match Evaluation
    jd_2_resp = await async_client.post(
        "/api/v1/jobs/analyze",
        headers=headers_a,
        json={
            "job_title": "Senior Distributed Systems Engineer",
            "company_name": "Netflix",
            "raw_text": "Requirements:\n- Python microservices.\n- Kafka event pipelines.",
        },
    )
    assert jd_2_resp.status_code == 201
    jd_2_id = jd_2_resp.json()["id"]

    match_2_resp = await async_client.post(
        "/api/v1/matches/evaluate",
        headers=headers_a,
        json={"resume_id": str(resume.id), "jd_id": jd_2_id},
    )
    assert match_2_resp.status_code == 201
    match_2_id = match_2_resp.json()["id"]

    app_2_resp = await async_client.post(
        "/api/v1/applications",
        headers=headers_a,
        json={
            "company_name": "Netflix",
            "job_title": "Senior Distributed Systems Engineer",
            "job_description_id": jd_2_id,
            "match_evaluation_id": match_2_id,
            "stage": "SCREENING",
            "priority": "HIGH",
            "salary_range": "$250k - $320k",
        },
    )
    assert app_2_resp.status_code == 201
    app_2_id = app_2_resp.json()["id"]

    # 6. Compare Opportunities Side-by-Side
    comp_resp = await async_client.post(
        "/api/v1/applications/compare",
        headers=headers_a,
        json={"application_ids": [app_1_id, app_2_id]},
    )
    assert comp_resp.status_code == 200
    comp_data = comp_resp.json()
    assert len(comp_data["opportunities"]) == 2
    assert "comparison_summary" in comp_data
    assert comp_data["opportunities"][0]["overall_match_score"] is not None
    assert comp_data["opportunities"][1]["overall_match_score"] is not None

    # 7. Verify Multi-Tenant Isolation
    # User B cannot see User A's applications
    b_list = await async_client.get("/api/v1/applications", headers=headers_b)
    assert b_list.status_code == 200
    assert len(b_list.json()) == 0

    # User B cannot access User A's application
    b_get = await async_client.get(f"/api/v1/applications/{app_1_id}", headers=headers_b)
    assert b_get.status_code == 404

    # User B cannot compare User A's applications
    b_comp = await async_client.post(
        "/api/v1/applications/compare",
        headers=headers_b,
        json={"application_ids": [app_1_id, app_2_id]},
    )
    assert b_comp.status_code == 400
