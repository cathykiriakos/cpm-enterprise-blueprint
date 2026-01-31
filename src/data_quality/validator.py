"""
Data Quality Validation Framework
Author: Catherine Kiriakos
"""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CheckSeverity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class CheckType(Enum):
    COMPLETENESS = "completeness"
    VALIDITY = "validity"
    UNIQUENESS = "uniqueness"
    CONSISTENCY = "consistency"
    TIMELINESS = "timeliness"


@dataclass
class QualityCheck:
    name: str
    check_type: CheckType
    severity: CheckSeverity
    description: str
    field: Optional[str] = None
    rule: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.params is None:
            self.params = {}


@dataclass
class CheckResult:
    check_name: str
    passed: bool
    severity: CheckSeverity
    records_checked: int
    records_failed: int
    failure_rate: float
    failed_record_ids: Optional[List[str]] = None
    details: Optional[str] = None
    
    def __post_init__(self):
        if self.failed_record_ids is None:
            self.failed_record_ids = []
    
    def to_dict(self) -> Dict:
        return {
            "check_name": self.check_name,
            "passed": self.passed,
            "severity": self.severity.value,
            "records_checked": self.records_checked,
            "records_failed": self.records_failed,
            "failure_rate": round(self.failure_rate, 4),
        }


@dataclass
class ValidationReport:
    dataset_name: str
    validation_timestamp: datetime
    total_records: int
    checks_run: int
    checks_passed: int
    checks_failed: int
    overall_pass: bool
    results: Optional[List[CheckResult]] = None
    
    def __post_init__(self):
        if self.results is None:
            self.results = []
    
    def summary(self) -> str:
        status = "✅ PASSED" if self.overall_pass else "❌ FAILED"
        lines = [
            f"\n{'='*60}",
            f"DATA QUALITY REPORT: {self.dataset_name}",
            f"{'='*60}",
            f"Status: {status}",
            f"Records: {self.total_records:,}",
            f"Checks: {self.checks_passed}/{self.checks_run} passed",
        ]
        for result in self.results:
            icon = "✓" if result.passed else "✗"
            lines.append(f"  {icon} {result.check_name}: {result.records_failed}/{result.records_checked} failed")
        return "\n".join(lines)


