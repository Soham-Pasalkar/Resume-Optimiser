"""Pre-seeded canonical skill ontology mapping common technical skills and their aliases."""

CANONICAL_SKILLS = [
    # Programming Languages
    {
        "canonical_name": "Python",
        "category": "Programming Languages",
        "aliases": ["python", "python3", "python 3", "py"],
    },
    {
        "canonical_name": "Go",
        "category": "Programming Languages",
        "aliases": ["go", "golang"],
    },
    {
        "canonical_name": "TypeScript",
        "category": "Programming Languages",
        "aliases": ["typescript", "ts"],
    },
    {
        "canonical_name": "JavaScript",
        "category": "Programming Languages",
        "aliases": ["javascript", "js", "es6", "ecmascript"],
    },
    {
        "canonical_name": "Java",
        "category": "Programming Languages",
        "aliases": ["java", "java 11", "java 17", "java 21"],
    },
    {
        "canonical_name": "C++",
        "category": "Programming Languages",
        "aliases": ["c++", "cpp", "c/c++"],
    },
    {
        "canonical_name": "C#",
        "category": "Programming Languages",
        "aliases": ["c#", "csharp", ".net c#"],
    },
    {
        "canonical_name": "Rust",
        "category": "Programming Languages",
        "aliases": ["rust", "rustlang"],
    },
    {
        "canonical_name": "SQL",
        "category": "Programming Languages",
        "aliases": ["sql", "structured query language", "ansi sql"],
    },
    {
        "canonical_name": "Ruby",
        "category": "Programming Languages",
        "aliases": ["ruby", "ruby on rails"],
    },
    {
        "canonical_name": "PHP",
        "category": "Programming Languages",
        "aliases": ["php", "php8"],
    },
    {
        "canonical_name": "Kotlin",
        "category": "Programming Languages",
        "aliases": ["kotlin"],
    },
    {
        "canonical_name": "Swift",
        "category": "Programming Languages",
        "aliases": ["swift", "swiftui"],
    },
    # Databases & Storage
    {
        "canonical_name": "PostgreSQL",
        "category": "Databases & Storage",
        "aliases": ["postgresql", "postgres", "pgsql", "postgres 14", "postgres 15"],
    },
    {
        "canonical_name": "MySQL",
        "category": "Databases & Storage",
        "aliases": ["mysql", "mariadb"],
    },
    {
        "canonical_name": "Redis",
        "category": "Databases & Storage",
        "aliases": ["redis", "redis cache"],
    },
    {
        "canonical_name": "MongoDB",
        "category": "Databases & Storage",
        "aliases": ["mongodb", "mongo"],
    },
    {
        "canonical_name": "DynamoDB",
        "category": "Databases & Storage",
        "aliases": ["dynamodb", "aws dynamodb"],
    },
    {
        "canonical_name": "Cassandra",
        "category": "Databases & Storage",
        "aliases": ["cassandra", "apache cassandra"],
    },
    {
        "canonical_name": "Elasticsearch",
        "category": "Databases & Storage",
        "aliases": ["elasticsearch", "elastic search", "opensearch", "elk"],
    },
    {
        "canonical_name": "SQLite",
        "category": "Databases & Storage",
        "aliases": ["sqlite", "sqlite3"],
    },
    {
        "canonical_name": "Snowflake",
        "category": "Databases & Storage",
        "aliases": ["snowflake"],
    },
    # Cloud & Infrastructure
    {
        "canonical_name": "AWS",
        "category": "Cloud & Infrastructure",
        "aliases": ["aws", "amazon web services", "amazon aws"],
    },
    {
        "canonical_name": "Google Cloud Platform",
        "category": "Cloud & Infrastructure",
        "aliases": ["gcp", "google cloud", "google cloud platform"],
    },
    {
        "canonical_name": "Microsoft Azure",
        "category": "Cloud & Infrastructure",
        "aliases": ["azure", "microsoft azure"],
    },
    {
        "canonical_name": "Docker",
        "category": "Cloud & Infrastructure",
        "aliases": ["docker", "containerization", "containers", "dockerfile"],
    },
    {
        "canonical_name": "Kubernetes",
        "category": "Cloud & Infrastructure",
        "aliases": ["kubernetes", "k8s", "eks", "gke", "container orchestration"],
    },
    {
        "canonical_name": "Terraform",
        "category": "Cloud & Infrastructure",
        "aliases": ["terraform", "iac", "infrastructure as code"],
    },
    {
        "canonical_name": "CI/CD",
        "category": "Cloud & Infrastructure",
        "aliases": [
            "ci/cd",
            "ci cd",
            "continuous integration",
            "github actions",
            "gitlab ci",
            "jenkins",
        ],
    },
    {
        "canonical_name": "Linux",
        "category": "Cloud & Infrastructure",
        "aliases": ["linux", "unix", "bash", "shell scripting", "ubuntu"],
    },
    {
        "canonical_name": "Microservices",
        "category": "Cloud & Infrastructure",
        "aliases": ["microservices", "microservice architecture", "distributed systems"],
    },
    # Web & Backend Frameworks
    {
        "canonical_name": "FastAPI",
        "category": "Web & Backend Frameworks",
        "aliases": ["fastapi", "fast-api"],
    },
    {
        "canonical_name": "React",
        "category": "Web & Backend Frameworks",
        "aliases": ["react", "react.js", "reactjs"],
    },
    {
        "canonical_name": "Next.js",
        "category": "Web & Backend Frameworks",
        "aliases": ["next.js", "nextjs", "next"],
    },
    {
        "canonical_name": "Node.js",
        "category": "Web & Backend Frameworks",
        "aliases": ["node.js", "nodejs", "node"],
    },
    {
        "canonical_name": "Django",
        "category": "Web & Backend Frameworks",
        "aliases": ["django", "django rest framework", "drf"],
    },
    {
        "canonical_name": "Flask",
        "category": "Web & Backend Frameworks",
        "aliases": ["flask"],
    },
    {
        "canonical_name": "Spring Boot",
        "category": "Web & Backend Frameworks",
        "aliases": ["spring boot", "spring", "spring framework"],
    },
    {
        "canonical_name": "GraphQL",
        "category": "Web & Backend Frameworks",
        "aliases": ["graphql", "apollo graphql"],
    },
    {
        "canonical_name": "REST APIs",
        "category": "Web & Backend Frameworks",
        "aliases": ["rest", "restful", "rest api", "rest apis", "restful apis"],
    },
    {
        "canonical_name": "gRPC",
        "category": "Web & Backend Frameworks",
        "aliases": ["grpc", "protocol buffers", "protobuf"],
    },
    # AI, Machine Learning & Data
    {
        "canonical_name": "PyTorch",
        "category": "AI, ML & Data",
        "aliases": ["pytorch", "torch"],
    },
    {
        "canonical_name": "TensorFlow",
        "category": "AI, ML & Data",
        "aliases": ["tensorflow", "tf", "keras"],
    },
    {
        "canonical_name": "Scikit-Learn",
        "category": "AI, ML & Data",
        "aliases": ["scikit-learn", "sklearn"],
    },
    {
        "canonical_name": "Pandas",
        "category": "AI, ML & Data",
        "aliases": ["pandas"],
    },
    {
        "canonical_name": "NumPy",
        "category": "AI, ML & Data",
        "aliases": ["numpy"],
    },
    {
        "canonical_name": "Large Language Models (LLMs)",
        "category": "AI, ML & Data",
        "aliases": [
            "llm",
            "llms",
            "large language models",
            "prompt engineering",
            "langchain",
            "rag",
        ],
    },
]
