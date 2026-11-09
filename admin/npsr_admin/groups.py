"""The six monitored groups of the direction and the mapping from report spellings to group keys."""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Group:
    key: str
    label: str
    branch: str


GROUPS: dict[str, Group] = {
    g.key: g
    for g in [
        Group("СР1", "СР1 ГБ", "Тверь"),
        Group("СР2", "СР2 Фин", "Тверь"),
        Group("СР3", "СР3 ГБ", "Тверь"),
        Group("СР5", "СР5 ГБ УД", "Тверь"),
        Group("СР6", "СР6 Право", "Тверь"),
        Group("СР9", "СР9 ГБА", "Тверь"),
    ]
}

# The direction is one filial (СР5 is formally in Тверь too), so branch rows would repeat the direction.
BRANCHES: list[str] = []

_GROUP_RE = re.compile(r"НП_СР_.*?_СР(\d+)(?:_|$)")


def match_group(name: object) -> str | None:
    """Group key for a department name like `КЦПК_НП_СР_Тверь_СР1_ГБ`; None for anything else."""
    if not isinstance(name, str):
        return None
    m = _GROUP_RE.search(name.strip())
    if not m:
        return None
    key = f"СР{m.group(1)}"
    return key if key in GROUPS else None
