"""
사용자 채용공고 조회 API
"""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.repositories.job_posting_repository import JobPostingRepository
from app.schemas.job_collection import (
    JobFilterOptionsResponse,
    JobPostingListResponse,
    JobPostingResponse,
)


router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=JobPostingListResponse)
def list_jobs(
    source: str | None = Query(default=None, max_length=20),
    keyword: str | None = Query(default=None, max_length=100),
    region: str | None = Query(default=None, max_length=40),
    education: str | None = Query(default=None, max_length=60),
    employment_type: str | None = Query(default=None, max_length=60),
    ncs_category: str | None = Query(default=None, max_length=100),
    location_code: str | None = Query(default=None, max_length=20),
    employment_type_code: str | None = Query(default=None, max_length=20),
    education_code: str | None = Query(default=None, max_length=20),
    career_level_code: str | None = Query(default=None, max_length=20),
    status_filter: str | None = Query(default=None, alias="status", max_length=20),
    data_source: str | None = Query(default=None, max_length=20),
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
            "region": region,
            "education": education,
            "employment_type": employment_type,
            "ncs_category": ncs_category,
            "location_code": location_code,
            "employment_type_code": employment_type_code,
            "education_code": education_code,
            "career_level_code": career_level_code,
            "status": status_filter,
            "data_source": data_source,
        },
    )
    return JobPostingListResponse(
        items=[JobPostingResponse.model_validate(posting) for posting in postings],
        total=total,
        page=page,
        size=size,
    )


@router.get("/filter-options", response_model=JobFilterOptionsResponse)
def get_filter_options(db: Session = Depends(get_db)) -> JobFilterOptionsResponse:
    """공고 데이터에서 추출한 지역/학력/고용형태/직종 선택지를 반환한다."""
    options = JobPostingRepository(db).filter_options()
    return JobFilterOptionsResponse(**options)


@router.get("/{job_id}", response_model=JobPostingResponse)
def get_job(job_id: int, db: Session = Depends(get_db)) -> JobPostingResponse:
    """채용공고 단건 상세를 조회한다."""
    posting = JobPostingRepository(db).get_by_id(job_id)
    if posting is None or (posting.status or "").strip().upper() == "HIDDEN":
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.JOB_NOT_FOUND,
            message="공고를 찾을 수 없습니다.",
        )
    return JobPostingResponse.model_validate(posting)
