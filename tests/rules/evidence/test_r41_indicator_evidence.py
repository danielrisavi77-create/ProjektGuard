from datetime import date
from projektguard.audit.runner import run_rule
from projektguard.audit.tolerance import TolerancePolicy
from projektguard.domain.enums import Verdict
from projektguard.domain.evidence import EvidenceRecord,EvidenceType,Indicator
from projektguard.domain.models import AuditContext,EligibilityPeriod,ProjectFinancials,SourceRef

def ctx(types,evidence):
 from projektguard.rules import load_evidence_integrity_rules; load_evidence_integrity_rules()
 ind=Indicator(indicator_id='I',title='x',unit='%',required_evidence_types=types)
 return AuditContext(project_id='P',as_of=date(2026,8,6),eligibility=EligibilityPeriod(start=date(2026,1,1),end=date(2026,12,31)),financials=ProjectFinancials(currency='EUR'),indicators=[ind],evidence=evidence)
def ev(t,when=date(2026,8,1),sourced=True): return EvidenceRecord(evidence_id=t.value,evidence_type=t,observed_at=when,supports_entity_type='indicator',supports_entity_id='I',sources=[SourceRef(document_id='d')] if sourced else [])
def v(c): return run_rule('R41',c,TolerancePolicy())[0].verdict
def test_R41_required_energy_audit_verified(): assert v(ctx([EvidenceType.ENERGY_AUDIT],[ev(EvidenceType.ENERGY_AUDIT)]))==Verdict.VERIFIED
def test_R41_completion_does_not_substitute_unknown(): assert v(ctx([EvidenceType.ENERGY_AUDIT],[ev(EvidenceType.PROJECT_COMPLETION)]))==Verdict.UNKNOWN
def test_R41_future_required_evidence_unknown(): assert v(ctx([EvidenceType.ENERGY_AUDIT],[ev(EvidenceType.ENERGY_AUDIT,date(2026,8,7))]))==Verdict.UNKNOWN
def test_R41_all_required_types_must_exist(): assert v(ctx([EvidenceType.ENERGY_AUDIT,EvidenceType.INDICATOR_REPORT],[ev(EvidenceType.ENERGY_AUDIT)]))==Verdict.UNKNOWN
def test_R41_source_less_required_evidence_unknown(): assert v(ctx([EvidenceType.ENERGY_AUDIT],[ev(EvidenceType.ENERGY_AUDIT,sourced=False)]))==Verdict.UNKNOWN
