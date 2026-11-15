# CareerPilot 2.0: Comprehensive Engineering Audit & Technical Assessment

**Date:** November 15, 2026  
**Auditor:** Principal Software Architect, AI/ML Systems & QA Engineering  
**Branch:** `feature/careerpilot-2.0`  
**Repository:** `https://github.com/Soham-Pasalkar/Resume-Optimiser`

---

## 1. Executive Summary

CareerPilot is an AI-powered career intelligence and resume optimization platform designed to operate locally with privacy-first execution via local Ollama LLMs and PostgreSQL persistence.

This engineering audit examines the repository's architecture, data flows, AI interactions, document generation pipelines, and user experience. While foundational capabilities for authentication and basic resume ingestion have been restored, this audit identifies critical architectural defects, heuristic shortcuts masquerading as AI, data-flow disconnections, and user experience fragmentation that prevent the application from delivering its core value proposition:

> **"Analyze a job. Understand your gaps. Build a better resume. Prepare for the opportunity."**

---

## 2. Architecture & Tech Stack Inventory

```
+---------------------------------------------------------------------------------------+
|                                    NEXT.JS 15 FRONTEND                                |
|  - React 19 (Server + Client Components)                                              |
|  - Tailwind CSS + Soft UI Neumorphic Design System                                    |
|  - Centralized AuthContext & Route Guards                                             |
|  - API Client abstraction (fetch wrapper with Bearer JWT tokens)                      |
+-------------------------------------------+-------------------------------------------+
                                            | HTTP REST (/api/v1)
                                            v
+-------------------------------------------+-------------------------------------------+
|                                   FASTAPI 0.115 BACKEND                               |
|  - Modular Monolith Architecture (app/modules/*)                                      |
|  - SQLAlchemy 2.0 Async ORM + AsyncPG / SQLite                                        |
|  - Pydantic v2 validation & schemas                                                  |
|  - JWT OAuth2 authentication (HMAC-SHA256) with Bcrypt password hashing               |
+---------------------+---------------------+---------------------+---------------------+
                      |                     |                     |
                      v                     v                     v
              +---------------+     +---------------+     +---------------+
              |  Local Ollama |     |  PostgreSQL   |     | Local Storage |
              |  LLM Engine   |     |  16 Database  |     |  / MinIO S3   |
              |  (Qwen/Llama) |     |  & pgvector   |     | Documents     |
              +---------------+     +---------------+     +---------------+
```

### Module Breakdown

| Module | Core Purpose | Backend Location | Frontend Route |
| :--- | :--- | :--- | :--- |
| **Authentication** | User signup, login, JWT issuance, profile management | `backend/app/api/v1/endpoints/auth.py`, `users.py` | `/(auth)/login`, `/(auth)/register` |
| **Resume Ingestion** | PDF/DOCX upload, OCR fallback, section segmentation | `backend/app/modules/ingestion/` | `/resumes` |
| **Candidate Profile** | Master skills extraction, evidence anchoring, candidate verification | `backend/app/modules/candidate/` | `/candidate` |
| **JD Intelligence** | Parsing job postings into requirements, seniority, salary | `backend/app/modules/jd_engine/` | `/jobs` |
| **Matching Engine** | Hybrid BM25 lexical + dense semantic matching, gap analysis | `backend/app/modules/matching/` | `/matches` |
| **Resume Studio** | Role-targeted resume tailoring, bullet rewriter, ATS export | `backend/app/modules/optimizer/` | `/optimizer` |
| **Career Learning** | Skill gap remediation roadmaps and project recommendations | `backend/app/modules/learning/` | `/learning` |
| **Interview Prep** | Role-specific technical, behavioral, and gap defense interview prep | `backend/app/modules/interview/` | `/interview` |
| **Application Tracker** | Job application lifecycle, interview notes, outcome tracking | `backend/app/modules/application/` | `/pipeline` |
| **Settings & Health** | Local Ollama daemon health, BYOK cloud keys, privacy GDPR | `backend/app/api/v1/endpoints/settings.py` | `/settings` |

---

## 3. Detailed Defect Analysis & Root Causes

