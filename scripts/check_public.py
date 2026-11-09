"""Refuse to let raw reports or local admin state into the public repository.

Usage: python scripts/check_public.py <paths...>   (exit 1 if any path is forbidden)
Used by the pre-commit hook (staged files) and by CI (all tracked files).
"""

import sys
from pathlib import PurePosixPath

FORBIDDEN_SUFFIXES = {".xls", ".xlsx", ".xlsb", ".xlsm", ".sqlite", ".db"}
FORBIDDEN_PARTS = {".superpowers"}


def forbidden(path: str) -> str | None:
    p = PurePosixPath(path.replace("\\", "/"))
    if p.suffix.lower() in FORBIDDEN_SUFFIXES:
        return "исходный отчёт или локальная история"
    if FORBIDDEN_PARTS & set(p.parts):
        return "локальные рабочие файлы"
    if p.name == "config.json" and "web" not in p.parts:
        return "локальный конфиг админки"
    return None


def main(paths: list[str]) -> int:
    bad = [(p, why) for p in paths if (why := forbidden(p))]
    for p, why in bad:
        print(f"ЗАПРЕЩЕНО в публичном репозитории: {p} ({why})", file=sys.stderr)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
