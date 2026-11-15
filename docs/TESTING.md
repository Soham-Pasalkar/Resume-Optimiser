# CareerPilot 2.0 Testing Strategy & Verification Suite

## 1. Test Architecture Overview

CareerPilot 2.0 maintains a dual-stack automated testing suite:

1. **Backend Testing (pytest + anyio / pytest-asyncio):**
   - 49 automated integration and unit test cases.
   - 100% passing rate with multi-tenant database isolation.
2. **Frontend Type & Build Verification (Next.js 15 + TypeScript 5.7):**
   - Strict Next.js production build compiling 15 static pages without errors or hydration mismatches.
   - Automated CI testing workflow strictly checking backend linting (Ruff), backend pytest suite, and frontend build with zero error-suppression flags (`|| true`).

---

## 2. Test Suite Breakdown

| Test File | Modules Tested | Cases | Key Verification Areas |
| :--- | :--- | :--- | :--- |
| `test_auth.py` | Module 1 | 10 | Argon2id registration, login, JWT refresh lifecycle, profile updates, multi-tenant isolation, GDPR deletion. |
| `test_resumes.py` | Module 2 | 10 | PDF/DOCX multi-format parsing, heading segmentation, section updates, tenant isolation, invalid format rejection. |
| `test_jd_and_candidate.py` | Module 3 & 4 | 5 | Skill ontology extraction, rule-based JD decomposition, narrative paragraph decomposition, candidate profile evidence anchoring. |
| `test_matching_and_gaps.py` | Module 5 & 6 | 4 | BM25 Okapi indexing, dense vector cosine similarity, 5-factor hybrid scoring, verified vs unverified gap classification. |
| `test_optimizer.py` | Module 7 & 11 | 7 | 5-layer factual guardrail (entity, metric, temporal, seniority), Content Intelligence requirement-to-evidence mapping, Composition IR & provenance, context-aware rewriter, ATS PDF/DOCX exporters, pre-export validation, restore original bullet API, and section toggling. |
| `test_career.py` | Module 8 & 9 | 4 | Curated learning roadmap blueprints, interview question generation (STAR guidelines without fake stories), rubric evaluations. |
| `test_applications.py` | Module 10 | 2 | Kanban/table application stages, activity timeline, multi-opportunity comparison. |
| `test_health.py` | System | 3 | API root `/`, health check endpoint, Ollama daemon status inspection. |
| `test_llm_config.py` | Core | 2 | LLM active model configurations and runtime parameter updates. |
| `test_e2e_journey.py` | All 10 | 1 | Complete end-to-end journey from registration through document export and GDPR account purge. |
| **TOTAL** | | **49** | **All 49 Passing** |

---

## 3. Running the Tests Locally

### Backend Test Execution

```bash
# Activate virtual environment
source venv/bin/activate

# Run all 49 backend tests
pytest backend/tests/ -v

# Run Resume Studio tests specifically
pytest backend/tests/test_optimizer.py -v

# Run Ruff linter
ruff check backend/
```

### Frontend Build & Verification

```bash
cd frontend

# Run production Next.js build (verifies types, dependencies, and all static routes)
npm run build
```
