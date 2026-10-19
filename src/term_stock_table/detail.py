"""Comprehensive stock detail view, technical indicators, and investment notes."""
from typing import List, Dict, Any, Optional
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.text import Text
from rich.box import ROUNDED, SIMPLE, DOUBLE_EDGE
from term_sparkline import sparkline, price_volume_sparkline
from .api import StockDataTracker
from .indicators import compute_bollinger_bands, compute_sma, compute_rsi
from .config import get_symbol_notes


def render_stock_detail(
    tracker: StockDataTracker,
    palette: str = "cn",
    notes: Optional[List[Dict[str, Any]]] = None,
) -> Layout:
    """Render comprehensive multi-panel stock detail view."""
    is_cn = (palette == "cn")
    chg = tracker.change
    chg_pct = tracker.change_pct
    
    col_style = "bright_red" if chg >= 0 else "bright_green"
    if not is_cn:
        col_style = "bright_green" if chg >= 0 else "bright_red"
    arrow = "▲" if chg >= 0 else "▼"

    root = Layout(name="root")
    root.split_column(
        Layout(name="header", size=4),
        Layout(name="middle", ratio=3),
        Layout(name="bottom", ratio=2),
    )

    # 1. Header Overview Bar
    header_text = Text()
    header_text.append(f" {tracker.name} ({tracker.symbol}) ", style="bold bright_white on grey23")
    header_text.append(f"  Price: {tracker.price:.2f} ", style=f"bold {col_style}")
    header_text.append(f" {chg_pct:+.2f}% ({chg:+.2f}) {arrow}  ", style=f"bold {col_style}")
    header_text.append(f"Open: {tracker.open:.2f} | High: {tracker.high:.2f} | Low: {tracker.low:.2f} | PrevClose: {tracker.prev_close:.2f}\n", style="dim white")
    header_text.append(f" Volume: {tracker.volume:,} | Amount: {tracker.amount:.1f}万 | Turnover: {tracker.turnover_rate:.2f}% | P/E: {tracker.pe:.1f} | P/B: {tracker.pb:.2f}", style="dim cyan")
    
    root["header"].update(Panel(header_text, box=ROUNDED, style="cyan"))

    # 2. Middle: Left (Trend & Indicators) + Right (5-Level Order Book)
    root["middle"].split_row(
        Layout(name="chart_and_indicators", ratio=3),
        Layout(name="order_book", ratio=2),
    )

    # Price Intraday Curve + Combo Sparkline
    price_list = list(tracker.prices)
    vol_list = list(tracker.volumes)
    
    combo_spark = price_volume_sparkline(
        price_list,
        vol_list,
        palette=palette,
        annotate=True,
    )

    upper, mid, lower, pct_b, b_width = compute_bollinger_bands(price_list, window=20)
    rsi_vals = compute_rsi(price_list, period=14)
    last_rsi = rsi_vals[-1] if rsi_vals else 50.0

    ma5 = compute_sma(price_list, 5)[-1] or tracker.price
    ma10 = compute_sma(price_list, 10)[-1] or tracker.price
    ma20 = compute_sma(price_list, 20)[-1] or tracker.price

    chart_content = Text()
    chart_content.append("─── Intraday Price & Volume Combo ───\n", style="bold gold1")
    chart_content.append(Text.from_ansi(combo_spark))
    chart_content.append("\n\n─── Technical Indicators ───\n", style="bold gold1")
    chart_content.append(f"• Moving Averages : MA5={ma5:.2f} | MA10={ma10:.2f} | MA20={ma20:.2f}\n", style="dim white")
    chart_content.append(f"• Bollinger Bands : Upper={upper:.2f} | Mid={mid:.2f} | Lower={lower:.2f} (%b={pct_b:.2f}, Width={b_width:.1f}%)\n", style="dim white")
    chart_content.append(f"• Relative Strength : RSI(14)={last_rsi:.1f} ({'超买 Overbought' if last_rsi>70 else ('超卖 Oversold' if last_rsi<30 else '中性 Neutral')})", style="dim white")

    root["middle"]["chart_and_indicators"].update(
        Panel(chart_content, title="📈 Technical Analysis & Intraday Sparklines", box=ROUNDED)
    )

    # 5-Level Order Book Table (买卖五档)
    book_table = Table(box=SIMPLE, expand=True, show_header=True, header_style="bold grey70")
    book_table.add_column("Level", justify="left", style="bold white", width=6)
    book_table.add_column("Price", justify="right", style=col_style, width=10)
    book_table.add_column("Vol (Hands)", justify="right", style="dim cyan", width=12)

    # Asks (Sell 5 to Sell 1 in reverse order)
    if tracker.asks:
        for idx in range(min(5, len(tracker.asks)) - 1, -1, -1):
            p, v = tracker.asks[idx]
            book_table.add_row(f"卖 {idx + 1}", f"{p:.2f}", f"{v:,}")
    else:
        for i in range(5, 0, -1):
            book_table.add_row(f"卖 {i}", f"{tracker.price + i*0.1:.2f}", f"{100*i:,}")

    book_table.add_row("────", "────────", "────────")

    # Bids (Buy 1 to Buy 5)
    if tracker.bids:
        for idx in range(min(5, len(tracker.bids))):
            p, v = tracker.bids[idx]
            book_table.add_row(f"买 {idx + 1}", f"{p:.2f}", f"{v:,}")
    else:
        for i in range(1, 6):
            book_table.add_row(f"买 {i}", f"{tracker.price - i*0.1:.2f}", f"{100*i:,}")

    root["middle"]["order_book"].update(
        Panel(book_table, title="📊 5-Level Order Book (五档盘口)", box=ROUNDED)
    )

    # 3. Bottom: Investment Notes & Journal
    notes_list = notes if notes is not None else get_symbol_notes(tracker.symbol)
    notes_table = Table(box=SIMPLE, expand=True, show_header=True, header_style="bold gold1")
    notes_table.add_column("Date / Time", justify="left", style="dim white", width=20)
    notes_table.add_column("Tags", justify="center", style="bold cyan", width=14)
    notes_table.add_column("Investment Logic & Trade Notes", justify="left", style="bright_white")

    if notes_list:
        for n in notes_list[:4]:  # Show latest 4 notes
            tag_str = "[" + ", ".join(n.get("tags", [])) + "]"
            notes_table.add_row(n.get("timestamp", "-"), tag_str, n.get("text", ""))
    else:
        notes_table.add_row(
            "No notes recorded yet.",
            "[default]",
            "Press 'n' in interactive TUI mode to add notes for this stock (e.g. Target price, Stop loss, Catalyst).",
        )

    root["bottom"].update(
        Panel(notes_table, title="📝 Investment Notes & Strategy Log (按 'n' 编辑笔记)", box=ROUNDED)
    )

    return root
