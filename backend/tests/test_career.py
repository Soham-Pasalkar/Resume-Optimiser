import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.career import InterviewQuestion
from app.models.jd import JDRequirement, JobDescription
from app.models.matching import MatchEvaluation, SkillGapItem
from app.modules.interview.evaluator import answer_evaluator
from app.modules.interview.prompt_generator import interview_prompt_generator
from app.modules.learning.generator import roadmap_generator


@pytest.mark.asyncio
async def test_roadmap_generator_curated_fallback():
    req_docker = JDRequirement(
        id=uuid.uuid4(),
        jd_id=uuid.uuid4(),
        requirement_text="Containerization with Docker",
        category="technical_skill",
        canonical_skill_name="Docker",
    )
    gap_docker = SkillGapItem(
        match_evaluation_id=uuid.uuid4(),
        requirement_id=req_docker.id,
        status="NOT_DEMONSTRATED",
        gap_severity="CRITICAL",
        suggested_action="Study Docker fundamentals and build multi-stage Dockerfiles.",
    )
    gap_docker.requirement = req_docker

    req_k8s = JDRequirement(
        id=uuid.uuid4(),
        jd_id=uuid.uuid4(),
        requirement_text="Container orchestration with Kubernetes",
        category="technical_skill",
        canonical_skill_name="Kubernetes",
    )
    gap_k8s = SkillGapItem(
        match_evaluation_id=uuid.uuid4(),
        requirement_id=req_k8s.id,
        status="PARTIAL",
        gap_severity="MODERATE",
        suggested_action="Deploy stateful workloads and Helm charts on Minikube.",
    )
    gap_k8s.requirement = req_k8s

    gaps = [gap_docker, gap_k8s]

    roadmap_data = await roadmap_generator.generate_roadmap(
        target_role="Senior DevOps Engineer",
        unresolved_gaps=gaps,
    )

    assert "estimated_total_hours" in roadmap_data
    assert roadmap_data["estimated_total_hours"] > 0
    milestones = roadmap_data.get("milestones", [])
    assert len(milestones) == 2

    # Check skill names and curated resources
    skills = [m["skill_name"] for m in milestones]
    assert "Docker" in skills
    assert "Kubernetes" in skills

    for m in milestones:
        assert len(m["curated_resources"]) > 0
        assert m["practical_project_brief"] is not None
        assert len(m["practical_project_brief"]) > 20


@pytest.mark.asyncio
async def test_interview_prompt_generator_questions():
    jd = JobDescription(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        job_title="Lead DevOps Engineer",
        company_name="CloudScale",
        raw_text="Looking for a Lead DevOps Engineer...",
    )
    req_kafka = JDRequirement(
        id=uuid.uuid4(),
        jd_id=jd.id,
        requirement_text="Kafka distributed event streaming",
        category="technical_skill",
        canonical_skill_name="Kafka",
    )
    match_eval = MatchEvaluation(
        id=uuid.uuid4(),
        user_id=jd.user_id,
        resume_id=uuid.uuid4(),
        jd_id=jd.id,
        overall_score=72.5,
        lexical_score=70.0,
        semantic_score=75.0,
        skill_match_score=68.0,
        experience_score=78.0,
        domain_score=70.0,
    )
    match_eval.job_description = jd
    gap_kafka = SkillGapItem(
        match_evaluation_id=match_eval.id,
        requirement_id=req_kafka.id,
        status="NOT_DEMONSTRATED",
        gap_severity="CRITICAL",
        suggested_action="Demonstrate distributed log fundamentals.",
    )
    gap_kafka.requirement = req_kafka
    match_eval.gap_items = [gap_kafka]

    questions = await interview_prompt_generator.generate_questions(match_eval)
    assert len(questions) == 10

    types = [q["question_type"] for q in questions]
    assert types.count("TECHNICAL") == 4
    assert types.count("BEHAVIORAL_STAR") == 3
    assert types.count("GAP_DEFENSE") == 3

    # Verify STAR guidelines for behavioral questions provide authentic framing guidance rather than fabricated stories
    star_qs = [q for q in questions if q["question_type"] == "BEHAVIORAL_STAR"]
    for q in star_qs:
        assert "situation" in q["star_guidelines"]
        assert "action" in q["star_guidelines"]
        assert "result" in q["star_guidelines"]
        assert "authentic" in q["star_guidelines"]["situation"].lower()
        assert "gRPC" not in q["star_guidelines"]["situation"]

    # Verify gap defense question addresses Kafka
    gap_qs = [q for q in questions if q["question_type"] == "GAP_DEFENSE"]
    assert any("Kafka" in (q["target_skill_or_gap"] or "") for q in gap_qs)


