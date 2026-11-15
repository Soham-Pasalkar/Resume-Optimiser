# CareerPilot 2.0 System Architecture & Technical Specification

## 1. System Overview & Core Promise

CareerPilot is an AI-powered, local-first career intelligence platform designed to eliminate the guesswork from technical job seeking. Its architecture transforms raw candidate experience documents into verifiable, evidence-anchored competencies, accurately assesses alignment against target job descriptions, and generates ATS-optimized resumes adhering strictly to factual preservation guardrails.

```
       ┌────────────────────────┐
       │   MY CAREER PROFILE    │
       │ (Documents & Evidence) │
       └───────────┬────────────┘
                   │
                   ▼
       ┌────────────────────────┐
       │      JOB ANALYSIS      │
       │ (Structured JD Engine) │
       └───────────┬────────────┘
                   │
                   ▼
       ┌────────────────────────┐
       │      GAP ANALYSIS      │
       │  (Hybrid 5-Factor Sim) │
       └───────────┬────────────┘
                   │
                   ▼
       ┌────────────────────────┐
       │     RESUME STUDIO      │
       │  (Google XYZ Formula)  │
       └───────────┬────────────┘
                   │
                   ▼
       ┌────────────────────────┐
       │   FACTUAL VALIDATION   │
       │  (Anti-Hallucination)  │
       └───────────┬────────────┘
                   │
                   ▼
       ┌────────────────────────┐
       │   ATS EXPORT ENGINE    │
       │     (PDF & DOCX)       │
       └────────────────────────┘
```

---

## 2. High-Level Architecture & Component Topology

```mermaid
flowchart TD
    subgraph Client ["Client Layer (Next.js 15 / React 19)"]
        UI["Soft-UI Neumorphic Interface"]
        APIClient["API Client Abstraction (lib/api.ts)"]
        AuthStorage["Secure Token Storage (cp_access_token)"]
    end

    subgraph Server ["Backend Layer (FastAPI / Python 3.14)"]
        Router["API Gateway /api/v1"]
        AuthDep["Authentication & Tenant Isolation Guard"]

        subgraph CoreEngines ["Core Intelligence Engines"]
            JDEngine["JD Deconstructor (Regex + Ollama)"]
            Ontology["Skill Ontology Normalizer (500+ Concepts)"]
            DenseEngine["Dense Semantic Vector Matcher"]
            BM25Engine["BM25 Okapi Lexical Index"]
            Scorer["Hybrid 5-Factor Scoring Engine"]
            Rewriter["Google XYZ Bullet Rewriter"]
            Guardrail["Syntactic & Entity Factual Guardrail"]
            Exporter["ATS Document Exporter (ReportLab + DOCX)"]
        end
    end

    subgraph DataLayer ["Persistence & External Services"]
        PG[("PostgreSQL / SQLite Storage")]
        OllamaLocal[("Local Ollama Daemon (qwen2.5-coder:14b)")]
    end

    UI --> APIClient
    APIClient --> AuthStorage
    APIClient --> Router
    Router --> AuthDep
    AuthDep --> CoreEngines
    CoreEngines --> PG
    CoreEngines --> OllamaLocal
```

---

## 3. Module Boundaries & Responsibilities

### Module 1: Authentication & Workspace Security
- **Endpoints:** `/api/v1/auth/register`, `/api/v1/auth/login`, `/api/v1/auth/refresh`, `/api/v1/users/me`
- **Security:** Argon2id / bcrypt password hashing, cryptographic JWT bearer tokens, sliding refresh window, GDPR account purge with cascading deletion.
- **Tenant Isolation:** Enforced on every database query via `user_id == current_user.id`.

### Module 2: Ingestion & Document Segmentation
- **Endpoints:** `/api/v1/resumes/upload`, `/api/v1/resumes`, `/api/v1/resumes/{id}`
- **Processing:** Multi-format parser (PDF via pdfplumber, DOCX via python-docx), heading hierarchy segmenter, granular item bullet extraction.

### Module 3: JD Intelligence Engine
- **Endpoints:** `/api/v1/jobs/analyze`, `/api/v1/jobs`, `/api/v1/jobs/{id}`
- **Intelligence:** Sentence-level requirement decomposition for both bulleted and narrative paragraph job descriptions, experience threshold extraction, mandatory vs. preferred classification.

### Module 4: Candidate Intelligence & Master Profile
- **Endpoints:** `/api/v1/candidate/profile`, `/api/v1/candidate/build-profile`, `/api/v1/candidate/skills/{id}/verify`
- **Integrity:** Anchors every competency to verbatim resume bullet evidence. Strictly isolates automatically extracted skills from candidate-verified competencies.

