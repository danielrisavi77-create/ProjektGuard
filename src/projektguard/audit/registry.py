from collections.abc import Callable
from dataclasses import dataclass

from projektguard.audit.finding import Finding
from projektguard.audit.tolerance import TolerancePolicy
from projektguard.domain.enums import ExecutionClass, Severity
from projektguard.domain.models import AuditContext

RuleFn = Callable[[AuditContext, TolerancePolicy], list[Finding]]


@dataclass(frozen=True)
class Rule:
    rule_id: str
    name: str
    execution_class: ExecutionClass
    default_severity: Severity
    evaluate: RuleFn


_RULES: dict[str, Rule] = {}


def register_rule(rule: Rule) -> None:
    _RULES[rule.rule_id] = rule


def get_rule(rule_id: str) -> Rule:
    try:
        return _RULES[rule_id]
    except KeyError as exc:
        raise KeyError(f"unknown rule: {rule_id}") from exc
