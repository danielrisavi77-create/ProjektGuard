from pathlib import Path

from projektguard.benchmark.loader import load_manifest
from projektguard.domain.enums import Verdict


def test_financial_integrity_manifest_loads_traceable_cases():
    manifest = load_manifest(Path("benchmark/financial_integrity_core/manifest.json"))
    assert manifest[0].test_id
    assert manifest[0].rule_id.startswith("R")
    assert isinstance(manifest[0].expected.verdict, Verdict)
    assert manifest[0].source_url.startswith("http") or manifest[0].source_url == "synthetic"
