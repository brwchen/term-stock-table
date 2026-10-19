"""Stock detail page: quote header, intraday/K-line chart with axes, order book, ticks and notes."""
from typing import Any, Dict, List, Optional

from rich.align import Align
from rich.box import ROUNDED, SIMPLE
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .api import StockDataTracker
from .config import get_symbol_notes
from .detail import CandleView, period_label
from .i18n import get_lang, t
from .indicators import (
    compute_bollinger_bands,
    compute_kdj,
    compute_macd,
    compute_rsi,
    compute_sma,
    estimate_valuation_percentile,
)
from .inline_spark import braille_curve
from .market import simulate_capital_flow

WIDE_LAYOUT_MIN = 72
BOOK_WIDTH = 28
CHART_ROWS = 10
BAR_LEVELS = " ▁▂▃▄▅▆▇█"
TIME_LABELS = [(0.0, "09:30"), (0.25, "10:30"), (0.5, "11:30"), (0.75, "14:00"), (1.0, "15:00")]


def trend_styles(palette: str) -> tuple:
    """Return (up_style, down_style) for the colour convention."""
    return ("bright_red", "bright_green") if palette == "cn" else ("bright_green", "bright_red")


def fmt_amount(value: float) -> str:
    v = abs(value)
    if get_lang() == "zh":
        if v >= 1e8:
            return f"{value / 1e8:.2f}亿"
        if v >= 1e4:
            return f"{value / 1e4:.2f}万"
    else:
        if v >= 1e9:
            return f"{value / 1e9:.2f}B"
        if v >= 1e6:
            return f"{value / 1e6:.2f}M"
        if v >= 1e3:
            return f"{value / 1e3:.1f}K"
    return f"{value:,.0f}"


def limit_pct(symbol: str, name: str = "") -> float:
    """Daily price-limit ratio for mainland A-shares (0 for markets without limits)."""
    if not (symbol.isdigit() and len(symbol) == 6):
        return 0.0
    if "ST" in name.upper():
        return 0.05
    if symbol.startswith(("300", "301", "688")):
        return 0.20
    if symbol.startswith(("8", "4")):
        return 0.30
    return 0.10


def minute_label(index: int) -> str:
    """Clock time of the n-th one-minute bar of an A-share session (09:30-11:30, 13:00-15:00)."""
    minutes = 9 * 60 + 30 + index if index < 120 else 13 * 60 + (index - 120)
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def style_for(value: float, ref: float, palette: str) -> str:
    up, down = trend_styles(palette)
    if value > ref:
        return up
    if value < ref:
        return down
    return "white"


class DetailHeader:
    """Name/code on top, big price on the left, key quote fields in a grid on the right."""

    def __init__(self, tracker: StockDataTracker, palette: str = "cn", expanded: bool = False):
        self.tracker, self.palette, self.expanded = tracker, palette, expanded

    def __rich_console__(self, console, options):
        tr = self.tracker
        up, down = trend_styles(self.palette)
        style = up if tr.change >= 0 else down
        arrow = "▲" if tr.change >= 0 else "▼"
        title = Text()
        title.append(tr.name, style="bold bright_white")
        title.append(f"  {tr.symbol}", style="dim")
        title.append("   ▴ " if self.expanded else "   ▾ ", style="bold cyan")
        title.append(t("d_collapse") if self.expanded else t("d_expand"), style="cyan")

        price = Text()
        price.append(f"{tr.price:.2f}\n", style=f"bold {style}")
        price.append(f"{tr.change:+.2f} {tr.change_pct:+.2f}% {arrow}", style=style)

        fields = [
            [("dh_high", f"{tr.high:.2f}", style_for(tr.high, tr.prev_close, self.palette)),
             ("dh_prev", f"{tr.prev_close:.2f}", "white"),
             ("dh_vol", fmt_amount(tr.volume), "white")],
            [("dh_low", f"{tr.low:.2f}", style_for(tr.low, tr.prev_close, self.palette)),
             ("dh_amp", f"{tr.amplitude:.2f}%", "white"),
             ("dh_turn", f"{tr.turnover_rate:.2f}%", "white")],
            [("dh_open", f"{tr.open:.2f}", style_for(tr.open, tr.prev_close, self.palette)),
             ("dh_pe", f"{tr.pe:.1f}", "white"),
             ("dh_amt", fmt_amount(tr.amount), "white")],
        ]
        grid = Table.grid(padding=(0, 1))
        for _ in range(3):
            grid.add_column(style="dim")
            grid.add_column(justify="right")
        for row in fields:
            cells = []
            for key, value, value_style in row:
                cells += [t(key), Text(value, style=value_style)]
            grid.add_row(*cells)

        outer = Table.grid(expand=True)
        outer.add_column(width=max(16, len(price.plain.split("\n")[1]) + 2))
        outer.add_column(justify="right", ratio=1)
        outer.add_row(price, grid)
        parts = [Align.center(title), outer]
        if self.expanded:
            parts.append(Text(t("d_market_data"), style="bold"))
            parts.append(self.extra_grid())
        yield Panel(Group(*parts), box=ROUNDED, border_style="cyan", padding=(0, 1))

    def extra_grid(self) -> Table:
        tr = self.tracker
        up, down = trend_styles(self.palette)
        limit = limit_pct(tr.symbol, tr.name)
        avg = tr.amount / tr.volume if tr.volume else 0.0
        if not (tr.low * 0.5 < avg < tr.high * 2):
            prices = list(tr.prices)
            avg = sum(prices) / len(prices) if prices else tr.price
        rows = [
            [("d_limit_up", f"{tr.prev_close * (1 + limit):.2f}" if limit else "-", up),
             ("d_avg", f"{avg:.2f}", style_for(avg, tr.prev_close, self.palette))],
            [("d_limit_down", f"{tr.prev_close * (1 - limit):.2f}" if limit else "-", down),
             ("dh_amp", f"{tr.amplitude:.2f}%", "white")],
            [("dh_prev", f"{tr.prev_close:.2f}", "white"), ("dh_amt", fmt_amount(tr.amount), "white")],
            [("d_volume_full", fmt_amount(tr.volume), "white"), ("dh_turn", f"{tr.turnover_rate:.2f}%", "white")],
            [("dh_pe", f"{tr.pe:.2f}", "white"), ("d_pb", f"{tr.pb:.2f}", "white")],
        ]
        grid = Table.grid(expand=True, padding=(0, 2))
        for _ in range(2):
            grid.add_column(style="dim", ratio=1)
            grid.add_column(justify="right", ratio=1)
        for row in rows:
            cells = []
            for key, value, st in row:
                cells += [t(key), Text(value, style=st)]
            grid.add_row(*cells)
        return grid


