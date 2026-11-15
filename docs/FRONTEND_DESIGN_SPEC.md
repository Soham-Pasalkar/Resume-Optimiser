# CareerPilot — Frontend Design Specification
## Complete 12-Interface Page-by-Page Specifications

> **Document Version:** 1.0.0-PROPOSAL  
> **Status:** Review Ready  
> **Aesthetic Language:** Soft UI Evolution  
> **Primary Canvas:** `#F0F4F8` | **Dual Shadows:** `-6px -6px 15px #FFFFFF, 6px 6px 15px #D1D9E6`

---

## 1. Global Layout & Shell Architecture

The authenticated application is wrapped in a responsive **Soft UI Master Shell**:
- **Desktop Layout:** Fixed left navigation sidebar (260px width) sculpted in `.surface` elevation, sticky top header (64px height) with workspace breadcrumbs, notification pill, and user avatar button, and a central scrollable content stage with fluid padding (`px-8 py-6`).
- **Mobile Layout:** Collapsible top app bar with mobile hamburger drawer, sticky bottom navigation bar with 4 primary icons (`Dashboard`, `Matches`, `Editor`, `Tracker`).
- **Visual Rhythm:** 24px (1.5rem) standard gutter between cards; strictly 1-level nesting (`.surface > .well`).

```
+-----------------------------------------------------------------------------------+
|  [Logo] CareerPilot        | Breadcrumbs: Applications > Senior Backend    [User] |
+----------------------------+------------------------------------------------------+
|  Sidebar (260px)           |  Central Application Canvas                          |
|  - Dashboard               |  (Fluid container, max-w-7xl mx-auto)                |
|  - Master Profile          |                                                      |
|  - Job Analyzer            |  [Page Content Area: Soft Surfaces & Inset Wells]    |
|  - Match Reports           |                                                      |
|  - Resume Optimizer        |                                                      |
|  - Learning Roadmaps       |                                                      |
|  - Interview Prep          |                                                      |
|  - Application Pipeline    |                                                      |
|  - Settings                |                                                      |
+----------------------------+------------------------------------------------------+
```

---

## 2. Page Specifications (1 through 12)

---

### PAGE 1: Marketing Landing Page

#### 1.1 Purpose & Value Proposition
Welcomes prospective candidates, establishes instant credibility through enterprise aesthetic refinement, explains the hybrid matching philosophy, and converts visitors into registered users.

#### 1.2 Layout & Information Hierarchy
- **Header:** Tactile navigation bar with Logo, Features, Methodology (PeopleLens sister project context), Pricing, and Soft Buttons (`Sign In`, `Get Started Free`).
- **Hero Section:**
  - High-impact headline: *"Navigate your career. Engineer your future."*
  - Supporting copy emphasizing zero-hallucination factual optimization and hybrid semantic-lexical matching.
  - Interactive Preview Widget: A dynamic interactive demo card showing a before/after resume bullet transformation with an explainable match score gauge.
  - Dual CTAs: `.btn-primary` ("Analyze Your Resume Free") and `.btn-soft` ("Explore Research Methodology").
- **Social Proof & Metrics Bar:** Inset well bar with metrics: *"0% Hallucination Guarantee"*, *"94% Interview Callback Increase"*, *"100% User Review Control"*.
- **Feature Deep Dive:** 4 feature cards in `.surface` styling showcasing:
  1. *JD Requirement Decomposition* (Separating mandatory from wishlist).
  2. *Hybrid Matching Engine* (BM25 + Dense Vectors + Skill Taxonomy).
  3. *Fact-Preserving Resume Optimizer* (Google XYZ bullet reframing).
  4. *Personalized Skill Roadmaps & Interview Prep*.
- **Interactive Methodology Explainer:** Tabbed section comparing crude keyword matching vs CareerPilot's evidence-grounded evaluation.
- **Footer:** Links, privacy declaration, security badges, and theme toggle.

#### 1.3 State Specifications
- **Loading:** SSR initial render; instant hydration.
- **Interactive:** Hero demo card allows toggling between "Raw Resume Bullet" and "CareerPilot Optimized".

---

### PAGE 2: Authentication Pages (Login, Register, Forgot Password)

