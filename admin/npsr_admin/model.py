"""Facts: the one shape every parser produces.

A metric's value at any level (employee, group, branch, direction) is sum(num) / sum(den) over the
facts of that level, so shares, per-person averages and plan fulfilment all aggregate correctly.
"""

from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True)
class Fact:
    metric: str
    period: str  # "YYYY-MM-DD" (day) or "YYYY.WW" (ISO week)
    group: str  # group key from GROUPS, or "*" for the whole direction
    employee: str | None  # None = a value of the group itself (pivot row), not a sum of employees
    num: float
    den: float


@dataclass
class ParseResult:
    source: str
    data_date: date | None
    facts: list[Fact] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
