
def test_unknown_rule_returns_nonzero():
    from projektguard.dev.rule_gate import main
    assert main(['R99']) != 0


def test_rule_gate_stops_on_first_failure(monkeypatch):
    import projektguard.dev.rule_gate as gate
    calls=[]
    monkeypatch.setattr(gate, 'run_command', lambda cmd: calls.append(cmd) or 7)
    assert gate.main(['R35']) == 7
    assert len(calls) == 1


def test_rule_gate_returns_zero_when_all_stages_pass(monkeypatch):
    import projektguard.dev.rule_gate as gate
    calls=[]
    monkeypatch.setattr(gate, 'run_command', lambda cmd: calls.append(cmd) or 0)
    assert gate.main(['R35']) == 0
    assert calls