#### 2.1 Layout & Components
- **Container:** Centered 440px wide `.surface` modal card on a `#F0F4F8` canvas.
- **Header:** Tactile CareerPilot compass logo mark, clear heading (`Welcome back` / `Create your career workspace`), and subtitle.
- **Form Controls:**
  - Email and Password inputs wrapped in `.input-well` with accessible labels.
  - Password visibility toggle with accessible ARIA labels.
  - "Remember me" custom soft checkbox.
  - Primary Action Button: `.btn-primary` ("Sign In" / "Create Account").
- **Social Auth Divider:** Fine hairline divider with "Or continue with".
- **OAuth Buttons:** Soft square icon buttons for Google and GitHub.

#### 2.2 Error & Loading States
- **Error State:** Inset alert well with `--soft-orange` accent border, alert icon, and clear corrective copy.
- **Loading State:** Button displays an accessible spinner and disables double-submission.

---

### PAGE 3: Main Dashboard (Candidate Command Center)

#### 3.1 Purpose & Layout
Provides a centralized overview of active job applications, master resume health, average role alignment score, and immediate action items.

#### 3.2 Layout & Components
- **Top Metric Cards Row (4 Columns):**
  1. *Master Profile Strength* (Radial progress indicator, 88% complete).
  2. *Active Applications* (Total count, active interview count).
  3. *Average Target Match* (78.4% alignment across tracked roles).
  4. *Identified Skill Gaps* (Count of high-priority addressable gaps).
- **Primary Stage (2-Column Grid 8/4):**
  - **Left (Col 8): Active Application Pipeline:** Quick-view Kanban preview of recently modified applications with company logo, job title, match score badge, and quick action buttons (`View Match`, `Optimize Resume`).
  - **Right (Col 4): Intelligence & Action Center:**
    - *Top Recommended Learning Action:* 1-click shortcut to high-impact gap milestone.
    - *Upcoming Interview Prep:* Practice scenario for next scheduled interview.
    - *Master Profile Quick Update:* Button to add newly verified skills.

#### 3.3 Empty State
- For new users: Shows a welcoming `.surface` card with an illustrated 3-step onboarding checklist:
  1. `[Upload Master Resume]` $\rightarrow$ 2. `[Paste Target Job Description]` $\rightarrow$ 3. `[Generate Match Strategy]`.

---

### PAGE 4: Resume Upload & Parsing Workspace

#### 4.1 Purpose & Layout
Enables candidates to upload their existing resume (PDF/DOCX), monitor the real-time extraction pipeline, and inspect/correct parsed resume sections.

#### 4.2 Layout & Components
- **Split-Screen Layout (6/6):**
  - **Left Pane: Upload & Source Viewer:**
    - Tactile Drag-and-Drop Zone: Inset `.well` with dashed soft border, upload icon, and format pills (`PDF`, `DOCX`, max 10MB).
    - Upon upload: Replaces dropzone with a high-fidelity PDF page previewer with zoom and page controls.
  - **Right Pane: Parsed Section Review:**
    - Accordion card stack representing detected sections:
      - `Personal Information` (Name, Email, Phone, Links).
      - `Professional Summary`.
      - `Work Experience` (Company, Role, Dates, Bullets).
      - `Education`.
      - `Technical Skills` (Normalized chip tags).
      - `Projects`.
    - Each section item includes an inline "Edit" button to correct any OCR/parsing anomalies before committing to the Master Profile.
- **Footer Action Bar:** Sticky bar with "Save & Update Master Profile" (`.btn-primary`) and "Discard".

#### 4.3 Loading State
- Interactive neumorphic pulsing skeleton showing extraction stages: *Reading Document $\rightarrow$ Segmenting Sections $\rightarrow$ Extracting Competencies*.

---

### PAGE 5: Job Description Analysis Workspace

#### 5.1 Purpose & Layout
Allows candidates to ingest target job descriptions via pasting or document upload, displaying an instant taxonomy breakdown of what the employer actually expects.

#### 5.2 Layout & Components
- **Top Input Bar:** Segmented control to choose `[Paste Plain Text]` or `[Upload JD Document (PDF/DOCX)]`.
- **Input Well:** Expansive text area in `.well` styling with character count and "Analyze Job Description" action button.
- **Analysis Results View (Triggered after processing):**
  - **Metadata Card:** Normalized Job Title, Company, Seniority Level, Work Mode.
  - **Decomposed Requirement Taxonomy (3 Columns):**
    1. *Mandatory Core Competencies (Must-Haves):* Weighted badges with explicit years of experience requirements.
    2. *Preferred & Bonus Qualifications (Nice-to-Haves):* Secondary skill tags.
    3. *Implicit Methodologies & Domain Knowledge:* Extracted soft skills and architectural expectations.
  - Action Button: *"Run Match Against My Profile"* (`.btn-primary`).

