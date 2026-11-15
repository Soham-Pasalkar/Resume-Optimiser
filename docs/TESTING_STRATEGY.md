# CareerPilot — Comprehensive Testing & Quality Assurance Strategy
## Multi-Tiered Verification, AI Benchmark & Compliance Architecture

> **Document Version:** 1.0.0-PROPOSAL  
> **Status:** Review Ready  
> **Testing Pyramid:** Unit $\rightarrow$ Integration $\rightarrow$ E2E $\rightarrow$ AI Benchmark $\rightarrow$ Accessibility & Security  
> **Lead:** Principal Software Architect & QA Lead

---

## 1. Quality Assurance Philosophy

CareerPilot verifies every software layer through an automated, multi-tiered testing pyramid. Because the system incorporates machine learning models and generative AI, conventional software tests are augmented with **deterministic AI regression harnesses**, **NLI factual verification suites**, and **automated cross-tenant security probes**.

```
                / \
               /   \
              / E2E \             Playwright (12 Interfaces)
             /-------\
            / AI Bench\           CareerBench-100, NLI Entailment, NDCG@10
           /-----------\
          / Integration \         FastAPI TestClient, Testcontainers Postgres+Redis
         /---------------\
        /   Unit Tests    \       Pytest (Backend), Vitest + RTL (Frontend)
       /-------------------\
```

---

## 2. Testing Pyramid & Tooling Suite

| Layer | Target Scope | Tooling & Framework | Execution Frequency | Target Coverage |
| :--- | :--- | :--- | :--- | :--- |
| **Unit Tests (Backend)** | Domain logic, BM25, scoring, Pydantic schemas | `pytest`, `pytest-asyncio`, `pytest-mock` | Pre-commit & CI | $\ge 90\%$ line coverage |
| **Unit Tests (Frontend)** | React components, Soft UI tokens, state | `Vitest`, `@testing-library/react` | Pre-commit & CI | $\ge 85\%$ component coverage |
| **Integration Tests** | DB queries, Celery tasks, S3/MinIO, vector queries | `pytest`, `Testcontainers` (Postgres, Redis) | Every PR build | $\ge 80\%$ integration paths |
| **AI Regression & Bench**| Benchmark evaluation, NLI guardrail, ranking | Python test harness, `CareerBench-100` | Nightly & Model updates | Hallucination rate = 0.0% |
| **End-to-End (E2E)** | Full candidate journeys across all 12 pages | `Playwright` (Chromium, Firefox, WebKit) | Nightly & Pre-release | 100% critical user paths |
| **Accessibility (a11y)** | WCAG 2.1 Level AA compliance, focus rings | `@axe-core/playwright`, `pa11y` | Every PR build | 0 critical/serious violations |
| **Security & Pen-Test** | IDOR tenant isolation, prompt injection fuzzing | Custom Pytest probe suite, `Bandit` | Weekly & Pre-release | Zero high/critical issues |
| **Performance & Load** | API throughput, concurrent document parsing | `Locust`, `k6` | Sprint boundary | $\le 200\text{ms}$ p95 for API |

---

## 3. Detailed Verification Strategies

---

### 3.1 Backend & Integration Testing (Pytest + Testcontainers)
- **Isolated Ephemeral Environments:** Database integration tests run against real PostgreSQL 16 containers with `pgvector` spawned via `testcontainers-python`.
- **Database Rollback on Each Test:** Tests execute within an isolated transaction that rolls back automatically upon completion, preventing state pollution.
- **Tenant Isolation Enforcement Suite:**
  ```python
  @pytest.mark.asyncio
  async def test_tenant_cannot_access_peer_resume(client, user_a_token, user_b_resume_id):
      """Ensure User A receives a 404 when querying User B's resume."""
      headers = {"Authorization": f"Bearer {user_a_token}"}
      response = await client.get(f"/api/v1/resumes/{user_b_resume_id}", headers=headers)
      assert response.status_code == 404
      assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"
  ```

---

