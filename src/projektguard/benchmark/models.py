from datetime import date
from enum import Enum

from pydantic import BaseModel

from projektguard.domain.enums import Severity, Verdict


class BenchmarkMode(str, Enum):
    SYNTHETIC = "synthetic"
    RETROSPECTIVE = "retrospective"
    PRE_CUTOFF = "pre_cutoff"


class BenchmarkExpectation(BaseModel):
    verdict: Verdict
    severity: Severity | None = None
    reason_code: str | None = None
    requires_source: bool = False


class BenchmarkCase(BaseModel):
    test_id: str
    case_id: str
    rule_id: str
    fixture: str
    expected: BenchmarkExpectation
    source_url: str
    source_observed_at: date | None = None
    ground_truth: str
    ground_truth_url: str | None = None
    ground_truth_observed_at: date | None = None
    ground_truth_verdict: Verdict | None = None
    mode: BenchmarkMode = BenchmarkMode.SYNTHETIC
