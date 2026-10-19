"""Smooth inline-image sparklines that stay aligned inside Rich tables."""
import os
import sys
from functools import lru_cache
from typing import Any, Optional, Sequence

from rich.console import Console, ConsoleOptions, RenderResult
from rich.segment import Segment
from rich.control import ControlType
from rich.console import RenderableType
from rich.table import Table
from rich.text import Text
from term_sparkline import detect_terminal_protocol, sparkline


def image_sparklines_supported() -> bool:
    """True when the terminal renders iTerm2 inline images (iTerm2, WezTerm, ...)."""
    forced = os.environ.get("STK_SPARK_MODE", "").lower()
    if forced:
        return forced == "image"
    try:
        return str(detect_terminal_protocol().value) == "iterm2"
    except Exception:
        return False


@lru_cache(maxsize=512)
def _image(series: tuple, length: int, palette: str, extra: tuple) -> str:
    return sparkline(list(series), length=length, mode="iterm2", annotate=False, palette=palette, **dict(extra))


def smart_spark(
    series: Sequence[float],
    length: int = 12,
    palette: str = "cn",
    annotation: Optional[Text] = None,
    fallback_mode: str = "block",
    **kwargs: Any,
) -> RenderableType:
    """Smooth image curve on iTerm2-like terminals, text sparkline elsewhere."""
    data = list(series)
    if len(data) >= 2 and sys.stdout.isatty() and image_sparklines_supported():
        return InlineSparkCell(data, length, annotation, palette=palette, **kwargs)
    text = Text.from_ansi(sparkline(data, length=length, mode=fallback_mode, palette=palette, annotate=False, **kwargs)) if data else Text(" " * length)
    if annotation is not None:
        text.append(" ")
        text.append_text(annotation)
    return text


def labeled(label: RenderableType, spark: RenderableType, length: int) -> Table:
    """One aligned line: text label followed by a spark cell of fixed width."""
    row = Table.grid(padding=(0, 1))
    row.add_column(no_wrap=True)
    row.add_column(no_wrap=True, width=length)
    row.add_row(label, spark)
    return row


class InlineSparkCell:
    """Cell that reserves `length` blank columns, then paints the image over them.

    The image escape is emitted as a zero-width control segment, so Rich's width
    math stays correct; a cursor-back moves over the reserved blanks first, and
    the image advances the cursor by exactly `length` columns.
    """

    def __init__(self, series: Sequence[float], length: int, annotation: Optional[Text] = None, palette: str = "cn", **kwargs: Any):
        self.length = length
        self.annotation = annotation
        self.image = _image(tuple(series), length, palette, tuple(sorted(kwargs.items())))

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield Segment(" " * self.length)
        yield Segment(f"\x1b[{self.length}D{self.image}", None, [(ControlType.BELL,)])
        if self.annotation is not None:
            yield Segment(" ")
            yield from console.render(self.annotation, options.update(width=max(1, options.max_width - self.length - 1)))
