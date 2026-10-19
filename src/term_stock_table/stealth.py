"""Stealth view: the same market data disguised as ops telemetry (log stream, latency charts)."""
import hashlib
import time
from typing import Any, Dict, List, Optional

from rich.align import Align
from rich.box import ROUNDED, SIMPLE_HEAD
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .api import StockDataTracker
from .inline_spark import braille_curve

SLO_MS = 180.0
CHART_ROWS = 10
CHART_COLOR = "deep_sky_blue1"
ERR_COLOR = "orange3"
TIME_AXIS = ["-30m", "-15m", "now"]
PERIOD_LABELS = {
    "intraday": "live", "m5": "5m", "m15": "15m", "m30": "30m",
    "m60": "60m", "day": "1d", "week": "7d", "month": "30d",
}
SERVICE_REGISTRY: Dict[str, str] = {}


def _initials(name: str) -> str:
    """Pinyin initials for Chinese names, leading letters for Latin names."""
    try:
        from pypinyin import Style, lazy_pinyin
        parts = lazy_pinyin(name, style=Style.FIRST_LETTER, errors=lambda chunk: [chunk])
    except ImportError:
        parts = [c for c in name if c.isascii()]
    letters = "".join(c for c in "".join(parts).lower() if c.isalnum())
    return letters[:5]


def service_name(symbol: str, name: str = "") -> str:
    """Stable per-session alias derived from the stock name initials."""
    if symbol not in SERVICE_REGISTRY:
        base = _initials(name) or f"{len(SERVICE_REGISTRY) + 1}"
        alias, n = f"svc-{base}", 2
        while alias in SERVICE_REGISTRY.values():
            alias, n = f"svc-{base}{n}", n + 1
        SERVICE_REGISTRY[symbol] = alias
    return SERVICE_REGISTRY[symbol]


def stealth_period_label(period: str) -> str:
    return PERIOD_LABELS.get(period, period)


def to_ms(price: float, prev: float) -> float:
    """Map a price onto a latency figure around the SLO so real prices never appear."""
    return price / prev * SLO_MS if prev else SLO_MS


def trace_id(symbol: str, k: int) -> str:
    return hashlib.md5(f"{symbol}{k}".encode()).hexdigest()[:8]


def level_for(change_pct: float) -> tuple:
    if change_pct <= -3:
        return "ERROR", "red"
    if change_pct <= -1:
        return "WARN ", "yellow"
    return "INFO ", "green"


def render_log_view(trackers: List[StockDataTracker], selected_symbol: Optional[str] = None):
    """Main-screen disguise: a top process list with the holdings mixed in."""
    from .boss import render_devops_top
    return render_devops_top(trackers, selected_symbol)


def quantile(values: List[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(q * len(ordered)))]


def series_ms(tracker: StockDataTracker) -> List[float]:
    prev = tracker.prev_close or 1.0
    return [to_ms(p, prev) for p in tracker.prices]


