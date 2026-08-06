from pathlib import Path
import subprocess
import sys

RULE_TESTS = {
    "R35": ["tests/rules/evidence/test_r35_execution_evidence.py"],
    "R36": ["tests/rules/evidence/test_r36_item_match.py"],
    "R37": ["tests/rules/evidence/test_r37_quantity_reconciliation.py"],
    "R38": ["tests/rules/evidence/test_r38_identifier_consistency.py"],
    "R39": ["tests/rules/evidence/test_r39_acceptance.py"],
    "R40": ["tests/rules/evidence/test_r40_indicator_traceability.py"],
    "R41": ["tests/rules/evidence/test_r41_indicator_evidence.py"],
    "R42": ["tests/rules/evidence/test_r42_indicator_actual.py"],
    "R43": ["tests/rules/evidence/test_r43_completion_not_achievement.py"],
}


def run_command(command: str) -> int:
    print(f"[rule-gate] {command}")
    return subprocess.run(command, shell=True, check=False).returncode


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1 or args[0] not in RULE_TESTS:
        print("usage: python -m projektguard.dev.rule_gate R35..R43")
        return 2
    rule_id = args[0]
    commands = [f"{sys.executable} -m pytest {' '.join(RULE_TESTS[rule_id])} -q"]
    adversarial = Path("tests/rules/evidence/test_adversarial_evidence.py")
    if adversarial.exists():
        commands.append(f"{sys.executable} -m pytest {adversarial} -q -k {rule_id}")
    for command in commands:
        code = run_command(command)
        if code:
            return code
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
