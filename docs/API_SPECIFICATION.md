# CareerPilot — REST API Specification
## OpenAPI 3.1 & Contract Design

> **Document Version:** 1.0.0-PROPOSAL  
> **Status:** Review Ready  
> **Base URL:** `/api/v1`  
> **Protocol:** HTTPS / TLS 1.3  
> **Serialization:** JSON (`application/json`) / Multipart (`multipart/form-data`)

---

## 1. Global API Standards & Conventions

### 1.1 Authentication & Tenant Context
All non-public endpoints require a valid JSON Web Token (JWT) passed in the `Authorization` header:
```http
Authorization: Bearer <access_token>
```
The token payload contains the `sub` claim (user UUID). The backend extracts and injects this as `current_user` into every database repository query.

### 1.2 Unified Error Envelope
All error responses strictly conform to this predictable schema:
```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "The requested resume does not exist or belongs to another user.",
    "details": [
      {
        "field": "resume_id",
        "issue": "UUID 'b9f1d07c-3f9b-4e1b-9a4f-561234567890' not found"
      }
    ],
    "timestamp": "2026-11-14T12:00:00Z"
  }
}
```

### 1.3 Asynchronous Task Contract
Long-running jobs (document OCR, LLM bullet rewriting, batch matching) return an immediate `202 Accepted` response with a task reference:
```json
{
  "task_id": "c1f72a44-8c88-4674-a69c-2917d5c58901",
  "status": "PROCESSING",
  "resource_id": "7a3560b3-8b74-4ec2-9111-e40263f3505c",
  "poll_url": "/api/v1/tasks/c1f72a44-8c88-4674-a69c-2917d5c58901",
  "sse_url": "/api/v1/tasks/c1f72a44-8c88-4674-a69c-2917d5c58901/events"
}
```

---

## 2. API Endpoints by Module

---

### MODULE 1: Authentication & User Workspace

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/auth/register` | Register a new user account | Public |
| `POST` | `/auth/login` | Authenticate and issue JWT pair | Public |
| `POST` | `/auth/refresh` | Refresh an expired access token | Refresh Token |
| `POST` | `/auth/logout` | Revoke tokens & terminate session | Bearer |
| `GET`  | `/users/me` | Fetch active user profile & preferences | Bearer |
| `PUT`  | `/users/me` | Update profile information | Bearer |
| `GET`  | `/settings/llm` | Get active LLM config (Ollama status & models) | Bearer |
| `PUT`  | `/settings/llm` | Configure Ollama host/model or BYOK API keys | Bearer |
| `DELETE`| `/users/me` | Complete account and data deletion | Bearer |

#### `POST /auth/login`
- **Request:**
  ```json
  {
    "email": "candidate@example.com",
    "password": "SecurePassword123!"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "refresh_token": "eyJhbGciOi...",
    "token_type": "Bearer",
    "expires_in": 900,
    "user": {
      "id": "e20b3294-811c-4b52-9b21-4fa1783cf634",
      "email": "candidate@example.com",
      "full_name": "Marcus Vance"
    }
  }
  ```

---

### MODULE 2: Resume Ingestion & Parsing

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/resumes/upload` | Upload resume file (PDF or DOCX) | Bearer |
| `GET`  | `/resumes` | List all uploaded resumes for user | Bearer |
| `GET`  | `/resumes/{id}` | Get parsed resume details & sections | Bearer |
| `PUT`  | `/resumes/{id}/sections` | Edit parsed resume sections manually | Bearer |
| `DELETE`| `/resumes/{id}` | Delete resume and stored binary | Bearer |

#### `POST /resumes/upload`
- **Request:** `multipart/form-data` with `file: binary` (PDF/DOCX, max 10MB) and `is_master: boolean`.
- **Response (202 Accepted):**
  ```json
  {
    "resume_id": "7a3560b3-8b74-4ec2-9111-e40263f3505c",
    "file_name": "Marcus_Vance_Resume.pdf",
    "status": "PROCESSING",
    "task_id": "c1f72a44-8c88-4674-a69c-2917d5c58901"
  }
  ```

---

### MODULE 3: Job Description Intelligence

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/job-descriptions/analyze` | Ingest and decompose a target JD | Bearer |
| `GET`  | `/job-descriptions` | List saved job descriptions | Bearer |
| `GET`  | `/job-descriptions/{id}` | Get structured JD requirements | Bearer |
| `DELETE`| `/job-descriptions/{id}` | Delete saved job description | Bearer |

#### `POST /job-descriptions/analyze`
- **Request:**
  ```json
  {
    "job_title": "Senior Backend Engineer",
    "company_name": "Stripe",
    "raw_text": "We are looking for a Senior Backend Engineer with 5+ years of experience in Go or Java. Experience with distributed systems and Kubernetes is required..."
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "id": "4d781b4e-2895-46f9-b88c-982a5c4e4321",
    "job_title": "Senior Backend Engineer",
    "company_name": "Stripe",
    "seniority_level": "Senior",
    "work_mode": "Hybrid",
    "requirements": [
      {
        "id": "req-01",
        "requirement_text": "5+ years experience in Go or Java",
        "category": "technical_skill",
        "is_mandatory": true,
        "importance_weight": 1.0,
        "min_years_experience": 5.0
      },
      {
        "id": "req-02",
        "requirement_text": "Experience with Kubernetes and container orchestration",
        "category": "technical_skill",
        "is_mandatory": false,
        "importance_weight": 0.7
      }
    ]
  }
  ```

---

### MODULE 4 & 5: Candidate-Role Hybrid Matching

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/matches/evaluate` | Trigger hybrid matching between Resume & JD | Bearer |
| `GET`  | `/matches/{id}` | Retrieve full explainable match report | Bearer |
| `GET`  | `/matches` | List previous match evaluations | Bearer |

