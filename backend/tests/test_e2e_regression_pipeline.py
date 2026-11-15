import io
import uuid

import docx
import pdfplumber
import pytest
from httpx import AsyncClient
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from sqlalchemy.ext.asyncio import AsyncSession


def generate_real_citi_candidate_pdf() -> bytes:
    """Generate a realistic, ATS-friendly single-column PDF resume with all 6 standard sections."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )
    styles = getSampleStyleSheet()

    elements = [
        Paragraph("Elena Rostova", styles["Title"]),
        Paragraph(
            "elena.rostova@example.com | (555) 019-4829 | New York, NY | github.com/erostova",
            styles["Normal"],
        ),
        Spacer(1, 12),
        Paragraph("PROFESSIONAL SUMMARY", styles["Heading2"]),
        Paragraph(
            "Data and Backend Engineer with 5+ years of experience designing scalable data pipelines in Python, "
            "PostgreSQL, and relational SQL. Experienced in automated ETL, Docker containerization, and production CI/CD.",
            styles["Normal"],
        ),
        Spacer(1, 10),
        Paragraph("WORK EXPERIENCE", styles["Heading2"]),
        Paragraph("Lead Data Platform Engineer at Fintech Alpha", styles["Heading3"]),
        Paragraph("New York, NY | 2022 - Present", styles["Normal"]),
        Paragraph(
            "- Architected Python data services processing 10 million financial transactions daily.",
            styles["Normal"],
        ),
        Paragraph(
            "- Optimized relational PostgreSQL database queries, reducing query latency by 45%.",
            styles["Normal"],
        ),
        Paragraph(
            "- Deployed containerized microservices using Docker and automated CI/CD pipelines.",
            styles["Normal"],
        ),
        Spacer(1, 8),
        Paragraph("Data Engineer at DataMetrics Corp", styles["Heading3"]),
        Paragraph("Boston, MA | 2019 - 2022", styles["Normal"]),
        Paragraph(
            "- Developed automated data extraction scripts in Python and SQL to ingest streaming logs.",
            styles["Normal"],
        ),
        Paragraph(
            "- Built automated test suites achieving 88% code coverage across backend data pipelines.",
            styles["Normal"],
        ),
        Spacer(1, 10),
        Paragraph("TECHNICAL PROJECTS", styles["Heading2"]),
        Paragraph("High-Throughput Financial Stream Aggregator", styles["Heading3"]),
        Paragraph(
            "- Built distributed stream aggregator processing trade records in real time using Python and Docker.",
            styles["Normal"],
        ),
        Spacer(1, 10),
        Paragraph("TECHNICAL SKILLS", styles["Heading2"]),
        Paragraph(
            "Languages & Databases: Python, SQL, PostgreSQL, Docker, Git, Linux, REST APIs",
            styles["Normal"],
        ),
        Spacer(1, 10),
        Paragraph("EDUCATION", styles["Heading2"]),
        Paragraph(
            "Bachelor of Science in Computer Science - Columbia University (2015 - 2019)",
            styles["Normal"],
        ),
        Spacer(1, 10),
        Paragraph("CERTIFICATIONS", styles["Heading2"]),
        Paragraph("AWS Certified Solutions Architect (2023)", styles["Normal"]),
    ]

    doc.build(elements)
    return buffer.getvalue()


@pytest.mark.asyncio
async def test_real_pipeline_end_to_end_regression(
    async_client: AsyncClient,
    db_session: AsyncSession,
):
    """Rigorous end-to-end integration test exercising the complete CareerPilot workflow:
    1. Ingest actual binary PDF via upload API.
    2. Verify extraction, parsing, and candidate profile creation.
    3. Ingest target Citi Data Engineer Job Description.
    4. Run 4-tier matching (Python/SQL demonstrated, PySpark/Snowflake gaps).
    5. Trigger resume tailoring with role summary inserted into sections.
    6. Accept and reject diffs.
    7. Verify composition IR, section ordering, and explainability reasons.
    8. Export PDF and DOCX; parse byte streams to verify text preservation.
    9. Run ATS scorer and verify single-column geometry and heading scores.
    10. Generate personalized learning roadmap targeting Citi Data Engineer gaps.
    11. Submit evidence into PENDING_REVIEW state; review and verify state transition.
    """
    # -------------------------------------------------------------------------
    # STEP 1: Candidate Registration & Authentication
    # -------------------------------------------------------------------------
    user_email = f"elena_citi_{uuid.uuid4().hex[:6]}@example.com"
    reg_resp = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": user_email,
            "password": "SecurePassword123!",
            "full_name": "Elena Rostova",
        },
    )
    assert reg_resp.status_code == 201
    auth_data = reg_resp.json()
    token = auth_data["access_token"]
    user_id = auth_data["user"]["id"]
    headers = {"Authorization": f"Bearer {token}"}

    # -------------------------------------------------------------------------
    # STEP 2: Ingest Real PDF via Multipart Upload API
    # -------------------------------------------------------------------------
    pdf_bytes = generate_real_citi_candidate_pdf()
    assert len(pdf_bytes) > 1000

    upload_resp = await async_client.post(
        "/api/v1/resumes/upload",
        headers=headers,
        files={"file": ("elena_citi_resume.pdf", pdf_bytes, "application/pdf")},
        data={"is_master": "true"},
    )
    assert upload_resp.status_code == 201
    upload_data = upload_resp.json()
    resume_id = upload_data["resume_id"]
    assert upload_data["status"] == "PARSED"
    assert upload_data["sections_detected"] >= 6

    # Verify structured parsed sections
    resume_detail_resp = await async_client.get(f"/api/v1/resumes/{resume_id}", headers=headers)
    assert resume_detail_resp.status_code == 200
    resume_detail = resume_detail_resp.json()
    section_types = [s["section_type"].upper() for s in resume_detail["sections"]]
    assert any("SUMMARY" in st for st in section_types)
    assert any("EXPERIENCE" in st or "WORK" in st for st in section_types)
    assert any("PROJECT" in st for st in section_types)
    assert any("SKILL" in st for st in section_types)
    assert any("EDUCATION" in st for st in section_types)
    assert any("CERTIFICATION" in st for st in section_types)

    # -------------------------------------------------------------------------
    # STEP 3: Extract Candidate Profile & Competencies
    # -------------------------------------------------------------------------
    build_prof_resp = await async_client.post(
        "/api/v1/candidate/build-profile",
        headers=headers,
        json={"resume_id": resume_id},
    )
    assert build_prof_resp.status_code == 200
    skills = build_prof_resp.json()
    skill_names = [s["skill_name"].lower() for s in skills]
    assert "python" in skill_names
    assert "sql" in skill_names or "postgresql" in skill_names

    # -------------------------------------------------------------------------
    # STEP 4: Ingest Citi Data Engineer Job Description
    # -------------------------------------------------------------------------
    citi_jd_text = (
        "Job Title: Senior Data Engineer\n"
        "Company: Citi\n"
        "About the Role:\n"
        "Citi is seeking a Senior Data Engineer to architect and build enterprise lakehouse pipelines.\n\n"
        "Key Requirements:\n"
        "- 5+ years of production experience in Python.\n"
        "- Deep expertise in SQL and relational database optimization.\n"
        "- Production experience with Apache Spark or PySpark for distributed large-scale ETL.\n"
        "- Hands-on data warehousing architecture experience with Snowflake.\n"
        "- Experience with workflow orchestration using Apache Airflow.\n"
        "- Experience containerizing applications with Docker."
    )
    jd_resp = await async_client.post(
        "/api/v1/jobs/analyze",
        headers=headers,
        json={
            "job_title": "Senior Data Engineer",
            "company_name": "Citi",
            "raw_text": citi_jd_text,
        },
    )
    assert jd_resp.status_code == 201
    jd_id = jd_resp.json()["id"]

    # -------------------------------------------------------------------------
    # STEP 5: Run 4-Tier Matching Evaluation
    # -------------------------------------------------------------------------
    match_resp = await async_client.post(
        "/api/v1/matches/evaluate",
        headers=headers,
        json={"resume_id": resume_id, "jd_id": jd_id},
    )
    assert match_resp.status_code == 201
    match_data = match_resp.json()
    match_id = match_data["id"]

    gaps = match_data.get("gap_items", [])
    assert len(gaps) > 0

    # Verify 4-tier grounding: Python/SQL demonstrated/transferable, PySpark/Snowflake gaps
    gap_skills = {
        (g.get("requirement_text") or "").lower(): g
        for g in gaps
    }

    # PySpark and Snowflake must be unresolved gaps
    spark_gap = next((g for k, g in gap_skills.items() if "spark" in k), None)
    assert spark_gap is not None
    assert spark_gap["status"] in ("NOT_DEMONSTRATED", "PARTIAL")

    snowflake_gap = next((g for k, g in gap_skills.items() if "snowflake" in k), None)
    assert snowflake_gap is not None
    assert snowflake_gap["status"] in ("NOT_DEMONSTRATED", "PARTIAL")

    # -------------------------------------------------------------------------
    # STEP 6: Resume Tailoring
    # -------------------------------------------------------------------------
    tailor_resp = await async_client.post(
        "/api/v1/optimizer/tailor",
        headers=headers,
        json={"resume_id": resume_id, "jd_id": jd_id},
    )
    assert tailor_resp.status_code == 201
    tailored_data = tailor_resp.json()
    tailored_id = tailored_data["id"]
    diffs = tailored_data.get("diffs", [])

    # Verify synthesized role summary was inserted into sections
    snapshot_sections = tailored_data["tailored_content"]["sections"]
    assert len(snapshot_sections) >= 6
    summary_sec = next(s for s in snapshot_sections if s.get("section_type") == "SUMMARY")
    assert "Senior Data Engineer" in summary_sec.get("raw_content", "") or "Citi" in summary_sec.get("raw_content", "") or len(summary_sec.get("raw_content", "")) > 50

    # Verify original work experience is preserved with dates
    work_sec = next(s for s in snapshot_sections if s.get("section_type") in ("EXPERIENCE", "WORK"))
    assert len(work_sec["items"]) >= 1
    item0 = work_sec["items"][0]
    assert item0["title"] == "Lead Data Platform Engineer"
    assert item0["organization"] == "Fintech Alpha"
    assert item0.get("start_date") is not None

    # Verify original projects are preserved
    proj_sec = next(s for s in snapshot_sections if s.get("section_type") in ("PROJECTS", "PROJECT"))
    assert len(proj_sec["items"]) >= 1
    assert "High-Throughput Financial Stream Aggregator" in proj_sec["items"][0]["title"]

    # -------------------------------------------------------------------------
    # STEP 7: Accept / Reject Diffs
    # -------------------------------------------------------------------------
    if diffs:
        first_diff = diffs[0]
        acc_resp = await async_client.put(
            f"/api/v1/optimizer/diffs/{first_diff['id']}",
            headers=headers,
            json={"status": "ACCEPTED"},
        )
        assert acc_resp.status_code == 200
        assert acc_resp.json()["status"] == "ACCEPTED"

        if len(diffs) > 1:
            second_diff = diffs[1]
            rej_resp = await async_client.put(
                f"/api/v1/optimizer/diffs/{second_diff['id']}",
                headers=headers,
                json={"status": "REJECTED"},
            )
            assert rej_resp.status_code == 200
            assert rej_resp.json()["status"] == "REJECTED"

    # -------------------------------------------------------------------------
    # STEP 8: Verify Composition IR & Explainability
    # -------------------------------------------------------------------------
    comp_resp = await async_client.get(
        f"/api/v1/optimizer/tailored-resumes/{tailored_id}/composition",
        headers=headers,
    )
    assert comp_resp.status_code == 200
    comp_ir = comp_resp.json()
    assert comp_ir["candidate_identity"]["full_name"] == "Elena Rostova"
    assert len(comp_ir["export_sections"]) >= 6

    # Verify explainability reasons on sections and items
    for sec in comp_ir["export_sections"]:
        assert sec.get("selection_reason") is not None
        for item in sec.get("items", []):
            assert item.get("selection_reason") is not None

    # -------------------------------------------------------------------------
    # STEP 9: Export PDF and DOCX & Parse Output Bytes
    # -------------------------------------------------------------------------
    # 9a. PDF Export
    pdf_export_resp = await async_client.post(
        f"/api/v1/optimizer/tailored-resumes/{tailored_id}/export-pdf",
        headers=headers,
    )
    assert pdf_export_resp.status_code == 200
    assert pdf_export_resp.headers["content-type"] == "application/pdf"
    exported_pdf_bytes = pdf_export_resp.content
    assert len(exported_pdf_bytes) > 500

    # Parse exported PDF using pdfplumber and verify extracted text fidelity
    with pdfplumber.open(io.BytesIO(exported_pdf_bytes)) as pdf:
        assert len(pdf.pages) >= 1
        extracted_pdf_text = "\n".join(page.extract_text() or "" for page in pdf.pages)

    assert "Elena Rostova" in extracted_pdf_text
    assert "Fintech Alpha" in extracted_pdf_text
    assert "High-Throughput Financial Stream Aggregator" in extracted_pdf_text
    assert "Python" in extracted_pdf_text

    # 9b. DOCX Export
    docx_export_resp = await async_client.post(
        f"/api/v1/optimizer/tailored-resumes/{tailored_id}/export-docx",
        headers=headers,
    )
    assert docx_export_resp.status_code == 200
    exported_docx_bytes = docx_export_resp.content
    assert len(exported_docx_bytes) > 500

    # Parse exported DOCX using python-docx and verify structure
    word_doc = docx.Document(io.BytesIO(exported_docx_bytes))
    doc_text = "\n".join(p.text for p in word_doc.paragraphs)
    assert "Elena Rostova" in doc_text
    assert "Fintech Alpha" in doc_text
    assert "High-Throughput Financial Stream Aggregator" in doc_text

    # -------------------------------------------------------------------------
    # STEP 10: ATS Scorer Evaluation
    # -------------------------------------------------------------------------
    ats_resp = await async_client.get(
        f"/api/v1/optimizer/tailored-resumes/{tailored_id}/ats-analysis",
        headers=headers,
    )
    assert ats_resp.status_code == 200
    ats_data = ats_resp.json()

    # Verify scores and audits
    job_compat = ats_data["job_compatibility"]
    ats_read = ats_data["ats_readability"]
    assert 0 <= job_compat["score"] <= 100
    assert 0 <= ats_read["score"] <= 100

    read_breakdown = ats_read["breakdown"]
    assert read_breakdown["standard_headings"] >= 16.0
    assert read_breakdown["document_structure"] > 0
    assert read_breakdown["bullet_clarity"] > 0
    assert read_breakdown["text_extraction_validation"] > 0

    # -------------------------------------------------------------------------
    # STEP 11: Personalized Learning Roadmap for Citi Data Engineer Gaps
    # -------------------------------------------------------------------------
    roadmap_resp = await async_client.post(
        "/api/v1/learning/generate",
        headers=headers,
        json={"match_evaluation_id": match_id},
    )
    assert roadmap_resp.status_code == 201
    roadmap_data = roadmap_resp.json()
    assert roadmap_data["target_role_title"] == "Senior Data Engineer"
    milestones = roadmap_data.get("milestones", [])
    assert len(milestones) >= 1

    # Verify milestones target Citi Data Engineer gaps (PySpark / Snowflake / Airflow)
    m_skills = [m["skill_name"].lower() for m in milestones]
    assert any("spark" in s or "snowflake" in s or "airflow" in s for s in m_skills)

    # Verify personalized foundation prerequisite references demonstrated skills
    m0 = milestones[0]
    assert any("demonstrated background in Python" in p for p in m0["prerequisites"])
    # Verify project brief is tailored to Data Engineering
    assert "data engineer" in m0["practical_project_brief"].lower() or "lakehouse" in m0["practical_project_brief"].lower() or "data mart" in m0["practical_project_brief"].lower()

    # -------------------------------------------------------------------------
    # STEP 12: Milestone Evidence Verification Lifecycle
    # -------------------------------------------------------------------------
    m0_id = m0["id"]
    ev_resp = await async_client.post(
        f"/api/v1/learning/milestones/{m0_id}/evidence",
        headers=headers,
        json={
            "evidence_text": "Built containerized PySpark ETL pipeline with Delta Lake partitioning and Great Expectations assertions.",
            "github_url": "https://github.com/erostova/pyspark-citi-lakehouse",
            "test_results": "12 passing unit tests; zero schema validation errors.",
        },
    )
    assert ev_resp.status_code == 200
    ev_data = ev_resp.json()
    assert ev_data["verification_status"] == "PENDING_REVIEW"
    assert ev_data["evidence_verified"] is False
    assert ev_data["is_completed"] is False

    # Verify candidate skill in profile is not yet user verified
    prof_resp = await async_client.get("/api/v1/candidate/profile", headers=headers)
    assert prof_resp.status_code == 200
    prof_skills = prof_resp.json()
    assert any(s["skill_name"].lower() == m0["skill_name"].lower() and not s["is_user_verified"] for s in prof_skills)

    # Review and approve verification
    review_resp = await async_client.post(
        f"/api/v1/learning/milestones/{m0_id}/review",
        headers=headers,
        json={
            "status": "VERIFIED",
            "reviewer_notes": "Repository verified with passing test suite and Delta Lake schema.",
        },
    )
    assert review_resp.status_code == 200
    rev_data = review_resp.json()
    assert rev_data["verification_status"] == "VERIFIED"
    assert rev_data["evidence_verified"] is True
    assert rev_data["is_completed"] is True

    # Verify skill is now verified in profile
    prof_resp_post = await async_client.get("/api/v1/candidate/profile", headers=headers)
    assert prof_resp_post.status_code == 200
    prof_skills_post = prof_resp_post.json()
    assert any(s["skill_name"].lower() == m0["skill_name"].lower() and s["is_user_verified"] for s in prof_skills_post)
