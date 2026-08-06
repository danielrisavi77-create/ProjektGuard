from datetime import date
from decimal import Decimal
from projektguard.audit.runner import run_rule
from projektguard.audit.tolerance import TolerancePolicy
from projektguard.domain.enums import Verdict
from projektguard.domain.evidence import EvidenceRecord, EvidenceType
from projektguard.domain.models import AuditContext, Cost, EligibilityPeriod, ProjectFinancials, SourceRef


def ctx(evidence=None, costs=None, claimed=None, as_of=date(2026,8,6)):
    from projektguard.rules import load_evidence_integrity_rules
    load_evidence_integrity_rules()
    return AuditContext(project_id='P',as_of=as_of,eligibility=EligibilityPeriod(start=date(2026,1,1),end=date(2026,12,31)),financials=ProjectFinancials(currency='EUR'),evidence=evidence or [],costs=costs or [],claimed_cost_ids=claimed or [])

def cost(cid): return Cost(cost_id=cid,invoice_number=cid,invoice_date=date(2026,8,1),amount=Decimal('10'),currency='EUR',budget_line_id='B')
def ev(cid, when=date(2026,8,1), sourced=True): return EvidenceRecord(evidence_id='E-'+cid,evidence_type=EvidenceType.DELIVERY_NOTE,observed_at=when,supports_entity_type='cost',supports_entity_id=cid,sources=[SourceRef(document_id='d-'+cid)] if sourced else [])

def test_R35_sourced_observable_delivery_evidence_verifies_cost():
    f=run_rule('R35',ctx(evidence=[ev('C1')],costs=[cost('C1')],claimed=['C1']),TolerancePolicy())[0]
    assert f.verdict==Verdict.VERIFIED and f.subject_id=='C1'

def test_R35_missing_evidence_is_unknown():
    assert run_rule('R35',ctx(costs=[cost('C1')],claimed=['C1']),TolerancePolicy())[0].verdict==Verdict.UNKNOWN

def test_R35_future_evidence_is_unknown():
    assert run_rule('R35',ctx(evidence=[ev('C1',date(2026,8,7))],costs=[cost('C1')],claimed=['C1']),TolerancePolicy())[0].verdict==Verdict.UNKNOWN

def test_R35_second_cost_missing_is_not_hidden_by_first():
    fs=run_rule('R35',ctx(evidence=[ev('C1')],costs=[cost('C1'),cost('C2')],claimed=['C1','C2']),TolerancePolicy())
    assert {f.subject_id:f.verdict for f in fs}=={'C1':Verdict.VERIFIED,'C2':Verdict.UNKNOWN}
