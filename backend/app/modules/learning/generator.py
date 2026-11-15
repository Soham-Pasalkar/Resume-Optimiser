import json
import logging
import re
from typing import Any

from app.core.llm import ollama_client
from app.models.matching import SkillGapItem

logger = logging.getLogger(__name__)

CURATED_DOMAINS: dict[str, dict[str, Any]] = {
    "snowflake": {
        "title": "Cloud Data Warehousing & Performance Tuning with Snowflake",
        "why_it_matters": "Snowflake is an industry standard for scalable enterprise data warehousing and analytical query performance.",
        "desc": "Master virtual warehouse scaling, micro-partitioning, clustering keys, Snowpark, streams, tasks, and zero-copy cloning.",
        "prerequisites": ["SQL modeling fundamentals", "Relational database architecture"],
        "objectives": [
            "Configure auto-scaling multi-cluster virtual warehouses and resource monitors",
            "Design clustering keys to optimize scan pruning across large analytical tables",
            "Build automated data pipelines utilizing Snowflake Streams and Scheduled Tasks",
        ],
        "resources": [
            {
                "title": "Snowflake Architecture & Administration Guide",
                "url": "https://docs.snowflake.com/en/user-guide-getting-started",
                "type": "Documentation",
            },
            {
                "title": "Snowflake Performance Optimization Deep Dive",
                "url": "https://quickstarts.snowflake.com/",
                "type": "Interactive Guide",
            },
        ],
        "exercises": [
            "Exercise 1: Analyze query profiles to identify remote disk spillage and optimize warehouse sizing",
            "Exercise 2: Implement Change Data Capture (CDC) utilizing Snowflake Streams on raw landing tables",
        ],
        "project": "Architect an automated Snowflake data mart with multi-cluster warehouse scaling, automated clustering keys, and zero-copy clone disaster recovery.",
        "deliverables": [
            "SQL DDL scripts for database, schemas, tables, and clustering keys",
            "Automated Snowpark / Python ingestion script with error logging",
            "Benchmark report demonstrating sub-second analytical queries on 10M rows",
        ],
        "criteria": [
            "Zero partition pruning errors on date-partitioned fact queries",
            "Warehouse auto-suspend and auto-resume configured within 60-second timeouts",
            "Automated task runs without failure and handles backpressure gracefully",
        ],
        "hours": 18,
    },
    "dbt": {
        "title": "Modular Analytics Engineering & Data Testing with dbt",
        "why_it_matters": "dbt standardizes transformation logic, version-controlled testing, and lineage documentation in modern data stacks.",
        "desc": "Master modular SQL transformations, Jinja macros, generic and custom tests, incremental materializations, and dbt docs.",
        "prerequisites": ["Advanced SQL (CTEs, Window Functions)", "Git version control"],
        "objectives": [
            "Structure staged, intermediate, and dimensional mart models according to dbt best practices",
            "Implement automated data quality assertions (unique, not_null, accepted_values, relationships)",
            "Deploy incremental models handling high-volume append and upsert operations",
        ],
        "resources": [
            {
                "title": "dbt Core Official Documentation",
                "url": "https://docs.getdbt.com/docs/build/projects",
                "type": "Documentation",
            },
            {
                "title": "dbt Best Practices: How we structure our dbt projects",
                "url": "https://docs.getdbt.com/best-practices/how-we-structure/1-guide-overview",
                "type": "Best Practice Guide",
            },
        ],
        "exercises": [
            "Exercise 1: Convert a legacy monolithic SQL script into clean modular staging and mart models",
            "Exercise 2: Write a custom Jinja test verifying business logic constraints across joined tables",
        ],
        "project": "Build a production-grade dbt project with modular dimensional modeling, automated CI testing, and interactive DAG lineage documentation.",
        "deliverables": [
            "Complete dbt project repository with schema.yml, sources.yml, and models directory",
            "Automated dbt test suite with 100% test coverage on primary and foreign keys",
            "Generated dbt docs and lineage graph exported for review",
        ],
        "criteria": [
            "dbt run and dbt test pass with zero errors or warnings",
            "Incremental models process new data batches without full table rebuilds",
            "Clean modular DAG without circular dependencies",
        ],
        "hours": 16,
    },
    "spark": {
        "title": "Distributed Big Data Processing & Lakehouse Architecture with Apache Spark",
        "why_it_matters": "Apache Spark powers high-throughput distributed computation and large-scale ETL for enterprise data engineering.",
        "desc": "Master PySpark DataFrame APIs, Catalyst query optimization, shuffle tuning, broadcast joins, and Delta Lake ACID tables.",
        "prerequisites": ["Python programming", "Distributed systems concepts"],
        "objectives": [
            "Optimize Spark execution plans by tuning shuffle partitions and mitigating data skew",
            "Implement high-performance columnar transformations using broadcast hash joins and window operations",
            "Integrate Delta Lake for ACID transactions, schema evolution, and time-travel rollbacks",
        ],
        "resources": [
            {
                "title": "Apache Spark Official Programming Guide",
                "url": "https://spark.apache.org/docs/latest/programming-guide.html",
                "type": "Documentation",
            },
            {
                "title": "Delta Lake ACID Architecture & Best Practices",
                "url": "https://docs.delta.io/latest/index.html",
                "type": "Tutorial",
            },
        ],
        "exercises": [
            "Exercise 1: Profile a slow Spark job with Spark UI and resolve memory bottleneck or task skew",
            "Exercise 2: Implement time-travel rollback and schema evolution on a Delta Lake dataset",
        ],
        "project": "Build a containerized PySpark ETL pipeline processing 50M records with Delta Lake partitioning, Great Expectations data assertions, and comprehensive unit tests.",
        "deliverables": [
            "PySpark application code with automated PyTest test suite",
            "Dockerfile and docker-compose.yml running local Spark master and worker nodes",
            "Great Expectations validation report certifying data completeness and schema conformance",
        ],
        "criteria": [
            "All unit and integration tests pass cleanly under isolated Docker environment",
            "Zero out-of-memory (OOM) errors during 50M record batch processing",
            "Output written to optimized Parquet/Delta format with Snappy compression",
        ],
        "hours": 22,
    },
    "pyspark": {
        "title": "Distributed Big Data Processing & Lakehouse Architecture with Apache Spark",
        "why_it_matters": "PySpark is the primary distributed data transformation engine in enterprise cloud data platforms.",
        "desc": "Master PySpark DataFrame APIs, Catalyst query optimization, shuffle tuning, broadcast joins, and Delta Lake ACID tables.",
        "prerequisites": ["Python programming", "SQL and relational data structures"],
        "objectives": [
            "Tune Spark Catalyst optimization and reduce stage boundaries",
            "Handle skewed datasets with salting techniques and broadcast joins",
            "Deploy Delta Lake tables with automated vacuuming and compaction",
        ],
        "resources": [
            {
                "title": "PySpark API Reference",
                "url": "https://spark.apache.org/docs/latest/api/python/",
                "type": "Documentation",
            },
        ],
        "exercises": [
            "Exercise 1: Replace slow Python UDFs with native Spark SQL built-in expressions",
            "Exercise 2: Write PySpark aggregation queries with sliding window frames",
        ],
        "project": "Build an end-to-end PySpark ETL pipeline ingesting real-time JSON logs into partitioned Delta Lake tables with automated data quality checks.",
        "deliverables": [
            "Modular PySpark Python package with setup.py and pytest test suite",
            "Docker deployment environment demonstrating reproducible pipeline runs",
            "Performance analysis document detailing join strategies and memory allocation",
        ],
        "criteria": [
            "Pipeline successfully executes within memory constraints without disk spilling",
            "Data quality assertions verify 0 null values on non-nullable target fields",
            "100% reproducible execution via Docker",
        ],
        "hours": 20,
    },
    "airflow": {
        "title": "Production Orchestration & Workflow Scheduling with Apache Airflow",
        "why_it_matters": "Airflow orchestrates complex multi-stage data pipelines with SLA monitoring, automated retries, and dependency graphs.",
        "desc": "Author robust DAGs, custom operators, dynamic task mapping, SLA alerts, and idempotent backfill pipelines.",
        "prerequisites": ["Python scripting", "Data pipeline architecture"],
        "objectives": [
            "Design idempotent DAGs with deterministic execution dates and failure retry policies",
            "Implement Dynamic Task Mapping to scale parallel workers based on runtime parameters",
            "Configure Airflow Connection secrets, variables, and automated Slack/email alerting",
        ],
        "resources": [
            {
                "title": "Apache Airflow Official Documentation",
                "url": "https://airflow.apache.org/docs/apache-airflow/stable/index.html",
                "type": "Documentation",
            },
            {
                "title": "Astronomer Airflow Best Practices",
                "url": "https://www.astronomer.io/docs/learn/category/best-practices",
                "type": "Architecture Guide",
            },
        ],
        "exercises": [
            "Exercise 1: Convert a sequential pipeline into a parallel DAG with TaskFlow API (@task)",
            "Exercise 2: Implement custom SLA callbacks and dead-letter alert webhooks",
        ],
        "project": "Implement a modular ELT workflow orchestrating data transformations with retry policies, Slack alerting, and automated backfills.",
        "deliverables": [
            "Airflow DAG definitions utilizing TaskFlow API and DockerOperator",
            "Unit tests for DAG integrity verifying acyclic structure and task dependencies",
            "CI/CD workflow testing DAG syntax and import errors with pytest",
        ],
        "criteria": [
            "All DAG files load with zero import warnings or syntax errors",
            "Tasks execute idempotently, producing identical outputs upon manual re-run",
            "Automated alert callbacks trigger correctly upon simulated task failure",
        ],
        "hours": 16,
    },
    "kubernetes": {
        "title": "Production Container Orchestration with Kubernetes",
        "why_it_matters": "Kubernetes provides resilient scaling, self-healing, and service discovery for microservice architectures.",
        "desc": "Master Pod lifecycles, Deployments, StatefulSets, Ingress controllers, and RBAC security models.",
        "prerequisites": ["Docker containerization", "Linux networking fundamentals"],
        "objectives": [
            "Write production Kubernetes manifests with resource limits and liveness/readiness probes",
            "Configure Helm charts for multi-environment templating (dev, staging, prod)",
            "Implement RBAC policies and NetworkPolicies enforcing least-privilege isolation",
        ],
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
        "exercises": [
            "Exercise 1: Deploy a high-availability multi-replica application with rolling updates",
            "Exercise 2: Implement Horizontal Pod Autoscaling (HPA) responding to simulated CPU load",
        ],
        "project": "Architect an automated GitOps deployment pipeline using Helm charts and ingress routing for a multi-tier web application.",
        "deliverables": [
            "Version-controlled Helm chart repository with values.yaml for dev and prod",
            "Manifests including Deployment, Service, Ingress, and HPA resources",
            "Automated test script validating rolling updates with zero downtime",
        ],
        "criteria": [
            "Deployment sustains continuous HTTP traffic during rolling pod upgrade",
            "Pods restart automatically upon simulated crash in readiness probe",
            "Strict resource limits prevent cluster-wide memory exhaustion",
        ],
        "hours": 20,
    },
    "docker": {
        "title": "Production Containerization with Docker",
        "why_it_matters": "Docker creates immutable, portable runtime environments eliminating 'works on my machine' defects.",
        "desc": "Build optimized multi-stage Dockerfiles, manage volume persistence, and orchestrate local multi-service topologies.",
        "prerequisites": ["Linux command line", "Basic software build processes"],
        "objectives": [
            "Design multi-stage Dockerfiles reducing production image footprint by over 70%",
            "Implement non-root security contexts and vulnerability scanning with Trivy",
            "Orchestrate local development topologies with Docker Compose networks and volumes",
        ],
        "resources": [
            {
                "title": "Docker Best Practices Guide",
                "url": "https://docs.docker.com/develop/develop-images/dockerfile_best-practices/",
                "type": "Documentation",
            },
            {
                "title": "Docker Curriculum & Hands-on Labs",
                "url": "https://docker-curriculum.com/",
                "type": "Tutorial",
            },
        ],
        "exercises": [
            "Exercise 1: Refactor a monolithic 1.2GB image into a 65MB distroless container",
            "Exercise 2: Configure healthchecks and dependency orders in docker-compose.yml",
        ],
        "project": "Create a secure, non-root, multi-stage Docker environment minimizing image size by 70% with distroless base and automated security scanning.",
        "deliverables": [
            "Optimized Dockerfile utilizing multi-stage caching and distroless runtime",
            "docker-compose.yml spinning up application, database, and cache",
            "Security vulnerability scan report verifying zero CRITICAL CVEs",
        ],
        "criteria": [
            "Image builds cleanly with layer caching enabled",
            "Container runs as non-privileged non-root user",
            "Zero high/critical vulnerabilities reported by Trivy scanner",
        ],
        "hours": 12,
    },
    "postgresql": {
        "title": "Advanced Relational Data Modeling & Indexing in PostgreSQL",
        "why_it_matters": "PostgreSQL is the backbone of relational transactions, demanding deep indexing and concurrency mastery.",
        "desc": "Master EXPLAIN ANALYZE execution plans, B-tree/GIN indexing, transaction isolation levels, and vacuum tuning.",
        "prerequisites": ["Standard SQL queries", "Database schema design"],
        "objectives": [
            "Interpret EXPLAIN (ANALYZE, BUFFERS) plans to diagnose sequential scan bottlenecks",
            "Design partial and expression indexes accelerating high-frequency query filters",
            "Manage ACID transaction isolation and mitigate deadlocks under concurrent write loads",
        ],
        "resources": [
            {
                "title": "PostgreSQL Official Documentation",
                "url": "https://www.postgresql.org/docs/current/",
                "type": "Documentation",
            },
            {
                "title": "Use The Index, Luke! Database Indexing Tutorial",
                "url": "https://use-the-index-luke.com/",
                "type": "Interactive Guide",
            },
        ],
        "exercises": [
            "Exercise 1: Tune a slow multi-join query from 4,500ms down to sub-15ms using composite indexes",
            "Exercise 2: Set up table partitioning by range for high-volume time-series data",
        ],
        "project": "Design a normalized database schema with partitioning and GIN indexing handling 100,000 queries/sec with sub-5ms p99 latency.",
        "deliverables": [
            "DDL schema script with primary, foreign keys, check constraints, and range partitioning",
            "Benchmarking script using pgbench testing read/write transactions under load",
            "EXPLAIN ANALYZE comparison report before and after indexing optimizations",
        ],
        "criteria": [
            "All high-volume query paths execute as Index Scans with zero sequential scans",
            "p99 query latency remains under 5ms during 1,000 concurrent client connections",
            "Zero foreign key integrity violations under parallel write bursts",
        ],
        "hours": 18,
    },
    "kafka": {
        "title": "Event-Driven Distributed Messaging with Apache Kafka",
        "why_it_matters": "Kafka enables fault-tolerant real-time event streaming across enterprise microservices.",
        "desc": "Implement durable topic partitioning, consumer group rebalancing, and exactly-once processing semantics.",
        "prerequisites": ["Distributed systems concepts", "Java or Python concurrency"],
        "objectives": [
            "Configure topic partitions and replication factors for high availability and throughput",
            "Implement idempotent producers and transaction-aware consumers",
            "Design dead-letter queue (DLQ) architectures for resilient error handling",
        ],
        "resources": [
            {
                "title": "Apache Kafka Quickstart & Architecture",
                "url": "https://kafka.apache.org/documentation/",
                "type": "Documentation",
            },
            {
                "title": "Confluent Developer Kafka Tutorials",
                "url": "https://developer.confluent.io/",
                "type": "Tutorial",
            },
        ],
        "exercises": [
            "Exercise 1: Build a consumer group demonstrating automatic partition rebalancing upon worker failure",
            "Exercise 2: Implement schema validation using Avro and Schema Registry",
        ],
        "project": "Build an event-driven pub/sub data processing pipeline handling real-time telemetry streaming and dead-letter queues.",
        "deliverables": [
            "Producer and consumer application code with error retry policies",
            "Docker compose setup running Zookeeper/KRaft, Kafka brokers, and Schema Registry",
            "Integration test suite verifying message ordering within partitions and DLQ routing",
        ],
        "criteria": [
            "Zero message loss during broker restart simulation",
            "Strict FIFO ordering preserved within individual topic partitions",
            "Corrupt payloads automatically routed to dead-letter topic without halting consumer group",
        ],
        "hours": 20,
    },
    "aws": {
        "title": "Cloud Infrastructure Architecture on AWS",
        "why_it_matters": "AWS is the leading cloud provider for deploying scalable compute, storage, and networking platforms.",
        "desc": "Design resilient multi-AZ VPC topologies, IAM least-privilege policies, and auto-scaling container services on ECS/EKS.",
        "prerequisites": ["Networking basics (CIDR, Subnets, Gateways)", "Cloud computing concepts"],
        "objectives": [
            "Architect multi-AZ VPC networks with public, private, and database subnets",
            "Implement least-privilege IAM policies, roles, and Service Control Policies",
            "Deploy highly-available compute services behind Application Load Balancers",
        ],
        "resources": [
            {
                "title": "AWS Well-Architected Framework",
                "url": "https://aws.amazon.com/architecture/well-architected/",
                "type": "Whitepaper",
            },
            {
                "title": "AWS Skill Builder Training",
                "url": "https://explore.skillbuilder.aws/",
                "type": "Course",
            },
        ],
        "exercises": [
            "Exercise 1: Build an isolated VPC with NAT Gateways and private subnet route tables",
            "Exercise 2: Write an IAM policy granting least-privilege S3 bucket access with condition keys",
        ],
        "project": "Deploy an automated Terraform configuration provisioning an isolated VPC, RDS Multi-AZ instance, and Application Load Balancer.",
        "deliverables": [
            "Modular Terraform / CloudFormation code provisioning cloud topology",
            "Network architecture diagram showing AZ redundancy and security groups",
            "Automated healthcheck script validating end-to-end connectivity",
        ],
        "criteria": [
            "Database instances completely isolated in private subnets without public IPs",
            "Application Load Balancer healthcheck returns 200 OK across multiple availability zones",
            "Zero security group rules permitting open ingress (0.0.0.0/0) on private ports",
        ],
        "hours": 24,
    },
    "python": {
        "title": "High-Performance Asynchronous Python & Backend Architecture",
        "why_it_matters": "Python powers enterprise backend systems, data pipelines, and machine learning infrastructure.",
        "desc": "Master Python 3.12+ concurrency, asyncio event loops, pydantic validation models, and pytest fixtures.",
        "prerequisites": ["Basic Python syntax", "HTTP REST concepts"],
        "objectives": [
            "Write non-blocking asynchronous I/O code utilizing asyncio and async/await syntax",
            "Design robust data schemas and serialization using Pydantic v2",
            "Structure clean modular architectures following Dependency Injection patterns",
        ],
        "resources": [
            {
                "title": "FastAPI Official Documentation & Tutorial",
                "url": "https://fastapi.tiangolo.com/tutorial/",
                "type": "Documentation",
            },
            {
                "title": "Real Python: Async IO in Python",
                "url": "https://realpython.com/async-io-python/",
                "type": "Guide",
            },
        ],
        "exercises": [
            "Exercise 1: Refactor a blocking HTTP crawler to run concurrently using httpx and asyncio.gather",
            "Exercise 2: Write custom Pydantic validators and serialization aliases",
        ],
        "project": "Build an asynchronous microservice with connection pooling, structured logging, rate limiting, and 100% pytest test coverage.",
        "deliverables": [
            "Production-ready Python repository with pyproject.toml and ruff linting config",
            "Comprehensive test suite using pytest-asyncio with >90% code coverage",
            "Dockerized deployment with health endpoints and metrics export",
        ],
        "criteria": [
            "All unit and integration tests pass cleanly without deprecation warnings",
            "Async event loop processes 5,000 concurrent mock requests with sub-10ms latency",
            "Zero blocking I/O calls on the main event loop thread",
        ],
        "hours": 16,
    },
    "redis": {
        "title": "Distributed Caching & In-Memory Topologies with Redis",
        "why_it_matters": "Redis provides microsecond data retrieval and distributed concurrency synchronization.",
        "desc": "Implement cache-aside, write-through strategies, Redis Streams, pub/sub messaging, and distributed Redlock primitives.",
        "prerequisites": ["Basic key-value storage concepts", "Backend API development"],
        "objectives": [
            "Design resilient cache-aside architectures with TTL expiration and jitter",
            "Implement distributed rate limiting using Redis sliding window algorithms",
            "Deploy Redis Streams for durable in-memory message queuing",
        ],
        "resources": [
            {
                "title": "Redis Official Documentation",
                "url": "https://redis.io/docs/latest/",
                "type": "Documentation",
            },
        ],
        "exercises": [
            "Exercise 1: Implement a sliding-window rate limiter protecting API endpoints",
            "Exercise 2: Configure Redis Sentinel / Cluster failover and client retry logic",
        ],
        "project": "Design a distributed sliding-window rate limiter and session storage layer ensuring sub-1ms response times under load.",
        "deliverables": [
            "Python / Go middleware implementing distributed sliding-window rate limiting",
            "Integration test suite validating cache hit/miss semantics and TTL expiration",
            "Load test script demonstrating stable sub-1ms performance under 20,000 req/sec",
        ],
        "criteria": [
            "Rate limiter accurately throttles clients exceeding window quotas",
            "Cache stampede mitigation prevents database crashes upon cache expiration",
            "Sub-1ms response latency maintained throughout load tests",
        ],
        "hours": 12,
    },
    "terraform": {
        "title": "Cloud Infrastructure as Code with HashiCorp Terraform",
        "why_it_matters": "Terraform enables declarative, reproducible, version-controlled cloud infrastructure management.",
        "desc": "Master HCL module design, remote state locking with S3/DynamoDB, workspace isolation, and drift detection.",
        "prerequisites": ["Cloud provider basics", "Command line proficiency"],
        "objectives": [
            "Author modular, reusable HCL definitions with strict variable validation",
            "Configure remote S3 state backends with DynamoDB state locking",
            "Integrate automated drift detection and speculative plans in CI/CD",
        ],
        "resources": [
            {
                "title": "Terraform Official Tutorials",
                "url": "https://developer.hashicorp.com/terraform/tutorials",
                "type": "Tutorial",
            },
        ],
        "exercises": [
            "Exercise 1: Create a reusable module deploying VPC subnets across dynamic availability zones",
            "Exercise 2: Perform safe state migration and refactoring using terraform state mv",
        ],
        "project": "Author reusable Terraform modules deploying a production Kubernetes cluster with auto-scaling node pools and security policies.",
        "deliverables": [
            "Modular Terraform codebase with root module, submodules, and terraform.tfvars",
            "Automated GitHub Actions workflow running terraform fmt, validate, and tflint",
            "State lock verification test ensuring concurrent apply prevention",
        ],
        "criteria": [
            "terraform validate and tflint pass with zero errors",
            "State locking successfully prevents simultaneous concurrent applies",
            "Clean idempotency: running terraform plan on unchanged code outputs 'No changes'",
        ],
        "hours": 18,
    },
}