---

### PAGE 6: Candidate-Role Match Report

#### 6.1 Purpose & Layout
The flagship analytical view: presents a multi-dimensional, explainable alignment score between the candidate's master profile and the target role.

#### 6.2 Layout & Components
- **Hero Alignment Banner:**
  - Left: Neumorphic radial gauge showing Overall Match Score (e.g., `82% - Strong Match`).
  - Right: Executive Alignment Summary explaining strengths and priority gaps in natural language.
- **Multi-Factor Score Breakdown (5 Horizontal Meter Bars):**
  1. *Core Technical Skills Overlap* (88%)
  2. *Dense Semantic Alignment* (80%)
  3. *Lexical Keyword Alignment (BM25)* (74%)
  4. *Seniority & Experience Depth* (90%)
  5. *Domain & Project Relevance* (76%)
- **Evidence-Grounded Alignment Table:**
  - Table of JD requirements alongside matching candidate resume evidence.
  - Clicking any requirement opens a slide-over **Evidence Drawer** showing the exact source snippet, similarity score, and why the match was made.
- **Action Strip:** Direct links to `[View Skill Gaps]`, `[Tailor Resume for this Role]`, and `[Practice Interview]`.

---

### PAGE 7: Skill Gap Analysis

#### 7.1 Purpose & Layout
Categorizes requirements into four actionable buckets and empowers candidates to verify unmentioned capabilities or formulate learning strategies.

#### 7.2 Layout & Components
- **Filter Tabs:** `All Requirements (18)`, `Demonstrated (11)`, `Partially Demonstrated (3)`, `Skill Gaps (4)`, `Needs Verification (2)`.
- **Card Grid:**
  - Each requirement rendered as a distinct `.surface` card:
    - Requirement name, category, and importance badge (`Mandatory` vs `Preferred`).
    - Status Chip: `[✓ Demonstrated]`, `[~ Partial]`, `[! Missing]`, `[? Verify]`.
    - Detailed Rationale: Explanation of what the JD requires and what the resume contains.
    - Contextual Action:
      - For Missing: *"Add to Learning Roadmap"* or *"I actually know this (Verify)"*.
      - For Partial: *"Strengthen bullet in Resume Editor"*.
- **Quick-Verification Modal:**
  - Triggered when candidate clicks "I know this":
  - Modal prompt: *"Where did you use [Tool X] and for how long?"*
  - Inset input field $\rightarrow$ saves directly to candidate profile and instantly recalculates match score.

---

### PAGE 8: Resume Editor & Live ATS Preview

#### 8.1 Purpose & Layout
The central optimization workspace: displays side-by-side comparison of original vs role-tailored resume bullets with strict factual preservation, interactive diff approval, and live ATS preview.

#### 8.2 Layout & Components
- **Two-Pane Split Screen (50/50 Layout):**
  - **Left Pane: Tailoring & Diff Review:**
    - Role selector dropdown: Active target JD.
    - Interactive Bullet Diff Cards:
      - Red strikethrough for replaced passive phrasing.
      - Green highlight for optimized active framing (Google XYZ format).
      - Rationale tooltip: *"Highlights query optimization metric aligned with JD Requirement #3"*.
      - Individual Actions: `[Accept]`, `[Reject]`, `[Edit Manually]`.
      - Factual Integrity Badge: `[100% Factually Grounded - Zero Hallucinations]`.
  - **Right Pane: Live ATS Document Preview:**
    - Real-time rendered document canvas mimicking high-grade single-column ATS resume.
    - Instant live update as diffs are accepted or rejected.
    - Export Toolbar: `[Download ATS PDF]` and `[Download DOCX]`.

---

### PAGE 9: Personalized Learning Roadmap

#### 9.1 Purpose & Layout
Converts unresolved skill gaps into a structured, chronological curriculum with measurable milestones and concrete portfolio deliverables.

