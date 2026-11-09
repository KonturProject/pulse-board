"""Report parsers: each turns one report file into a ParseResult of facts."""

from collections.abc import Callable
from pathlib import Path

from ..model import ParseResult
from . import ak, attempts300, funnel_days, gkg, oper, orders, oz_attempts, oz_speed

REGISTRY: dict[str, Callable[[Path], ParseResult]] = {
    "oper": oper.parse,
    "funnel": funnel_days.parse,
    "gkg": gkg.parse,
    "attempts300": attempts300.parse,
    "ak": ak.parse,
    "orders": orders.parse,
    "oz_speed": oz_speed.parse,
    "oz_attempts": oz_attempts.parse,
}
