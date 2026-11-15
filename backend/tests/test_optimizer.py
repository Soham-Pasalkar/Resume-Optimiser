import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate import CandidateSkill
from app.models.jd import JDRequirement, JobDescription
from app.models.optimizer import TailoredBulletDiff, TailoredResume
from app.models.resume import Resume, ResumeItem, ResumeSection
from app.modules.optimizer.ats_scorer import ats_evaluator
from app.modules.optimizer.composer import resume_composer
from app.modules.optimizer.exporter import resume_exporter
from app.modules.optimizer.intelligence import content_intelligence
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

    # 1. Valid rephrasing (ENTAILMENT / VERIFIED)
    valid_opt = "Architected backend microservices and optimized database queries using Python and PostgreSQL."
    status, rationale = nli_guardrail.verify_bullet(orig, valid_opt, cand_skills)
    assert status in ["ENTAILMENT", "VERIFIED"]

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

    # 4. Fabricating temporal dates not in source (FLAGGED)
    hallucinated_temporal = "Architected Python backend microservices during 2024 for 3 years."
    status, rationale = nli_guardrail.verify_bullet(orig, hallucinated_temporal, cand_skills)
    assert status == "FLAGGED"
    assert "calendar dates/years" in rationale

    # 5. Seniority inflation (FLAGGED)
    seniority_inflated = "Served as Chief Architect and CTO scaling backend microservices using Python."
    status, rationale = nli_guardrail.verify_bullet(orig, seniority_inflated, cand_skills)
    assert status == "FLAGGED"
    assert "Seniority distortion" in rationale


@pytest.mark.asyncio
async def test_content_intelligence_and_requirement_mapping():
    user_id = uuid.uuid4()
    resume = Resume(
        user_id=user_id,
        file_name="resume.pdf",
        file_key="resumes/resume.pdf",
        file_format="pdf",
        file_size_bytes=2048,
        raw_text="Sample Resume Text",
    )
    sec_exp = ResumeSection(
        resume_id=resume.id,
        section_type="EXPERIENCE",
        heading="Work Experience",
        display_order=1,
    )
    item_exp = ResumeItem(
        section_id=sec_exp.id,
        title="Senior Backend Engineer",
        organization="CloudScale Corp",
        bullets=[
            "Architected distributed event-driven microservices using Python and Kafka.",
            "Designed relational schemas and optimized high-concurrency SQL queries in PostgreSQL.",
        ],
    )
    sec_exp.items = [item_exp]

    sec_skills = ResumeSection(
        resume_id=resume.id,
        section_type="SKILLS",
        heading="Technical Skills",
        raw_content="Python, PostgreSQL, Kafka, Docker, Linux",
        display_order=2,
    )
    sec_skills.items = []
    resume.sections = [sec_exp, sec_skills]

    jd = JobDescription(
        user_id=user_id,
        job_title="Lead Data Engineer",
        company_name="Apex Data",
        raw_text="Seeking a Lead Data Engineer.",
    )
    req1 = JDRequirement(
        jd_id=jd.id,
        requirement_text="5+ years building distributed pipelines with Kafka and Python.",
        is_mandatory=True,
        canonical_skill_name="Kafka",
        category="technical_skill",
    )
    req2 = JDRequirement(
        jd_id=jd.id,
        requirement_text="Deep expertise in Snowflake data warehousing.",
        is_mandatory=False,
        canonical_skill_name="Snowflake",
        category="technical_skill",
    )
    jd.requirements = [req1, req2]

    cand_skills = [
        CandidateSkill(
            user_id=user_id,
            skill_name="Kafka",
            normalized_name="kafka",
            category="Frameworks & Libraries",
            is_user_verified=True,
        )
    ]

    analysis = await content_intelligence.analyze_and_map(
        resume=resume,
        jd=jd,
        candidate_skills=cand_skills,
    )

    # 1. Requirement mappings
    mappings = analysis["requirement_mappings"]
    assert len(mappings) >= 1
    kafka_map = next(m for m in mappings if "kafka" in (m["canonical_skill_name"] or "").lower())
    assert kafka_map["is_mandatory"] is True
    assert kafka_map["verification_status"] == "CANDIDATE_VERIFIED"
    assert kafka_map["matching_method"] in ["RESUME_DIRECT_EVIDENCE", "ONTOLOGY_EXACT", "DENSE_OLLAMA_NEURAL", "DENSE_OLLAMA"]
    assert kafka_map["confidence_score"] >= 0.50

    # 2. Missing requirements (Snowflake is not in resume or profile)
    missing = analysis["missing_requirements"]
    assert any("Snowflake" in m["requirement_text"] for m in missing)
    snow_missing = next(m for m in missing if "Snowflake" in m["requirement_text"])
    assert "do not fabricate" in snow_missing["suggested_action"].lower()

    # 3. Content decisions
    decisions = analysis["content_decisions"]
    assert len(decisions) >= 2
    assert any(d["decision"] in ["PROPOSED_REWRITE", "INCLUDED"] for d in decisions)


