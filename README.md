# CareerPilot 2.0 — AI-Powered Career Intelligence Platform

> **Analyze a job. Understand your gaps. Build a better resume. Prepare for the opportunity.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Next.js: 15](https://img.shields.io/badge/Next.js-15-black.svg)](https://nextjs.org/)
[![Tests: 46/46 Passed](https://img.shields.io/badge/Tests-46%2F46%20Passed-success)](docs/TESTING.md)
[![Design: Soft UI Evolution](https://img.shields.io/badge/Design-Soft%20UI%20Evolution-blue)](docs/DESIGN_SYSTEM.md)
[![Cost: 100% Free Local AI](https://img.shields.io/badge/Cost-100%25%20Free%20Local-success)](docs/AI_AND_MATCHING_METHODOLOGY.md)

---

## 1. What is CareerPilot 2.0?

**CareerPilot 2.0** is an enterprise-grade, locally operated career intelligence platform. It bridges the divide between technical job seekers and hiring teams by deconstructing complex job postings into granular requirements, objectively evaluating candidate qualifications using a hybrid 5-factor scientific matching engine, and generating tailored, ATS-compliant single-column resumes bounded by strict factual preservation guardrails.

### The 5-Step Core Workflow Journey

```
MY CAREER PROFILE  ──►  JOB ANALYSIS  ──►  GAP ANALYSIS  ──►  RESUME STUDIO  ──►  ATS EXPORT
 (Raw Docs & Proof)    (Decomposed JD)   (5-Factor Match)   (Google XYZ Diff)   (PDF & DOCX)
```

1. **My Career Profile (`/candidate`):** Manage master resume documents (PDF/DOCX) and factual, evidence-anchored competencies. Extracted skills are clearly distinguished from candidate-verified competencies.
2. **Analyze a Job (`/jobs`):** Deconstruct job postings into mandatory vs. preferred criteria, experience thresholds, and taxonomy skills—for both bulleted and narrative paragraph postings.
3. **Gap Analysis (`/matches`):** Audit alignment using BM25 lexical ranking, dense vector cosine similarity, and skill ontology coverage with atomic bullet evidence snippets.
4. **Resume Studio (`/optimizer`):** Tailor work experience and project bullets using the Google XYZ formula (`Accomplished [X] as measured by [Y] by doing [Z]`) mapped via semantic relevance to target requirements.
5. **Factual Validation & ATS Export:** Strict anti-hallucination guardrails guarantee zero fabricated metrics, percentages, dates, or technologies before exporting single-column ATS PDF or DOCX documents.

---

## 2. Core Engineering Pillars

1. **Zero Operational Cost / 100% Local AI First:**
   Operates out-of-the-box using local **Ollama** LLMs (`qwen2.5-coder:14b` or `llama3.1:8b`) with automated failover to deterministic rule engines when Ollama is offline.
2. **Strict Factual Preservation (Zero Hallucination):**
   The Syntactic & Entity Factual Guardrail inspects entity deltas, quantitative metric invariants, and calendar dates to guarantee that candidate resumes remain 100% truthful.
3. **Atomic Evidence Retrieval:**
   Only discrete item bullets and lines are indexed as evidence chunks. No unrelated multi-paragraph section text is ever attached as evidence for technical requirements.
4. **Guided Workflow Handoffs:**
   Context flows naturally across the candidate journey: Job Analysis $\to$ Gap Evaluation $\to$ Resume Studio $\to$ Interview Preparation $\to$ Application Pipeline.
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
- Node.js 18+ and npm
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
# Run all 46 backend tests
pytest backend/tests/ -v

# Run Next.js production typecheck and build
cd frontend
npm run build
```

---

## 5. Architectural Documentation

- [CareerPilot 2.0 Engineering Audit](docs/CAREERPILOT_2_0_AUDIT.md)
- [System Architecture & Data-Flow](docs/CAREERPILOT_2_0_ARCHITECTURE.md)
- [Resume Studio & Optimization Engine](docs/RESUME_OPTIMIZATION_ENGINE.md)
- [AI & Matching Methodology](docs/AI_AND_MATCHING_METHODOLOGY.md)
- [Testing & Quality Assurance Guide](docs/TESTING.md)
- [Implementation Status & Defect Matrix](docs/IMPLEMENTATION_STATUS.md)

---

## 6. License
MIT License. Open source and free for individual career development and technical research.
