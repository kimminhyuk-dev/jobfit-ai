"""
이력서 업로드/조회 비즈니스 로직
"""

import logging
from pathlib import Path
from typing import Any
from uuid import uuid4

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.resume import Resume
from app.repositories.resume_repository import ResumeRepository
from app.services.resume_parser import (
    ResumeParseError,
    extract_resume_text,
    parse_resume_text,
    parse_resume_with_llm,
)


class ResumeNotFoundError(Exception):
    """이력서를 찾을 수 없음"""


class ResumeFileTooLargeError(Exception):
    """이력서 파일 크기 초과"""


class ResumeUnsupportedFileTypeError(Exception):
    """지원하지 않는 이력서 파일 형식"""


ALLOWED_CONTENT_TYPES = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "text/plain": ".txt",
}

ALLOWED_SUFFIXES = {".pdf", ".docx", ".txt"}

logger = logging.getLogger(__name__)


def _parse_with_best_available(raw_text: str) -> dict[str, Any]:
    """GEMINI_API_KEY가 있으면 LLM 파서, 없거나 실패하면 정규식 파서로 폴백."""
    api_key = settings.gemini_api_key
    if api_key:
        try:
            return parse_resume_with_llm(raw_text, api_key)
        except Exception as exc:
            logger.warning("LLM 파싱 실패, 정규식 파서로 폴백: %s", exc)
    return parse_resume_text(raw_text)


def _extract_structured_projects(parsed_data: dict[str, Any]) -> list[dict[str, Any]]:
    """parsed_data에서 구조화 프로젝트 목록을 추출한다."""
    projects = parsed_data.get("projects") or []
    result = []
    for p in projects:
        if isinstance(p, dict):
            result.append(p)
        elif isinstance(p, str) and p.strip():
            # 구버전 호환: 문자열이면 raw_text로 포장
            result.append({"raw_text": p, "name": None, "period": None,
                           "role": None, "description": None, "review": None,
                           "tech_stack": []})
    return result


def _extract_structured_sections(parsed_data: dict[str, Any]) -> list[dict[str, str]]:
    """parsed_data.cover_letter_sections를 [{title, content}] 목록으로 변환한다."""
    sections = parsed_data.get("cover_letter_sections") or {}
    if isinstance(sections, dict):
        return [{"title": k, "content": v} for k, v in sections.items() if k and v]
    return []


