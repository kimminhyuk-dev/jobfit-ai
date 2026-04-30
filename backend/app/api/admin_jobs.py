"""
관리자 채용공고 수집 API 라우터
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin_user
from app.core.config import settings
from app.core.database import get_db
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.models.user import User
from app.schemas.job_collection import (
    AlioCollectRequest,
    AlioCollectResponse,
    MockLoadRequest,
    MockLoadResponse,
    Work24CollectRequest,
    Work24CollectResponse,
)
from app.services.alio_collection_service import (
    AlioCollectionError,
    AlioCollectionService,
)
from app.services.mock_loader_service import MockLoaderError, MockLoaderService
from app.services.work24_collection_service import (
    Work24CollectionError,
    Work24CollectionService,
)


router = APIRouter(prefix="/admin", tags=["admin-jobs"])


def get_alio_collection_service(
    db: Session = Depends(get_db),
) -> AlioCollectionService:
    """AlioCollectionService 의존성"""
    return AlioCollectionService(db)


def get_work24_collection_service(
    db: Session = Depends(get_db),
) -> Work24CollectionService:
    """Work24CollectionService 의존성"""
    return Work24CollectionService(db)


def get_mock_loader_service(
    db: Session = Depends(get_db),
) -> MockLoaderService:
    """MockLoaderService 의존성"""
    return MockLoaderService(db)


@router.post(
    "/job-sources/alio/collect",
    response_model=AlioCollectResponse,
)
def collect_alio_jobs(
    collect_request: AlioCollectRequest,
    current_user: User = Depends(get_current_admin_user),
    collection_service: AlioCollectionService = Depends(get_alio_collection_service),
) -> AlioCollectResponse:
    """관리자가 ALIO 공공기관 채용정보 수집을 수동 실행한다."""
    if not settings.alio_api_key:
        raise AppException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code=ErrorCode.JOB_API_KEY_MISSING,
            message="ALIO API 키가 설정되지 않았습니다.",
        )

    try:
        run = collection_service.collect_jobs(
            params=collect_request.model_dump(),
            triggered_by=str(current_user.user_id),
            idempotency_key=collect_request.idempotency_key,
        )
    except AlioCollectionError:
        raise AppException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            code=ErrorCode.JOB_COLLECTION_FAILED,
            message="ALIO 채용정보 수집에 실패했습니다.",
        )

    return AlioCollectResponse.model_validate(run)


@router.post(
    "/jobs/sources/work24/collect",
    response_model=Work24CollectResponse,
)
def collect_work24_jobs(
    collect_request: Work24CollectRequest,
    current_user: User = Depends(get_current_admin_user),
    collection_service: Work24CollectionService = Depends(
        get_work24_collection_service
    ),
) -> Work24CollectResponse:
    """관리자가 Work24 채용정보 수집을 수동 실행한다."""
    try:
        run = collection_service.collect_jobs(
            params=collect_request.model_dump(),
            triggered_by=str(current_user.user_id),
            idempotency_key=collect_request.idempotency_key,
        )
    except Work24CollectionError:
        raise AppException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            code=ErrorCode.JOB_COLLECTION_FAILED,
            message="Work24 채용정보 수집에 실패했습니다.",
        )

    return Work24CollectResponse.model_validate(run)


@router.post(
    "/jobs/sources/mock/load",
    response_model=MockLoadResponse,
)
def load_mock_jobs(
    load_request: MockLoadRequest,
    current_user: User = Depends(get_current_admin_user),
    mock_loader_service: MockLoaderService = Depends(get_mock_loader_service),
) -> MockLoadResponse:
    """관리자가 Mock 채용공고 JSON 파일을 DB에 로드한다."""
    try:
        run = mock_loader_service.load_mock_data(
            file_path=load_request.file_path,
            triggered_by=str(current_user.user_id),
        )
    except MockLoaderError:
        raise AppException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code=ErrorCode.JOB_COLLECTION_FAILED,
            message="Mock 데이터 로드에 실패했습니다. 파일 경로와 JSON 구조를 확인하세요.",
        )
    return MockLoadResponse.model_validate(run)
