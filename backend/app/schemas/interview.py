import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class GenerateInterviewPrepRequest(BaseModel):
    match_evaluation_id: uuid.UUID


class EvaluateAnswerRequest(BaseModel):
    practice_response: str = Field(
        ..., min_length=10, description="Candidate typed practice response"
    )


class InterviewFeedback(BaseModel):
    score: float
    strengths: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)
    critique: str


class InterviewQuestionResponse(BaseModel):
    id: uuid.UUID
    prep_id: uuid.UUID
    question_type: str
    question_text: str
    target_skill_or_gap: str | None = None
    evaluation_criteria: str
    star_guidelines: dict[str, Any] = Field(default_factory=dict)
    practice_response: str | None = None
    ai_feedback: dict[str, Any] | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class InterviewPrepResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    match_evaluation_id: uuid.UUID
    target_role_title: str
    company_name: str | None = None
    questions_count: int = 0
    questions: list[InterviewQuestionResponse] = Field(default_factory=list)
    created_at: datetime

    class Config:
        from_attributes = True


class InterviewPrepSummaryResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    match_evaluation_id: uuid.UUID
    target_role_title: str
    company_name: str | None = None
    questions_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True
