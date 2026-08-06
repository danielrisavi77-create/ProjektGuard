from datetime import date
from decimal import Decimal

from projektguard.audit.finding import Finding
from projektguard.audit.registry import Rule, register_rule
from projektguard.audit.runner import run_rule
from projektguard.audit.tolerance import TolerancePolicy
from projektguard.domain.enums import ExecutionClass, Severity, Verdict
from projektguard.domain.models import AuditContext, EligibilityPeriod, ProjectFinancials


def _context():
    return AuditContext(
        project_id="P1",
        as_of=date(2026, 1, 1),
        eligibility=EligibilityPeriod(start=date(2026, 1, 1), end=date(2026, 12, 31)),
        financials=ProjectFinancials(
            total_project_cost=Decimal("100"),
            eligible_cost=Decimal("90"),
            grant_amount=Decimal("50"),
            currency="EUR",
        ),
    )


def test_runner_returns_registered_rule_findings():
    def fake_rule(context, tolerance):
        return [
            Finding(
                rule_id="RX",
                verdict=Verdict.VERIFIED,
                severity=Severity.INFO,
                reason_code="OK",
                message="ok",
            )
        ]

    register_rule(Rule("RX", "Fake", ExecutionClass.DETERMINISTIC, Severity.INFO, fake_rule))
    findings = run_rule("RX", _context(), TolerancePolicy())
    assert findings[0].reason_code == "OK"
