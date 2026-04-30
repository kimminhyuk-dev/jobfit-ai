"""
사용자 채용공고 조회 API
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.job_posting_repository import JobPostingRepository
from app.schemas.job_collection import JobPostingListResponse, JobPostingResponse


router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=JobPostingListResponse)
def list_jobs(
    source: str | None = Query(default=None, max_length=20),
    keyword: str | None = Query(default=None, max_length=100),
    location_code: str | None = Query(default=None, max_length=20),
    employment_type_code: str | None = Query(default=None, max_length=20),
    education_code: str | None = Query(default=None, max_length=20),
    career_level_code: str | None = Query(default=None, max_length=20),
    status: str | None = Query(default=None, max_length=20),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> JobPostingListResponse:
    """DB에 저장된 채용공고만 조회한다."""
    repository = JobPostingRepository(db)
    postings, total = repository.list_by_filter(
        page=page,
        size=size,
        filters={
            "source": source,
            "keyword": keyword,
            "location_code": location_code,
            "employment_type_code": employment_type_code,
            "education_code": education_code,
            "career_level_code": career_level_code,
            "status": status,
        },
    )
    return JobPostingListResponse(
        items=[JobPostingResponse.model_validate(posting) for posting in postings],
        total=total,
        page=page,
        size=size,
    )
