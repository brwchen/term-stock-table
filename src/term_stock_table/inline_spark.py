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


IMAGE_ENABLED = True


def set_image_enabled(enabled: bool) -> None:
    """Disable inline images in hosts that cannot pass raw escapes (e.g. Textual)."""
    global IMAGE_ENABLED
    IMAGE_ENABLED = enabled


_BRAILLE_BITS = ((1, 8), (2, 16), (4, 32), (64, 128))


def braille_curve(
    series: Sequence[float],
    width: int = 16,
    rows: int = 1,
    palette: str = "cn",
    fill: bool = False,
    baseline: Optional[float] = None,
) -> Text:
    """Connected braille line chart: (2*width) x (4*rows) dots, continuous like a smooth curve."""
    data = [float(v) for v in series]
    if len(data) < 2:
        return Text(" " * width)
    pw, ph = width * 2, rows * 4
    lo, hi = min(data), max(data)
    if baseline is not None:
        lo, hi = min(lo, baseline), max(hi, baseline)
    span = (hi - lo) or 1.0

    def level(v: float) -> int:
        return round((v - lo) / span * (ph - 1)) if hi != lo else (ph - 1) // 2

    n = len(data)
    spans = []
    for x in range(pw):
        if n > pw:
            # Envelope of every sample falling in this pixel column keeps spikes visible
            chunk = data[x * n // pw: max(x * n // pw + 1, (x + 1) * n // pw)]
            spans.append((level(min(chunk)), level(max(chunk))))
        else:
            pos = x * (n - 1) / (pw - 1)
            i = min(int(pos), n - 2)
            frac = pos - i
            y = level(data[i] * (1 - frac) + data[i + 1] * frac)
            spans.append((y, y))

    grid = [[0] * width for _ in range(rows)]

    def plot(x: int, y: int) -> None:
        row, dy = divmod(ph - 1 - y, 4)
        grid[row][x // 2] |= _BRAILLE_BITS[dy][x % 2]

    prev_mid = None
    for x, (y_lo, y_hi) in enumerate(spans):
        mid = (y_lo + y_hi) // 2
        lo_y, hi_y = y_lo, y_hi
        if prev_mid is not None:
            lo_y, hi_y = min(lo_y, prev_mid), max(hi_y, prev_mid)
        prev_mid = mid
        for yy in range(lo_y, hi_y + 1):
            plot(x, yy)
        if fill:
            for yy in range(0, lo_y):
                if (x + yy) % 2 == 0:
                    plot(x, yy)

    up = data[-1] >= data[0]
    red, green = "bright_red", "bright_green"
    style = (red if up else green) if palette == "cn" else (green if up else red)
    return Text("\n".join("".join(chr(0x2800 + c) for c in r) for r in grid), style=style)


class AutoCurve:
    """Braille curve that stretches to the available width."""

    def __init__(self, series: Sequence[float], rows: int = 4, palette: str = "cn", fill: bool = True):
        self.series, self.rows, self.palette, self.fill = list(series), rows, palette, fill

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield braille_curve(self.series, max(8, options.max_width), self.rows, self.palette, self.fill)


def image_sparklines_supported() -> bool:
    """True when the terminal renders iTerm2 inline images (iTerm2, WezTerm, ...)."""
    if not IMAGE_ENABLED:
        return False
    forced = os.environ.get("STK_SPARK_MODE", "").lower()
    if forced:
        return forced == "image"
    try:
        return str(detect_terminal_protocol().value) == "iterm2"
    except Exception:
        return False


@lru_cache(maxsize=512)
def _image(series: tuple, length: int, palette: str, extra: tuple) -> str:
    return sparkline(list(series), length=length, mode="iterm2", annotate=False, palette=palette, width_px=length * 12, height_px=24, **dict(extra))


def smart_spark(
    series: Sequence[float],
    length: int = 12,
    palette: str = "cn",
    annotation: Optional[Text] = None,
    rows: int = 1,
    **kwargs: Any,
) -> RenderableType:
    """Smooth image curve on iTerm2-like terminals, connected braille curve elsewhere."""
    data = list(series)
    if rows == 1 and len(data) >= 2 and sys.stdout.isatty() and image_sparklines_supported():
        return InlineSparkCell(data, length, annotation, palette=palette, **kwargs)
    text = braille_curve(data, length, rows, palette, fill=bool(kwargs.get("fill")))
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
