"""Comprehensive stock detail view, technical indicators, and investment notes."""
from typing import List, Dict, Any, Optional
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.text import Text
from rich.box import ROUNDED, SIMPLE, DOUBLE_EDGE
from term_sparkline import sparkline, price_volume_sparkline
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


def render_stock_detail(
    tracker: StockDataTracker,
    palette: str = "cn",
    notes: Optional[List[Dict[str, Any]]] = None,
    show_candlestick: bool = False,
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
        Layout(name="middle", ratio=4),
        Layout(name="bottom", ratio=2),
    )

    # 1. Header Overview Bar with Valuation Percentile
    val_pct, val_status, val_badge = estimate_valuation_percentile(tracker.pe)
    
    header_text = Text()
    header_text.append(f" {tracker.name} ({tracker.symbol}) ", style="bold bright_white on grey23")
    header_text.append(f"  Price: {tracker.price:.2f} ", style=f"bold {col_style}")
    header_text.append(f" {chg_pct:+.2f}% ({chg:+.2f}) {arrow}  ", style=f"bold {col_style}")
    header_text.append(f"Open: {tracker.open:.2f} | High: {tracker.high:.2f} | Low: {tracker.low:.2f} | PrevClose: {tracker.prev_close:.2f}\n", style="dim white")
    header_text.append(f" Volume: {tracker.volume:,} | Turnover: {tracker.turnover_rate:.2f}% | P/E: {tracker.pe:.1f} ({val_status} {val_pct:.0f}%) | P/B: {tracker.pb:.2f}", style="dim cyan")
    
    root["header"].update(Panel(header_text, box=ROUNDED, style="cyan"))

    # 2. Middle: Left (Trend & Quant Indicators) + Right (5-Level Order Book & Capital Flow)
    root["middle"].split_row(
        Layout(name="chart_and_indicators", ratio=3),
        Layout(name="depth_and_flow", ratio=2),
    )

    price_list = list(tracker.prices)
    vol_list = list(tracker.volumes)

    # Calculate indicators
    upper, mid, lower, pct_b, b_width = compute_bollinger_bands(price_list, window=20)
    rsi_vals = compute_rsi(price_list, period=14)
    last_rsi = rsi_vals[-1] if rsi_vals else 50.0

    dif, dea, macd_hist = compute_macd(price_list)
    last_dif = dif[-1] if dif else 0.0
    last_dea = dea[-1] if dea else 0.0
    last_hist = macd_hist[-1] if macd_hist else 0.0

    k_vals, d_vals, j_vals = compute_kdj(price_list)
    last_k = k_vals[-1] if k_vals else 50.0
    last_d = d_vals[-1] if d_vals else 50.0
    last_j = j_vals[-1] if j_vals else 50.0

    ma5 = compute_sma(price_list, 5)[-1] or tracker.price
    ma10 = compute_sma(price_list, 10)[-1] or tracker.price
    ma20 = compute_sma(price_list, 20)[-1] or tracker.price

    chart_content = Text()
    if show_candlestick:
        # Generate sample intraday candles
        sample_candles = []
        step = max(1, len(price_list) // 10)
        for i in range(0, len(price_list), step):
            sub = price_list[i : i + step]
            if sub:
                sample_candles.append({
                    "open": sub[0],
                    "high": max(sub) * 1.002,
                    "low": min(sub) * 0.998,
                    "close": sub[-1],
                })
        candle_str = render_candlestick_chart(sample_candles, height=6, palette=palette)
        chart_content.append("─── Multi-Period Candlestick (K-Line) ───\n", style="bold gold1")
        chart_content.append(Text.from_ansi(candle_str))
    else:
        combo_spark = price_volume_sparkline(
            price_list,
            vol_list,
            palette=palette,
            annotate=True,
        )
        chart_content.append("─── Intraday Price & Volume Combo ───\n", style="bold gold1")
        chart_content.append(Text.from_ansi(combo_spark))

    chart_content.append("\n\n─── Technical & Quant Indicators ───\n", style="bold gold1")
    chart_content.append(f"• Moving Avg  : MA5={ma5:.2f} | MA10={ma10:.2f} | MA20={ma20:.2f}\n", style="dim white")
    chart_content.append(f"• Bollinger   : Upper={upper:.2f} | Mid={mid:.2f} | Lower={lower:.2f} (%b={pct_b:.2f})\n", style="dim white")
    chart_content.append(f"• MACD (12,26): DIF={last_dif:+.2f} | DEA={last_dea:+.2f} | Hist={last_hist:+.2f} ({'金叉 Bull' if last_hist>0 else '死叉 Bear'})\n", style="dim white")
    chart_content.append(f"• KDJ (9,3,3) : K={last_k:.1f} | D={last_d:.1f} | J={last_j:.1f} | RSI(14)={last_rsi:.1f}", style="dim white")

    root["middle"]["chart_and_indicators"].update(
        Panel(chart_content, title="📈 Technical Analysis & Curves (按 'k' 切换K线/走势)", box=ROUNDED)
    )

    # Right Column: Order Book + Capital Flow split
    root["middle"]["depth_and_flow"].split_column(
        Layout(name="order_book", ratio=3),
        Layout(name="capital_flow", ratio=2),
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

    root["middle"]["depth_and_flow"]["order_book"].update(
        Panel(book_table, title="📊 5-Level Order Book (五档盘口)", box=ROUNDED)
    )

    # Capital Flow Breakdown
    flow = simulate_capital_flow(tracker.symbol, tracker.price, tracker.volume)
    flow_table = Table(box=SIMPLE, expand=True, show_header=False)
    flow_table.add_column("Tier", style="dim cyan")
    flow_table.add_column("Amount", justify="right")
    
    main_val = flow["main_net"] / 10_000.0
    main_col = "bright_red" if is_cn and main_val > 0 else ("bright_green" if not is_cn and main_val > 0 else ("bright_green" if is_cn else "bright_red"))
    main_sign = "+" if main_val > 0 else ""
    
    flow_table.add_row("主力净流入", f"[{main_col}]{main_sign}{main_val:,.1f}万[/{main_col}]")
    flow_table.add_row("超大单净额", f"{flow['super_large']/10000:+,.1f}万")
    flow_table.add_row("散户净额", f"{flow['retail_net']/10000:+,.1f}万")

    root["middle"]["depth_and_flow"]["capital_flow"].update(
        Panel(flow_table, title="💰 Capital Flow (资金流向)", box=ROUNDED)
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