### 3.1 Defect A: Enormous Resume Sections Attached as Evidence to Skill Gaps
- **Location:** `backend/app/modules/matching/scorer.py` (lines 60–73, 120–123, 146–150) and `dense.py`.
- **Root Cause:** When populating `resume_chunks` for dense semantic matching and evidence snippet retrieval, the engine appended `section.raw_content.strip()`. For multi-paragraph sections (such as an entire 5-year work history block), this single chunk contained thousands of characters. In `dense.py`, the fallback n-gram hashing algorithm computed an inflated cosine similarity due to the sheer volume of subword tokens in large text blocks. As a result, the entire work experience or education section was returned as the `evidence_snippet` for discrete requirements like `"Git"` or `"Docker"`.
- **Impact:** Match reports displayed overwhelming, unreadable walls of text under individual skill gap items, defeating the purpose of concise evidence verification.

### 3.2 Defect B: Conflation of Extraction with Candidate Verification
- **Location:** `backend/app/modules/matching/scorer.py` (lines 252–260) and `candidate/service.py`.
- **Root Cause:** In `_classify_gap`, if a skill was matched and had an `evidence_text` string, the action was set to:
  ```python
  action = f"Verified alignment with candidate competency '{direct_skill.skill_name}'."
  ```
  even when `direct_skill.is_user_verified` was `False`.
- **Impact:** Automatically extracted skills were reported as "verified" to the user, creating a false sense of security and violating strict human-in-the-loop integrity rules.

### 3.3 Defect C: Generic Job Requirement Extraction on Paragraph JDs
- **Location:** `backend/app/modules/jd_engine/extractor.py` (lines 223–236).
- **Root Cause:** The rule-based fallback assumed job descriptions were formatted strictly with bullet points (`-`, `•`, `*`). When given unstructured paragraph text or narrative job summaries without bullets, the parser defaulted to generating synthetic generic requirements:
  ```python
  ExtractedRequirement(
      requirement_text=f"Demonstrated proficiency in {skill['canonical_name']}",
      category="technical_skill",
  )
  ```
- **Impact:** Extracted requirements lost the nuance, scope, and specific responsibilities of the real job posting.

### 3.4 Defect D: Insignificant Resume Rewriting & Missing Full-Document Tailoring
- **Location:** `backend/app/modules/optimizer/service.py` (lines 101–128) and `rewriter.py`.
- **Root Cause:**
  1. The optimizer iterated through experience bullets and assigned target requirements using round-robin modulo arithmetic:
     ```python
     target_req = req_cycle[req_idx % len(req_cycle)]
     ```
     This completely decoupled the bullet's actual subject matter from the requirement it supposedly targeted.
  2. The candidate's name was derived from the uploaded file name (`resume.file_name.replace(".pdf", "").title()`), causing generated documents to display names like `"Resume Final V2"`.
  3. The optimizer only offered bullet-by-bullet rewrites, failing to prioritize relevant projects, reorder sections, align skills, or eliminate irrelevant background.
- **Impact:** Generated resumes felt like superficial regex word substitutions rather than tailored executive career documents.

### 3.5 Defect E: Disconnected End-to-End Workflow
- **Root Cause:** Users had to jump between disconnected pages without context passing:
  1. Analyze a job at `/jobs`.
  2. Separately go to `/matches`, click "New Match", and re-select the resume and job from dropdowns.
  3. Separately go to `/optimizer`, click "New Tailoring", and re-select the resume and job again.
- **Impact:** Severe UX friction. The product operated as a collection of disjointed tools rather than a guided, end-to-end career intelligence journey.

### 3.6 Defect F: Generic Learning Milestones with Placeholder URLs
- **Location:** `backend/app/modules/learning/generator.py` (lines 211–235).
- **Root Cause:** When a skill gap did not match the 5 hardcoded domains in `CURATED_DOMAINS` (`kubernetes`, `docker`, `postgresql`, `kafka`, `aws`), the fallback generated generic milestones:
  ```python
  milestone_title = f"Production Implementation & Mastery of {skill_name}"
  url = "https://devdocs.io/"
  ```
- **Impact:** Roadmaps lacked actionable, grounded learning recommendations for modern tech stacks.

### 3.7 Defect G: Fabricated Candidate Stories in Interview Preparation
- **Location:** `backend/app/modules/interview/prompt_generator.py` (lines 193–198).
- **Root Cause:** The STAR interview preparation fallback manufactured specific past stories for the candidate (e.g. *"Disagreement over choosing REST vs gRPC... Built quick proof-of-concept benchmarks"*), even when the candidate had never worked with those technologies.
- **Impact:** Fabricating candidate experiences in interview answers destroys interview credibility and violates the platform's core zero-hallucination mandate.

