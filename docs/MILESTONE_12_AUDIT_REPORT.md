# CareerPilot 2.0 — Milestone 12 Technical Audit Report

## 1. Executive Summary

This audit investigates the end-to-end data pipeline of CareerPilot 2.0 to identify the root causes of the observed application failures:
- Gap analysis identified 39 requirements for a Citi Data Engineer role, but Resume Studio reported only 1 diff (which merely added punctuation to a language list).
- Exported resumes compressed to 1 page, losing substantial experience, projects, and achievements.
- Experience and project sections lacked achievement bullets or were placed under incorrect headings.
- Absence of transparent ATS compatibility and readability scoring.
- Learning roadmaps produced generic, repetitive milestones and irrelevant search links.

This report traces the pipeline from document ingestion through export and specifies the exact engineering corrections required.

---

## 2. End-to-End Pipeline Trace & Root Cause Analysis

```
Original Resume (PDF/DOCX)
   │
   ▼
[1. File Ingestion & Storage] ─────────── (backend/app/modules/ingestion/service.py)
   │
   ▼
[2. Text Extraction (pdfplumber/docx)] ── (backend/app/modules/ingestion/extractor.py)
   │
   ▼
[3. Layout & Section Segmentation] ────── (backend/app/modules/ingestion/segmenter.py)  ◄── DEFECT 1 & 2
   │
   ▼
[4. Candidate Profile & Evidence Sync] ── (backend/app/modules/candidate/service.py)
   │
   ▼
[5. Job Description Analysis] ─────────── (backend/app/modules/jd_engine/extractor.py)
   │
   ▼
[6. Requirement-to-Evidence Mapping] ──── (backend/app/modules/optimizer/intelligence.py) ◄── DEFECT 3 & 5
   │
   ▼
[7. Resume Tailoring & Bullet Rewriter] ─ (backend/app/modules/optimizer/rewriter.py)    ◄── DEFECT 3
   │
   ▼
[8. Composition Engine & Structured IR] ─ (backend/app/modules/optimizer/composer.py)    ◄── DEFECT 4
   │
   ▼
[9. ATS Compatibility & Readability] ──── (backend/app/modules/optimizer/ats_scorer.py)  ◄── DEFECT 6 (MISSING)
   │
   ▼
[10. ATS PDF / DOCX Export] ───────────── (backend/app/modules/optimizer/exporter.py)    ◄── DEFECT 4
   │
   ▼
[11. Personalized Learning Roadmaps] ──── (backend/app/modules/learning/generator.py)    ◄── DEFECT 7
```

---

## 3. Detailed Root Causes & Proposed Corrections

### Defect 1: Silent Dropping of Non-Bulleted Experience & Project Lines
- **Affected Module:** `backend/app/modules/ingestion/segmenter.py` (`SectionSegmenter._extract_work_or_project_items`).
- **Root Cause:** When lines in experience or project sections did not start with standard bullet glyphs (`[-•*▪▸–—]`), the parsing logic fell into an `else:` branch that only accepted a second line if `len(line) < 60` and `current_org` was unset. All subsequent non-bullet lines (e.g. sentences describing architecture, achievements, and responsibilities) were silently dropped!
- **Consequence:** `ResumeItem.bullets` was left empty or had only 1 bullet per job. In the regression resume, entire paragraphs of work experience were discarded during ingestion.
- **Proposed Correction:** Re-engineer `_extract_work_or_project_items` to detect headers (title, company, dates, location) and treat all subsequent descriptive sentences as atomic achievement entries even if bullet glyphs are absent in raw text extraction.

### Defect 2: Rigid Heading Classification Omission
- **Affected Module:** `backend/app/modules/ingestion/segmenter.py` (`SectionSegmenter.SECTION_PATTERNS`).
- **Root Cause:** Only 6 hardcoded regex patterns existed (`summary`, `experience`, `education`, `skills`, `projects`, `certifications`). Common sections like `internships`, `publications`, `achievements`, `leadership`, `extracurricular`, `activities`, and `awards` were unrecognized.
- **Consequence:** Unrecognized sections defaulted to `personal_info` or merged into preceding sections, causing project and internship information to be misplaced under incorrect headings or lost.
- **Proposed Correction:** Expand `SECTION_PATTERNS` to explicitly classify `internships`, `achievements`, `publications`, `leadership`, `extracurricular`, and map related aliases.