### 3.2 AI Regression & Factual Integrity Testing
The AI test harness ensures that generative optimizations remain 100% factually grounded:
1. **Deterministic Scoring Assertions:** A suite of 20 golden Resume-JD pairs is evaluated on every build. Because BM25, Sentence Transformers, and ontology matching are mathematically formulated, the resulting overall match score must match golden benchmarks to within $\pm 0.001$.
2. **NLI Guardrail Unit Tests:**
   ```python
   def test_hallucinated_metric_is_rejected(nli_verifier):
       original = "Managed a team of software engineers building web apps."
       hallucinated = "Led 15 software engineers to increase company revenue by 45% ($2.1M)."
       
       result = nli_verifier.evaluate_bullet_pair(original, hallucinated)
       assert result.is_entailed is False
       assert result.classification in ["NEUTRAL", "CONTRADICTION"]
       assert "revenue" in result.unsupported_tokens
   ```
3. **Pydantic Schema Validation:** 100% of LLM extraction outputs are validated against strict Pydantic schemas; failures trigger automatic retries with structured error correction.

---

### 3.3 Frontend Component & Accessibility Testing
- **Soft UI Evolution Component Tests:**
  - Verify that buttons render with dual box shadows and transition smoothly.
  - Verify that input fields apply `.input-well` inset styling and clear error outlines.
- **Automated WCAG 2.1 AA Auditing:**
  Every page is visited via Playwright and analyzed with `axe-core`:
  ```typescript
  import { test, expect } from '@playwright/test';
  import AxeBuilder from '@axe-core/playwright';

  test('Match Report page passes WCAG AA accessibility audit', async ({ page }) => {
    await page.goto('/dashboard/matches/sample-match-id');
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa'])
      .analyze();
    expect(accessibilityScanResults.violations).toEqual([]);
  });
  ```
- **Keyboard Navigation Verification:** Automated Playwright scripts traverse all interactive elements (`Tab`, `Shift+Tab`, `Enter`, `Escape`) to verify logical focus order and visible 2px focus rings.

---

### 3.4 End-to-End (E2E) User Flow Testing
Playwright executes full multi-step workflows:
1. **Flow 1 (Registration & Ingestion):** User registers $\rightarrow$ uploads sample PDF resume $\rightarrow$ monitors parsing progress via SSE $\rightarrow$ reviews parsed sections in editor $\rightarrow$ saves to Master Profile.
2. **Flow 2 (JD Analysis & Match):** User inputs target job description $\rightarrow$ triggers hybrid match evaluation $\rightarrow$ verifies radial score gauge and multi-factor breakdown $\rightarrow$ opens slide-over evidence drawer.
3. **Flow 3 (Skill Gap Verification):** User views skill gaps $\rightarrow$ clicks "I actually know this" verification modal $\rightarrow$ enters evidence $\rightarrow$ verifies instantaneous match score update.
4. **Flow 4 (Resume Optimization & Diff Review):** User generates tailored resume $\rightarrow$ accepts 3 proposed line diffs, rejects 1, edits 1 $\rightarrow$ exports ATS-compliant PDF $\rightarrow$ verifies PDF text readability via `pdfplumber`.
5. **Flow 5 (Application Tracking):** User moves application from "Tailoring" to "Applied" on Kanban board $\rightarrow$ refreshes page $\rightarrow$ verifies state persistence.

---

### 3.5 Security & Penetration Testing
1. **Prompt Injection Resistance:** Fuzzing tests upload resumes containing prompt injection vectors (e.g. system override instructions, delimiter escapes). Test validates that system prompt rules remain inviolate and scores remain calculated purely via deterministic formulas.
2. **File Upload Security:** Upload tests submit malicious files (polyglot PDFs, executable payloads, oversized 50MB files, corrupt DOCX files). Validates that strict MIME-type sniffing, antivirus/content scanning, and file size quotas reject invalid inputs.
3. **Dependency Scanning:** Automated CI checks via `pip-audit`, `npm audit`, and GitHub Dependabot for known CVEs.

---

### 3.6 Performance & Load Testing
Using **Locust**, the system is benchmarked against defined SLAs:
- **Test Profile 1 (Interactive API):** 50 concurrent virtual users browsing dashboards, viewing match reports, and updating applications $\rightarrow$ Target: **p95 latency $< 180\text{ms}$**, 0 HTTP 5xx errors.
- **Test Profile 2 (Heavy Document Processing):** 10 concurrent virtual users uploading 5-page PDF resumes simultaneously $\rightarrow$ Target: Celery queue processes all 10 resumes within 15 seconds without starving API requests.
