from dataclasses import dataclass, field
from typing import Dict, Optional
from datetime import timedelta


@dataclass
class TableAudit:
    """Audit information for a single table's join."""
    table: str
    total_joined_pairs: int
    kept_pairs: int
    dropped_future_pairs: int
    max_future_delta: Optional[timedelta] = None


@dataclass
class AuditReport:
    """Audit report for a build_features run."""
    tables: Dict[str, TableAudit] = field(default_factory=dict)
