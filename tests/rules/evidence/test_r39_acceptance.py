from datetime import date
from projektguard.audit.runner import run_rule
from projektguard.audit.tolerance import TolerancePolicy
from projektguard.domain.enums import Verdict
from projektguard.domain.evidence import AcceptanceRecord, AcceptanceType, EvidenceRecord, EvidenceType, ExecutionRecord
from projektguard.domain.models import AuditContext, EligibilityPeriod, ProjectFinancials, SourceRef

def base(acceptances=None,evidence=None):
    from projektguard.rules import load_evidence_integrity_rules
    load_evidence_integrity_rules()
    return AuditContext(project_id='P',as_of=date(2026,8,6),eligibility=EligibilityPeriod(start=date(2026,1,1),end=date(2026,12,31)),financials=ProjectFinancials(currency='EUR'),executions=[ExecutionRecord(execution_id='X')],acceptances=acceptances or [],evidence=evidence or [])
def a(value,eid='EV'): return AcceptanceRecord(acceptance_id='A',execution_id='X',acceptance_type=AcceptanceType.COMMISSIONING,accepted=value,evidence_ids=[eid])
def e(when=date(2026,8,1)): return EvidenceRecord(evidence_id='EV',evidence_type=EvidenceType.COMMISSIONING_RECORD,observed_at=when,supports_entity_type='execution',supports_entity_id='X',sources=[SourceRef(document_id='commission.pdf')])
def verdict(c): return run_rule('R39',c,TolerancePolicy())[0].verdict

def test_R39_accepted_with_evidence_verified(): assert verdict(base([a(True)],[e()]))==Verdict.VERIFIED
def test_R39_missing_acceptance_unknown(): assert verdict(base())==Verdict.UNKNOWN
def test_R39_unknown_acceptance_unknown(): assert verdict(base([a(None)],[e()]))==Verdict.UNKNOWN
def test_R39_rejected_acceptance_warning(): assert verdict(base([a(False)],[e()]))==Verdict.WARNING
def test_R39_future_acceptance_evidence_unknown(): assert verdict(base([a(True)],[e(date(2026,8,7))]))==Verdict.UNKNOWN
