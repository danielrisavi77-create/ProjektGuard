import subprocess
import sys


def run_command(command: str) -> int:
    print(f"[slice-gate] {command}")
    return subprocess.run(command, shell=True, check=False).returncode


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args != ["evidence-integrity"]:
        print("usage: python -m projektguard.dev.slice_gate evidence-integrity")
        return 2
    commands = [
        f"{sys.executable} -m pytest tests/rules/evidence -q",
        f"{sys.executable} -m pytest tests/rules/evidence/test_adversarial_evidence.py -q",
        f"{sys.executable} -m pytest --cov=projektguard --cov-report=term --cov-fail-under=90",
        f"{sys.executable} -m projektguard.benchmark.cli --manifest benchmark/financial_integrity_core/manifest.json --json-output benchmark-summary.json",
        f"{sys.executable} -m projektguard.benchmark.evidence_cli --manifest benchmark/evidence_integrity/manifest.json --json-output evidence-benchmark-summary.json",
    ]
    for command in commands:
        code = run_command(command)
        if code:
            return code
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