@pytest.mark.asyncio
async def test_answer_evaluator_rubrics():
    strong_q = InterviewQuestion(
        prep_id=uuid.uuid4(),
        question_type="BEHAVIORAL_STAR",
        question_text="Tell me about a time you resolved a major production outage.",
        evaluation_criteria="Clear Situation, Task, decisive Action, and quantified Result with post-mortem.",
        star_guidelines={
            "situation": "Identify the critical production failure.",
            "task": "Your direct responsibility during triage.",
            "action": "Remediation and RCA steps taken.",
            "result": "Quantifiable MTTR and prevention mechanisms.",
        },
    )

    strong_response = (
        "In my previous role as Senior Engineer, our primary PostgreSQL cluster experienced lock saturation "
        "causing a 99.9% failure rate across API endpoints. As the incident commander, I immediately established "
        "the triage bridge, identified the rogue analytics batch query locking table rows, and terminated the PID. "
        "I then implemented read-replica isolation and query timeout guards, reducing MTTR to 14 minutes and "
        "preventing $120,000 in potential transaction loss during peak trading hours."
    )

    eval_result = await answer_evaluator.evaluate_response(strong_q, strong_response)
    assert eval_result["score"] >= 80.0
    assert len(eval_result["strengths"]) > 0
    assert len(eval_result["improvements"]) >= 0

    # Weak/shallow response
    weak_response = (
        "We had an outage and I fixed it by rebooting the server. It worked fine after that."
    )
    weak_eval = await answer_evaluator.evaluate_response(strong_q, weak_response)
    assert weak_eval["score"] <= 60.0
    assert len(weak_eval["improvements"]) > 0


