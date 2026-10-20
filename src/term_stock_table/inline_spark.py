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
    up: Optional[bool] = None,
    lo: Optional[float] = None,
    hi: Optional[float] = None,
    color: Optional[str] = None,
    guide: Optional[float] = None,
) -> Text:
    """Connected braille line chart: (2*width) x (4*rows) dots, continuous like a smooth curve."""
    data = [float(v) for v in series]
    if len(data) < 2:
        return Text(" " * width)
    pw, ph = width * 2, rows * 4
    lo_override, hi_override = lo, hi
    lo, hi = min(data), max(data)
    if baseline is not None:
        lo, hi = min(lo, baseline), max(hi, baseline)
    if lo_override is not None and hi_override is not None:
        lo, hi = lo_override, hi_override
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
    area = [[0] * width for _ in range(rows)]

    def plot(x: int, y: int, target=None) -> None:
        row, dy = divmod(ph - 1 - y, 4)
        (target or grid)[row][x // 2] |= _BRAILLE_BITS[dy][x % 2]

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
                plot(x, yy, area)

    if up is None:
        up = data[-1] >= data[0]
    red, green = ("bright_red", "bright_green")
    dim_red, dim_green = ("red3", "green4")
    is_red = up if palette == "cn" else not up
    style = red if is_red else green
    dim_style = dim_red if is_red else dim_green
    if color:
        style, dim_style = color, color
    guide_row = None
    if guide is not None and lo <= guide <= hi:
        guide_row = (ph - 1 - level(guide)) // 4
    text = Text()
    for r in range(rows):
        if r:
            text.append("\n")
        for c in range(width):
            line_bits, area_bits = grid[r][c], area[r][c]
            if guide_row == r and not (line_bits | area_bits):
                text.append("┄", style="grey35")
                continue
            ch = chr(0x2800 + (line_bits | area_bits))
            text.append(ch, style=style if line_bits else dim_style)
    return text


class AutoCurve:
    """Braille curve that stretches to the available width."""

    def __init__(self, series: Sequence[float], rows: int = 4, palette: str = "cn", fill: bool = True):
        self.series, self.rows, self.palette, self.fill = list(series), rows, palette, fill

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield braille_curve(self.series, max(8, options.max_width), self.rows, self.palette, self.fill)


OVERLAY_BLANK_WIDTH = 20
OVERLAY_QUEUE: Optional[list] = None


def overlay_begin() -> list:
    """Start collecting trend cells that the TUI paints as images after each frame."""
    global OVERLAY_QUEUE
    OVERLAY_QUEUE = []
    return OVERLAY_QUEUE


def overlay_end() -> None:
    global OVERLAY_QUEUE
    OVERLAY_QUEUE = None


def overlay_blank(width: int) -> str:
    return "\u2800" * width


def terminal_supports_images() -> bool:
    forced = os.environ.get("STK_SPARK_MODE", "").lower()
    if forced:
        return forced == "image"
    try:
        return str(detect_terminal_protocol().value) == "iterm2"
    except Exception:
        return False


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
@lru_cache(maxsize=512)
def flatten_on(escape: str, rgb: tuple) -> str:
    """Composite a transparent inline PNG onto the cell colour so it blends with the TUI.

    iTerm2 shows transparent pixels over the default terminal background, which
    differs from the explicit colours Textual paints, so the image is made opaque.
    """
    import base64
    import io
    import re

    m = re.search(r"File=([^:]*):([A-Za-z0-9+/=]+)", escape)
    if not m:
        return escape
    try:
        from PIL import Image

        img = Image.open(io.BytesIO(base64.b64decode(m.group(2)))).convert("RGBA")
        out = Image.new("RGBA", img.size, tuple(rgb) + (255,))
        out.alpha_composite(img)
        buf = io.BytesIO()
        out.save(buf, format="PNG")
        data = base64.b64encode(buf.getvalue()).decode("ascii")
    except Exception:
        return escape
    return escape[: m.start(2)] + data + escape[m.end(2):]


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
    if OVERLAY_QUEUE is not None and rows == 1 and len(data) >= 2:
        OVERLAY_QUEUE.append((data, length, palette))
        text = Text(overlay_blank(length))
        if annotation is not None:
            text.append(" ")
            text.append_text(annotation)
        return text
    if rows == 1 and len(data) >= 2 and sys.stdout.isatty() and image_sparklines_supported():
        return InlineSparkCell(data, length, annotation, palette=palette, **{k: v for k, v in kwargs.items() if k != "up"})
    text = braille_curve(data, length, rows, palette, fill=bool(kwargs.get("fill")), up=kwargs.get("up"))
    if annotation is not None:
        lines = text.split("\n")
        lines[0].append(" ")
        lines[0].append_text(annotation)
        text = Text("\n").join(lines)
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
