# CareerPilot — AI-Powered Career Intelligence Platform

> **Navigate your career. Engineer your future.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Next.js: 15](https://img.shields.io/badge/Next.js-15-black.svg)](https://nextjs.org/)
[![Design: Soft UI Evolution](https://img.shields.io/badge/Design-Soft%20UI%20Evolution-blue)](docs/DESIGN_SYSTEM.md)
[![Operational Cost: $0.00 Free](https://img.shields.io/badge/Cost-100%25%20Free%20Local-success)](docs/PROJECT_BRIEF.md)

---

## 1. What is CareerPilot?

**CareerPilot** is an enterprise-grade, research-oriented career intelligence platform. It bridges the gap between job seekers and employers by decoding complex job postings, objectively evaluating qualifications through hybrid semantic-lexical analysis, providing transparent evidence-backed skill gap assessments, optimizing resumes without factual hallucination, and generating role-targeted interview preparation.

### Sister Project Relationship: PeopleLens (Resume-Ranker)
CareerPilot is the strategic candidate-facing counterpart to [PeopleLens (Resume-Ranker)](https://github.com/Soham-Pasalkar/Resume-Ranker). While PeopleLens assists recruiters in discovering and evaluating talent pools, **CareerPilot empowers candidates to understand opportunities, highlight genuine strengths, and prepare for career progression.**

---

## 2. Core Pillars & Capabilities

1. **Zero Operational Cost / 100% Free Default:**
   Runs out-of-the-box using local **Ollama** LLMs (`llama3.1:8b`, `qwen2.5:7b`, `mistral:7b`), local Sentence Transformers embeddings, and open-source infrastructure. No paid API keys required.
2. **Bring Your Own Key (BYOK) Option:**
   Users who wish to utilize cloud providers (OpenAI, Anthropic Claude, Google Gemini, Groq) can configure optional API keys in settings.
3. **Strict Factual Preservation (Zero Hallucination):**
   Automated NLI cross-encoders (DeBERTa-v3) and quantitative entity delta checking guarantee that resume bullets are never embellished with fabricated metrics, credentials, or technologies.
4. **Hybrid Matching Engine:**
   Combines exact lexical retrieval (Okapi BM25), dense vector embeddings (BGE-Small), and hierarchical skill ontologies to produce an explainable, auditable 5-factor alignment report.
5. **Personalized Learning & Interview Intelligence:**
   Automated milestone curricula with curated documentation and real-world portfolio deliverables, plus 10 role-tailored interview questions evaluated against bar-raiser rubrics.
6. **Kanban Application Pipeline & Opportunity Comparison:**
   Track opportunities across 6 recruitment stages (`Wishlist`, `Applied`, `Screening`, `Interviewing`, `Offer`, `Archived`) with 1-click stage progression and side-by-side qualification benchmarking.
7. **Soft UI Evolution Aesthetics:**
   A refined neumorphic design language featuring subtle tactile depth, soft dual ambient shadows, inset wells, and strict WCAG 2.1 Level AA accessibility.

---

## 3. Implemented Modules Overview

| Module | Core Functionality | Status |
| :--- | :--- | :--- |
| **Module 1: Authentication & User Workspaces** | Multi-tenant auth, JWT refresh, profile management, GDPR account purge | `Operational (Passed)` |
| **Module 2: Resume Ingestion & Parsing** | PDF/DOCX ingestion with pdfplumber and OCR fallback, rule-based section segmentation | `Operational (Passed)` |
| **Module 3: JD Intelligence Engine** | Job description parsing, required vs. preferred criteria, tech extraction | `Operational (Passed)` |
| **Module 4: Candidate Intelligence Engine** | Reusable master candidate profile with verbatim evidence anchoring | `Operational (Passed)` |
| **Module 5: Hybrid Matching Engine** | Okapi BM25 + Dense Sentence Transformers + 5-factor scoring model | `Operational (Passed)` |
| **Module 6: Skill Gap Analysis** | 4-tier gap classification (`DEMONSTRATED`, `PARTIAL`, `NOT_DEMONSTRATED`, `REQUIRES_VERIFICATION`) with live verification | `Operational (Passed)` |
| **Module 7: AI Resume Optimizer** | Google XYZ formula rewriter, NLI factual guardrails, single-column ATS PDF & DOCX exporter | `Operational (Passed)` |
| **Module 8: Personalized Learning Engine** | Skill gap curriculum generator, study hours estimation, practical project briefs | `Operational (Passed)` |
| **Module 9: Interview Intelligence** | Technical, STAR behavioral, and gap-defense question bank with AI rubric evaluation | `Operational (Passed)` |
| **Module 10: Application Pipeline Tracker** | 6-stage Kanban board, stage transition audit history, multi-opportunity comparison matrix | `Operational (Passed)` |

---

## 3. Technology Stack

- **Frontend:** Next.js 15 (App Router), React 19, TypeScript, Tailwind CSS v4, Radix UI Primitives, Lucide Icons, TanStack React Query v5.
- **Backend:** FastAPI (Python 3.11+), Pydantic v2, SQLAlchemy 2.0 (Async), Alembic, Celery, Redis.
- **Persistence:** PostgreSQL 16 with native `pgvector` extension.
- **AI & NLP:** Local Ollama daemon (`http://localhost:11434`), Sentence Transformers (`BAAI/bge-small-en-v1.5`), `rank-bm25`, DeBERTa-v3 NLI cross-encoder.
- **Document Processing:** `pdfplumber`, `python-docx`, `Tesseract OCR` fallback.

---

## 4. Quick Start (Local Development)

### Prerequisites
- Python 3.11+ (`python3.11`)
- Node.js 18+ and npm (`node -v`, `npm -v`)
- [Ollama](https://ollama.ai/) installed (`ollama run llama3.1:8b`)
- PostgreSQL 16 with `pgvector` & Redis 7 (or run via Docker)

### 1. Clone Repository & Setup Environment
```bash
git clone https://github.com/Soham-Pasalkar/Resume-Optimiser.git
cd Resume-Optimiser

# Copy environment variables
cp .env.example .env
```

### 2. Automated Setup via Makefile
```bash
make setup
```

### 3. Run Backend (FastAPI)
```bash
make dev-backend
# API will be live at: http://localhost:8000
# OpenAPI Interactive Docs: http://localhost:8000/docs
```

### 4. Run Frontend (Next.js)
```bash
make dev-frontend
# Web interface will be live at: http://localhost:3000
```

### 5. (Alternative) Run Everything via Docker Compose
```bash
docker compose up -d
```

---

## 5. Architectural Documentation Index

The complete planning and research specification is available under the [`docs/`](docs/) directory:

- [Project Brief & Identity](docs/PROJECT_BRIEF.md)
- [Product Requirements Document (PRD)](docs/PRD.md)
- [System Architecture](docs/SYSTEM_ARCHITECTURE.md)
- [Frontend Design Specification (12 Pages)](docs/FRONTEND_DESIGN_SPEC.md)
- [Design System (Soft UI Evolution)](docs/DESIGN_SYSTEM.md)
- [Database Design & pgvector Schema](docs/DATABASE_DESIGN.md)
- [REST API Specification](docs/API_SPECIFICATION.md)
- [AI Research & Verification Plan](docs/AI_RESEARCH_PLAN.md)
- [Implementation Roadmap (Phases 0–8)](docs/IMPLEMENTATION_ROADMAP.md)
- [Risk Register](docs/RISK_REGISTER.md)
- [Testing & Quality Assurance Strategy](docs/TESTING_STRATEGY.md)

---

## 6. License
MIT License. Open source and free for individual career development and technical research.
