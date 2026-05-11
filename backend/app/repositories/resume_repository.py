"""
Resume 테이블 및 구조화 서브테이블 DB 접근 계층
"""

from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.resume import Resume
from app.models.resume_cover_letter_section import ResumeCoverLetterSection
from app.models.resume_project import ResumeProject


class ResumeRepository:
    """이력서 DB 작업을 담당한다."""

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------ #
    # resumes 기본 CRUD
    # ------------------------------------------------------------------ #

    def list_by_user(self, user_id: int) -> list[Resume]:
        stmt = (
            select(Resume)
            .where(Resume.user_id == user_id)
            .where(Resume.is_deleted.is_(False))
            .order_by(Resume.is_default.desc(), Resume.resume_id.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_by_id(
        self,
        resume_id: int,
        user_id: int,
        include_deleted: bool = False,
    ) -> Resume | None:
        stmt = select(Resume).where(
            Resume.resume_id == resume_id,
            Resume.user_id == user_id,
        )
        if not include_deleted:
            stmt = stmt.where(Resume.is_deleted.is_(False))
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_id_no_user(
        self,
        resume_id: int,
        include_deleted: bool = False,
    ) -> Resume | None:
        stmt = select(Resume).where(Resume.resume_id == resume_id)
        if not include_deleted:
            stmt = stmt.where(Resume.is_deleted.is_(False))
        return self.db.execute(stmt).scalar_one_or_none()

    def clear_default(self, user_id: int, actor_id: int, request_ip: str | None) -> None:
        resumes = self.list_by_user(user_id)
        for resume in resumes:
            if resume.is_default:
                resume.is_default = False
                resume.updated_by = actor_id
                resume.updated_ip = request_ip

    def create(
        self,
        *,
        user_id: int,
        title: str,
        original_filename: str,
        stored_filename: str,
        file_path: str,
        file_size: int,
        content_type: str,
        raw_text: str | None,
        parsed_data: dict[str, Any] | None,
        parse_status: str,
        parse_error: str | None,
        is_default: bool,
        actor_id: int,
        request_ip: str | None,
    ) -> Resume:
        resume = Resume(
            user_id=user_id,
            title=title,
            original_filename=original_filename,
            stored_filename=stored_filename,
            file_path=file_path,
            file_size=file_size,
            content_type=content_type,
            raw_text=raw_text,
            parsed_data=parsed_data,
            parse_status=parse_status,
            parse_error=parse_error,
            is_default=is_default,
            created_by=actor_id,
            created_ip=request_ip,
            updated_by=actor_id,
            updated_ip=request_ip,
        )
        self.db.add(resume)
        self.db.flush()
        return resume

    def soft_delete(self, resume: Resume, actor_id: int, request_ip: str | None) -> None:
        resume.is_deleted = True
        resume.is_default = False
        resume.title = "삭제된 이력서"
        resume.original_filename = ""
        resume.stored_filename = f"deleted-{resume.resume_id}"
        resume.file_path = ""
        resume.file_size = 0
        resume.content_type = "application/octet-stream"
        resume.raw_text = None
        resume.parsed_data = None
        resume.parse_status = "DELETED"
        resume.parse_error = None
        resume.updated_by = actor_id
        resume.updated_ip = request_ip
        # 구조화 서브테이블도 함께 삭제 (CASCADE 백업)
        self._delete_structured_data(resume.resume_id)
        self.db.flush()

    def update_parsed_data(
        self,
        resume: Resume,
        parsed_data: dict[str, Any],
    ) -> Resume:
        resume.parsed_data = parsed_data
        resume.parse_status = "COMPLETED"
        resume.parse_error = None
        self.db.flush()
        return resume

    def update_resume_content(
        self,
        resume: Resume,
        *,
        title: str | None,
        raw_text: str | None,
        parsed_data: dict[str, Any] | None,
        actor_id: int,
        request_ip: str | None,
    ) -> Resume:
        if title is not None:
            resume.title = title
        if raw_text is not None:
            resume.raw_text = raw_text
        if parsed_data is not None:
            resume.parsed_data = parsed_data
            resume.parse_status = "COMPLETED"
            resume.parse_error = None
        resume.updated_by = actor_id
        resume.updated_ip = request_ip
        self.db.flush()
        return resume

    # ------------------------------------------------------------------ #
    # 구조화 서브테이블 CRUD
    # ------------------------------------------------------------------ #

    def get_projects(self, resume_id: int) -> list[ResumeProject]:
        stmt = (
            select(ResumeProject)
            .where(ResumeProject.resume_id == resume_id)
            .order_by(ResumeProject.order_index)
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_cover_letter_sections(self, resume_id: int) -> list[ResumeCoverLetterSection]:
        stmt = (
            select(ResumeCoverLetterSection)
            .where(ResumeCoverLetterSection.resume_id == resume_id)
            .order_by(ResumeCoverLetterSection.order_index)
        )
        return list(self.db.execute(stmt).scalars().all())

    def replace_projects(
        self,
        resume_id: int,
        projects: list[dict[str, Any]],
        actor_id: int,
        request_ip: str | None,
    ) -> list[ResumeProject]:
        """기존 프로젝트를 모두 교체한다 (upsert 대신 delete-insert)."""
        self.db.execute(
            delete(ResumeProject).where(ResumeProject.resume_id == resume_id)
        )
        rows: list[ResumeProject] = []
        for idx, p in enumerate(projects):
            tech = p.get("tech_stack") or []
            if isinstance(tech, str):
                tech = [t.strip() for t in tech.split(",") if t.strip()]
            row = ResumeProject(
                resume_id=resume_id,
                order_index=idx,
                name=p.get("name") or None,
                period=p.get("period") or None,
                role=p.get("role") or None,
                description=p.get("description") or None,
                review=p.get("review") or None,
                tech_stack=tech if isinstance(tech, list) else [],
                raw_text=p.get("raw_text") or None,
                created_by=actor_id,
                created_ip=request_ip,
                updated_by=actor_id,
                updated_ip=request_ip,
            )
            self.db.add(row)
            rows.append(row)
        self.db.flush()
        return rows

    def replace_cover_letter_sections(
        self,
        resume_id: int,
        sections: list[dict[str, str]],
        actor_id: int,
        request_ip: str | None,
    ) -> list[ResumeCoverLetterSection]:
        """기존 자기소개서 목차를 모두 교체한다."""
        self.db.execute(
            delete(ResumeCoverLetterSection).where(
                ResumeCoverLetterSection.resume_id == resume_id
            )
        )
        rows: list[ResumeCoverLetterSection] = []
        for idx, s in enumerate(sections):
            title = (s.get("title") or "").strip()
            content = (s.get("content") or "").strip()
            if not title:
                continue
            row = ResumeCoverLetterSection(
                resume_id=resume_id,
                order_index=idx,
                title=title,
                content=content,
                created_by=actor_id,
                created_ip=request_ip,
                updated_by=actor_id,
                updated_ip=request_ip,
            )
            self.db.add(row)
            rows.append(row)
        self.db.flush()
        return rows

    def _delete_structured_data(self, resume_id: int) -> None:
        self.db.execute(
            delete(ResumeProject).where(ResumeProject.resume_id == resume_id)
        )
        self.db.execute(
            delete(ResumeCoverLetterSection).where(
                ResumeCoverLetterSection.resume_id == resume_id
            )
        )
