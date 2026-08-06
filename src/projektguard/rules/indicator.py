from decimal import Decimal, InvalidOperation

from projektguard.audit.finding import Finding
from projektguard.audit.registry import Rule, register_rule
from projektguard.audit.tolerance import TolerancePolicy
from projektguard.domain.enums import ExecutionClass, Severity, Verdict
from projektguard.domain.evidence import EvidenceType
from projektguard.domain.evidence_queries import evidence_by_id, evidence_for, observable_evidence
from projektguard.domain.models import AuditContext


def _source_visible(row, context):
    return bool(row.sources) and any(s.available_from is None or s.available_from <= context.as_of for s in row.sources)


def _indicator_rows(context, indicator_id, types=None):
    rows=evidence_for(context,entity_type='indicator',entity_id=indicator_id,evidence_types=types)
    return [r for r in rows if _source_visible(r,context)]


def _dec(value):
    if value is None: return None
    try: return Decimal(str(value))
    except (InvalidOperation, ValueError): return None


def evaluate_r40(context: AuditContext, tolerance: TolerancePolicy) -> list[Finding]:
    if not context.indicators:
        return [Finding(rule_id='R40',verdict=Verdict.NOT_APPLICABLE,severity=Severity.HIGH,reason_code='NO_INDICATORS',message='No indicators.')]
    out=[]
    for ind in context.indicators:
        resolved=[]
        for eid in ind.source_ids:
            row=evidence_by_id(context,eid)
            if row is not None and _source_visible(row,context): resolved.append(row)
        if ind.baseline is None or ind.target is None or not ind.source_ids or len(resolved)!=len(ind.source_ids):
            verdict=Verdict.UNKNOWN; reason='INDICATOR_BASELINE_TARGET_NOT_TRACEABLE'
        else:
            baselines={v for row in resolved if (v:=_dec(row.facts.get('baseline'))) is not None}
            targets={v for row in resolved if (v:=_dec(row.facts.get('target'))) is not None}
            if len(baselines)>1 or len(targets)>1:
                verdict=Verdict.EXPERT_REVIEW; reason='INDICATOR_APPROVED_VALUES_CONFLICT'
            elif (baselines and ind.baseline not in baselines) or (targets and ind.target not in targets):
                verdict=Verdict.EXPERT_REVIEW; reason='INDICATOR_APPROVED_VALUES_CONFLICT'
            else:
                verdict=Verdict.VERIFIED; reason='INDICATOR_BASELINE_TARGET_TRACEABLE'
        out.append(Finding(rule_id='R40',verdict=verdict,severity=Severity.HIGH,reason_code=reason,message='Indicator baseline/target traceability evaluated.',subject_type='indicator',subject_id=ind.indicator_id,sources=[s for r in resolved for s in r.sources],requires_expert_review=verdict==Verdict.EXPERT_REVIEW))
    return out


def evaluate_r41(context: AuditContext, tolerance: TolerancePolicy) -> list[Finding]:
    if not context.indicators:
        return [Finding(rule_id='R41',verdict=Verdict.NOT_APPLICABLE,severity=Severity.HIGH,reason_code='NO_INDICATORS',message='No indicators.')]
    out=[]
    for ind in context.indicators:
        if not ind.required_evidence_types:
            verdict=Verdict.NOT_APPLICABLE; reason='NO_PRESCRIBED_EVIDENCE_TYPES'; rows=[]
        else:
            rows=_indicator_rows(context,ind.indicator_id,set(ind.required_evidence_types))
            present={r.evidence_type for r in rows}
            ok=all(t in present for t in ind.required_evidence_types)
            verdict=Verdict.VERIFIED if ok else Verdict.UNKNOWN
            reason='PRESCRIBED_INDICATOR_EVIDENCE_PRESENT' if ok else 'PRESCRIBED_INDICATOR_EVIDENCE_NOT_AVAILABLE'
        out.append(Finding(rule_id='R41',verdict=verdict,severity=Severity.HIGH,reason_code=reason,message='Prescribed indicator evidence evaluated.',subject_type='indicator',subject_id=ind.indicator_id,sources=[s for r in rows for s in r.sources]))
    return out


