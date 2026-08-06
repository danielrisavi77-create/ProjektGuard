from projektguard.audit.finding import Finding
from projektguard.audit.registry import get_rule
from projektguard.audit.tolerance import TolerancePolicy
from projektguard.domain.models import AuditContext


def run_rule(rule_id: str, context: AuditContext, tolerance: TolerancePolicy) -> list[Finding]:
    return get_rule(rule_id).evaluate(context, tolerance)


def run_rules(rule_ids: list[str], context: AuditContext, tolerance: TolerancePolicy) -> list[Finding]:
    findings: list[Finding] = []
    for rule_id in rule_ids:
        findings.extend(run_rule(rule_id, context, tolerance))
    return findings
