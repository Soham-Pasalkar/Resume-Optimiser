# CareerPilot 2.0 — AI-Powered Career Intelligence Platform

> **Analyze a job. Understand your gaps. Build a better resume. Prepare for the opportunity.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Next.js: 15](https://img.shields.io/badge/Next.js-15-black.svg)](https://nextjs.org/)
[![Tests: 49/49 Passed](https://img.shields.io/badge/Tests-49%2F49%20Passed-success)](docs/TESTING.md)
[![Design: Soft UI Evolution](https://img.shields.io/badge/Design-Soft%20UI%20Evolution-blue)](docs/DESIGN_SYSTEM.md)
[![Cost: 100% Free Local AI](https://img.shields.io/badge/Cost-100%25%20Free%20Local-success)](docs/AI_AND_MATCHING_METHODOLOGY.md)

---

## 1. What is CareerPilot 2.0?

**CareerPilot 2.0** is an enterprise-grade, locally operated career intelligence platform. It bridges the divide between technical job seekers and hiring teams by deconstructing complex job postings into granular requirements, objectively evaluating candidate qualifications using a hybrid 5-factor scientific matching engine, and generating tailored, ATS-compliant single-column resumes bounded by strict factual preservation guardrails.

### The 5-Step Core Workflow Journey

```
MY CAREER PROFILE  ──►  JOB ANALYSIS  ──►  GAP ANALYSIS  ──►  RESUME STUDIO  ──►  ATS EXPORT
 (Raw Docs & Proof)    (Decomposed JD)   (5-Factor Match)   (Structured IR)     (PDF & DOCX)
```

1. **My Career Profile (`/candidate`):** Manage master resume documents (PDF/DOCX) and factual, evidence-anchored competencies. Extracted skills are clearly distinguished from candidate-verified competencies.
2. **Analyze a Job (`/jobs`):** Deconstruct job postings into mandatory vs. preferred criteria, experience thresholds, and taxonomy skills—for both bulleted and narrative paragraph postings.
3. **Gap Analysis (`/matches`):** Audit alignment using BM25 lexical ranking, dense vector cosine similarity, and skill ontology coverage with atomic bullet evidence snippets.
4. **Resume Studio 2.0 (`/optimizer`):** Tailor experience and project bullets targeting job requirements with structured requirement-to-evidence mappings, multi-layer factual guardrails, candidate section toggling, and 1-click restore controls.
5. **Factual Validation & ATS Export:** Multi-layer anti-hallucination guardrails guarantee zero fabricated metrics, percentages, dates, technologies, or inflated titles before exporting single-column ATS PDF or DOCX documents.

---

## 2. Core Engineering Pillars

1. **Zero Operational Cost / 100% Local AI First:**
   Operates out-of-the-box using local **Ollama** LLMs (`qwen2.5-coder:14b` or `llama3.1:8b`) with automated failover to deterministic rule engines when Ollama is offline.
2. **Strict Factual Preservation (Zero Hallucination):**
   The 5-Layer Factual Guardrail inspects technology inventory deltas, quantitative metric invariants, temporal markers, and seniority claims to guarantee that candidate resumes remain 100% truthful.
3. **Transparent Evidence Mapping:**
   Every JD requirement is mapped to candidate resume items with explicit matching methods (`ONTOLOGY_EXACT`, `DENSE_OLLAMA`, `LEXICAL_BM25_FALLBACK`, `DENSE_HASH_FALLBACK`) and candidate verification labels (`CANDIDATE_VERIFIED` vs `EXTRACTED_UNCONFIRMED`).
4. **Structured Composition IR & Source Provenance:**
   Tailored resumes are assembled into an Intermediate Representation (IR) maintaining an end-to-end audit trail from each output bullet back to the source text and candidate review choice.
5. **Soft UI Evolution Aesthetics:**
   Refined neumorphic tactile depth, subtle dual ambient shadows, inset wells, and full WCAG 2.1 Level AA color contrast compliance.

---

## 3. Technology Stack

- **Frontend:** Next.js 15.1.7 (App Router), React 19, TypeScript 5.7, Tailwind CSS, Lucide Icons.
- **Backend:** FastAPI (Python 3.11+ / 3.14), Pydantic v2, SQLAlchemy 2.0 (Async), ReportLab, python-docx, pdfplumber.
- **Persistence:** PostgreSQL 16 (production) / SQLite async (local/testing).
- **AI & Retrieval:** Local Ollama daemon (`http://localhost:11434`), Okapi BM25 (`rank-bm25`), Cosine Similarity Embedding Matcher.

---

## 4. Quick Start Guide

### Prerequisites
- Python 3.11+
- Node.js 20+ and npm
- (Optional) [Ollama](https://ollama.ai/) running `qwen2.5-coder:14b` or `llama3.1:8b`

### 1. Clone & Setup
```bash
git clone https://github.com/Soham-Pasalkar/Resume-Optimiser.git
cd Resume-Optimiser
git checkout feature/careerpilot-2.0
```

### 2. Run Backend
```bash
# Setup Python virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# Start FastAPI Server
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
# API live at: http://localhost:8000
# OpenAPI Docs: http://localhost:8000/docs
```

### 3. Run Frontend
```bash
cd frontend
npm install
npm run dev
# Web application live at: http://localhost:3000
```

### 4. Run Test Suite
```bash
# Run all 49 backend tests
pytest backend/tests/ -v

# Run Resume Studio tests specifically
pytest backend/tests/test_optimizer.py -v

# Run Next.js production typecheck and build
cd frontend
npm run build
```