@pytest.mark.asyncio
async def test_career_api_lifecycle(async_client: AsyncClient, db_session: AsyncSession):
    from app.models.resume import Resume, ResumeItem, ResumeSection

    # 1. Register User A
    user_a_email = f"career_user_{uuid.uuid4().hex[:6]}@example.com"
    reg_a = await async_client.post(
        "/api/v1/auth/register",
        json={"email": user_a_email, "password": "Password123!", "full_name": "Career User A"},
    )
    assert reg_a.status_code == 201
    token_a = reg_a.json()["access_token"]
    user_a_id = uuid.UUID(reg_a.json()["user"]["id"])
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. Register User B (for multi-tenant isolation verification)
    user_b_email = f"career_user_b_{uuid.uuid4().hex[:6]}@example.com"
    reg_b = await async_client.post(
        "/api/v1/auth/register",
        json={"email": user_b_email, "password": "Password123!", "full_name": "Career User B"},
    )
    assert reg_b.status_code == 201
    token_b = reg_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 3. Create Resume and JD for User A
    resume_a = Resume(
        user_id=user_a_id,
        file_name="career_resume.pdf",
        file_key="resumes/career_resume.pdf",
        file_format="pdf",
        file_size_bytes=1024,
        raw_text="Career Resume Text",
        is_master=True,
    )
    db_session.add(resume_a)
    await db_session.flush()

    sec_a = ResumeSection(
        resume_id=resume_a.id,
        section_type="EXPERIENCE",
        heading="Experience",
        raw_content="Backend Engineer with Python",
        display_order=1,
    )
    db_session.add(sec_a)
    await db_session.flush()

    item_a = ResumeItem(
        section_id=sec_a.id,
        item_type="EXPERIENCE",
        title="Backend Engineer",
        organization="CloudScale",
        bullets=["Built Python microservices and configured CI/CD."],
    )
    db_session.add(item_a)
    await db_session.commit()

    jd_resp = await async_client.post(
        "/api/v1/jobs/analyze",
        headers=headers_a,
        json={
            "job_title": "Lead Platform Engineer",
            "company_name": "CloudScale Inc",
            "raw_text": (
                "Job Title: Lead Platform Engineer\n"
                "Requirements:\n"
                "- 5+ years of experience with Python.\n"
                "- Strong proficiency with Docker and Kubernetes.\n"
                "- Experience with distributed systems and Kafka.\n"
            ),
        },
    )
    assert jd_resp.status_code == 201
    jd_id = jd_resp.json()["id"]

    # 4. Trigger Matching Evaluation
    match_resp = await async_client.post(
        "/api/v1/matches/evaluate",
        headers=headers_a,
        json={"resume_id": str(resume_a.id), "jd_id": jd_id},
    )
    assert match_resp.status_code == 201
    match_id = match_resp.json()["id"]

    # 5. Generate Learning Roadmap
    roadmap_resp = await async_client.post(
        "/api/v1/learning/generate",
        headers=headers_a,
        json={"match_evaluation_id": match_id},
    )
    assert roadmap_resp.status_code == 201
    roadmap = roadmap_resp.json()
    roadmap_id = roadmap["id"]
    assert roadmap["target_role_title"] == "Lead Platform Engineer"
    assert roadmap["total_milestones"] > 0
    assert roadmap["status"] == "ACTIVE"

    # 6. List Roadmaps
    list_roadmaps = await async_client.get("/api/v1/learning", headers=headers_a)
    assert list_roadmaps.status_code == 200
    assert len(list_roadmaps.json()) == 1
    assert list_roadmaps.json()[0]["id"] == roadmap_id

    # Multi-tenant check: User B cannot see User A's roadmaps
    list_b = await async_client.get("/api/v1/learning", headers=headers_b)
    assert list_b.status_code == 200
    assert len(list_b.json()) == 0

    # 7. Get Roadmap Detail
    detail_roadmap = await async_client.get(f"/api/v1/learning/{roadmap_id}", headers=headers_a)
    assert detail_roadmap.status_code == 200
    milestone_0 = detail_roadmap.json()["milestones"][0]
    milestone_id = milestone_0["id"]
    assert milestone_0["is_completed"] is False
    # Verify 10 structured milestone elements
    assert milestone_0["why_it_matters"] is not None
    assert len(milestone_0["prerequisites"]) > 0
    assert len(milestone_0["learning_objectives"]) > 0
    assert len(milestone_0["curated_resources"]) > 0
    assert len(milestone_0["practical_exercises"]) > 0
    assert milestone_0["practical_project_brief"] is not None
    assert len(milestone_0["expected_deliverables"]) > 0
    assert len(milestone_0["verification_criteria"]) > 0
    assert milestone_0["estimated_hours"] > 0

    # 8. Submit Milestone Project Evidence (verifies deliverable and syncs to Candidate Profile)
    ev_resp = await async_client.post(
        f"/api/v1/learning/milestones/{milestone_id}/evidence",
        headers=headers_a,
        json={
            "evidence_text": "Built containerized automated pipeline with full test coverage and Great Expectations data assertions.",
            "github_url": "https://github.com/candidate/spark-etl-pipeline",
            "test_results": "15 unit tests passing, zero errors.",
        },
    )
    assert ev_resp.status_code == 200
    ev_data = ev_resp.json()
    assert ev_data["is_completed"] is True
    assert ev_data["evidence_verified"] is True
    assert ev_data["completed_evidence"]["github_url"] == "https://github.com/candidate/spark-etl-pipeline"

    # Verify skill was synchronized to Candidate Profile
    prof_resp = await async_client.get("/api/v1/candidate/profile", headers=headers_a)
    assert prof_resp.status_code == 200
    prof_skills = prof_resp.json()
    assert any(s["skill_name"].lower() == milestone_0["skill_name"].lower() and s["is_user_verified"] for s in prof_skills)

    # 9. Generate Interview Prep
    prep_resp = await async_client.post(
        "/api/v1/interview/generate",
        headers=headers_a,
        json={"match_evaluation_id": match_id},
    )
    assert prep_resp.status_code == 201
    prep = prep_resp.json()
    prep_id = prep["id"]
    assert prep["target_role_title"] == "Lead Platform Engineer"
    assert prep["questions_count"] == 10
    assert len(prep["questions"]) == 10

    # 10. List Interview Preps
    list_preps = await async_client.get("/api/v1/interview", headers=headers_a)
    assert list_preps.status_code == 200
    assert len(list_preps.json()) == 1

    # Multi-tenant check: User B cannot access User A's interview prep
    b_get = await async_client.get(f"/api/v1/interview/{prep_id}", headers=headers_b)
    assert b_get.status_code == 404

    # 11. Practice and Evaluate an Interview Answer
    question_0 = prep["questions"][0]
    q_id = question_0["id"]

    practice_answer = (
        "In our microservices architecture, we implemented containerization with multi-stage Docker builds "
        "to reduce image footprint by 60%. We configured health checks and graceful termination hooks to eliminate "
        "downtime during rolling updates."
    )

    eval_api_resp = await async_client.post(
        f"/api/v1/interview/questions/{q_id}/evaluate",
        headers=headers_a,
        json={"practice_response": practice_answer},
    )
    assert eval_api_resp.status_code == 200
    evaluated_q = eval_api_resp.json()
    assert evaluated_q["practice_response"] == practice_answer
    assert evaluated_q["ai_feedback"] is not None
    assert "score" in evaluated_q["ai_feedback"]
    assert "strengths" in evaluated_q["ai_feedback"]
    assert "critique" in evaluated_q["ai_feedback"]

    # 12. Delete Roadmap
    del_roadmap = await async_client.delete(f"/api/v1/learning/{roadmap_id}", headers=headers_a)
    assert del_roadmap.status_code == 204

    # 13. Delete Interview Prep
    del_prep = await async_client.delete(f"/api/v1/interview/{prep_id}", headers=headers_a)
    assert del_prep.status_code == 204
