"""Find the newest report in each configured folder, copy it locally, parse it, store the facts.

One failing source never stops the others: its error is reported in its CollectItem.
"""

import shutil
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from .config import Config, home
from .parsers import REGISTRY
from .store import Store


@dataclass
class CollectItem:
    source: str
    file: str | None = None
    data_date: date | None = None
    facts: int = 0
    warnings: list[str] = field(default_factory=list)
    error: str | None = None


def find_latest(folder: Path, pattern: str) -> Path | None:
    files = [p for p in Path(folder).glob(pattern) if p.is_file() and not p.name.startswith("~$")]
    return max(files, key=lambda p: p.stat().st_mtime) if files else None


def collect(cfg: Config, store: Store, files: dict[str, Path] | None = None,
            progress: Callable[[str], None] = print) -> list[CollectItem]:
    files = files or {}
    cache = home() / "cache"
    cache.mkdir(parents=True, exist_ok=True)
    items = []
    for source, rc in cfg.reports.items():
        item = CollectItem(source)
        items.append(item)
        try:
            src = files.get(source)
            if src is None:
                folder = Path(rc.folder) if rc.folder else None
                if folder is None or not folder.is_dir():
                    item.error = f"папка недоступна: {rc.folder}" if rc.folder else "папка не указана"
                    progress(f"{source}: {item.error}")
                    continue
                src = find_latest(folder, rc.pattern)
                if src is None:
                    item.error = f"в папке нет файла по шаблону {rc.pattern}"
                    progress(f"{source}: {item.error}")
                    continue
            item.file = str(src)
            progress(f"{source}: копирую {Path(src).name}")
            local = cache / f"{source}{Path(src).suffix.lower()}"
            if Path(src).resolve() != local.resolve():
                shutil.copy2(src, local)
            progress(f"{source}: считаю показатели")
            result = REGISTRY[source](local)
            if not result.facts:
                result.warnings.append("0 записей — похоже, отчёт поменял вид; данные не обновлены")
            elif result.data_date is None:  # weekly pivots carry no day: judge freshness by the file's date
                result.data_date = date.fromtimestamp(Path(src).stat().st_mtime)
            store.save(result)
            item.data_date, item.facts, item.warnings = result.data_date, len(result.facts), result.warnings
            progress(f"{source}: готово, {item.facts} записей")
        except Exception as e:  # noqa: BLE001 — any report problem must stay local to that report
            item.error = f"{type(e).__name__}: {e}"
            progress(f"{source}: ошибка — {item.error}")
    return items
