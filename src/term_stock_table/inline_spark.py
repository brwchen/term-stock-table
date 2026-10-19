"""Smooth inline-image sparklines that stay aligned inside Rich tables."""
import os
from typing import Any, Sequence

from rich.console import Console, ConsoleOptions, RenderResult
from rich.segment import Segment
from rich.control import ControlType
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


class InlineSparkCell:
    """Cell that reserves `length` blank columns, then paints the image over them.

    The image escape is emitted as a zero-width control segment, so Rich's width
    math stays correct; a cursor-back moves over the reserved blanks first, and
    the image advances the cursor by exactly `length` columns.
    """

    def __init__(self, series: Sequence[float], length: int, annotation: Text, **kwargs: Any):
        self.length = length
        self.annotation = annotation
        self.image = sparkline(series, length=length, mode="iterm2", annotate=False, **kwargs)

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield Segment(" " * self.length)
        yield Segment(f"\x1b[{self.length}D{self.image}", None, [(ControlType.BELL,)])
        yield Segment(" ")
        yield from console.render(self.annotation, options.update(width=max(1, options.max_width - self.length - 1)))
