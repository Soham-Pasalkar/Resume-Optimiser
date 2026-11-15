# CareerPilot — Project Brief & Product Identity

> **Version:** 1.0.0-PROPOSAL  
> **Status:** Draft / Architectural Review  
> **Author:** Principal Software Architect, Senior AI Engineer, Product Designer  
> **Target System:** Public Multi-User SaaS Platform  
> **Repository:** `https://github.com/Soham-Pasalkar/CareerPilot` (Local: `/Users/soham/Github/Resume-Optimiser`)

---

## 1. Executive Summary

**CareerPilot** is an enterprise-grade, research-oriented AI career intelligence platform. It bridges the critical structural gap between job seekers and employers by decoding job requirements, objectively evaluating candidate qualifications through hybrid semantic-lexical analysis, providing transparent and evidence-grounded skill gap assessments, optimizing resumes without hallucination or factual distortion, and formulating personalized career progression pathways.

Unlike generic resume builders or black-box "ATS checkers" that peddle arbitrary percentage scores and keyword stuffing, CareerPilot functions as a personal career strategist and technical advocate. It provides defensible, auditable insights backed by rigorous AI engineering and an accessible, tactile **Soft UI Evolution** user experience.

---

## 2. Product Identity & Brand Voice

- **Project Name:** CareerPilot
- **Tagline:** *Navigate your career. Engineer your future.*
- **Category:** AI-Powered Career Intelligence & Application Optimization Platform
- **Cost & Operational Model:** **100% Free & Open-Source (Zero Operational Cost)**
  - **Default Local AI Engine:** Powered by local **Ollama** models (e.g., `llama3.1:8b`, `qwen2.5:7b`, `mistral:7b`) running on the user's own machine.
  - **Zero Paid API Requirement:** Entire workflow (ingestion, OCR, embeddings, matching, rewriting, gap analysis, roadmap generation) operates completely free without requiring paid subscriptions or external API credits.
  - **Flexible BYOK (Bring Your Own Key) Option:** Users who wish to utilize cloud providers (OpenAI, Anthropic, Google Gemini, Groq) can optionally provide their own API keys in settings.
  - **Complete Privacy & Data Sovereignty:** With local Ollama and local embeddings, candidate resumes and job descriptions never leave the host environment.
- **Target Audience:** Job seekers, engineers, technical professionals, mid-to-senior career changers, and students seeking defensible alignment with high-value technical and professional roles.
- **Brand Personality:**
  - **Authoritative & Defensible:** Never provides ungrounded scores; every rating links directly to source evidence.
  - **Ethical & Fact-Preserving:** Strictly forbids fabrication, credential invention, or deceptive metric inflation.
  - **Empowering & Constructive:** Evaluates lack of resume evidence as a verification prompt rather than an absolute candidate deficiency.
  - **Refined & Modern:** Embodies understated enterprise luxury through the tactile Soft UI Evolution design system.

---

## 3. The Problem Space

Modern recruitment processes are broken on both sides of the hiring equation:

1. **The Asymmetric Information Problem:** Job descriptions (JDs) are often bloated, combining mandatory core competencies with aspirational wishlists, vague jargon, and unstated hiring team expectations. Candidates do not know what truly matters.
2. **The "Black-Box ATS" Myth & Keyword Misinformation:** Commercial resume checkers generate meaningless "ATS Score: 78%" widgets based on crude keyword counting, encouraging candidates to perform unreadable "keyword stuffing" that harms human recruiter review.
3. **The Presentation Deficit:** Qualified candidates fail to communicate their genuine accomplishments using structured impact frameworks (e.g., Google XYZ or STAR methodologies), burying critical competencies under weak, passive language.
4. **The Factual Integrity Risk of Generative AI:** Naive LLM resume rewriters frequently hallucinate experience, invent programming languages never touched by the candidate, or introduce exaggerated performance metrics, creating catastrophic credibility failures in technical interviews.
5. **The Disjointed Workflow:** Candidates manage resumes in Word/Google Docs, track applications in spreadsheets, research interview questions on Reddit, and find tutorials across disparate websites without a unified intelligence pipeline.

---

## 4. Relationship to Sister Project: PeopleLens (Resume-Ranker)

CareerPilot is the strategic counterpart to **PeopleLens (Resume-Ranker)** (`https://github.com/Soham-Pasalkar/Resume-Ranker`), a recruiter-facing talent intelligence platform.

