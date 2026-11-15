import json
import logging
import re
from typing import Any

from app.core.llm import ollama_client
from app.models.matching import MatchEvaluation

logger = logging.getLogger(__name__)


class InterviewPromptGenerator:
    """Generates role-tailored technical, STAR behavioral, and gap-defense interview questions."""

    PROMPT_TEMPLATE = """You are a Principal Engineering Director and bar-raiser interviewer.
Generate 10 structured, rigorous interview questions for the role: '{role}' at '{company}'.

Candidate Background & Match Context:
Match Score: {score}/100
Demonstrated Strengths: {strengths}
Identified Gaps: {gaps}

Generate structured JSON with exactly 10 questions:
- 4 'TECHNICAL' deep-dive questions probing architecture and edge cases.
- 3 'BEHAVIORAL_STAR' questions testing leadership, technical disagreements, and cross-functional impact.
- 3 'GAP_DEFENSE' questions probing the identified gaps to test candidate adaptability.

Schema:
{{
  "questions": [
    {{
      "question_type": "TECHNICAL | BEHAVIORAL_STAR | GAP_DEFENSE",
      "question_text": "string",
      "target_skill_or_gap": "string or null",
      "evaluation_criteria": "string what excellent answers must demonstrate",
      "star_guidelines": {{
        "situation": "string",
        "task": "string",
        "action": "string",
        "result": "string"
      }}
    }}
  ]
}}
Return ONLY valid JSON.
"""

    async def generate_questions(
        self,
        match_eval: MatchEvaluation,
    ) -> list[dict[str, Any]]:
        target_role = (
            match_eval.job_description.job_title
            if match_eval.job_description
            else "Software Engineer"
        )
        company = match_eval.job_description.company_name or "Target Company"

        # 1. Try local Ollama generation
        try:
            status = await ollama_client.get_status()
            if status.is_available:
                strengths = ", ".join(
                    g.requirement.canonical_skill_name or g.requirement.requirement_text[:30]
                    for g in match_eval.gap_items
                    if g.status == "DEMONSTRATED" and g.requirement
                )[:200]
                gaps = ", ".join(
                    g.requirement.canonical_skill_name or g.requirement.requirement_text[:30]
                    for g in match_eval.gap_items
                    if g.status != "DEMONSTRATED" and g.requirement
                )[:200]

                prompt = self.PROMPT_TEMPLATE.format(
                    role=target_role,
                    company=company,
                    score=match_eval.overall_score,
                    strengths=strengths or "General backend engineering",
                    gaps=gaps or "Cloud-native infrastructure",
                )
                resp = await ollama_client.generate(
                    prompt=prompt,
                    system_prompt="You generate structured technical and behavioral interview questions in valid JSON.",
                    format_json=True,
                    temperature=0.3,
                )
                raw_json = resp.get("response", "").strip()
                if raw_json.startswith("```"):
                    raw_json = re.sub(r"^```(?:json)?", "", raw_json).strip()
                    raw_json = re.sub(r"```$", "", raw_json).strip()

                parsed = json.loads(raw_json)
                questions = parsed.get("questions", [])
                if len(questions) >= 5:
                    return questions
        except Exception as exc:
            logger.warning(
                "Ollama interview generator unavailable (%s). Using curated question templates.",
                exc,
            )

        # 2. Curated Blueprint Fallback
        return self._generate_curated_fallback(match_eval, target_role, company)

    def _generate_curated_fallback(
        self,
        match_eval: MatchEvaluation,
        target_role: str,
        company: str,
    ) -> list[dict[str, Any]]:
        questions = []

        # Find demonstrated vs gap skills
        demonstrated = [
            g.requirement.canonical_skill_name or g.requirement.requirement_text[:30]
            for g in match_eval.gap_items
            if g.status == "DEMONSTRATED" and g.requirement
        ]
        gaps = [
            g.requirement.canonical_skill_name or g.requirement.requirement_text[:30]
            for g in match_eval.gap_items
            if g.status != "DEMONSTRATED" and g.requirement
        ]

        top_strength = demonstrated[0] if demonstrated else "backend architecture"
        top_gap = gaps[0] if gaps else "distributed systems scaling"

        # Technical Questions (4)
        questions.append(
            {
                "question_type": "TECHNICAL",
                "question_text": f"How would you design a low-latency, highly available microservices architecture for {target_role} leveraging {top_strength}?",
                "target_skill_or_gap": top_strength,
                "evaluation_criteria": "Demonstrates clear understanding of trade-offs, horizontal scaling, database connection pooling, and circuit breaker patterns.",
                "star_guidelines": {
                    "situation": "Complex distributed architecture requirement",
                    "task": "Maintain sub-50ms latency under high request concurrency",
                    "action": "Decouple services, apply caching, configure asynchronous worker queues",
                    "result": "Zero downtime with resilient graceful degradation",
                },
            }
        )
        questions.append(
            {
                "question_type": "TECHNICAL",
                "question_text": "Walk me through how you troubleshoot and optimize a database query that is causing a CPU spike in production.",
                "target_skill_or_gap": "Database Optimization",
                "evaluation_criteria": "Mentions EXPLAIN plans, index inspection, query plan caching, connection limits, and lock contention.",
                "star_guidelines": {
                    "situation": "Critical p99 latency degradation on production database",
                    "task": "Isolate slow queries without restarting the database cluster",
                    "action": "Analyzed slow query logs, identified missing composite index, deployed migration",
                    "result": "Reduced query execution time from 1.8s to 12ms",
                },
            }
        )
        questions.append(
            {
                "question_type": "TECHNICAL",
                "question_text": "How do you handle idempotency and data consistency in asynchronous event-driven architectures?",
                "target_skill_or_gap": "Asynchronous Systems",
                "evaluation_criteria": "Covers outbox pattern, unique idempotency keys, dead-letter queues, and at-least-once delivery semantics.",
                "star_guidelines": {
                    "situation": "Event duplication causing double billing in payment pipeline",
                    "task": "Enforce strict deduplication and transaction atomicity",
                    "action": "Implemented idempotency keys in Redis with transactional outbox in PostgreSQL",
                    "result": "Eliminated duplicate transactions completely",
                },
            }
        )
        questions.append(
            {
                "question_type": "TECHNICAL",
                "question_text": f"What strategies would you apply to ensure zero-downtime deployments for services built for {company}?",
                "target_skill_or_gap": "DevOps & Reliability",
                "evaluation_criteria": "Discusses blue/green deployments, canary releases, backward-compatible database schema migrations, and health checks.",
                "star_guidelines": {
                    "situation": "High-risk breaking API version rollout",
                    "task": "Deploy updates without dropping active user connections",
                    "action": "Configured rolling updates with readiness probes and expanded-contract database changes",
                    "result": "Zero dropped requests across 1M daily sessions",
                },
            }
        )

        # Behavioral Questions (3)
        questions.append(
            {
                "question_type": "BEHAVIORAL_STAR",
                "question_text": "Tell me about a time you had a strong technical disagreement with a team member or tech lead. How did you resolve it?",
                "target_skill_or_gap": "Technical Leadership & Collaboration",
                "evaluation_criteria": "Objective benchmarking, data-driven compromise, ego-free communication, and committing to the final team decision.",
                "star_guidelines": {
                    "situation": "Disagreement over choosing REST vs gRPC for internal service communications",
                    "task": "Align on an architecture that met team delivery speed and latency SLAs",
                    "action": "Built quick proof-of-concept benchmarks and evaluated operational complexity with team",
                    "result": "Agreed on pragmatic path; team hit launch deadline 2 weeks ahead of schedule",
                },
            }
        )
        questions.append(
            {
                "question_type": "BEHAVIORAL_STAR",
                "question_text": "Describe a scenario where a critical production outage occurred under your watch. How did you diagnose, resolve, and follow up?",
                "target_skill_or_gap": "Incident Management & Ownership",
                "evaluation_criteria": "Decisive incident response, clear stakeholder communication, blameless post-mortem, and permanent automated prevention.",
                "star_guidelines": {
                    "situation": "Authentication service unresponsive during morning traffic peak",
                    "task": "Restore service availability rapidly and identify root cause",
                    "action": "Rolled back bad deploy, scaled connection pool, authored comprehensive post-mortem",
                    "result": "Service restored in 7 minutes; added canary gating to prevent recurrence",
                },
            }
        )
        questions.append(
            {
                "question_type": "BEHAVIORAL_STAR",
                "question_text": "Give an example of a project where you had to deliver under ambiguous or rapidly changing requirements.",
                "target_skill_or_gap": "Adaptability & Execution",
                "evaluation_criteria": "Proactive requirement scoping, modular architecture, and incremental iterative delivery.",
                "star_guidelines": {
                    "situation": "Product specifications shifting weekly during prototype phase",
                    "task": "Deliver core functional MVP on an aggressive 4-week deadline",
                    "action": "Modularized core domain boundaries and established bi-weekly milestone syncs",
                    "result": "Shipped MVP on schedule, onboarded first 50 enterprise pilots",
                },
            }
        )

        # Gap-Defense Questions (3)
        questions.append(
            {
                "question_type": "GAP_DEFENSE",
                "question_text": f"Your background showcases strong expertise in {top_strength}, but this position specifically requires {top_gap}. How will you ramp up and contribute immediately?",
                "target_skill_or_gap": top_gap,
                "evaluation_criteria": "Humility, rapid self-directed learning history, transferring foundational conceptual knowledge, and proactive initiative.",
                "star_guidelines": {
                    "situation": "Candidate's resume shows strong adjacent experience but no direct commercial evidence for top gap",
                    "task": "Convince the interviewer of capability to reach high velocity rapidly",
                    "action": "Cite prior fast ramp-ups; draw direct conceptual parallels to familiar paradigms",
                    "result": "Demonstrates high learning agility and low hiring risk",
                },
            }
        )
        second_gap = gaps[1] if len(gaps) > 1 else "cloud infrastructure automation"
        questions.append(
            {
                "question_type": "GAP_DEFENSE",
                "question_text": f"If tasked with architecting a solution using {second_gap} on day one, what would be your 30-day execution and onboarding plan?",
                "target_skill_or_gap": second_gap,
                "evaluation_criteria": "Structured onboarding strategy: codebase inspection, shadow deployments, building small non-critical features first.",
                "star_guidelines": {
                    "situation": "Immediate project assignment involving an unfamiliar framework",
                    "task": "Deliver productive code contributions without slowing down senior team members",
                    "action": "Map system architecture, build isolated test harness, consult official RFCs and documentation",
                    "result": "Ship first pull request in week 2; independent ownership by day 30",
                },
            }
        )
        questions.append(
            {
                "question_type": "GAP_DEFENSE",
                "question_text": f"Why is this {target_role} role at {company} the right strategic move for your career, and how will you overcome your experience gaps?",
                "target_skill_or_gap": "Role Motivation & Gap Ownership",
                "evaluation_criteria": "Authentic enthusiasm, deep research into the company's product, and honest self-awareness about growth areas.",
                "star_guidelines": {
                    "situation": "Probing candidate intent and long-term retention",
                    "task": "Articulate alignment with company mission and personal career trajectory",
                    "action": "Connected past successes to company's current scaling challenges",
                    "result": "Inspires high hiring confidence in candidate maturity and drive",
                },
            }
        )

        return questions


# Global generator instance
interview_prompt_generator = InterviewPromptGenerator()
