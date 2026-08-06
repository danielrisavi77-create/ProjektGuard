FINANCIAL_INTEGRITY_RULE_IDS = (
    "R04", "R07", "R09", "R11", "R18", "R22", "R26", "R30", "R32",
    "R44", "R51", "R53", "R54", "R61", "R62",
)


def load_financial_integrity_rules() -> None:
    from projektguard.rules import baseline, budget, duplicate, payment, procurement  # noqa: F401


EVIDENCE_INTEGRITY_RULE_IDS = ("R35", "R36", "R37", "R38", "R39", "R40", "R41", "R42", "R43")


def load_evidence_integrity_rules() -> None:
    from projektguard.rules import evidence_presence, evidence_reconciliation, indicator  # noqa: F401
