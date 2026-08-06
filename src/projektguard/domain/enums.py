from enum import Enum


class Verdict(str, Enum):
    VERIFIED = "VERIFIED"
    WARNING = "WARNING"
    UNKNOWN = "UNKNOWN"
    EXPERT_REVIEW = "EXPERT_REVIEW"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class Severity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ExecutionClass(str, Enum):
    DETERMINISTIC = "D"
    EVIDENCE = "E"
    HUMAN = "H"
