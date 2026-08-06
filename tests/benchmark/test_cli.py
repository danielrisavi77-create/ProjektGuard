import json
import subprocess
import sys
from pathlib import Path


def test_cli_writes_json_summary(tmp_path: Path):
    output = tmp_path / "summary.json"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "projektguard.benchmark.cli",
            "--manifest",
            "benchmark/financial_integrity_core/manifest.json",
            "--json-output",
            str(output),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["pass_rate"] >= 0.98