class DataValidator:
    PATTERNS = {
        'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        'phone': r'^\d{10,11}$',
        'zip': r'^\d{5}(-\d{4})?$',
    }
    
    def __init__(self):
        self.checks: List[QualityCheck] = []
    
    def add_check(self, check: QualityCheck):
        self.checks.append(check)
    
    def add_checks(self, checks: List[QualityCheck]):
        self.checks.extend(checks)
    
    def validate(self, data, dataset_name: str = "dataset") -> ValidationReport:
        import pandas as pd
        df = pd.DataFrame(data) if isinstance(data, list) else data
        
        results = []
        for check in self.checks:
            result = self._run_check(check, df)
            results.append(result)
        
        checks_passed = sum(1 for r in results if r.passed)
        error_failures = [r for r in results if not r.passed and r.severity == CheckSeverity.ERROR]
        
        return ValidationReport(
            dataset_name=dataset_name,
            validation_timestamp=datetime.now(),
            total_records=len(df),
            checks_run=len(results),
            checks_passed=checks_passed,
            checks_failed=len(results) - checks_passed,
            overall_pass=len(error_failures) == 0,
            results=results,
        )
    
    def _run_check(self, check: QualityCheck, df) -> CheckResult:
        try:
            if check.check_type == CheckType.COMPLETENESS:
                return self._check_completeness(check, df)
            elif check.check_type == CheckType.VALIDITY:
                return self._check_validity(check, df)
            elif check.check_type == CheckType.UNIQUENESS:
                return self._check_uniqueness(check, df)
            else:
                return CheckResult(check.name, True, check.severity, len(df), 0, 0)
        except Exception as e:
            return CheckResult(check.name, False, check.severity, 0, 0, 0, details=str(e))
    
    def _check_completeness(self, check: QualityCheck, df) -> CheckResult:
        if check.field not in df.columns:
            return CheckResult(check.name, False, check.severity, len(df), len(df), 1.0, 
                             details=f"Field '{check.field}' not found")
        
        is_empty = df[check.field].isna() | (df[check.field].astype(str).str.strip() == '')
        failed = int(is_empty.sum())
        rate = failed / len(df) if len(df) > 0 else 0
        threshold = check.params.get('threshold', 0.0) if check.params else 0.0
        
        return CheckResult(check.name, rate <= threshold, check.severity, len(df), failed, rate)
    
    def _check_validity(self, check: QualityCheck, df) -> CheckResult:
        if check.field not in df.columns:
            return CheckResult(check.name, False, check.severity, len(df), len(df), 1.0)
        
        non_null = df[check.field].dropna()
        failed = 0
        
        params = check.params or {}
        if 'pattern' in params:
            pattern = self.PATTERNS.get(params['pattern'], params['pattern'])
            is_valid = non_null.astype(str).str.match(pattern, na=False)
            failed = int((~is_valid).sum())
        elif 'allowed_values' in params:
            is_valid = non_null.isin(params['allowed_values'])
            failed = int((~is_valid).sum())
        elif 'min_value' in params or 'max_value' in params:
            min_v = params.get('min_value', float('-inf'))
            max_v = params.get('max_value', float('inf'))
            is_valid = (non_null >= min_v) & (non_null <= max_v)
            failed = int((~is_valid).sum())
        
        rate = failed / len(non_null) if len(non_null) > 0 else 0
        threshold = params.get('threshold', 0.0)
        
        return CheckResult(check.name, rate <= threshold, check.severity, len(non_null), failed, rate)
    
    def _check_uniqueness(self, check: QualityCheck, df) -> CheckResult:
        if check.field not in df.columns:
            return CheckResult(check.name, False, check.severity, len(df), len(df), 1.0)
        
        duplicates = df[df.duplicated(subset=[check.field], keep=False)]
        failed = len(duplicates)
        
        return CheckResult(check.name, failed == 0, check.severity, len(df), failed,
                          failed / len(df) if len(df) > 0 else 0)


def get_constituent_checks() -> List[QualityCheck]:
    return [
        QualityCheck("constituent_id_not_null", CheckType.COMPLETENESS, CheckSeverity.ERROR,
                    "Constituent ID required", field="constituent_id"),
        QualityCheck("constituent_id_unique", CheckType.UNIQUENESS, CheckSeverity.ERROR,
                    "Constituent ID must be unique", field="constituent_id"),
        QualityCheck("email_format", CheckType.VALIDITY, CheckSeverity.WARNING,
                    "Email format validation", field="canonical_email",
                    params={"pattern": "email", "threshold": 0.05}),
        QualityCheck("lifecycle_valid", CheckType.VALIDITY, CheckSeverity.ERROR,
                    "Valid lifecycle stage", field="lifecycle_stage",
                    params={"allowed_values": ["prospect", "one_time_donor", "sustainer", "major_donor", "lapsed"]}),
        QualityCheck("churn_score_range", CheckType.VALIDITY, CheckSeverity.WARNING,
                    "Churn score 0-1", field="churn_risk_score",
                    params={"min_value": 0, "max_value": 1}),
    ]


if __name__ == "__main__":
    import pandas as pd
    
    test_data = pd.DataFrame({
        'constituent_id': ['UC-001', 'UC-002', 'UC-003'],
        'canonical_email': ['test@example.com', 'bad', 'good@test.org'],
        'lifecycle_stage': ['sustainer', 'prospect', 'invalid'],
        'churn_risk_score': [0.5, 0.8, 1.5],
    })
    
    validator = DataValidator()
    validator.add_checks(get_constituent_checks())
    report = validator.validate(test_data, "test")
    print(report.summary())