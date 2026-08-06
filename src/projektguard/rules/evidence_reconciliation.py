from collections import Counter
from decimal import Decimal, InvalidOperation

from projektguard.audit.finding import Finding
from projektguard.audit.registry import Rule, register_rule
from projektguard.audit.tolerance import TolerancePolicy
from projektguard.domain.enums import ExecutionClass, Severity, Verdict
from projektguard.domain.evidence import EvidenceType
from projektguard.domain.evidence_queries import evidence_for
from projektguard.domain.models import AuditContext


def _norm(value) -> str | None:
    if value is None:
        return None
    text = str(value).strip().casefold()
    return text or None


def _requirement(context: AuditContext, execution_id: str):
    rows = evidence_for(context, entity_type="execution", entity_id=execution_id, evidence_types={EvidenceType.EXECUTION_REPORT, EvidenceType.DELIVERY_NOTE})
    return next((row for row in reversed(rows) if row.sources), None)


def evaluate_r36(context: AuditContext, tolerance: TolerancePolicy) -> list[Finding]:
    if not context.executions:
        return [Finding(rule_id="R36", verdict=Verdict.NOT_APPLICABLE, severity=Severity.HIGH, reason_code="NO_EXECUTIONS", message="No execution records.")]
    out = []
    for execution in context.executions:
        requirement = _requirement(context, execution.execution_id)
        expected = _norm(requirement.facts.get("expected_item_name")) if requirement else None
        actual = _norm(execution.item_name)
        if expected is None or actual is None:
            verdict, reason = Verdict.UNKNOWN, "ITEM_IDENTITY_INSUFFICIENT"
        elif expected == actual:
            verdict, reason = Verdict.VERIFIED, "ITEM_IDENTITY_MATCH"
        else:
            verdict, reason = Verdict.WARNING, "ITEM_IDENTITY_MISMATCH"
        out.append(Finding(rule_id="R36", verdict=verdict, severity=Severity.HIGH, reason_code=reason, message="Item identity reconciliation evaluated.", subject_type="execution", subject_id=execution.execution_id, facts={"expected": expected, "actual": actual}, sources=requirement.sources if requirement else []))
    return out


def evaluate_r37(context: AuditContext, tolerance: TolerancePolicy) -> list[Finding]:
    if not context.executions:
        return [Finding(rule_id="R37", verdict=Verdict.NOT_APPLICABLE, severity=Severity.HIGH, reason_code="NO_EXECUTIONS", message="No execution records.")]
    out = []
    for execution in context.executions:
        requirement = _requirement(context, execution.execution_id)
        raw = requirement.facts.get("expected_quantity") if requirement else None
        expected_unit = _norm(requirement.facts.get("expected_unit")) if requirement else None
        actual_unit = _norm(execution.unit)
        try:
            expected = Decimal(str(raw)) if raw is not None else None
        except InvalidOperation:
            expected = None
        actual = execution.quantity
        if expected is None or actual is None or expected_unit is None or actual_unit is None:
            verdict, reason = Verdict.UNKNOWN, "QUANTITY_RECONCILIATION_INSUFFICIENT"
        elif expected_unit != actual_unit:
            verdict, reason = Verdict.EXPERT_REVIEW, "QUANTITY_UNIT_MISMATCH"
        elif expected == actual:
            verdict, reason = Verdict.VERIFIED, "QUANTITY_MATCH"
        else:
            verdict, reason = Verdict.WARNING, "QUANTITY_MISMATCH"
        out.append(Finding(rule_id="R37", verdict=verdict, severity=Severity.HIGH, reason_code=reason, message="Quantity reconciliation evaluated.", subject_type="execution", subject_id=execution.execution_id, facts={"expected_quantity": expected, "actual_quantity": actual, "expected_unit": expected_unit, "actual_unit": actual_unit}, sources=requirement.sources if requirement else [], requires_expert_review=verdict == Verdict.EXPERT_REVIEW))
    return out


def evaluate_r38(context: AuditContext, tolerance: TolerancePolicy) -> list[Finding]:
    if not context.executions:
        return [Finding(rule_id="R38", verdict=Verdict.NOT_APPLICABLE, severity=Severity.HIGH, reason_code="NO_EXECUTIONS", message="No execution records.")]
    serials = Counter(_norm(execution.serial_number) for execution in context.executions if _norm(execution.serial_number))
    out = []
    for execution in context.executions:
        requirement = _requirement(context, execution.execution_id)
        facts = requirement.facts if requirement else {}
        actual_serial, actual_model, actual_reference = _norm(execution.serial_number), _norm(execution.model), _norm(execution.reference)
        expected_serial, expected_model, expected_reference = _norm(facts.get("expected_serial_number")), _norm(facts.get("expected_model")), _norm(facts.get("expected_reference"))
        if actual_serial and serials[actual_serial] > 1:
            verdict, reason = Verdict.WARNING, "DUPLICATE_EXECUTION_IDENTIFIER"
        else:
            required = [(expected_serial, actual_serial), (expected_model, actual_model), (expected_reference, actual_reference)]
            required = [pair for pair in required if pair[0] is not None]
            if not required:
                verdict, reason = Verdict.UNKNOWN, "IDENTIFIER_REQUIREMENT_UNKNOWN"
            elif any(actual is None for _, actual in required):
                verdict, reason = Verdict.UNKNOWN, "REQUIRED_IDENTIFIER_MISSING"
            elif any(expected != actual for expected, actual in required):
                verdict, reason = Verdict.WARNING, "IDENTIFIER_MISMATCH"
            else:
                verdict, reason = Verdict.VERIFIED, "IDENTIFIERS_MATCH"
        out.append(Finding(rule_id="R38", verdict=verdict, severity=Severity.HIGH, reason_code=reason, message="Execution identifiers evaluated.", subject_type="execution", subject_id=execution.execution_id, facts={"expected_serial": expected_serial, "actual_serial": actual_serial, "expected_model": expected_model, "actual_model": actual_model}, sources=requirement.sources if requirement else []))
    return out


register_rule(Rule("R36", "Delivered item matches approved item", ExecutionClass.EVIDENCE, Severity.HIGH, evaluate_r36))
register_rule(Rule("R37", "Execution quantity reconciles", ExecutionClass.EVIDENCE, Severity.HIGH, evaluate_r37))
register_rule(Rule("R38", "Execution identifiers are consistent", ExecutionClass.EVIDENCE, Severity.HIGH, evaluate_r38))
