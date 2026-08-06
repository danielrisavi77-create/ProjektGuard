import json
from pathlib import Path

from pydantic import BaseModel

from projektguard.audit.finding import Finding
from projektguard.audit.runner import run_rule
from projektguard.audit.tolerance import TolerancePolicy
from projektguard.domain.enums import Severity, Verdict
from projektguard.domain.models import AuditContext
from projektguard.rules import load_evidence_integrity_rules


class EvidenceBenchmarkCase(BaseModel):
    test_id: str
    rule_id: str
    fixture: str
    expected_verdict: Verdict
    expected_reason_code: str
    requires_source: bool = False
    mode: str = 'synthetic'


class EvidenceBenchmarkResult(BaseModel):
    test_id: str
    rule_id: str
    expected_verdict: Verdict
    actual_verdict: Verdict
    severity: Severity
    passed: bool
    source_required: bool
    source_ok: bool
    mode: str


class EvidenceBenchmarkSummary(BaseModel):
    total: int
    passed: int
    pass_rate: float
    critical_false_positives: int
    unknown_expected: int
    unknown_correct: int
    unknown_discipline: float
    source_required_cases: int
    high_critical_source_completeness: float
    retrospective_cases: int
    pre_cutoff_cases: int


_PRIORITY={Verdict.NOT_APPLICABLE:0,Verdict.VERIFIED:1,Verdict.UNKNOWN:2,Verdict.EXPERT_REVIEW:3,Verdict.WARNING:4}


def _decisive(findings: list[Finding]) -> Finding:
    if not findings: raise AssertionError('rule returned no findings')
    return max(findings,key=lambda f:(_PRIORITY[f.verdict], f.severity.value))


def load_cases(path: Path) -> list[EvidenceBenchmarkCase]:
    return [EvidenceBenchmarkCase.model_validate(row) for row in json.loads(path.read_text(encoding='utf-8'))]


def evaluate_manifest(path: Path) -> tuple[list[EvidenceBenchmarkResult],EvidenceBenchmarkSummary]:
    load_evidence_integrity_rules()
    rows=[]
    for case in load_cases(path):
        context=AuditContext.model_validate_json((path.parent/case.fixture).read_text(encoding='utf-8'))
        finding=_decisive(run_rule(case.rule_id,context,TolerancePolicy()))
        source_ok=(not case.requires_source) or bool(finding.sources)
        passed=finding.verdict==case.expected_verdict and finding.reason_code==case.expected_reason_code and source_ok
        rows.append(EvidenceBenchmarkResult(test_id=case.test_id,rule_id=case.rule_id,expected_verdict=case.expected_verdict,actual_verdict=finding.verdict,severity=finding.severity,passed=passed,source_required=case.requires_source,source_ok=source_ok,mode=case.mode))
    total=len(rows); passed=sum(r.passed for r in rows); unknown=[r for r in rows if r.expected_verdict==Verdict.UNKNOWN]; sourced=[r for r in rows if r.source_required]
    summary=EvidenceBenchmarkSummary(total=total,passed=passed,pass_rate=1 if not total else passed/total,critical_false_positives=sum(1 for r in rows if r.severity==Severity.CRITICAL and r.actual_verdict==Verdict.WARNING and r.expected_verdict!=Verdict.WARNING),unknown_expected=len(unknown),unknown_correct=sum(r.actual_verdict==Verdict.UNKNOWN for r in unknown),unknown_discipline=1 if not unknown else sum(r.actual_verdict==Verdict.UNKNOWN for r in unknown)/len(unknown),source_required_cases=len(sourced),high_critical_source_completeness=1 if not sourced else sum(r.source_ok for r in sourced)/len(sourced),retrospective_cases=sum(r.mode=='retrospective' for r in rows),pre_cutoff_cases=sum(r.mode=='pre_cutoff' for r in rows))
    return rows,summary
