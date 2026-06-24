"""RAG 검색 요청과 응답 스키마."""

from pydantic import BaseModel, Field, model_validator


class ResumeChunkRetrieveRequest(BaseModel):
    """이력서 청크 검색 요청."""

    job_posting_id: int | None = None
    query_text: str | None = None
    top_k: int = Field(default=5, ge=1, le=20)
    sections: list[str] | None = None

    @model_validator(mode="after")
    def validate_query_source(self) -> "ResumeChunkRetrieveRequest":
        """공고 ID 또는 직접 쿼리 중 하나는 필요하다."""

        if self.job_posting_id is None and not (self.query_text or "").strip():
            raise ValueError("job_posting_id 또는 query_text가 필요합니다.")
        return self


class ResumeChunkRetrieveResult(BaseModel):
    """검색된 이력서 청크."""

    chunk_id: int
    section: str
    content: str
    distance: float
    similarity: float


class ResumeChunkRetrieveResponse(BaseModel):
    """이력서 청크 검색 응답."""

    resume_id: int
    query_preview: str
    top_k: int
    results: list[ResumeChunkRetrieveResult]
