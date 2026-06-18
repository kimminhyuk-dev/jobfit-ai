"""Matching score response schemas."""

from pydantic import BaseModel, ConfigDict, Field


class ApplicationMatchScoreResponse(BaseModel):
    """Stored matching score summary for an application."""

    model_config = ConfigDict(from_attributes=True)

    score: int
    grade: str
    summary: str
    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    model: str
    algorithm_version: str