class RoadmapGenerator:
    """Generates structured, actionable learning milestones targeting candidate skill gaps
    complete with 10 structured milestone elements and portfolio deliverables.
    """

    PROMPT_TEMPLATE = """You are a Principal Software Architect and technical curriculum designer.
Construct a highly structured, professional learning roadmap to bridge the following skill gaps for the role: '{role}'.

Candidate Context:
- Demonstrated Skills: {demonstrated}
- Transferable Skills: {transferable}
- Candidate Projects: {projects}

Skill Gaps to Address:
{gaps}

Instructions:
1. Reference what the candidate already demonstrates when defining prerequisites (e.g. 'Builds on candidate's demonstrated background in Python & SQL').
2. Tailor milestone titles, why it matters, and practical project briefs specifically for the '{role}' opportunity (e.g. for a Data Engineer, produce lakehouse ETL or data warehouse architectures, not generic web applications).
3. Specify concrete portfolio deliverables and rigorous verification criteria (noting that formal review is required for verified skill recognition).

Generate structured JSON containing milestones with all 10 essential fields:
{{
  "estimated_total_hours": 60,
  "milestones": [
    {{
      "sequence_order": 1,
      "skill_name": "string",
      "milestone_title": "string",
      "why_it_matters": "string explaining significance for the role",
      "description": "string",
      "prerequisites": ["string"],
      "learning_objectives": ["string"],
      "curated_resources": [
        {{"title": "string", "url": "string", "type": "Documentation | Tutorial | Guide"}}
      ],
      "practical_exercises": ["string"],
      "practical_project_brief": "string concrete portfolio deliverable",
      "expected_deliverables": ["string"],
      "verification_criteria": ["string"],
      "estimated_hours": 20
    }}
  ]
}}
Return ONLY valid JSON.
"""

    async def generate_roadmap(
        self,
        target_role: str,
        unresolved_gaps: list[SkillGapItem],
        candidate_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Generate structured milestones and concrete project briefs."""
        context = candidate_context or {}
        demonstrated = ", ".join(context.get("demonstrated_skills", [])) or "None recorded"
        transferable = ", ".join(context.get("transferable_skills", [])) or "None recorded"
        existing_projs = context.get("existing_projects", [])
        proj_str = (
            ", ".join(p.get("title", "") for p in existing_projs[:3] if p.get("title"))
            or "Standard background"
        )

        # 1. Try local Ollama generation
        try:
            status = await ollama_client.get_status()
            if status.is_available:
                gaps_summary = "\n".join(
                    f"- {g.requirement.requirement_text} (Category: {g.requirement.category}, Severity: {g.gap_severity})"
                    for g in unresolved_gaps[:5]
                    if g.requirement
                )
                prompt = self.PROMPT_TEMPLATE.format(
                    role=target_role,
                    gaps=gaps_summary,
                    demonstrated=demonstrated,
                    transferable=transferable,
                    projects=proj_str,
                )
                resp = await ollama_client.generate(
                    prompt=prompt,
                    system_prompt="You generate structured technical learning roadmaps in valid JSON with all 10 milestone fields.",
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
        return self._generate_curated_fallback(target_role, unresolved_gaps, candidate_context)

    def _generate_curated_fallback(
        self,
        target_role: str,
        unresolved_gaps: list[SkillGapItem],
        candidate_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        milestones = []
        total_hours = 0
        order = 1

        context = candidate_context or {}
        demonstrated = context.get("demonstrated_skills", [])
        transferable = context.get("transferable_skills", [])
        existing_projects = context.get("existing_projects", [])

        # Build personalized foundation prerequisite string
        if demonstrated:
            foundation_prereq = f"Builds on candidate's demonstrated background in {', '.join(demonstrated[:3])}"
        elif transferable:
            foundation_prereq = f"Builds on transferable foundation in {', '.join(transferable[:2])}"
        else:
            foundation_prereq = "Core software engineering and computer science principles"

        # Sort gaps: CRITICAL first, then MODERATE, then LOW
        priority_order = {"CRITICAL": 0, "MODERATE": 1, "LOW": 2}
        sorted_gaps = sorted(
            unresolved_gaps,
            key=lambda g: priority_order.get(g.gap_severity, 3),
        )

        verification_standard = (
            "Code repository with test coverage (>80%) submitted for peer review; "
            "independent deliverable evaluation required to achieve verified skill status."
        )

        for gap in sorted_gaps[:5]:
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
                # Personalize title and project for target role
                title_suffix = f" for {target_role}" if target_role and target_role != "Target Role" else ""
                curated_title = f"{bp['title']}{title_suffix}"
                
                # Role-tailored project brief
                base_project = bp["project"]
                if target_role and "data engineer" in target_role.lower():
                    if name.lower() in ("spark", "pyspark"):
                        project_brief = (
                            f"Architect an automated PySpark Lakehouse ETL pipeline tailored for {target_role}, "
                            "ingesting high-volume records into partitioned Delta Lake tables with Great Expectations "
                            "assertions, automated tests, and Docker reproducible runtime."
                        )
                    elif name.lower() == "snowflake":
                        project_brief = (
                            f"Design and benchmark an automated Snowflake data mart tailored for {target_role}, "
                            "featuring multi-cluster warehouse scaling, auto-clustering keys, Snowpark ingestion, and zero-copy clone DR."
                        )
                    else:
                        project_brief = f"{base_project} Engineered to meet production data engineering standards for {target_role}."
                else:
                    project_brief = f"{base_project} (Tailored for {target_role})"

                prereqs = [foundation_prereq] + [p for p in bp.get("prerequisites", []) if p != foundation_prereq]
                criteria = bp.get("criteria", []) + [verification_standard]

                milestones.append(
                    {
                        "sequence_order": order,
                        "skill_name": name,
                        "milestone_title": curated_title,
                        "why_it_matters": (
                            f"Directly satisfies core requirements for the {target_role} role. "
                            f"{bp.get('why_it_matters', '')}"
                        ),
                        "description": bp["desc"],
                        "prerequisites": prereqs,
                        "learning_objectives": bp.get("objectives", [f"Master production implementation of {name}"]),
                        "curated_resources": bp["resources"],
                        "practical_exercises": bp.get("exercises", [f"Hands-on configuration and debugging of {name}"]),
                        "practical_project_brief": project_brief,
                        "expected_deliverables": bp.get("deliverables", ["Repository code and unit tests"]),
                        "verification_criteria": criteria,
                        "estimated_hours": bp.get("hours", 18),
                    }
                )
                total_hours += bp.get("hours", 18)
            else:
                skill_name = req.canonical_skill_name or req.requirement_text[:30]
                clean_req = req.requirement_text.rstrip(".")
                doc_query = skill_name.lower().replace(" ", "-")
                title_suffix = f" for {target_role}" if target_role and target_role != "Target Role" else ""

                milestones.append(
                    {
                        "sequence_order": order,
                        "skill_name": skill_name,
                        "milestone_title": f"Production Implementation & Mastery of {skill_name}{title_suffix}",
                        "why_it_matters": (
                            f"Mastering {skill_name} directly addresses a key requirement identified for the {target_role} opportunity, "
                            f"demonstrating engineering capability and production readiness."
                        ),
                        "description": f"Master the architectural principles, best practices, and integration patterns for {skill_name} as required for the {target_role} role.",
                        "prerequisites": [
                            foundation_prereq,
                            "Version control with Git",
                            "Automated testing methodologies",
                        ],
                        "learning_objectives": [
                            f"Understand core architecture and runtime behavior of {skill_name}",
                            f"Implement robust error handling and performance optimizations for {skill_name}",
                            f"Design automated test suites ensuring production reliability of {skill_name}",
                        ],
                        "curated_resources": [
                            {
                                "title": f"{skill_name} Official Reference & Standards",
                                "url": f"https://github.com/topics/{doc_query}",
                                "type": "Reference Implementations",
                            },
                            {
                                "title": "System Architecture & Design Standards",
                                "url": "https://github.com/donnemartin/system-design-primer",
                                "type": "Architecture Guide",
                            },
                        ],
                        "practical_exercises": [
                            f"Exercise 1: Build a minimal working proof-of-concept demonstrating {skill_name} core capabilities",
                            f"Exercise 2: Write unit and integration tests verifying failure modes and recovery for {skill_name}",
                        ],
                        "practical_project_brief": f"Engineer a working production deliverable for {target_role} directly demonstrating '{clean_req}' with unit test coverage, containerization, and structured logging.",
                        "expected_deliverables": [
                            f"Clean GitHub repository implementing {skill_name} deliverable",
                            "Comprehensive automated test suite with >80% code coverage",
                            "Architecture documentation detailing design decisions and performance characteristics",
                        ],
                        "verification_criteria": [
                            "End-to-end execution without errors in isolated environment",
                            "Passing test suite verifying core business logic (>80% coverage)",
                            verification_standard,
                        ],
                        "estimated_hours": 16,
                    }
                )
                total_hours += 16

            order += 1

        if not milestones:
            milestones.append(
                {
                    "sequence_order": 1,
                    "skill_name": "System Design & Architecture",
                    "milestone_title": f"High-Scale Architecture for {target_role}",
                    "why_it_matters": f"Essential architectural foundation for designing scalable systems as a {target_role}.",
                    "description": "Learn scalable distributed patterns, asynchronous event streaming, and resilient caching.",
                    "prerequisites": [foundation_prereq, "Distributed systems fundamentals"],
                    "learning_objectives": [
                        "Design horizontally scalable service topologies",
                        "Implement multi-layer caching and load balancing",
                    ],
                    "curated_resources": [
                        {
                            "title": "The System Design Primer",
                            "url": "https://github.com/donnemartin/system-design-primer",
                            "type": "Guide",
                        },
                    ],
                    "practical_exercises": [
                        "Exercise 1: Design data model and API specs for high-concurrency event ingestion",
                    ],
                    "practical_project_brief": f"Design and document an end-to-end distributed system for {target_role} handling 10M daily active requests with caching and disaster recovery.",
                    "expected_deliverables": [
                        "Complete technical architecture document with C4 component diagrams",
                    ],
                    "verification_criteria": [
                        "System handles 10M requests without single points of failure",
                        verification_standard,
                    ],
                    "estimated_hours": 20,
                }
            )
            total_hours = 20

        return {
            "estimated_total_hours": total_hours,
            "milestones": milestones,
        }


# Global generator instance
roadmap_generator = RoadmapGenerator()
