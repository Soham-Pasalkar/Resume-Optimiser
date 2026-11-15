import io

import pytest
from docx import Document
from httpx import AsyncClient
from pypdf import PdfWriter

from app.modules.ingestion.extractor import DocumentExtractor
from app.modules.ingestion.segmenter import SectionSegmenter

SAMPLE_RESUME_TEXT = """
Marcus Vance
Email: marcus.vance@example.com | Phone: (555) 019-2834 | Seattle, WA
GitHub: github.com/marcusvance | LinkedIn: linkedin.com/in/marcusvance

PROFESSIONAL SUMMARY
Senior Backend Engineer with 5+ years of experience designing scalable distributed systems in Go, Python, and PostgreSQL. Experienced in asynchronous event pipelines, Docker, and Kubernetes orchestration.

WORK EXPERIENCE
Senior Software Engineer at Acme Corp
Seattle, WA | 2022 - Present
• Architected high-throughput Go microservices processing 15,000 requests/sec with p99 latency under 25ms.
• Designed distributed Redis caching layer reducing database query load by 42%.
• Migrated legacy monolithic architecture to containerized microservices managed via Kubernetes.

Software Engineer at CloudScale Inc
San Francisco, CA | 2019 - 2022
• Developed Python FastAPI backend endpoints for real-time telemetry analytics platform.
• Automated CI/CD deployment pipelines using GitHub Actions and Docker.

TECHNICAL SKILLS
Languages: Go, Python, TypeScript, SQL
Databases & Caching: PostgreSQL, Redis, DynamoDB
Cloud & DevOps: Docker, Kubernetes, AWS (ECS, S3, RDS), GitHub Actions, CI/CD

EDUCATION
Bachelor of Science in Computer Science - University of Washington
Seattle, WA | Graduated 2019

PROJECTS
CareerPilot Platform
• Built open-source candidate-job matching engine with hybrid BM25 and vector embeddings.
"""


def create_mock_docx_bytes() -> bytes:
    """Helper to generate an in-memory valid DOCX resume file."""
    doc = Document()
    doc.add_heading("Marcus Vance", 0)
    doc.add_paragraph("marcus.vance@example.com | Seattle, WA")
    doc.add_heading("Professional Summary", level=1)
    doc.add_paragraph("Senior Backend Engineer with experience in Go and PostgreSQL.")
    doc.add_heading("Work Experience", level=1)
    doc.add_paragraph("Senior Software Engineer at Acme Corp")
    doc.add_paragraph("Architected Go microservices handling 15,000 req/sec.", style="List Bullet")
    doc.add_paragraph("Optimized PostgreSQL queries reducing latency by 35%.", style="List Bullet")
    doc.add_heading("Technical Skills", level=1)
    doc.add_paragraph("Go, Python, PostgreSQL, Docker, Kubernetes")

    file_stream = io.BytesIO()
    doc.save(file_stream)
    return file_stream.getvalue()


def create_mock_pdf_bytes() -> bytes:
    """Helper to generate an in-memory valid PDF resume file using pypdf."""
    writer = PdfWriter()
    # Add blank page
    writer.add_blank_page(width=612, height=792)
    stream = io.BytesIO()
    writer.write(stream)
    return stream.getvalue()


def test_segmenter_extracts_sections():
    """Verify SectionSegmenter correctly identifies sections and bullet items."""
    sections = SectionSegmenter.segment_text(SAMPLE_RESUME_TEXT)
    assert len(sections) >= 5

    types = [s["section_type"] for s in sections]
    assert "personal_info" in types
    assert "summary" in types
    assert "experience" in types
    assert "skills" in types
    assert "education" in types

    # Check experience section items
    exp_sec = next(s for s in sections if s["section_type"] == "experience")
    assert len(exp_sec["items"]) >= 1
    assert "Go microservices" in exp_sec["items"][0]["bullets"][0]


def test_extractor_docx():
    """Verify DocumentExtractor parses paragraphs and bullets from DOCX."""
    docx_bytes = create_mock_docx_bytes()
    text = DocumentExtractor.extract_from_docx(docx_bytes)
    assert "Marcus Vance" in text
    assert "Professional Summary" in text
    assert "Go microservices" in text


