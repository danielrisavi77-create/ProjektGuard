from datetime import date

from pydantic import BaseModel, Field


class SourceRef(BaseModel):
    document_id: str
    page: int | None = Field(default=None, ge=1)
    url: str | None = None
    available_from: date | None = None