class PriceChart:
    """Intraday curve with prev-close baseline, +/-% axes and a coloured volume strip."""

    def __init__(self, tracker: StockDataTracker, palette: str):
        self.tracker, self.palette = tracker, palette

    def __rich_console__(self, console, options):
        tr, palette = self.tracker, self.palette
        up, down = trend_styles(palette)
        prices = list(tr.prices)
        vols = list(tr.volumes)
        prev = tr.prev_close or (prices[0] if prices else 1.0)
        width = options.max_width

        if len(prices) < 2:
            yield Text(t("d_loading"), style="dim")
            return

        dev = max(abs(max(prices) - prev), abs(min(prices) - prev), prev * 0.002)
        hi, lo = prev + dev, prev - dev
        pct = dev / prev * 100 if prev else 0.0
        avg = sum(prices) / len(prices)
        last_style = style_for(prices[-1], prev, palette)

        info = Text()
        info.append(f"{t('d_avg')}: {avg:.2f}  ", style="yellow")
        info.append(f"{t('d_latest')}: {prices[-1]:.2f}  ", style=last_style)
        info.append(f"{prices[-1] - prev:+.2f}  {(prices[-1] - prev) / prev * 100:+.2f}%" if prev else "", style=last_style)
        yield info

        def side(top: str, mid: str, bottom: str, styles: tuple, justify: str) -> Text:
            text = Text(justify=justify)
            for i in range(CHART_ROWS):
                label, st = ("", "")
                if i == 0:
                    label, st = top, styles[0]
                elif i == CHART_ROWS // 2:
                    label, st = mid, styles[1]
                elif i == CHART_ROWS - 1:
                    label, st = bottom, styles[2]
                text.append(label + ("\n" if i < CHART_ROWS - 1 else ""), style=st)
            return text

        left = side(f"{hi:.2f}", f"{prev:.2f}", f"{lo:.2f}", (up, "grey62", down), "left")
        right = side(f"+{pct:.2f}%", "0.00%", f"-{pct:.2f}%", (up, "grey62", down), "right")
        chart_w = max(10, width - 16)
        curve = braille_curve(prices, chart_w, CHART_ROWS, palette, True, baseline=prev,
                              up=prices[-1] >= prev, lo=lo, hi=hi)

        grid = Table.grid(expand=True)
        grid.add_column(width=8)
        grid.add_column(width=chart_w)
        grid.add_column(width=8, justify="right")
        grid.add_row(left, curve, right)
        axis = [" "] * chart_w
        for frac, label in TIME_LABELS:
            start = min(max(0, round(frac * (chart_w - 1)) - len(label) // 2), chart_w - len(label))
            if frac == 0.0:
                start = 0
            axis[start:start + len(label)] = list(label)
        grid.add_row("", Text("".join(axis), style="grey62"), "")
        if vols:
            grid.add_row(Text(t("d_vol_short"), style="grey62"), self.volume_strip(prices, vols, chart_w, prev), "")
        yield grid

    def volume_strip(self, prices: List[float], vols: List[float], width: int, prev: float) -> Text:
        n = min(len(prices), len(vols))
        prices, vols = prices[-n:], vols[-n:]
        up, down = trend_styles(self.palette)
        buckets = []
        for x in range(width):
            a, b = x * n // width, max(x * n // width + 1, (x + 1) * n // width)
            seg = vols[a:b] or [0]
            i = min(b, n) - 1
            rising = prices[i] >= (prices[i - 1] if i > 0 else prev)
            buckets.append((max(seg), up if rising else down))
        ordered = sorted(v for v, _ in buckets)
        peak = ordered[min(len(ordered) - 1, int(len(ordered) * 0.95))] or max(ordered) or 1
        rows = 2
        lines = [Text() for _ in range(rows)]
        for v, st in buckets:
            level = min(rows * 8, round(v / peak * rows * 8))
            for r in range(rows):
                cell = min(8, max(0, level - (rows - 1 - r) * 8))
                lines[r].append(BAR_LEVELS[cell], style=st)
        out = Text()
        for i, line in enumerate(lines):
            if i:
                out.append("\n")
            out.append_text(line)
        return out


def order_book(tracker: StockDataTracker, palette: str) -> Table:
    book = Table(box=None, show_header=False, expand=True, padding=(0, 1))
    book.add_column(width=3, style="grey62")
    book.add_column(justify="right")
    book.add_column(justify="right", style="white")
    prev = tracker.prev_close
    asks = tracker.asks or [(tracker.price + i * 0.01, 100 * i) for i in range(1, 6)]
    bids = tracker.bids or [(tracker.price - i * 0.01, 100 * i) for i in range(1, 6)]
    for idx in range(min(5, len(asks)) - 1, -1, -1):
        p, v = asks[idx]
        book.add_row(f"{t('d_sell')}{idx + 1}", Text(f"{p:.2f}", style=style_for(p, prev, palette)), fmt_amount(v))
    book.add_row("", "", "")
    for idx in range(min(5, len(bids))):
        p, v = bids[idx]
        book.add_row(f"{t('d_buy')}{idx + 1}", Text(f"{p:.2f}", style=style_for(p, prev, palette)), fmt_amount(v))
    return book


def tick_table(tracker: StockDataTracker, palette: str, count: int = 5) -> Table:
    ticks = Table(box=None, show_header=False, expand=True, padding=(0, 1))
    ticks.add_column(style="grey62")
    ticks.add_column(justify="right")
    ticks.add_column(justify="right", style="white")
    prices, vols = list(tracker.prices), list(tracker.volumes)
    n = min(len(prices), len(vols))
    for i in range(n - 1, max(0, n - count) - 1, -1):
        ref = prices[i - 1] if i > 0 else tracker.prev_close
        ticks.add_row(minute_label(i), Text(f"{prices[i]:.2f}", style=style_for(prices[i], ref, palette)), fmt_amount(vols[i]))
    return ticks


def side_panel(tracker: StockDataTracker, palette: str):
    return Group(
        Panel(order_book(tracker, palette), title=t("d_book"), box=ROUNDED, border_style="cyan", padding=(0, 1)),
        Panel(tick_table(tracker, palette), title=t("d_ticks"), box=ROUNDED, border_style="cyan", padding=(0, 1)),
    )


def render_detail_header(tracker: StockDataTracker, palette: str = "cn", expanded: bool = False) -> DetailHeader:
    return DetailHeader(tracker, palette, expanded)


def indicator_text(price_list: List[float], tracker: StockDataTracker) -> Text:
    upper, mid, lower, pct_b, _ = compute_bollinger_bands(price_list, window=20)
    rsi_vals = compute_rsi(price_list, period=14)
    dif, dea, hist = compute_macd(price_list)
    k_vals, d_vals, j_vals = compute_kdj(price_list)
    ma5 = compute_sma(price_list, 5)[-1] or tracker.price
    ma10 = compute_sma(price_list, 10)[-1] or tracker.price
    ma20 = compute_sma(price_list, 20)[-1] or tracker.price
    last_hist = hist[-1] if hist else 0.0
    text = Text()
    text.append(f"• MA    : MA5={ma5:.2f} | MA10={ma10:.2f} | MA20={ma20:.2f}\n", style="dim white")
    text.append(f"• BOLL  : Upper={upper:.2f} | Mid={mid:.2f} | Lower={lower:.2f} (%b={pct_b:.2f})\n", style="dim white")
    text.append(
        f"• MACD  : DIF={(dif[-1] if dif else 0.0):+.2f} | DEA={(dea[-1] if dea else 0.0):+.2f} | "
        f"Hist={last_hist:+.2f} ({'金叉 Bull' if last_hist > 0 else '死叉 Bear'})\n",
        style="dim white",
    )
    text.append(
        f"• KDJ   : K={(k_vals[-1] if k_vals else 50.0):.1f} | D={(d_vals[-1] if d_vals else 50.0):.1f} | "
        f"J={(j_vals[-1] if j_vals else 50.0):.1f} | RSI(14)={(rsi_vals[-1] if rsi_vals else 50.0):.1f}",
        style="dim white",
    )
    return text


def flow_panel(tracker: StockDataTracker, palette: str) -> Panel:
    up, down = trend_styles(palette)
    flow = simulate_capital_flow(tracker.symbol, tracker.price, tracker.volume)
    table = Table(box=SIMPLE, expand=True, show_header=False)
    table.add_column(style="dim cyan")
    table.add_column(justify="right")
    unit = t("d_unit")
    main_val = flow["main_net"] / 10_000.0
    table.add_row(t("d_main_net"), Text(f"{main_val:+,.1f}{unit}", style=up if main_val > 0 else down))
    table.add_row(t("d_super_large"), f"{flow['super_large'] / 10000:+,.1f}{unit}")
    table.add_row(t("d_retail"), f"{flow['retail_net'] / 10000:+,.1f}{unit}")
    return Panel(table, title=t("d_panel_flow"), box=ROUNDED)


def notes_panel(tracker: StockDataTracker, notes: Optional[List[Dict[str, Any]]]) -> Panel:
    notes_list = notes if notes is not None else get_symbol_notes(tracker.symbol)
    table = Table(box=SIMPLE, expand=True, show_header=True, header_style="bold gold1")
    table.add_column(t("d_notes_dt"), style="dim white", width=20)
    table.add_column(t("d_notes_tags"), justify="center", style="bold cyan", width=14)
    table.add_column(t("d_notes_text"), style="bright_white")
    if notes_list:
        for n in notes_list[:4]:
            table.add_row(n.get("timestamp", "-"), "[" + ", ".join(n.get("tags", [])) + "]", n.get("text", ""))
    else:
        table.add_row(t("d_no_notes"), "[default]", t("d_no_notes_hint"))
    return Panel(table, title=t("d_panel_notes"), box=ROUNDED)


class DetailBody:
    """Chart + order book (side by side when wide, stacked when narrow), then indicators and notes."""

    def __init__(self, tracker, palette, notes, period, candles, period_note):
        self.tracker, self.palette, self.notes = tracker, palette, notes
        self.period, self.candles, self.period_note = period, candles, period_note

    def __rich_console__(self, console, options):
        tr = self.tracker
        k_mode = self.period != "intraday" and bool(self.candles)
        price_list = [c["close"] for c in self.candles] if k_mode else list(tr.prices)
        main = CandleView(self.candles, self.period, self.palette) if k_mode else PriceChart(tr, self.palette)
        main = Panel(main, title=period_label(self.period), box=ROUNDED, border_style="cyan", padding=(0, 1))

        if self.period != "intraday" and self.period_note and not k_mode:
            yield Text(self.period_note, style="bold yellow")
        side = side_panel(tr, self.palette)
        if options.max_width >= WIDE_LAYOUT_MIN:
            grid = Table.grid(expand=True, padding=(0, 1, 0, 0))
            grid.add_column(ratio=1)
            grid.add_column(width=BOOK_WIDTH)
            grid.add_row(main, side)
            yield grid
        else:
            yield main
            yield side
        yield Panel(indicator_text(price_list, tr), title=t("d_indicators"), box=ROUNDED, border_style="cyan", padding=(0, 1))
        yield flow_panel(tr, self.palette)
        yield notes_panel(tr, self.notes)


def render_detail_body(tracker, palette="cn", notes=None, period="intraday", candles=None, period_note="") -> DetailBody:
    return DetailBody(tracker, palette, notes, period, candles, period_note)


def render_stock_detail(
    tracker: StockDataTracker,
    palette: str = "cn",
    notes: Optional[List[Dict[str, Any]]] = None,
    period: str = "intraday",
    candles: Optional[List[Dict[str, Any]]] = None,
    period_note: str = "",
) -> Group:
    """Full detail page (header, period tabs, body) for one-shot printing."""
    tabs = Text()
    for p in ("intraday", "day", "week", "month"):
        tabs.append(f" {period_label(p)} ", style="bold reverse" if p == period else "dim")
        tabs.append("  ")
    return Group(DetailHeader(tracker, palette), Text(""), tabs, Text(""), DetailBody(tracker, palette, notes, period, candles, period_note))
