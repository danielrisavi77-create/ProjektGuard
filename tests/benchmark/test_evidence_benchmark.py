from pathlib import Path

def test_evidence_benchmark_acceptance_contract():
    from projektguard.benchmark.evidence_evaluator import evaluate_manifest
    rows,summary=evaluate_manifest(Path('benchmark/evidence_integrity/manifest.json'))
    assert summary.total >= 18
    assert summary.pass_rate >= .98
    assert summary.unknown_discipline >= .95
    assert summary.critical_false_positives == 0
    assert summary.high_critical_source_completeness == 1.0


def test_evidence_cli_writes_summary_and_returns_zero(tmp_path):
    from projektguard.benchmark.evidence_cli import main
    output=tmp_path/'evidence-summary.json'
    code=main(['--manifest','benchmark/evidence_integrity/manifest.json','--json-output',str(output)])
    assert code==0
    assert '"total": 18' in output.read_text()