### 3.8 Defect H: Fragmented, Technical Navigation
- **Location:** `frontend/src/components/layout/sidebar.tsx`.
- **Root Cause:** The sidebar listed 10 flat navigation links using internal engineering terms ("Resume Ingestion", "JD Intelligence", "Match Reports", "AI Resume Optimizer", "Learning Roadmaps", "Application Pipeline").
- **Impact:** Users were not guided on what actions to take or in what order to achieve a tailored resume.

---

## 4. Hard-Coded & Mock Data Inventory

| File / Component | What is Hardcoded / Mocked | Risk / Impact | Required Fix |
| :--- | :--- | :--- | :--- |
| `backend/app/modules/learning/generator.py` | `CURATED_DOMAINS` limited to 5 hardcoded domains | Gaps outside these 5 get generic `devdocs.io` links | Expand curated knowledge base; generate dynamic, domain-aware learning objectives |
| `backend/app/modules/interview/prompt_generator.py` | Hardcoded STAR scenario stories | Invents candidate past experiences | Replace with candidate answer frameworks and evaluation rubrics |
| `backend/app/modules/optimizer/service.py` | `candidate_name` parsed from file name | Generates resumes titled "Resume V1" | Retrieve actual candidate name from `User` / `UserProfile` |
| `backend/app/modules/optimizer/rewriter.py` | `STRONG_ACTION_VERBS` dictionary | Word-for-word regex replacement | Combine with intelligent, evidence-grounded bullet re-structuring |
| `backend/app/modules/matching/dense.py` | MD5 n-gram hashing fallback | Keyword overlap treated as semantic similarity | Accurately label hash-based overlap as lexical heuristic; use genuine embeddings when Ollama is online |

---

## 5. AI Integration & Local LLM Audit

1. **Ollama Integration (`app/core/llm.py`)**:
   - Uses `httpx.AsyncClient` targeting `http://localhost:11434`.
   - Supports `/api/generate` with `format="json"`, temperature, and timeout controls.
   - Robust status probe (`/api/tags`) detects daemon availability and lists installed models.
2. **Current Deficiencies**:
   - Single fallback behavior without clear UI indication when Ollama is offline or uninstalled.
   - Prompts in `JDExtractor`, `BulletRewriter`, `RoadmapGenerator`, and `InterviewPromptGenerator` lack strict Pydantic JSON schema enforcement, occasionally causing markdown code-fence parsing errors.
3. **Required Improvements**:
   - Explicitly communicate to users whether an output was generated by the local LLM (`qwen2.5-coder:14b` / `llama3.1:8b`) or via verified deterministic heuristics.
   - Implement structured outputs with Pydantic schemas.

---

## 6. Implementation Roadmap & Milestones

- **M1: Product Experience & Navigation Redesign**: Reorganize routes into Workspace, Career Development, and Settings. Establish seamless handoff between Job Analysis $\to$ Gap Analysis $\to$ Resume Studio.
- **M2: Granular Evidence Retrieval & Multi-Dimensional Gap Engine**: Break resume text into atomic bullet chunks. Implement 6 gap dimensions (`TECHNICAL`, `EXPERIENCE`, `EDUCATION`, `PROJECT`, `CERTIFICATION`, `DOMAIN`). Distinguish extracted vs. candidate-verified evidence.
- **M3: End-to-End Resume Studio**: Ground bullet transformations in verified candidate profile data. Eliminate modulo requirement cycling. Retrieve real candidate profile names and contact info. Enable full-document ATS tailoring.
- **M4: Factual Validation & ATS Document Generation**: Implement syntactic and semantic factual verification layers. Verify PDF and DOCX exports against approved content.
- **M5: Gap-Derived Learning & Grounded Interview Intelligence**: Generate specific, verified curriculum for missing skills. Replace fabricated interview stories with STAR guidance frameworks.
- **M6: Application Tracker & SaaS UI Polish**: Connect applications to job analyses and tailored resumes. Polish typography, spacing, and micro-interactions.
- **M7: Automated Testing & GitHub Delivery**: End-to-end integration test suite. Multi-tenant isolation verification. Production Next.js build. Git commits pushed to `feature/careerpilot-2.0`.
