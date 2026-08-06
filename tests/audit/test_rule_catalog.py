from projektguard.audit.registry import get_rule
from projektguard.rules import FINANCIAL_INTEGRITY_RULE_IDS, load_financial_integrity_rules


def test_financial_integrity_rule_catalog_contains_exact_slice():
    expected = {
        "R04", "R07", "R09", "R11", "R18", "R22", "R26", "R30", "R32",
        "R44", "R51", "R53", "R54", "R61", "R62",
    }
    assert set(FINANCIAL_INTEGRITY_RULE_IDS) == expected
    load_financial_integrity_rules()
    for rule_id in expected:
        assert get_rule(rule_id).rule_id == rule_id
