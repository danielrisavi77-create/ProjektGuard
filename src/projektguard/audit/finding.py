from typing import Any

from pydantic import BaseModel, Field

from projektguard.domain.enums import Severity, Verdict
from projektguard.domain.models import SourceRef


class Finding(BaseModel):
    rule_id: str
    verdict: Verdict
    severity: Severity
    reason_code: str
    message: str
    subject_type: str | None = None
    subject_id: str | None = None
    facts: dict[str, Any] = Field(default_factory=dict)
    sources: list[SourceRef] = Field(default_factory=list)
    requires_expert_review: bool = False
