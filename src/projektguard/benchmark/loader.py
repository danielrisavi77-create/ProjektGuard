import json
from pathlib import Path

from projektguard.benchmark.models import BenchmarkCase
from projektguard.domain.models import AuditContext


def load_manifest(path: Path) -> list[BenchmarkCase]:
    return [BenchmarkCase.model_validate(item) for item in json.loads(path.read_text(encoding="utf-8"))]


def load_context(path: Path) -> AuditContext:
    return AuditContext.model_validate_json(path.read_text(encoding="utf-8"))