def test_resume_composition_ir_and_provenance():
    user_id = uuid.uuid4()
    jd = JobDescription(user_id=user_id, job_title="Senior Platform Engineer", company_name="Starlight AI")
    req = JDRequirement(jd_id=jd.id, requirement_text="Kubernetes cluster management", canonical_skill_name="Kubernetes")
    jd.requirements = [req]

    tailored = TailoredResume(
        user_id=user_id,
        source_resume_id=uuid.uuid4(),
        target_jd_id=jd.id,
        version_title="Tailored for Starlight AI",
        tailored_content={
            "full_name": "Jordan Lee",
            "contact_info": "jordan@example.com | Seattle, WA",
            "sections": [
                {
                    "id": "sec_1",
                    "section_type": "EXPERIENCE",
                    "heading": "Work Experience",
                    "is_included": True,
                    "display_order": 1,
                    "items": [
                        {
                            "id": "item_1",
                            "title": "Platform Engineer",
                            "organization": "InfraCorp",
                            "bullets": [
                                "Administered production Kubernetes clusters across AWS and GCP.",
                            ],
                        }
                    ],
                }
            ],
        },
    )
    tailored.target_jd = jd

    diff = TailoredBulletDiff(
        tailored_resume_id=tailored.id,
        section_id="sec_1",
        item_id="item_1",
        bullet_index=0,
        original_text="Administered production Kubernetes clusters across AWS and GCP.",
        optimized_text="Architected and scaled production Kubernetes clusters across AWS and GCP.",
        rationale="Elevated technical action verb; highlighted alignment with target competency Kubernetes.",
        targeted_requirement_id=req.id,
        nli_verification_status="VERIFIED",
        status="ACCEPTED",
    )

    ir = resume_composer.build_composition_ir(tailored, [diff])

    assert ir["candidate_identity"]["full_name"] == "Jordan Lee"
    assert len(ir["sections"]) == 1
    assert ir["sections"][0]["items"][0]["bullets"][0]["text"] == diff.optimized_text
    assert ir["sections"][0]["items"][0]["bullets"][0]["source_status"] == "ACCEPTED_REWRITE"
    assert len(ir["provenance"]) == 1
    assert ir["provenance"][0]["diff_id"] == str(diff.id)
    assert ir["metadata"]["applied_diffs"] == 1


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
    assert result["nli_verification_status"] in ["ENTAILMENT", "VERIFIED"]


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
                "heading": "Technical Projects",
                "section_type": "PROJECTS",
                "items": [
                    {
                        "title": "Cloud Lakehouse Framework",
                        "organization": "Open Source",
                        "location": "Remote",
                        "start_date": "2022",
                        "end_date": "2023",
                        "bullets": [
                            "Built open-source Delta Lake ingestion utility for batch processing.",
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


def test_exporter_pre_validation():
    # Empty content raises ValueError
    with pytest.raises(ValueError, match="Cannot export empty resume content"):
        resume_exporter.generate_pdf({})

    # Missing name raises ValueError
    with pytest.raises(ValueError, match="missing candidate name"):
        resume_exporter.generate_pdf({"candidate_name": "", "sections": [{"heading": "Skills"}]})

    # Missing sections raises ValueError
    with pytest.raises(ValueError, match="at least one resume section is required"):
        resume_exporter.generate_pdf({"candidate_name": "John Doe", "sections": []})


def test_ats_evaluator_and_four_tier_taxonomy():
    jd = JobDescription(
        user_id=uuid.uuid4(),
        job_title="Senior Data Engineer",
        company_name="Citi",
        raw_text="Citi Senior Data Engineer",
    )
    req1 = JDRequirement(
        id=uuid.uuid4(),
        jd_id=jd.id,
        requirement_text="5+ years of building large-scale ETL pipelines with PySpark.",
        is_mandatory=True,
        canonical_skill_name="Spark",
        category="technical_skill",
    )
    req2 = JDRequirement(
        id=uuid.uuid4(),
        jd_id=jd.id,
        requirement_text="Deep expertise in Snowflake analytical warehousing.",
        is_mandatory=True,
        canonical_skill_name="Snowflake",
        category="technical_skill",
    )
    req3 = JDRequirement(
        id=uuid.uuid4(),
        jd_id=jd.id,
        requirement_text="Experience with SQL relational databases.",
        is_mandatory=False,
        canonical_skill_name="SQL",
        category="technical_skill",
    )
    jd.requirements = [req1, req2, req3]

    content = {
        "candidate_name": "Elena Rostova",
        "contact_info": "elena@example.com | San Francisco, CA | linkedin.com/in/elena | github.com/elena",
        "sections": [
            {
                "heading": "Professional Summary",
                "section_type": "SUMMARY",
                "raw_content": "Experienced Data Engineer specializing in distributed systems and cloud data architecture.",
            },
            {
                "heading": "Work Experience",
                "section_type": "EXPERIENCE",
                "items": [
                    {
                        "title": "Lead Data Engineer",
                        "organization": "Enterprise Data Corp",
                        "location": "San Francisco, CA",
                        "start_date": "2021",
                        "end_date": "Present",
                        "bullets": [
                            "Architected distributed PySpark ETL pipelines processing 50M daily events with Delta Lake.",
                            "Optimized SQL analytical queries reducing query execution duration by 45%.",
                            "Engineered automated data validation suites asserting schema integrity across data marts.",
                        ],
                    },
                    {
                        "title": "Data Engineer",
                        "organization": "Fintech Solutions",
                        "location": "New York, NY",
                        "start_date": "2019",
                        "end_date": "2021",
                        "bullets": [
                            "Implemented PostgreSQL indexing and table partitioning mitigating I/O contention.",
                            "Deployed containerized batch processors with automated error alerting.",
                        ],
                    },
                ],
            },
            {
                "heading": "Education",
                "section_type": "EDUCATION",
                "items": [
                    {
                        "title": "B.S. in Computer Science",
                        "organization": "University of California, Berkeley",
                        "location": "Berkeley, CA",
                        "start_date": "2015",
                        "end_date": "2019",
                        "bullets": [],
                        "description": "Graduated Magna Cum Laude. Coursework in Distributed Systems, Database Architecture, and Algorithms.",
                    }
                ],
            },
            {
                "heading": "Technical Projects",
                "section_type": "PROJECTS",
                "items": [
                    {
                        "title": "Cloud Lakehouse Framework",
                        "organization": "Open Source",
                        "location": "Remote",
                        "start_date": "2022",
                        "end_date": "2023",
                        "bullets": [
                            "Built open-source Delta Lake ingestion utility for batch processing.",
                        ],
                    }
                ],
            },
            {
                "heading": "Technical Skills",
                "section_type": "SKILLS",
                "raw_content": "PySpark, Python, SQL, PostgreSQL, Kafka, Docker, Kubernetes, Snowflake",
            },
            {
                "heading": "Certifications",
                "section_type": "CERTIFICATIONS",
                "raw_content": "Databricks Certified Spark Developer, Snowflake SnowPro Core",
            },
        ],
    }

    # Generate PDF bytes
    pdf_bytes = resume_exporter.generate_pdf(content)
    assert pdf_bytes.startswith(b"%PDF")

    # Generate DOCX bytes
    docx_bytes = resume_exporter.generate_docx(content)
    assert len(docx_bytes) > 500

    # 1. Evaluate Job Compatibility Score
    mock_mappings = [
        {
            "requirement_id": str(req1.id),
            "match_category": "DEMONSTRATED",
            "is_mandatory": True,
            "confidence_score": 0.90,
        },
        {
            "requirement_id": str(req2.id),
            "match_category": "PROFILE_LISTED",
            "is_mandatory": True,
            "confidence_score": 0.60,
        },
        {
            "requirement_id": str(req3.id),
            "match_category": "DEMONSTRATED",
            "is_mandatory": False,
            "confidence_score": 0.85,
        },
    ]

    comp_eval = ats_evaluator.evaluate_job_compatibility(
        tailored_content=content,
        jd=jd,
        requirement_mappings=mock_mappings,
    )

    assert 0 <= comp_eval["score"] <= 100
    assert comp_eval["tier_counts"]["demonstrated"] == 2
    assert comp_eval["tier_counts"]["profile_listed"] == 1
    assert len(comp_eval["strengths"]) > 0
    assert "CareerPilot Algorithmic Estimate" in comp_eval["disclaimer"]

    # 2. Evaluate ATS Readability Score with real PDF byte extraction
    read_eval = ats_evaluator.evaluate_ats_readability(
        tailored_content=content,
        document_bytes=pdf_bytes,
        file_format="pdf",
    )

    assert read_eval["score"] >= 85.0
    assert read_eval["extracted_character_count"] > 200
    assert read_eval["page_count"] >= 1
    assert read_eval["breakdown"]["text_extraction_validation"] == 20.0
    assert read_eval["breakdown"]["standard_headings"] == 20.0
    assert read_eval["breakdown"]["contact_completeness"] == 15.0
    assert any("byte-level text extraction" in f.lower() for f in read_eval["findings"])


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
    jd_data = jd_resp.json()
    jd_id = jd_data["id"]

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
    assert "requirement_mappings" in tailored_data["tailored_content"]

    diff_0 = tailored_data["diffs"][0]
    assert diff_0["nli_verification_status"] in ["ENTAILMENT", "VERIFIED"]
    assert diff_0["status"] == "PENDING"
    diff_id = diff_0["id"]

    # 5. List Tailored Resumes
    list_resp = await async_client.get("/api/v1/optimizer/tailored-resumes", headers=headers_a)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    # 6. Get Composition IR
    ir_resp = await async_client.get(
        f"/api/v1/optimizer/tailored-resumes/{tailored_id}/composition",
        headers=headers_a,
    )
    assert ir_resp.status_code == 200
    ir_data = ir_resp.json()
    assert "candidate_identity" in ir_data
    assert "provenance" in ir_data
    assert "export_sections" in ir_data

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
    work_sec = next(s for s in snapshot["sections"] if s.get("section_type") in ("EXPERIENCE", "WORK"))
    exp_bullets = work_sec["items"][0]["bullets"]
    assert exp_bullets[0] == diff_0["optimized_text"]

    # 8. Restore Diff to Original Text
    restore_resp = await async_client.post(
        f"/api/v1/optimizer/diffs/{diff_id}/restore",
        headers=headers_a,
    )
    assert restore_resp.status_code == 200
    assert restore_resp.json()["status"] == "REJECTED"

    # Verify snapshot restored to original text
    refreshed_detail_restored = await async_client.get(
        f"/api/v1/optimizer/tailored-resumes/{tailored_id}",
        headers=headers_a,
    )
    work_sec_restored = next(s for s in refreshed_detail_restored.json()["tailored_content"]["sections"] if s.get("section_type") in ("EXPERIENCE", "WORK"))
    exp_bullets_restored = work_sec_restored["items"][0]["bullets"]
    assert exp_bullets_restored[0] == diff_0["original_text"]

    # 9. Edit a diff with custom text
    custom_bullet = "Architected mission-critical Python microservices with verified sub-10ms latency."
    edit_resp = await async_client.put(
        f"/api/v1/optimizer/diffs/{diff_id}",
        headers=headers_a,
        json={"status": "EDITED", "edited_text": custom_bullet},
    )
    assert edit_resp.status_code == 200
    assert edit_resp.json()["status"] == "EDITED"

    # 10. Toggle Section Visibility
    sec_id_to_toggle = str(sec_a.id)
    toggle_resp = await async_client.put(
        f"/api/v1/optimizer/tailored-resumes/{tailored_id}/sections",
        headers=headers_a,
        json={"section_id": sec_id_to_toggle, "is_included": False},
    )
    assert toggle_resp.status_code == 200

    # 11. Re-enable section for export
    toggle_on_resp = await async_client.put(
        f"/api/v1/optimizer/tailored-resumes/{tailored_id}/sections",
        headers=headers_a,
        json={"section_id": sec_id_to_toggle, "is_included": True},
    )
    assert toggle_on_resp.status_code == 200

    # 12. Export PDF
    pdf_resp = await async_client.post(
        f"/api/v1/optimizer/tailored-resumes/{tailored_id}/export-pdf",
        headers=headers_a,
    )
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert len(pdf_resp.content) > 500
    assert pdf_resp.content.startswith(b"%PDF")

    # 13. Export DOCX
    docx_resp = await async_client.post(
        f"/api/v1/optimizer/tailored-resumes/{tailored_id}/export-docx",
        headers=headers_a,
    )
    assert docx_resp.status_code == 200
    assert "wordprocessingml" in docx_resp.headers["content-type"]
    assert len(docx_resp.content) > 500

    # 13b. Check ATS Analysis endpoint
    ats_resp = await async_client.get(
        f"/api/v1/optimizer/tailored-resumes/{tailored_id}/ats-analysis",
        headers=headers_a,
    )
    assert ats_resp.status_code == 200
    ats_data = ats_resp.json()
    assert "job_compatibility" in ats_data
    assert "ats_readability" in ats_data
    assert 0 <= ats_data["job_compatibility"]["score"] <= 100
    assert 0 <= ats_data["ats_readability"]["score"] <= 100
    assert ats_data["ats_readability"]["extracted_character_count"] > 100
    assert ats_data["ats_readability"]["page_count"] >= 1

    # 13c. Add Custom Evidence to a requirement
    # Pick first requirement from JD
    jd_req_id = jd_data["requirements"][0]["id"]
    custom_ev_resp = await async_client.post(
        f"/api/v1/optimizer/tailored-resumes/{tailored_id}/custom-evidence",
        headers=headers_a,
        json={
            "requirement_id": jd_req_id,
            "evidence_text": "Completed advanced enterprise production data pipeline deployment with Delta Lake and Spark.",
            "section_name": "Project Portfolio",
        },
    )
    assert custom_ev_resp.status_code == 200
    updated_tailored = custom_ev_resp.json()
    req_mappings = updated_tailored["tailored_content"]["requirement_mappings"]
    target_mapping = next(m for m in req_mappings if m["requirement_id"] == jd_req_id)
    assert target_mapping["match_category"] == "TRANSFERABLE"
    assert target_mapping["verification_status"] == "PENDING_REVIEW"
    assert target_mapping["requires_human_verification"] is True
    assert target_mapping["confidence_score"] <= 0.60

    # 14. Multi-tenant boundary check with User B
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

    # 15. User A deletes tailored resume
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


@pytest.mark.asyncio
async def test_adversarial_requirement_matching_and_verification():
    """Adversarial testing verifying zero-hallucination requirement matching:
    1. Python experience alone does NOT demonstrate PySpark.
    2. SQL usage alone does NOT demonstrate Snowflake.
    3. Technology in an unrelated personal project does NOT prove enterprise professional experience.
    4. Skill listed only in profile remains PROFILE_LISTED.
    5. Candidate-submitted statement remains unverified until approved.
    """
    user_id = uuid.uuid4()
    resume = Resume(
        user_id=user_id,
        file_name="elena_data_engineer.pdf",
        file_key="resumes/elena.pdf",
        file_format="pdf",
        file_size_bytes=4096,
        raw_text="Elena Rostova Resume",
    )
    # Work experience with pure Python and PostgreSQL SQL
    sec_exp = ResumeSection(
        resume_id=resume.id,
        section_type="EXPERIENCE",
        heading="Professional Work Experience",
        display_order=1,
    )
    item_exp = ResumeItem(
        section_id=sec_exp.id,
        title="Backend Software Engineer",
        organization="Fintech Tech Inc",
        bullets=[
            "Engineered high-throughput REST APIs and asynchronous worker tasks using Python and FastAPI.",
            "Wrote complex SQL analytical queries, table indexes, and views in PostgreSQL.",
        ],
    )
    sec_exp.items = [item_exp]

    # Personal project mentioning Docker
    sec_proj = ResumeSection(
        resume_id=resume.id,
        section_type="PROJECTS",
        heading="Personal Projects",
        display_order=2,
    )
    item_proj = ResumeItem(
        section_id=sec_proj.id,
        title="Home Lab Docker Automation",
        organization="Personal",
        bullets=[
            "Configured local multi-container Docker services for personal media streaming.",
        ],
    )
    sec_proj.items = [item_proj]

    # Skills section mentioning Airflow (no bullets)
    sec_skills = ResumeSection(
        resume_id=resume.id,
        section_type="SKILLS",
        heading="Technical Skills",
        raw_content="Python, SQL, PostgreSQL, Docker, Apache Airflow",
        display_order=3,
    )
    sec_skills.items = []
    resume.sections = [sec_exp, sec_proj, sec_skills]

    # Target JD requirements
    jd = JobDescription(
        user_id=user_id,
        job_title="Principal Data Engineer",
        company_name="Citigroup",
        raw_text="Citigroup Principal Data Engineer JD",
    )
    req_pyspark = JDRequirement(
        id=uuid.uuid4(),
        jd_id=jd.id,
        requirement_text="5+ years of production experience architecting distributed data pipelines using PySpark and Spark dataframes.",
        canonical_skill_name="PySpark",
        category="technical_skill",
        is_mandatory=True,
    )
    req_snowflake = JDRequirement(
        id=uuid.uuid4(),
        jd_id=jd.id,
        requirement_text="Deep production expertise in Snowflake cloud data warehousing.",
        canonical_skill_name="Snowflake",
        category="technical_skill",
        is_mandatory=True,
    )
    req_docker = JDRequirement(
        id=uuid.uuid4(),
        jd_id=jd.id,
        requirement_text="Enterprise experience deploying microservices on Kubernetes and Docker.",
        canonical_skill_name="Docker",
        category="technical_skill",
        is_mandatory=False,
    )
    req_airflow = JDRequirement(
        id=uuid.uuid4(),
        jd_id=jd.id,
        requirement_text="Authoring DAG workflows using Apache Airflow.",
        canonical_skill_name="Airflow",
        category="technical_skill",
        is_mandatory=False,
    )
    jd.requirements = [req_pyspark, req_snowflake, req_docker, req_airflow]

    # Candidate profile skills (Airflow is profile-listed only, not in experience bullets)
    cand_skills = [
        CandidateSkill(
            user_id=user_id,
            skill_name="Apache Airflow",
            normalized_name="airflow",
            category="Data Engineering",
            is_user_verified=False,
        )
    ]

    analysis = await content_intelligence.analyze_and_map(
        resume=resume,
        jd=jd,
        candidate_skills=cand_skills,
    )

    all_mappings = {m["requirement_id"]: m for m in analysis["all_requirement_mappings"]}

    # Adversarial Assertion 1: Python experience must NOT demonstrate PySpark
    pyspark_map = all_mappings[str(req_pyspark.id)]
    assert pyspark_map["match_category"] != "DEMONSTRATED", "FAIL: Python was falsely promoted to DEMONSTRATED PySpark!"
    assert pyspark_map["match_category"] in ("TRANSFERABLE", "MISSING")
    assert pyspark_map["confidence_score"] <= 0.60
    assert pyspark_map["requires_human_verification"] is True

    # Adversarial Assertion 2: SQL usage must NOT demonstrate Snowflake
    snowflake_map = all_mappings[str(req_snowflake.id)]
    assert snowflake_map["match_category"] != "DEMONSTRATED", "FAIL: SQL was falsely promoted to DEMONSTRATED Snowflake!"
    assert snowflake_map["match_category"] == "MISSING"
    assert snowflake_map["confidence_score"] == 0.0
    assert any(m["requirement_id"] == str(req_snowflake.id) for m in analysis["missing_requirements"])

    # Adversarial Assertion 3: Technology in an unrelated project must NOT prove professional employment experience
    docker_map = all_mappings[str(req_docker.id)]
    assert docker_map["match_category"] != "DEMONSTRATED", "FAIL: Project Docker was falsely promoted to DEMONSTRATED enterprise employment!"
    assert docker_map["match_category"] == "TRANSFERABLE"
    assert "project context" in docker_map["explanation"].lower()
    assert docker_map["requires_human_verification"] is True

    # Adversarial Assertion 4: Skill listed only in a profile must remain PROFILE_LISTED
    airflow_map = all_mappings[str(req_airflow.id)]
    assert airflow_map["match_category"] == "PROFILE_LISTED"
    assert "lacks supporting achievement bullet" in airflow_map["explanation"].lower()
    assert airflow_map["requires_human_verification"] is True