### Module 5 & 6: Hybrid Matching & Skill Gap Analysis
- **Endpoints:** `/api/v1/matches/evaluate`, `/api/v1/matches`, `/api/v1/matches/{id}`, `/api/v1/matches/{id}/gaps/verify`
- **Engine:** Combines BM25 lexical ranking (15%), dense semantic cosine similarity (25%), skill ontology overlap (35%), experience depth (15%), and domain relevance (10%).

### Module 7 & 11: Resume Studio 2.0 & ATS Document Generation
- **Endpoints:** `/api/v1/optimizer/tailor`, `/api/v1/optimizer/tailored-resumes/{id}`, `/api/v1/optimizer/diffs/{id}`, `/api/v1/optimizer/diffs/{id}/restore`, `/api/v1/optimizer/tailored-resumes/{id}/sections`, `/api/v1/optimizer/tailored-resumes/{id}/composition`, `/api/v1/optimizer/tailored-resumes/{id}/export-pdf`, `/api/v1/optimizer/tailored-resumes/{id}/export-docx`
- **Subsystems:**
  - *Content Intelligence & Selection:* Maps job requirements to candidate resume evidence across all sections, categorizes decisions (`INCLUDED`, `PROPOSED_REWRITE`, `REORDERED`, `EXCLUDED`), and isolates missing requirements without fabricating ungrounded claims.
  - *Requirement-to-Evidence Matrix:* Explicit matching methods (`ONTOLOGY_EXACT`, `DENSE_OLLAMA`, `LEXICAL_BM25_FALLBACK`, `DENSE_HASH_FALLBACK`) and candidate verification labels (`CANDIDATE_VERIFIED` vs `EXTRACTED_UNCONFIRMED`).
  - *Context-Aware Rewriter:* Strong technical action verbs, preservation of quantitative metrics when present, avoidance of forced XYZ or AI jargon when metrics are not present.
  - *5-Layer Factual Guardrail:* Deterministic entity, metric, temporal, and seniority invariant checks with standardized human review statuses (`VERIFIED`, `FLAGGED`, `REQUIRES_REVIEW`, `NOT_VERIFIED`).
  - *Composition Intermediate Representation (IR):* Structured document state with source-to-output provenance, section inclusion toggles, and 1-click restore to candidate's original text.
  - *ATS Document Exporters:* Single-column ReportLab PDF & python-docx generation with orphan heading prevention (`keepWithNext=True`), Unicode normalization, and pre-export content validation.

### Module 8 & 9: Career Development Intelligence
- **Endpoints:** `/api/v1/learning/generate`, `/api/v1/learning/milestones/{id}`, `/api/v1/interview/generate`, `/api/v1/interview/questions/{id}/evaluate`
- **Curriculum:** Curated technical learning blueprints for 15+ engineering domains and practical portfolio projects.
- **Interviews:** STAR framing guidelines (Situation, Task, Action, Result) providing authentic candidate answering frameworks without fabricating fake past stories.

### Module 10: Application Pipeline
- **Endpoints:** `/api/v1/applications`, `/api/v1/applications/{id}/stage`, `/api/v1/applications/compare`
- **Tracking:** Kanban and table views tracking opportunities across 6 hiring stages, directly linked to target JDs, gap evaluations, and tailored resume snapshots.

---

## 4. Database Entity-Relationship Model

```mermaid
erDiagram
    USERS ||--o{ RESUMES : owns
    USERS ||--o{ CANDIDATE_SKILLS : maintains
    USERS ||--o{ JOB_DESCRIPTIONS : analyzes
    USERS ||--o{ MATCH_EVALUATIONS : computes
    USERS ||--o{ TAILORED_RESUMES : authors
    USERS ||--o{ JOB_APPLICATIONS : tracks
    USERS ||--o| USER_PROFILES : configures

    RESUMES ||--o{ RESUME_SECTIONS : contains
    RESUME_SECTIONS ||--o{ RESUME_ITEMS : contains

    JOB_DESCRIPTIONS ||--o{ JD_REQUIREMENTS : defines

    MATCH_EVALUATIONS ||--o{ SKILL_GAP_ITEMS : evaluates
    MATCH_EVALUATIONS ||--o| LEARNING_ROADMAPS : derives
    MATCH_EVALUATIONS ||--o| INTERVIEW_PREP : derives

    TAILORED_RESUMES ||--o{ TAILORED_BULLET_DIFFS : proposes

    LEARNING_ROADMAPS ||--o{ LEARNING_MILESTONES : schedules
    INTERVIEW_PREP ||--o{ INTERVIEW_QUESTIONS : presents
```
