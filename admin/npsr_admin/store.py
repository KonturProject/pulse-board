"""Local history of facts (SQLite, outside the repository).

A new collection of a source replaces that source's facts for every (metric, period) it contains, so recomputed
past days overwrite old values and repeated collections never duplicate.
"""

import sqlite3
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from .model import Fact, ParseResult
from .weeks import iso_week


@dataclass(frozen=True)
class SourceInfo:
    source: str
    data_date: date | None
    collected_at: str


class Store:
    def __init__(self, path: Path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS facts (source TEXT, metric TEXT, period TEXT, grp TEXT, employee TEXT,
                                              num REAL, den REAL);
            CREATE INDEX IF NOT EXISTS facts_sp ON facts (source, period);
            CREATE TABLE IF NOT EXISTS sources (source TEXT PRIMARY KEY, data_date TEXT, collected_at TEXT);
            """
        )

    def save(self, result: ParseResult) -> None:
        """Replace this source's facts for each (metric, period) it brings; an empty result changes nothing
        and an older file never moves the source's data date back."""
        if not result.facts:
            return
        keys = sorted({(f.metric, f.period) for f in result.facts})
        row = self.db.execute("SELECT data_date FROM sources WHERE source = ?", (result.source,)).fetchone()
        dates = [d for d in (row[0] if row else None, result.data_date.isoformat() if result.data_date else None) if d]
        with self.db:
            self.db.executemany("DELETE FROM facts WHERE source = ? AND metric = ? AND period = ?",
                                [(result.source, m, p) for m, p in keys])
            self.db.executemany(
                "INSERT INTO facts VALUES (?, ?, ?, ?, ?, ?, ?)",
                [(result.source, f.metric, f.period, f.group, f.employee, f.num, f.den) for f in result.facts],
            )
            self.db.execute(
                "INSERT OR REPLACE INTO sources VALUES (?, ?, ?)",
                (result.source, max(dates) if dates else None, datetime.now().isoformat(timespec="seconds")),
            )

    def facts(self, since: date) -> list[Fact]:
        day, week = since.isoformat(), iso_week(since)
        rows = self.db.execute("SELECT metric, period, grp, employee, num, den FROM facts").fetchall()
        return [Fact(*r) for r in rows if (r[1] >= day if "-" in r[1] else r[1] >= week)]

    def sources(self) -> list[SourceInfo]:
        rows = self.db.execute("SELECT source, data_date, collected_at FROM sources ORDER BY source").fetchall()
        return [SourceInfo(s, date.fromisoformat(d) if d else None, c) for s, d, c in rows]
