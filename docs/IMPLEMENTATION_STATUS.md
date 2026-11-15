# CareerPilot 2.0 Implementation Status & Defect Resolution Matrix

## 1. Defect Resolution Summary

| Defect ID | Defect Description | Root Cause in Legacy Code | CareerPilot 2.0 Solution | Status |
| :--- | :--- | :--- | :--- | :---: |
| **Defect A** | Enormous resume sections attached as evidence to skill gaps | Entire raw multi-line section text was appended to `resume_chunks`. Fallback dense hash vectors had high similarity to long text blocks. | Chunking now strictly operates on discrete atomic bullets and lines. Introduced a strict relevance cutoff ($\text{sim} \ge 0.48$); otherwise returns honest `None`. | **RESOLVED** |
| **Defect B** | Extracted skills marked as candidate-verified | `scorer.py` emitted "Verified alignment" even when `is_user_verified` was `False`. | Distinct statuses: "Candidate-verified alignment" ($1.0$) vs "Extracted from resume evidence (candidate confirmation recommended)" ($0.90$). | **RESOLVED** |
| **Defect C** | Generic requirement extraction on narrative/paragraph JDs | Non-bullet JDs defaulted to synthetic `Demonstrated proficiency in {skill}`. | Implemented sentence boundary decomposition on paragraph JDs, extracting real requirements, responsibilities, and experience thresholds. | **RESOLVED** |
| **Defect D** | Insignificant resume rewrites & candidate name from filename | Bullets assigned to requirements via modulo round-robin (`req_idx % len(req_cycle)`). Candidate name parsed from raw file name (`Resume Final V2`). | Bullets mapped to requirements via semantic & lexical similarity. Candidate name & contact retrieved from `User.full_name` & `UserProfile`. | **RESOLVED** |
| **Defect E** | Disconnected workflow handoffs | User had to navigate manually between modules and re-select dropdowns from scratch. | Added guided workflow journeys: Job $\to$ Gap Analysis (`/matches?jd_id=...`) $\to$ Resume Studio (`/optimizer?match_id=...&jd_id=...&resume_id=...`). | **RESOLVED** |
| **Defect F** | Generic learning milestones with placeholder URLs | Only 5 skills curated; uncurated skills generated identical fallback milestones with `devdocs.io`. | Expanded curated blueprints to 15+ modern technologies; dynamic fallback derives targeted portfolio deliverables directly from requirement texts. | **RESOLVED** |
| **Defect G** | Fabricated candidate stories in STAR interview answers | Behavioral questions fabricated fake past stories ("Disagreement over REST vs gRPC..."). | Replaced fabricated stories with authentic candidate answering guidelines and interviewer evaluation rubrics. | **RESOLVED** |
| **Defect H** | Technical navigation labels without guidance | Sidebar navigation used technical jargon without clear user goal alignment. | Restructured sidebar and overview page into user-goal-oriented sections: Workspace, Career Development, Settings. | **RESOLVED** |
| **Defect I (M11)** | Superficial bullet rewrites & forced XYZ on non-metric bullets | Rewriter forced artificial metrics into non-metric bullets or made generic transformations. | Multi-layer factual guardrail (entity, metric, temporal, seniority); context-aware rewriter preserving facts; full candidate controls (Accept, Reject, Edit, Restore Original). | **RESOLVED** |
| **Defect J (M11)** | Lack of transparent requirement-to-evidence mapping | Unclear why a bullet was tailored or what job requirement it addressed. | Structured requirement-to-evidence matrix with explicit matching methods (`ONTOLOGY_EXACT`, `DENSE_OLLAMA`, `LEXICAL_BM25_FALLBACK`, `DENSE_HASH_FALLBACK`) and verification labels. | **RESOLVED** |

---

## 2. Functional Module Delivery Status

- **Module 1 (Authentication & Multi-Tenant Isolation):** Operational. 10/10 tests passing.
- **Module 2 (Resume Ingestion & Section Segmentation):** Operational. 10/10 tests passing.
- **Module 3 (JD Intelligence Engine):** Operational. 5/5 tests passing.
- **Module 4 (Candidate Intelligence & Profile):** Operational. 5/5 tests passing.
- **Module 5 & 6 (Hybrid Matching & Skill Gap Analysis):** Operational. 4/4 tests passing.
- **Module 7 & 11 (Resume Studio 2.0 Engineering Upgrade):** Operational. 7/7 dedicated tests passing (49/49 total backend tests passing).
  - *M11.1 Content Intelligence & Selection:* Section decomposition, prioritization, missing gap detection.
  - *M11.2 Requirement-to-Evidence Mapping:* Structured matrix with transparent fallback labeling.
  - *M11.3 Context-Aware Rewriter:* Strong action verbs, technical contribution, zero AI jargon.
  - *M11.4 5-Layer Factual Guardrail:* Entity, metric, temporal, and seniority preservation with standardized review statuses (`VERIFIED`, `FLAGGED`, `REQUIRES_REVIEW`, `NOT_VERIFIED`).
  - *M11.5 Resume Composition Engine:* Structured Composition IR, source-to-output provenance, section reordering and 1-click restore.
  - *M11.6 Interactive Frontend:* Target role context, matrix explorer, section toggles, telemetry, live ATS canvas.
  - *M11.7 ATS Exporters:* Single-column PDF & DOCX generation, orphan header prevention, Unicode normalization, pre-export validation.
- **Module 8 (Personalized Learning Roadmaps):** Operational. 4/4 tests passing.
- **Module 9 (Interview Preparation & Rubric Evaluation):** Operational. 4/4 tests passing.
- **Module 10 (Job Application Pipeline):** Operational. 2/2 tests passing.
- **Module E2E (End-to-End Pipeline Journey):** Operational. 1/1 test passing.
- **CI Workflow (.github/workflows/ci.yml):** Strict linting, typechecking, Next.js build verification, and test execution with no `|| true` suppressions.
