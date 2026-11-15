from pydantic import BaseModel, Field


class ExtractedRequirement(BaseModel):
    requirement_text: str = Field(..., description="Verbatim or decomposed requirement statement")
    category: str = Field(
        default="technical_skill",
        description="Category: technical_skill, soft_skill, qualification, responsibility, tool",
    )
    is_mandatory: bool = Field(
        default=True, description="True if required/must-have; False if preferred/nice-to-have"
    )
    importance_weight: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Relative importance weight between 0.0 and 1.0"
    )
    min_years_experience: float | None = Field(
        default=None, description="Minimum years of experience required if specified"
    )
    canonical_skill_name: str | None = Field(
        default=None, description="Matched canonical skill from ontology if applicable"
    )


class DecomposedJD(BaseModel):
    job_title: str = Field(default="Untitled Position", description="Extracted job title")
    company_name: str | None = Field(default=None, description="Hiring company or organization")
    department: str | None = Field(default=None, description="Department or business unit")
    seniority_level: str | None = Field(
        default=None, description="e.g. Entry, Mid-Level, Senior, Lead, Principal, Staff"
    )
    work_mode: str | None = Field(default=None, description="e.g. Remote, Hybrid, On-site")
    location: str | None = Field(default=None, description="Geographic location or office")
    salary_range: str | None = Field(
        default=None, description="Mentioned salary or compensation range"
    )
    requirements: list[ExtractedRequirement] = Field(
        default_factory=list, description="List of decomposed requirements"
    )
    raw_text: str = Field(default="", description="Original raw text of the job description")