#### `POST /matches/evaluate`
- **Request:**
  ```json
  {
    "resume_id": "7a3560b3-8b74-4ec2-9111-e40263f3505c",
    "jd_id": "4d781b4e-2895-46f9-b88c-982a5c4e4321"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "match_id": "90e271a3-11bb-4f32-849c-38c201a45700",
    "overall_score": 82.5,
    "rating_label": "Strong Alignment",
    "sub_scores": {
      "skill_match": 88.0,
      "semantic_similarity": 81.5,
      "lexical_bm25": 75.0,
      "experience_depth": 90.0,
      "domain_relevance": 78.0
    },
    "scoring_breakdown": {
      "mandatory_coverage_ratio": 0.90,
      "preferred_coverage_ratio": 0.72
    },
    "summary_analysis": "Candidate demonstrates strong alignment with core backend engineering and distributed caching requirements. Primary gap is commercial Kubernetes orchestration."
  }
  ```

---

### MODULE 6: Skill Gap Analysis

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET`  | `/matches/{id}/gaps` | Fetch categorized requirement gaps | Bearer |
| `POST` | `/matches/{id}/gaps/verify` | Candidate verifies unmentioned capability | Bearer |

#### `POST /matches/{id}/gaps/verify`
- **Request:**
  ```json
  {
    "gap_item_id": "c4938a10-449e-4a61-9c12-32a819b91012",
    "has_experience": true,
    "years_experience": 2.0,
    "verification_evidence": "Built Docker Compose local dev environments and managed ECS task definitions at Acme Corp."
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "status": "VERIFIED",
    "updated_overall_score": 85.5,
    "message": "Candidate profile updated. Match score recalculated."
  }
  ```

---

### MODULE 7: AI Resume Optimizer

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/optimizer/tailor` | Generate tailored resume bullet diffs | Bearer |
| `GET`  | `/optimizer/tailored-resumes/{id}` | Fetch tailored resume draft & diffs | Bearer |
| `PUT`  | `/optimizer/diffs/{diff_id}` | Accept, reject, or edit proposed diff | Bearer |
| `POST` | `/optimizer/tailored-resumes/{id}/export-pdf` | Export ATS-compliant PDF | Bearer |
| `POST` | `/optimizer/tailored-resumes/{id}/export-docx`| Export editable DOCX | Bearer |

#### `POST /optimizer/tailor`
- **Request:**
  ```json
  {
    "resume_id": "7a3560b3-8b74-4ec2-9111-e40263f3505c",
    "jd_id": "4d781b4e-2895-46f9-b88c-982a5c4e4321"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "tailored_resume_id": "31bfa821-6d73-45ab-8521-998811223344",
    "diffs_count": 8,
    "diffs": [
      {
        "id": "diff-01",
        "original_text": "Worked on backend microservices and database queries.",
        "optimized_text": "Architected Go backend microservices handling 12,000 req/sec; optimized PostgreSQL queries reducing p99 latency by 34%.",
        "rationale": "Frames technical contribution using Google XYZ formula; highlights Go and PostgreSQL required in JD.",
        "nli_verification_status": "ENTAILMENT",
        "status": "PENDING"
      }
    ]
  }
  ```

---

### MODULE 8: Personalized Learning Roadmap

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/learning/generate` | Generate roadmap for unresolved gaps | Bearer |
| `GET`  | `/learning/{id}` | Fetch structured milestones & projects | Bearer |
| `PUT`  | `/learning/milestones/{id}` | Update milestone completion status | Bearer |

---

### MODULE 9: Interview Intelligence

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/interview/generate` | Generate role-specific interview prep | Bearer |
| `GET`  | `/interview/{id}` | Fetch questions, rubrics & STAR guides | Bearer |
| `POST` | `/interview/questions/{id}/evaluate` | Evaluate candidate practice answer | Bearer |

---

### MODULE 10: Job Application Management

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET`  | `/applications` | List tracked applications (Kanban) | Bearer |
| `POST` | `/applications` | Create new application entry | Bearer |
| `GET`  | `/applications/{id}` | Get application detail & stage history | Bearer |
| `PUT`  | `/applications/{id}/status` | Move application stage in Kanban | Bearer |
| `DELETE`| `/applications/{id}` | Delete tracked application | Bearer |