```
       RECRUITMENT INTELLIGENCE ECOSYSTEM
       
  [ Recruiter Perspective ]             [ Candidate Perspective ]
     +-----------------+                   +------------------+
     |   PeopleLens    |                   |   CareerPilot    |
     | (Resume-Ranker) |                   | (Career Support) |
     +--------+--------+                   +--------+---------+
              |                                     |
              | Finds best candidates               | Prepares best candidates
              | Evaluates candidate pool            | Clarifies job expectations
              | Rank-orders applicants              | Highlights genuine strengths
              | Reciprocal Rank Fusion              | Hybrid Candidate-JD Match
              v                                     v
     +-----------------+                   +------------------+
     | Recruiter Tools |                   | Candidate Tools  |
     +-----------------+                   +------------------+
              \                                     /
               \--- Shared Conceptual Research ----/
                    (Ontologies, Hybrid Matching,
                     Evidence-Based Evaluation)
```

### Architectural & Operational Separation
- **Strict Decoupling:** CareerPilot and PeopleLens maintain **completely separate repositories, databases, user credentials, application logic, and deployment environments**.
- **No Shared Runtime State:** Neither platform queries or accesses the other's operational data stores or API backends.
- **Conceptual Synergy:** Both leverage shared research insights:
  - Multi-tier skill ontologies (mapping variations like "React", "React.js", and "ReactJS" to unified concepts).
  - Hybrid lexical (BM25) and dense semantic embedding retrieval.
  - Reciprocal Rank Fusion (RRF) and multi-factor ranking.
  - Evidence-grounded qualification verification.

---

## 5. Core Philosophy & Guiding Principles

1. **Zero Hallucination / Absolute Factual Preservation:**
   Under no circumstances will CareerPilot invent work history, inflate titles, fabricate achievements, or add tools the candidate has never worked with. Optimization means *clarifying and framing authentic experience*, not engineering deceit.
2. **Explainable & Auditable Intelligence:**
   Every match score, missing skill alert, and resume suggestion must cite exact source phrases from the resume or the job description.
3. **Absence of Evidence is Not Evidence of Absence:**
   If a resume does not mention "PostgreSQL", CareerPilot flags this as *"Not Demonstrated in Resume — Requires User Verification"*, allowing the candidate to confirm whether they possess off-resume experience.
4. **Master Profile Reusability:**
   Users build a rich, validated **Master Candidate Profile** once. When applying to ten different positions, CareerPilot compares the master profile against each unique JD, producing role-tailored resumes and gap roadmaps without duplicate data entry.
5. **Tactile, Accessible Elegance (Soft UI Evolution):**
   The application avoids noisy gradients and inaccessible pseudo-3D effects in favor of soft, dual-shadow tactile surfaces, deeply considered inset wells, WCAG AA contrast compliance, and instantaneous responsiveness.

---

## 6. High-Level Product Scope

The platform encompasses ten unified functional modules:

```
+-------------------------------------------------------------------------------+
|                             CAREERPILOT PLATFORM                              |
+-------------------------------------------------------------------------------+
|  [01. Auth & Workspace]    |  [02. Ingestion & OCR]    |  [03. JD Intelligence]  |
|  Secure Multi-Tenant SaaS  |  PDF/DOCX & Scanned Docs  |  Requirement Extraction |
+----------------------------+---------------------------+-------------------------+
|  [04. Candidate Profile]   |  [05. Hybrid Matching]    |  [06. Skill Gap Engine] |
|  Master Competency Graph   |  Dense+Lexical Alignment  |  Demonstrated vs Void   |
+----------------------------+---------------------------+-------------------------+
|  [07. AI Resume Optimizer] |  [08. Learning Engine]    |  [09. Interview Prep]   |
|  Fact-Preserved Rewriting  |  Prioritized Curricula    |  STAR & Technical Mocks |
+----------------------------+---------------------------+-------------------------+
|                    [10. Job Application Management]                           |
|                    Kanban Tracker, Stage History, Tailored Resumes           |
+-------------------------------------------------------------------------------+
```

---

## 7. Key Success Metrics

| Dimension | Primary Metric | Target / Benchmark |
| :--- | :--- | :--- |
| **Factual Integrity** | Hallucination Rate in Tailored Bullets | **0.0%** (zero ungrounded claims generated) |
| **Matching Accuracy** | Correlation with Human Expert Alignment | **Pearson $r \ge 0.85$**, **NDCG@10 $\ge 0.90$** |
| **System Latency** | End-to-End Resume + JD Parse & Match | **$\le 5.0$ seconds** (async notification) |
| **Frontend Performance**| Lighthouse Performance & Accessibility | **$\ge 95$ Accessibility (WCAG AA)**, **$\ge 90$ Perf** |
| **User Agency** | Suggestion Review & Approval Rate | **100%** of generated changes require explicit user acceptance |