class StealthChart:
    """Latency line chart with an SLO guide, ms axis and relative time axis."""

    def __init__(self, tracker: StockDataTracker):
        self.tracker = tracker

    def __rich_console__(self, console, options):
        tr = self.tracker
        values = series_ms(tr)
        width = options.max_width
        svc = service_name(tr.symbol, tr.name)
        if len(values) < 2:
            yield Text("collecting samples...", style="dim")
            return
        span = max(max(values) - SLO_MS, SLO_MS - min(values), 2.0)
        hi, lo = SLO_MS + span, SLO_MS - span
        yield Text(f"{svc}  p99 latency (ms)   last={values[-1]:.1f}  slo={SLO_MS:.0f}", style="grey70")
        chart_w = max(10, width - 9)
        curve = braille_curve(values, chart_w, CHART_ROWS, "cn", True, lo=lo, hi=hi, color=CHART_COLOR, guide=SLO_MS)
        labels = Text()
        for i in range(CHART_ROWS):
            label = f"{hi:.0f}" if i == 0 else (f"{SLO_MS:.0f}" if i == CHART_ROWS // 2 else (f"{lo:.0f}" if i == CHART_ROWS - 1 else ""))
            labels.append(label.rjust(7) + ("\n" if i < CHART_ROWS - 1 else ""), style="grey62")
        grid = Table.grid()
        grid.add_column(width=8)
        grid.add_column(width=chart_w)
        grid.add_row(labels, curve)
        axis = [" "] * chart_w
        for frac, label in zip((0.0, 0.5, 1.0), TIME_AXIS):
            start = min(max(0, round(frac * (chart_w - 1)) - len(label) // 2), chart_w - len(label))
            axis[start:start + len(label)] = list(label)
        grid.add_row("", Text("".join(axis), style="grey62"))
        yield grid
        vols = list(tr.volumes)
        if vols:
            n = min(len(vols), chart_w)
            peak = max(vols[-n:]) or 1
            bars = "".join(" ▁▂▃▄▅▆▇█"[min(8, round(v / peak * 8))] for v in vols[-n:])
            yield Text("req/s".rjust(7) + " " + bars, style="grey50")


class StealthBars:
    """K-line replacement: per-interval request outcome bars (blue ok, orange err)."""

    def __init__(self, candles: List[Dict[str, Any]], period: str, height: int = 10):
        self.candles, self.period, self.height = candles, period, height

    def __rich_console__(self, console, options):
        n = max(8, (options.max_width - 4) // 2)
        shown = self.candles[-n:]
        peak = max((c["high"] - c["low"]) for c in shown) or 1.0
        yield Text(f"errors per interval ({stealth_period_label(self.period)})   ok ■  err ■", style="grey70")
        rows = []
        for r in range(self.height, 0, -1):
            line = Text("  ")
            for c in shown:
                filled = round((c["high"] - c["low"]) / peak * self.height)
                color = CHART_COLOR if c["close"] >= c["open"] else ERR_COLOR
                line.append("█ " if filled >= r else "  ", style=color)
            rows.append(line)
        yield Group(*rows)


class StealthHeader:
    def __init__(self, tracker: StockDataTracker):
        self.tracker = tracker

    def __rich_console__(self, console, options):
        tr = self.tracker
        values = series_ms(tr) or [SLO_MS]
        ms = values[-1]
        delta = (ms - SLO_MS) / SLO_MS * 100
        style = "green" if delta <= 0 else "yellow"
        left = Text()
        left.append(f"{ms:.1f} ms\n", style=f"bold {style}")
        left.append(f"{delta:+.2f}% vs slo", style=style)
        stats = Table.grid(padding=(0, 1))
        for _ in range(2):
            stats.add_column(style="dim")
            stats.add_column(justify="right")
        stats.add_row("p50", f"{quantile(values, .5):.1f}", "err", f"{tr.amplitude:.2f}%")
        stats.add_row("p95", f"{quantile(values, .95):.1f}", "cpu", f"{tr.turnover_rate:.1f}%")
        stats.add_row("p99", f"{quantile(values, .99):.1f}", "rps", f"{tr.volume / 1000:.1f}k")
        outer = Table.grid(expand=True)
        outer.add_column(width=20)
        outer.add_column(justify="right", ratio=1)
        outer.add_row(left, stats)
        yield Panel(Group(Align.center(Text(service_name(tr.symbol, tr.name), style="bold bright_white")), outer),
                    box=ROUNDED, border_style="grey50", padding=(0, 1))


class StealthBody:
    def __init__(self, tracker: StockDataTracker, period: str, candles: Optional[List[Dict[str, Any]]]):
        self.tracker, self.period, self.candles = tracker, period, candles

    def __rich_console__(self, console, options):
        k_mode = self.period != "intraday" and bool(self.candles)
        main = StealthBars(self.candles, self.period) if k_mode else StealthChart(self.tracker)
        yield Panel(main, title=stealth_period_label(self.period), box=ROUNDED, border_style="grey50", padding=(0, 1))
        values = series_ms(self.tracker)
        table = Table(box=None, expand=True, show_header=True, header_style="bold grey70")
        for col in ("metric", "value", "threshold", "status"):
            table.add_column(col, justify="left" if col == "metric" else "right")
        for name, value, limit in (
            ("p50 latency", quantile(values, .5), SLO_MS),
            ("p95 latency", quantile(values, .95), SLO_MS * 1.1),
            ("p99 latency", quantile(values, .99), SLO_MS * 1.2),
        ):
            ok = value <= limit
            table.add_row(name, f"{value:.1f} ms", f"{limit:.0f} ms", Text("OK" if ok else "WARN", style="green" if ok else "yellow"))
        yield Panel(table, title="thresholds", box=ROUNDED, border_style="grey50", padding=(0, 1))
