"""Read the pivot cache stored inside an .xlsb workbook (MS-XLSB binary records).

A pivot table only shows what its author expanded, but Excel keeps every source row in the pivot cache
(`xl/pivotCache/pivotCacheDefinitionN.bin` + `pivotCacheRecordsN.bin`). Reading the cache gives the full
detail — down to employees — no matter how the pivot is collapsed, protected or filtered.

Supported: field definitions with shared items (arrays and single items), calculated fields (only the
indices of the fields their formula refers to), records in both the detailed and the compact format.
"""

import re
import struct
import zipfile
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

BEGIN_FIELD, FIELD_ATTRS, ITEM_ARRAY, CALC_REF = 0x00B7, 0x00BD, 0x00BF, 0x00FF
ITEM_STRING = (0x18, 0x1F)
ITEM_NUMBER = (0x15, 0x1C)
ITEM_MISSING = (0x14, 0x1B)
REC_DETAILED, REC_COMPACT, REC_INDEX = 0x22, 0x21, 0x1A
NUMERIC_FLAGS = (0xD3, 0xC2)


def records(b: bytes) -> Iterator[tuple[int, bytes]]:
    """BIFF12 records: variable-length type (1–2 bytes) and size (1–4 bytes)."""
    i, n = 0, len(b)
    while i < n:
        t = b[i]
        i += 1
        if t & 0x80:
            t = (t & 0x7F) | (b[i] << 7)
            i += 1
        size, shift = 0, 0
        for _ in range(4):
            byte = b[i]
            i += 1
            size |= (byte & 0x7F) << shift
            shift += 7
            if not byte & 0x80:
                break
        yield t, b[i:i + size]
        i += size


def _wstr(d: bytes, off: int = 0) -> tuple[str, int]:
    n = struct.unpack_from("<I", d, off)[0]
    return d[off + 4: off + 4 + 2 * n].decode("utf-16le"), off + 4 + 2 * n


@dataclass
class CacheField:
    name: str
    calc: bool = False
    flags: int = 0
    count: int = 0  # number of shared items; 0 = values are stored inline in the records
    items: list = field(default_factory=list)
    refs: list[int] = field(default_factory=list)  # calculated field: indices of the fields in its formula


def read_definition(b: bytes) -> list[CacheField]:
    fields: list[CacheField] = []
    cur = None
    for t, d in records(b):
        if t == BEGIN_FIELD:
            cur = CacheField(name=_wstr(d, 20)[0], calc=len(d) > 1 and d[1] == 1)
            fields.append(cur)
        elif cur is None:
            continue
        elif t == FIELD_ATTRS:
            cur.flags = d[0]
            cur.count = struct.unpack_from("<I", d, 2)[0]
        elif t == ITEM_ARRAY:
            kind, n = struct.unpack_from("<HI", d, 0)
            off = 6
            for _ in range(n):
                if kind == 2:
                    s, off = _wstr(d, off)
                    cur.items.append(s)
                elif kind == 1:
                    cur.items.append(struct.unpack_from("<d", d, off)[0])
                    off += 8
                else:
                    raise ValueError(f"неизвестный тип массива {kind} в поле {cur.name}")
        elif t in ITEM_STRING:
            cur.items.append(_wstr(d)[0])
        elif t in ITEM_NUMBER:
            cur.items.append(struct.unpack_from("<d", d)[0])
        elif t in ITEM_MISSING:
            cur.items.append(None)
        elif t == CALC_REF:
            cur.refs.append(struct.unpack_from("<I", d)[0])
    for f in fields:
        if f.count and len(f.items) != f.count:
            raise ValueError(f"поле {f.name}: {len(f.items)} значений вместо {f.count}")
    return fields


def read_rows(b: bytes, fields: list[CacheField]) -> Iterator[dict]:
    db = [f for f in fields if not f.calc]
    names = [f.name for f in db]
    row: list | None = None
    for t, d in records(b):
        if t == REC_DETAILED:
            if row is not None:
                yield dict(zip(names, row))
            row = []
        elif t == REC_COMPACT:
            if row is not None:
                yield dict(zip(names, row))
                row = None
            vals, off = [], 0
            for f in db:
                if f.count:
                    vals.append(f.items[struct.unpack_from("<I", d, off)[0]])
                    off += 4
                elif f.flags in NUMERIC_FLAGS:
                    vals.append(struct.unpack_from("<d", d, off)[0])
                    off += 8
                else:
                    s, off = _wstr(d, off)
                    vals.append(s)
            if off != len(d):
                raise ValueError("не удалось разобрать строку кэша сводной")
            yield dict(zip(names, vals))
        elif row is not None:
            if t == REC_INDEX:
                row.append(db[len(row)].items[struct.unpack_from("<I", d)[0]])
            elif t in ITEM_NUMBER:
                row.append(struct.unpack_from("<d", d)[0])
            elif t in ITEM_STRING:
                row.append(_wstr(d)[0])
            elif t in ITEM_MISSING:
                row.append(None)
    if row is not None:
        yield dict(zip(names, row))


def find_cache(path: Path, calc_field_prefix: str) -> tuple[list[CacheField], CacheField, Iterator[dict]] | None:
    """The cache that has a calculated field whose name starts with `calc_field_prefix`:
    (fields, that calculated field, its rows) — or None."""
    with zipfile.ZipFile(path) as z:
        defs = sorted(n for n in z.namelist() if re.fullmatch(r"xl/pivotCache/pivotCacheDefinition\d+\.bin", n))
        for name in defs:
            fields = read_definition(z.read(name))
            calc = next((f for f in fields if f.calc and f.name.strip().startswith(calc_field_prefix)), None)
            if calc:
                rec = name.replace("Definition", "Records")
                return fields, calc, read_rows(z.read(rec), fields)
    return None