@pytest.mark.asyncio
async def test_upload_resume_docx(async_client: AsyncClient):
    """Test uploading a valid DOCX resume via POST /api/v1/resumes/upload."""
    # 1. Register user
    reg = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "docx.user@example.com",
            "password": "Password123!",
            "full_name": "Docx Tester",
        },
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    docx_bytes = create_mock_docx_bytes()
    files = {
        "file": (
            "resume.docx",
            docx_bytes,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    }
    data = {"is_master": "true"}

    response = await async_client.post(
        "/api/v1/resumes/upload", headers=headers, files=files, data=data
    )
    assert response.status_code == 201
    resp_data = response.json()
    assert resp_data["file_name"] == "resume.docx"
    assert resp_data["file_format"] == "docx"
    assert resp_data["is_master"] is True
    assert resp_data["sections_detected"] >= 3


@pytest.mark.asyncio
async def test_list_and_get_resume_detail(async_client: AsyncClient):
    """Test listing resumes and retrieving full structured section detail."""
    reg = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "detail.user@example.com",
            "password": "Password123!",
            "full_name": "Detail Tester",
        },
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Upload
    docx_bytes = create_mock_docx_bytes()
    files = {
        "file": (
            "detail_resume.docx",
            docx_bytes,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    }
    up_res = await async_client.post("/api/v1/resumes/upload", headers=headers, files=files)
    resume_id = up_res.json()["resume_id"]

    # List resumes
    list_res = await async_client.get("/api/v1/resumes", headers=headers)
    assert list_res.status_code == 200
    resumes = list_res.json()
    assert len(resumes) >= 1
    assert any(r["id"] == resume_id for r in resumes)

    # Get detail
    detail_res = await async_client.get(f"/api/v1/resumes/{resume_id}", headers=headers)
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["id"] == resume_id
    assert len(detail["sections"]) >= 3


@pytest.mark.asyncio
async def test_update_resume_sections(async_client: AsyncClient):
    """Test updating section content via PUT /api/v1/resumes/{id}/sections."""
    reg = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "edit.user@example.com",
            "password": "Password123!",
            "full_name": "Edit Tester",
        },
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Upload
    docx_bytes = create_mock_docx_bytes()
    files = {
        "file": (
            "edit_resume.docx",
            docx_bytes,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    }
    up_res = await async_client.post("/api/v1/resumes/upload", headers=headers, files=files)
    resume_id = up_res.json()["resume_id"]

    # Get section to update
    detail_res = await async_client.get(f"/api/v1/resumes/{resume_id}", headers=headers)
    section = detail_res.json()["sections"][0]
    section_id = section["id"]

    # Update section
    update_payload = {
        "sections": [
            {
                "id": section_id,
                "heading": "Custom Corrected Heading",
                "raw_content": "Manually corrected contact and summary details.",
            }
        ]
    }
    update_res = await async_client.put(
        f"/api/v1/resumes/{resume_id}/sections", headers=headers, json=update_payload
    )
    assert update_res.status_code == 200
    updated_sections = update_res.json()["sections"]
    target_sec = next(s for s in updated_sections if s["id"] == section_id)
    assert target_sec["heading"] == "Custom Corrected Heading"
    assert "Manually corrected" in target_sec["raw_content"]


@pytest.mark.asyncio
async def test_resume_tenant_isolation(async_client: AsyncClient):
    """Verify User A cannot access or delete User B's resume."""
    # User A
    reg_a = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "tenant.a@example.com", "password": "Password123!", "full_name": "Tenant A"},
    )
    token_a = reg_a.json()["access_token"]

    # User B
    reg_b = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "tenant.b@example.com", "password": "Password123!", "full_name": "Tenant B"},
    )
    token_b = reg_b.json()["access_token"]

    # User A uploads a resume
    docx_bytes = create_mock_docx_bytes()
    files = {
        "file": (
            "tenant_a_resume.docx",
            docx_bytes,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    }
    up_res = await async_client.post(
        "/api/v1/resumes/upload", headers={"Authorization": f"Bearer {token_a}"}, files=files
    )
    resume_a_id = up_res.json()["resume_id"]

    # User B attempts to access User A's resume -> 404
    probe_res = await async_client.get(
        f"/api/v1/resumes/{resume_a_id}", headers={"Authorization": f"Bearer {token_b}"}
    )
    assert probe_res.status_code == 404

    # User B attempts to delete User A's resume -> 404
    del_probe = await async_client.delete(
        f"/api/v1/resumes/{resume_a_id}", headers={"Authorization": f"Bearer {token_b}"}
    )
    assert del_probe.status_code == 404


@pytest.mark.asyncio
async def test_delete_resume_success(async_client: AsyncClient):
    """Test deleting resume purges it from database."""
    reg = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "del.user@example.com",
            "password": "Password123!",
            "full_name": "Del Tester",
        },
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    docx_bytes = create_mock_docx_bytes()
    files = {
        "file": (
            "to_delete.docx",
            docx_bytes,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    }
    up_res = await async_client.post("/api/v1/resumes/upload", headers=headers, files=files)
    resume_id = up_res.json()["resume_id"]

    # Delete
    del_res = await async_client.delete(f"/api/v1/resumes/{resume_id}", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "deleted"

    # Subsequent GET -> 404
    check_res = await async_client.get(f"/api/v1/resumes/{resume_id}", headers=headers)
    assert check_res.status_code == 404


@pytest.mark.asyncio
async def test_unauthenticated_resume_endpoints_fail(async_client: AsyncClient):
    """Verify that protected resume endpoints return 401 when no auth header is supplied."""
    # List resumes unauthenticated
    list_res = await async_client.get("/api/v1/resumes")
    assert list_res.status_code == 401
    assert list_res.json()["detail"] == "Not authenticated"

    # Upload unauthenticated
    files = {"file": ("test.pdf", b"%PDF-1.5 mock", "application/pdf")}
    up_res = await async_client.post("/api/v1/resumes/upload", files=files)
    assert up_res.status_code == 401
    assert up_res.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_resume_upload_and_auto_candidate_profile_sync(async_client: AsyncClient):
    """Verify complete end-to-end flow: Ingest resume -> build candidate profile -> anchored evidence."""
    reg = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "sync.candidate@example.com",
            "password": "Password123!",
            "full_name": "Sync Candidate",
        },
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Upload valid resume
    docx_bytes = create_mock_docx_bytes()
    files = {
        "file": (
            "sync_resume.docx",
            docx_bytes,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    }
    up_res = await async_client.post(
        "/api/v1/resumes/upload", headers=headers, files=files, data={"is_master": "true"}
    )
    assert up_res.status_code == 201
    resume_id = up_res.json()["resume_id"]
    assert up_res.json()["is_master"] is True
    assert up_res.json()["sections_detected"] >= 3

    # 2. Build candidate profile with explicit resume_id
    sync_res = await async_client.post(
        "/api/v1/candidate/build-profile",
        headers=headers,
        json={"resume_id": resume_id},
    )
    assert sync_res.status_code == 200
    skills = sync_res.json()
    assert len(skills) > 0

    skill_names = [s["normalized_name"].lower() for s in skills]
    # Check that Go and Python or PostgreSQL were extracted
    assert any(s in skill_names for s in ["go", "python", "postgresql", "docker", "kubernetes"])

    # 3. Verify evidence anchoring
    for skill in skills:
        assert skill["evidence_text"] is not None
        assert len(skill["evidence_text"]) > 0

    # 4. Fetch candidate profile and verify persistence
    profile_res = await async_client.get("/api/v1/candidate/profile", headers=headers)
    assert profile_res.status_code == 200
    profile_skills = profile_res.json()
    assert len(profile_skills) == len(skills)


@pytest.mark.asyncio
async def test_candidate_build_profile_tenant_isolation(async_client: AsyncClient):
    """Verify that User B cannot trigger candidate profile synchronization on User A's resume."""
    # User A
    reg_a = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "iso.a@example.com", "password": "Password123!", "full_name": "Iso A"},
    )
    token_a = reg_a.json()["access_token"]

    # User B
    reg_b = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "iso.b@example.com", "password": "Password123!", "full_name": "Iso B"},
    )
    token_b = reg_b.json()["access_token"]

    # User A uploads resume
    docx_bytes = create_mock_docx_bytes()
    files = {
        "file": (
            "iso_a.docx",
            docx_bytes,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    }
    up_res = await async_client.post(
        "/api/v1/resumes/upload", headers={"Authorization": f"Bearer {token_a}"}, files=files
    )
    resume_a_id = up_res.json()["resume_id"]

    # User B passes User A's resume_id -> must fail with 404
    probe_res = await async_client.post(
        "/api/v1/candidate/build-profile",
        headers={"Authorization": f"Bearer {token_b}"},
        json={"resume_id": resume_a_id},
    )
    assert probe_res.status_code == 404
    assert "not found or does not belong to current user" in probe_res.json()["detail"]


@pytest.mark.asyncio
async def test_upload_invalid_file_extension_rejected(async_client: AsyncClient):
    """Verify that unsupported file extensions are rejected with 400 Bad Request."""
    reg = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "invalid.ext@example.com", "password": "Password123!", "full_name": "Ext Tester"},
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    files = {"file": ("malicious.exe", b"MZ fake executable content", "application/octet-stream")}
    res = await async_client.post("/api/v1/resumes/upload", headers=headers, files=files)
    assert res.status_code == 400
    assert "Unsupported file format" in res.json()["detail"]