### Defect 3: Shallow Bullet Rewriting & Single-Diff Artifact
- **Affected Module:** `backend/app/modules/optimizer/service.py` & `intelligence.py`.
- **Root Cause:** Because Defect 1 left items with 0 or 1 bullet, the rewriter loop only encountered one valid bullet (which in the regression case was a misclassified skill line). Because the rewriter had a fallback that merely capitalized and ensured a period, it generated a single trivial diff: adding a period to a list of languages.
- **Consequence:** The candidate saw 23 mapped requirements but only 1 superficial diff.
- **Proposed Correction:** Extract bullets comprehensively from all experience, project, internship, and leadership sections. Implement role-specific content prioritization and generation grounded in candidate evidence.

### Defect 4: Exporter Truncation and Incomplete Fallback
- **Affected Module:** `backend/app/modules/optimizer/exporter.py` & `composer.py`.
- **Root Cause:** The exporter logic `if not section.get("items") and section.get("raw_content"):` meant that if a section had an item with empty bullets, `raw_content` was ignored, rendering an empty title. Additionally, ReportLab document flow lacked multi-page space management, causing content clipping.
- **Consequence:** The exported resume was compressed to 1 page, losing substantial experience and project information.
- **Proposed Correction:** The Composition Engine must assemble complete sections from the structured IR. If items lack bullets, their descriptive content must be preserved and rendered. Ensure multi-page flow with proper margins and headers.

### Defect 5: Requirement-to-Evidence Classification Lacking 4-Tier Taxonomies
- **Affected Module:** `backend/app/modules/optimizer/intelligence.py`.
- **Root Cause:** The engine used binary/unconfirmed status labels (`CANDIDATE_VERIFIED` vs `EXTRACTED_UNCONFIRMED`), failing to distinguish between:
  1. `DEMONSTRATED`: Directly supported by resume evidence.
  2. `TRANSFERABLE`: Related experience supporting partial relevance.
  3. `PROFILE_LISTED`: Listed in candidate profile but unverified by experience.
  4. `MISSING`: No evidence found.
- **Proposed Correction:** Implement 4-tier evidence classification with explicit similarity thresholds and explanations.

### Defect 6: Missing Transparent ATS Compatibility & Readability Analysis
- **Affected Module:** `backend/app/modules/optimizer/` (Missing dedicated ATS evaluation service).
- **Root Cause:** CareerPilot lacked independent **Job Compatibility** and **ATS Readability** scoring engines. No text extraction was run against generated document bytes to verify machine readability.
- **Proposed Correction:** Build `ATSEvaluator` calculating:
  - Job Compatibility Score (0-100) based on demonstrated mandatory/preferred requirements and evidence strength.
  - ATS Readability Score (0-100) evaluating standard headings, contact completeness, date formats, font hierarchy, and verifying real text extraction via `pdfplumber` / `python-docx`.

### Defect 7: Repetitive & Generic Learning Roadmaps
- **Affected Module:** `backend/app/modules/learning/generator.py`.
- **Root Cause:** Only 12 hardcoded blueprints existed. All other skill gaps fell back to identical generic text pointing to MDN search URLs, even for backend/data skills. Lacked the 10 milestone elements specified in Phase F.
- **Proposed Correction:** Re-engineer roadmap generator to take role, target JD, demonstrated skills, transferable skills, missing skills, and candidate profile. Generate the 10 required milestone elements with concrete, gap-specific portfolio projects (e.g. PySpark ETL pipeline for Data Engineers) and verified technical resources. Support marking milestones complete and attaching evidence.

---

## 4. Implementation Roadmap

1. **Phase B:** Fix Ingestion & Layout Segmentation (`segmenter.py`, `service.py`, `intelligence.py`).
2. **Phase C:** Upgrade Resume Studio Intelligence & Role-Specific Content Selection (`service.py`, `rewriter.py`, `composer.py`).
3. **Phase D:** Implement Transparent ATS Scoring (`ats_scorer.py`).
4. **Phase E:** Rebuild Resume Studio Frontend (`frontend/src/app/optimizer/page.tsx`, `api.ts`).
5. **Phase F:** Personalize Learning Roadmaps & Project Completion (`generator.py`, `service.py`, `career.py`).
6. **Phase H & I:** Export Quality, Regression Prevention & End-to-End Integration Tests.
