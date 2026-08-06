from pydantic import BaseModel

from projektguard.domain.enums import Severity, Verdict


class BenchmarkExpectation(BaseModel):
    verdict: Verdict
    severity: Severity | None = None
    reason_code: str | None = None


class BenchmarkCase(BaseModel):
    test_id: str
    case_id: str
    rule_id: str
    fixture: str
    expected: BenchmarkExpectation
    source_url: str
    ground_truth: str