class ResumeService:
    """이력서 관련 비즈니스 로직"""

    def __init__(self, db: Session):
        self.db = db
        self.resume_repository = ResumeRepository(db)

    def list_resumes(self, user_id: int) -> list[Resume]:
        return self.resume_repository.list_by_user(user_id)

    def get_resume(self, resume_id: int, user_id: int) -> Resume:
        resume = self.resume_repository.get_by_id(resume_id, user_id)
        if resume is None:
            raise ResumeNotFoundError
        return resume

    def get_resume_for_admin(self, resume_id: int) -> Resume:
        """관리자용: 특정 이력서 상세 정보를 조회한다."""
        resume = self.resume_repository.get_by_id_no_user(resume_id)
        if resume is None:
            raise ResumeNotFoundError
        return resume

    def get_structured_projects(self, resume_id: int):
        return self.resume_repository.get_projects(resume_id)

    def get_structured_cover_letter_sections(self, resume_id: int):
        return self.resume_repository.get_cover_letter_sections(resume_id)

    def create_resume(
        self,
        *,
        user_id: int,
        original_filename: str,
        content_type: str,
        file_bytes: bytes,
        title: str | None,
        is_default: bool,
        request_ip: str | None,
    ) -> Resume:
        max_bytes = settings.resume_max_upload_mb * 1024 * 1024
        if len(file_bytes) > max_bytes:
            raise ResumeFileTooLargeError

        suffix = Path(original_filename).suffix.lower()
        if content_type not in ALLOWED_CONTENT_TYPES and suffix not in ALLOWED_SUFFIXES:
            raise ResumeUnsupportedFileTypeError
        if not suffix:
            suffix = ALLOWED_CONTENT_TYPES.get(content_type, "")

        upload_dir = Path(settings.resume_upload_dir) / str(user_id)
        upload_dir.mkdir(parents=True, exist_ok=True)
        stored_filename = f"{uuid4().hex}{suffix}"
        file_path = upload_dir / stored_filename
        file_path.write_bytes(file_bytes)

        raw_text: str | None = None
        parsed_data: dict[str, Any] | None = None
        parse_status = "COMPLETED"
        parse_error: str | None = None
        try:
            raw_text = extract_resume_text(file_path, content_type)
            parsed_data = _parse_with_best_available(raw_text)
        except ResumeParseError as exc:
            parse_status = "FAILED"
            parse_error = str(exc)

        try:
            resume_title = (title or Path(original_filename).stem).strip() or "내 이력서"
            if is_default:
                self.resume_repository.clear_default(
                    user_id,
                    actor_id=user_id,
                    request_ip=request_ip,
                )

            resume = self.resume_repository.create(
                user_id=user_id,
                title=resume_title[:120],
                original_filename=original_filename,
                stored_filename=stored_filename,
                file_path=str(file_path),
                file_size=len(file_bytes),
                content_type=content_type,
                raw_text=raw_text,
                parsed_data=parsed_data,
                parse_status=parse_status,
                parse_error=parse_error,
                is_default=is_default,
                actor_id=user_id,
                request_ip=request_ip,
            )

            # 구조화 서브테이블 저장
            if parsed_data:
                self._save_structured_data(resume.resume_id, parsed_data, user_id, request_ip)

            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            self._unlink_file(file_path)
            raise

        self.db.refresh(resume)
        return resume

    def delete_resume(
        self,
        resume_id: int,
        user_id: int,
        request_ip: str | None,
    ) -> None:
        resume = self.get_resume(resume_id, user_id)
        file_path = Path(resume.file_path)
        self.resume_repository.soft_delete(
            resume,
            actor_id=user_id,
            request_ip=request_ip,
        )
        try:
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise
        self._unlink_file(file_path)

    def update_resume_content_for_admin(
        self,
        resume_id: int,
        *,
        actor_id: int,
        title: str | None,
        raw_text: str | None,
        parsed_data: dict[str, Any] | None,
        structured_projects: list[dict[str, Any]] | None,
        structured_cover_letter_sections: list[dict[str, str]] | None,
        request_ip: str | None,
    ) -> Resume:
        resume = self.resume_repository.get_by_id_no_user(resume_id)
        if resume is None:
            raise ResumeNotFoundError
        return self._update_resume_content(
            resume,
            actor_id=actor_id,
            title=title,
            raw_text=raw_text,
            parsed_data=parsed_data,
            structured_projects=structured_projects,
            structured_cover_letter_sections=structured_cover_letter_sections,
            request_ip=request_ip,
        )

    def _update_resume_content(
        self,
        resume: Resume,
        *,
        actor_id: int,
        title: str | None,
        raw_text: str | None,
        parsed_data: dict[str, Any] | None,
        structured_projects: list[dict[str, Any]] | None = None,
        structured_cover_letter_sections: list[dict[str, str]] | None = None,
        request_ip: str | None,
    ) -> Resume:
        normalized_title = title.strip() if title is not None else None
        if normalized_title == "":
            normalized_title = None
        try:
            updated = self.resume_repository.update_resume_content(
                resume,
                title=normalized_title,
                raw_text=raw_text,
                parsed_data=parsed_data,
                actor_id=actor_id,
                request_ip=request_ip,
            )

            # 구조화 서브테이블 갱신
            if structured_projects is not None:
                self.resume_repository.replace_projects(
                    resume.resume_id, structured_projects, actor_id, request_ip
                )
            elif parsed_data is not None:
                self._save_structured_data(resume.resume_id, parsed_data, actor_id, request_ip)

            if structured_cover_letter_sections is not None:
                self.resume_repository.replace_cover_letter_sections(
                    resume.resume_id, structured_cover_letter_sections, actor_id, request_ip
                )

            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise
        self.db.refresh(updated)
        return updated

    def _save_structured_data(
        self,
        resume_id: int,
        parsed_data: dict[str, Any],
        actor_id: int,
        request_ip: str | None,
    ) -> None:
        """parsed_data에서 구조화 서브테이블을 동기화한다."""
        projects = _extract_structured_projects(parsed_data)
        if projects:
            self.resume_repository.replace_projects(resume_id, projects, actor_id, request_ip)
        sections = _extract_structured_sections(parsed_data)
        if sections:
            self.resume_repository.replace_cover_letter_sections(
                resume_id, sections, actor_id, request_ip
            )

    @staticmethod
    def _unlink_file(file_path: Path) -> None:
        try:
            if file_path.is_file():
                file_path.unlink()
        except OSError:
            logger.warning("이력서 파일 삭제에 실패했습니다: %s", file_path)

    def _refresh_parsed_data_if_empty(self, resume: Resume) -> None:
        if not self._needs_parsed_data_refresh(resume.parsed_data):
            return
        raw_text = resume.raw_text
        if resume.file_path:
            file_path = Path(resume.file_path)
            if file_path.is_file():
                try:
                    raw_text = extract_resume_text(file_path, resume.content_type)
                except ResumeParseError:
                    pass
        if not raw_text:
            return
        parsed_data = _parse_with_best_available(raw_text)
        self.resume_repository.update_parsed_data(resume, parsed_data)
        self._save_structured_data(resume.resume_id, parsed_data, resume.user_id, None)
        self.db.commit()
        self.db.refresh(resume)

    @staticmethod
    def _needs_parsed_data_refresh(parsed_data: dict[str, Any] | None) -> bool:
        if parsed_data is None:
            return True
        if "profile" not in parsed_data or "sections" not in parsed_data:
            return True
        if settings.gemini_api_key and parsed_data.get("parsed_by") is None:
            return True
        return not any(
            parsed_data.get(key)
            for key in ("emails", "phones", "urls", "skills")
        )