def evaluate_r42(context: AuditContext, tolerance: TolerancePolicy) -> list[Finding]:
    if not context.indicators:
        return [Finding(rule_id='R42',verdict=Verdict.NOT_APPLICABLE,severity=Severity.HIGH,reason_code='NO_INDICATORS',message='No indicators.')]
    out=[]
    for ind in context.indicators:
        rows=_indicator_rows(context,ind.indicator_id,set(ind.required_evidence_types) if ind.required_evidence_types else None)
        if ind.actual is None:
            verdict=Verdict.UNKNOWN; reason='INDICATOR_ACTUAL_NOT_AVAILABLE'
        elif ind.calculation_method not in (None,'direct'):
            verdict=Verdict.EXPERT_REVIEW; reason='INDICATOR_CALCULATION_REQUIRES_EXPERT_REVIEW'
        elif ind.required_evidence_types and not all(t in {r.evidence_type for r in rows} for t in ind.required_evidence_types):
            verdict=Verdict.UNKNOWN; reason='INDICATOR_SUPPORTING_EVIDENCE_NOT_AVAILABLE'
        else:
            values={v for r in rows if (v:=_dec(r.facts.get('actual_value'))) is not None}
            if not values:
                verdict=Verdict.UNKNOWN; reason='INDICATOR_ACTUAL_EVIDENCE_VALUE_NOT_AVAILABLE'
            elif len(values)>1:
                verdict=Verdict.EXPERT_REVIEW; reason='INDICATOR_ACTUAL_EVIDENCE_CONFLICT'
            elif ind.actual in values:
                verdict=Verdict.VERIFIED; reason='INDICATOR_ACTUAL_SUPPORTED'
            else:
                verdict=Verdict.WARNING; reason='INDICATOR_ACTUAL_MISMATCH'
        out.append(Finding(rule_id='R42',verdict=verdict,severity=Severity.HIGH,reason_code=reason,message='Indicator actual value support evaluated.',subject_type='indicator',subject_id=ind.indicator_id,sources=[s for r in rows for s in r.sources],requires_expert_review=verdict==Verdict.EXPERT_REVIEW))
    return out


def evaluate_r43(context: AuditContext, tolerance: TolerancePolicy) -> list[Finding]:
    if not context.indicators:
        return [Finding(rule_id='R43',verdict=Verdict.NOT_APPLICABLE,severity=Severity.HIGH,reason_code='NO_INDICATORS',message='No indicators.')]
    completions=[r for r in observable_evidence(context) if r.evidence_type==EvidenceType.PROJECT_COMPLETION and _source_visible(r,context)]
    out=[]
    for ind in context.indicators:
        prescribed=_indicator_rows(context,ind.indicator_id,set(ind.required_evidence_types) if ind.required_evidence_types else None)
        prescribed_ok=not ind.required_evidence_types or all(t in {r.evidence_type for r in prescribed} for t in ind.required_evidence_types)
        if ind.actual is not None and prescribed_ok:
            verdict=Verdict.NOT_APPLICABLE; reason='INDICATOR_HAS_OWN_EVIDENCE'
        elif completions or context.executions:
            verdict=Verdict.UNKNOWN; reason='COMPLETION_DOES_NOT_VERIFY_INDICATOR'
        else:
            verdict=Verdict.NOT_APPLICABLE; reason='NO_COMPLETION_INFERENCE_PRESENT'
        out.append(Finding(rule_id='R43',verdict=verdict,severity=Severity.HIGH,reason_code=reason,message='Project completion is not used as outcome proof.',subject_type='indicator',subject_id=ind.indicator_id,sources=[s for r in completions for s in r.sources]))
    return out

register_rule(Rule('R40','Indicator baseline and target are traceable',ExecutionClass.EVIDENCE,Severity.HIGH,evaluate_r40))
register_rule(Rule('R41','Required indicator evidence exists',ExecutionClass.EVIDENCE,Severity.HIGH,evaluate_r41))
register_rule(Rule('R42','Indicator actual value is supported',ExecutionClass.EVIDENCE,Severity.HIGH,evaluate_r42))
register_rule(Rule('R43','Completion does not imply indicator achievement',ExecutionClass.EVIDENCE,Severity.HIGH,evaluate_r43))
