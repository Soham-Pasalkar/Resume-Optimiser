from fastapi import APIRouter

from app.api.v1.endpoints import (
    applications,
    auth,
    candidate,
    health,
    interview,
    job_descriptions,
    learning,
    matching,
    optimizer,
    resumes,
    settings,
    users,
)

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(resumes.router, prefix="/resumes", tags=["Resumes"])
api_router.include_router(job_descriptions.router, prefix="/jobs", tags=["Job Descriptions"])
api_router.include_router(candidate.router, prefix="/candidate", tags=["Candidate Intelligence"])
api_router.include_router(matching.router, prefix="/matches", tags=["Matching & Skill Gaps"])
api_router.include_router(optimizer.router, prefix="/optimizer", tags=["AI Resume Optimizer"])
api_router.include_router(learning.router, prefix="/learning", tags=["Personalized Learning"])
api_router.include_router(interview.router, prefix="/interview", tags=["Interview Intelligence"])
api_router.include_router(
    applications.router, prefix="/applications", tags=["Application Pipeline"]
)
api_router.include_router(settings.router, prefix="/settings", tags=["Settings"])
