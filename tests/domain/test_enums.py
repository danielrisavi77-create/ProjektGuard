from projektguard.domain.enums import ExecutionClass, Severity, Verdict


def test_verdict_values_are_stable():
    assert [item.value for item in Verdict] == [
        "VERIFIED",
        "WARNING",
        "UNKNOWN",
        "EXPERT_REVIEW",
        "NOT_APPLICABLE",
    ]


def test_severity_values_are_stable():
    assert [item.value for item in Severity] == [
        "INFO",
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL",
    ]


def test_execution_class_values_are_stable():
    assert [item.value for item in ExecutionClass] == ["D", "E", "H"]
