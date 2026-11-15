import json
import logging
import re
from typing import Any

from app.core.llm import ollama_client
from app.models.matching import SkillGapItem

logger = logging.getLogger(__name__)

CURATED_DOMAINS: dict[str, dict[str, Any]] = {
    "kubernetes": {
        "title": "Production Container Orchestration with Kubernetes",
        "desc": "Master Pod lifecycles, Deployments, StatefulSets, Ingress controllers, and RBAC security models.",
        "resources": [
            {
                "title": "Kubernetes Official Documentation",
                "url": "https://kubernetes.io/docs/home/",
                "type": "Documentation",
            },
            {
                "title": "Kubernetes by Example",
                "url": "https://kubernetesbyexample.com/",
                "type": "Interactive Tutorial",
            },
        ],
        "project": "Architect an automated GitOps deployment pipeline using Helm charts and ingress routing for a multi-tier web application.",
        "hours": 20,
    },
    "docker": {
        "title": "Production Containerization with Docker",
        "desc": "Build optimized multi-stage Dockerfiles, manage volume persistence, and orchestrate local multi-service topologies.",
        "resources": [
            {
                "title": "Docker Best Practices Guide",
                "url": "https://docs.docker.com/develop/develop-images/dockerfile_best-practices/",
                "type": "Documentation",
            },
            {"title": "Docker Labs", "url": "https://docker-curriculum.com/", "type": "Tutorial"},
        ],
        "project": "Create a secure, non-root, multi-stage Docker image minimizing image size by 70% with distroless base.",
        "hours": 12,
    },
    "postgresql": {
        "title": "Advanced Relational Data Modeling & Indexing in PostgreSQL",
        "desc": "Master EXPLAIN ANALYZE execution plans, B-tree/GIN indexing, transaction isolation levels, and vacuum tuning.",
        "resources": [
            {
                "title": "PostgreSQL Documentation",
                "url": "https://www.postgresql.org/docs/current/",
                "type": "Documentation",
            },
            {
                "title": "Use The Index, Luke!",
                "url": "https://use-the-index-luke.com/",
                "type": "Interactive Guide",
            },
        ],
        "project": "Design a normalized database schema with partitioning and GIN indexing handling 100,000 queries/sec with sub-5ms p99 latency.",
        "hours": 18,
    },
    "kafka": {
        "title": "Event-Driven Distributed Messaging with Apache Kafka",
        "desc": "Implement durable topic partitioning, consumer group rebalancing, and exactly-once processing semantics.",
        "resources": [
            {
                "title": "Apache Kafka Quickstart",
                "url": "https://kafka.apache.org/quickstart",
                "type": "Documentation",
            },
            {
                "title": "Confluent Kafka Architecture Guide",
                "url": "https://developer.confluent.io/",
                "type": "Tutorial",
            },
        ],
        "project": "Build an event-driven pub/sub data processing pipeline handling real-time telemetry streaming and dead-letter queues.",
        "hours": 20,
    },
    "aws": {
        "title": "Cloud Infrastructure Architecture on AWS",
        "desc": "Design resilient multi-AZ VPC topologies, IAM least-privilege policies, and auto-scaling container services on ECS/EKS.",
        "resources": [
            {
                "title": "AWS Well-Architected Framework",
                "url": "https://aws.amazon.com/architecture/well-architected/",
                "type": "Whitepaper",
            },
            {
                "title": "AWS Skill Builder",
                "url": "https://explore.skillbuilder.aws/",
                "type": "Course",
            },
        ],
        "project": "Deploy an automated Terraform configuration provisioning an isolated VPC, RDS Multi-AZ instance, and Application Load Balancer.",
        "hours": 24,
    },
}


