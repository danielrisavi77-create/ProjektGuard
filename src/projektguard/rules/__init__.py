FINANCIAL_INTEGRITY_RULE_IDS = (
    "R04", "R07", "R09", "R11", "R18", "R22", "R26", "R30", "R32",
    "R44", "R51", "R53", "R54", "R61", "R62",
)


def load_financial_integrity_rules() -> None:
    from projektguard.rules import baseline, budget, duplicate, payment, procurement  # noqa: F401
