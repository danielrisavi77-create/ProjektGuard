
def test_slice_gate_runs_five_stages_in_order(monkeypatch):
    import projektguard.dev.slice_gate as gate
    calls=[]
    monkeypatch.setattr(gate, 'run_command', lambda cmd: calls.append(cmd) or 0)
    assert gate.main(['evidence-integrity']) == 0
    assert len(calls) == 5
    assert 'tests/rules/evidence' in calls[0]
    assert 'test_adversarial_evidence.py' in calls[1]
    assert '--cov-fail-under=90' in calls[2]
    assert 'financial_integrity_core' in calls[3]
    assert 'evidence_integrity' in calls[4]


def test_slice_gate_stops_after_failure(monkeypatch):
    import projektguard.dev.slice_gate as gate
    results=iter([0,3])
    calls=[]
    monkeypatch.setattr(gate, 'run_command', lambda cmd: calls.append(cmd) or next(results))
    assert gate.main(['evidence-integrity']) == 3
    assert len(calls)==2