class RoadmapGenerator:
    """Generates structured, actionable learning milestones targeting candidate skill gaps."""

    PROMPT_TEMPLATE = """You are an expert technical curriculum designer and senior software engineering mentor.
Construct a structured, professional learning roadmap to bridge the following skill gaps for the role: '{role}'.

Skill Gaps to Address:
{gaps}

Generate structured JSON with milestones:
{{
  "estimated_total_hours": 60,
  "milestones": [
    {{
      "sequence_order": 1,
      "skill_name": "string",
      "milestone_title": "string",
      "description": "string",
      "curated_resources": [
        {{"title": "string", "url": "string", "type": "Documentation | Course | Tutorial"}}
      ],
      "practical_project_brief": "string concrete portfolio deliverable"
    }}
  ]
}}
Return ONLY valid JSON.
"""

    async def generate_roadmap(
        self,
        target_role: str,
        unresolved_gaps: list[SkillGapItem],
    ) -> dict[str, Any]:
        """Generate structured milestones and concrete project briefs."""
        # 1. Try local Ollama generation
        try:
            status = await ollama_client.get_status()
            if status.is_available:
                gaps_summary = "\n".join(
                    f"- {g.requirement.requirement_text} (Category: {g.requirement.category}, Severity: {g.gap_severity})"
                    for g in unresolved_gaps[:5]
                    if g.requirement
                )
                prompt = self.PROMPT_TEMPLATE.format(role=target_role, gaps=gaps_summary)
                resp = await ollama_client.generate(
                    prompt=prompt,
                    system_prompt="You generate structured technical learning roadmaps in valid JSON.",
                    format_json=True,
                    temperature=0.2,
                )
                raw_json = resp.get("response", "").strip()
                if raw_json.startswith("```"):
                    raw_json = re.sub(r"^```(?:json)?", "", raw_json).strip()
                    raw_json = re.sub(r"```$", "", raw_json).strip()

                parsed = json.loads(raw_json)
                if parsed.get("milestones"):
                    return parsed
        except Exception as exc:
            logger.warning(
                "Ollama roadmap generation unavailable (%s). Using curated curriculum fallback.",
                exc,
            )

        # 2. Curated Blueprint Fallback
        return self._generate_curated_fallback(target_role, unresolved_gaps)

    def _generate_curated_fallback(
        self,
        target_role: str,
        unresolved_gaps: list[SkillGapItem],
    ) -> dict[str, Any]:
        milestones = []
        total_hours = 0
        order = 1

        # Sort gaps: CRITICAL first, then MODERATE, then LOW
        priority_order = {"CRITICAL": 0, "MODERATE": 1, "LOW": 2}
        sorted_gaps = sorted(
            unresolved_gaps,
            key=lambda g: priority_order.get(g.gap_severity, 3),
        )

        for gap in sorted_gaps[:4]:
            req = gap.requirement
            if not req:
                continue

            skill_key = (req.canonical_skill_name or req.requirement_text).lower()
            matched_blueprint = None

            for key, bp in CURATED_DOMAINS.items():
                if key in skill_key:
                    matched_blueprint = (key.title(), bp)
                    break

            if matched_blueprint:
                name, bp = matched_blueprint
                milestones.append(
                    {
                        "sequence_order": order,
                        "skill_name": name,
                        "milestone_title": bp["title"],
                        "description": bp["desc"],
                        "curated_resources": bp["resources"],
                        "practical_project_brief": bp["project"],
                    }
                )
                total_hours += bp["hours"]
            else:
                skill_name = req.canonical_skill_name or req.requirement_text[:30]
                milestones.append(
                    {
                        "sequence_order": order,
                        "skill_name": skill_name,
                        "milestone_title": f"Production Implementation & Mastery of {skill_name}",
                        "description": f"Master the core operational principles, best practices, and integration patterns for {skill_name} as required for the {target_role} role.",
                        "curated_resources": [
                            {
                                "title": f"{skill_name} Official Reference",
                                "url": "https://devdocs.io/",
                                "type": "Documentation",
                            },
                            {
                                "title": "Production Engineering Best Practices",
                                "url": "https://github.com/donnemartin/system-design-primer",
                                "type": "Architecture Guide",
                            },
                        ],
                        "practical_project_brief": f"Build a production-ready reference service demonstrating {skill_name} integration with automated test coverage and health check endpoints.",
                    }
                )
                total_hours += 15

            order += 1

        if not milestones:
            milestones.append(
                {
                    "sequence_order": 1,
                    "skill_name": "System Design & Architecture",
                    "milestone_title": f"High-Scale Architecture for {target_role}",
                    "description": "Learn scalable distributed patterns, asynchronous event streaming, and resilient caching.",
                    "curated_resources": [
                        {
                            "title": "The System Design Primer",
                            "url": "https://github.com/donnemartin/system-design-primer",
                            "type": "Guide",
                        },
                    ],
                    "practical_project_brief": "Design and document an end-to-end distributed system handling 10M daily active requests with caching and disaster recovery.",
                }
            )
            total_hours = 20

        return {
            "estimated_total_hours": total_hours,
            "milestones": milestones,
        }


# Global generator instance
roadmap_generator = RoadmapGenerator()