#### 9.2 Layout & Components
- **Header:** Estimated time-to-readiness banner (e.g., *"Target Role Readiness: 3-4 weeks with 6 hours/week"*).
- **Interactive Roadmap Timeline (Vertical Stepper):**
  - **Milestone 1 (Week 1): Fundamentals & Core Syntax:**
    - Key learning outcomes, curated documentation links.
  - **Milestone 2 (Week 2): Architecture & Best Practices:**
    - Hands-on exercises and system design considerations.
  - **Milestone 3 (Week 3-4): Verifiable Portfolio Project:**
    - Specific project brief tailored to demonstrate the missing skill (e.g., *"Build an asynchronous Celery worker queue in Python with Redis"*).
  - Status Toggle: Candidates mark milestones as `In Progress` or `Completed` $\rightarrow$ automatically adds skill to Master Profile.

---

### PAGE 10: Interview Preparation Workspace

#### 10.1 Purpose & Layout
Generates role-specific behavioral, technical, and gap-targeted interview scenarios with structured STAR answering frameworks.

#### 10.2 Layout & Components
- **Filter Bar:** Filter questions by `All`, `Technical Deep-Dive`, `Behavioral (STAR)`, `Gap-Defense Questions`.
- **Interactive Question Cards:**
  - Question Prompt with target company context.
  - Expandable Answering Guide:
    - *What the interviewer is evaluating*.
    - *Recommended STAR Structure (Situation, Task, Action, Result)*.
    - *Key technical concepts to mention*.
    - *Common red flags / pitfalls to avoid*.
- **Interactive Practice Well:**
  - Inset text area allowing candidate to type bulleted practice answers.
  - "Evaluate My Answer" button: Instant AI critique analyzing clarity, metric inclusion, and role alignment.

---

### PAGE 11: Job Application Management & Pipeline

#### 11.1 Purpose & Layout
A full Kanban and tabular pipeline management hub for tracking every job application, linked tailored resumes, and interview stages.

#### 11.2 Layout & Components
- **View Toggle:** `[Kanban Board View]` vs `[Tabular List View]`.
- **Kanban Columns:**
  1. `Bookmarked` (Target roles discovered).
  2. `Tailoring` (Match report generated, resume being customized).
  3. `Applied` (Submitted to employer with submission date).
  4. `Interviewing` (Active screening, tech round, onsite).
  5. `Offer Received` (Compensation and decision deadline).
  6. `Archived / Closed`.
- **Application Card Elements:**
  - Company name & position title.
  - Match Score Badge (e.g., `85% Match`).
  - Linked Tailored Resume version link.
  - Next scheduled action date with soft indicator pill.

---

### PAGE 12: User Settings & Master Profile Hub

#### 12.1 Purpose & Layout
Allows users to edit their permanent Master Profile, manage account credentials, configure AI model preferences, and control personal data privacy.

#### 12.2 Layout & Components
- **Vertical Navigation Tabs:** `Master Profile`, `Account & Security`, `AI Preferences`, `Data & Privacy`.
- **Master Profile Tab:** Full form editor for Work History, Education, and Skills with evidence badges.
- **AI Preferences Tab:** Configure preferred model provider (e.g., Claude 3.5 Sonnet, GPT-4o) or custom API keys if self-hosting.
- **Data & Privacy Tab:**
  - One-click `[Export All Personal Data (JSON)]`.
  - One-click `[Purge All Resumes & History]`.
  - Account Deletion trigger with double-confirmation dialog.

---

## 3. Global Loading, Skeleton & Error Design

### 3.1 Soft UI Skeleton Shimmer
Instead of harsh gray rectangles, loading skeletons utilize subtle neumorphic inset wells with a smooth wave shimmer traveling top-left to bottom-right:
```css
.skeleton-well {
  border-radius: var(--radius-md);
  background: linear-gradient(
    90deg,
    var(--soft-bg) 0%,
    rgba(255, 255, 255, 0.6) 50%,
    var(--soft-bg) 100%
  );
  background-size: 200% 100%;
  animation: shimmer 1.8s infinite ease-in-out;
  box-shadow:
    inset -2px -2px 5px var(--soft-light),
    inset  2px  2px 5px var(--soft-shadow);
}
```

### 3.2 Error Bounds & Toasts
- **Form Errors:** Inset input highlights border in `--soft-orange` with an accessible error message below the field.
- **Global Toast Notifications:** Raised tactile pills (`.surface`) appearing in top-right with an icon, message, and auto-dismiss timer.
