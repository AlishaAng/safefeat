from dataclasses import dataclass, field
from typing import Dict, Optional
from datetime import timedelta


@dataclass
class TableAudit:
    """Audit information for a single table's join.

    Attributes
    ----------
    table:
        Name of the events table.
    total_joined_pairs:
        Number of entity-cutoff × event pairs created by the join before any
        point-in-time filtering.
    kept_pairs:
        Number of pairs retained after applying the point-in-time "no future"
        rule.
    dropped_future_pairs:
        Number of pairs removed because the event occurred after the cutoff
        (subject to ``allowed_lag``).
    max_future_delta:
        The maximum time delta by which dropped events were in the future,
        or ``None`` if no events were dropped.
    """
    table: str
    total_joined_pairs: int
    kept_pairs: int
    dropped_future_pairs: int
    max_future_delta: Optional[timedelta] = None


@dataclass
class AuditReport:
    """Audit report for a :func:`build_features` run.

    This container maps table names to :class:`TableAudit` objects and is
    returned when ``build_features(..., return_report=True)`` is used.
    """
    tables: Dict[str, TableAudit] = field(default_factory=dict)

    def add_table(self, audit: TableAudit) -> None:
        """Add or replace the audit entry for a table."""
        self.tables[audit.table] = audit
