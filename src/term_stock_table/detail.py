"""Comprehensive stock detail view, technical indicators, and investment notes."""
from typing import List, Dict, Any, Optional
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.text import Text
from rich.box import ROUNDED, SIMPLE, DOUBLE_EDGE
from term_sparkline import sparkline
from .inline_spark import AutoCurve
from .api import StockDataTracker
from .indicators import (
    compute_bollinger_bands,
    compute_sma,
    compute_rsi,
    compute_macd,
    compute_kdj,
    render_candlestick_chart,
    estimate_valuation_percentile,
)
from .market import simulate_capital_flow
from .config import get_symbol_notes
from .i18n import t




def candles_from_prices(prices: List[float], count: int = 30) -> List[Dict[str, Any]]:
    """Bucket a price series into synthetic candles (used when real K-lines are unavailable)."""
    if len(prices) < 2:
        return []
    step = max(1, len(prices) // count)
    out = []
    for i in range(0, len(prices), step):
        sub = prices[i : i + step]
        out.append({"date": f"#{len(out) + 1}", "open": sub[0], "close": sub[-1], "high": max(sub), "low": min(sub), "volume": 0.0})
    return out


class CandleView:
    """Candlestick + volume block that sizes itself to the available width at render time."""

    def __init__(self, candles: List[Dict[str, Any]], period: str, palette: str = "cn"):
        self.candles = candles
        self.period = period
        self.palette = palette

    def __rich_console__(self, console, options):
        n = max(8, (options.max_width - 12) // 2)
        shown = self.candles[-n:]
        last = shown[-1]
        yield Text(f"─── {t('d_kline')} [{period_label(self.period)}] {shown[0]['date']} → {last['date']} ───", style="bold gold1")
        for line in render_candlestick_chart(shown, height=10, palette=self.palette, gap=1).split("\n"):
            yield Text.from_ansi(line)
        yield Text(
            f"O {last['open']:.2f}  H {last['high']:.2f}  L {last['low']:.2f}  C {last['close']:.2f}",
            style="dim white",
        )
        vols = [c.get("volume", 0.0) for c in shown]
        if any(vols):
            yield Text(f"─── {t('d_volume')} ───", style="bold gold1")
            yield Text.from_ansi(sparkline(vols, length=len(vols), mode="block", palette=self.palette, annotate=False))


def period_label(period: str) -> str:
    key = f"p_{period}"
    label = t(key)
    return period if label == key else label


from .detail_view import render_stock_detail, render_detail_header, render_detail_body  # noqa: E402,F401
