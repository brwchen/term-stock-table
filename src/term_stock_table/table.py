"""Rich table generator for professional terminal stock monitoring."""
from typing import List, Optional, Dict, Any
from rich.table import Table
from rich.text import Text
from rich.box import ROUNDED, HEAVY_EDGE, SIMPLE
from term_sparkline import sparkline
from .api import StockDataTracker
from .indicators import compute_bollinger_bands, render_bollinger_badge


def format_volume(vol: int) -> str:
    """Format volume into readable human units."""
    if vol >= 100_000_000:
        return f"{vol / 100_000_000:.2f}亿"
    elif vol >= 10_000:
        return f"{vol / 10_000:.2f}万"
    return str(vol)


def format_amount(amt: float) -> str:
    """Format turnover amount into readable human units."""
    if amt >= 100_000:
        return f"{amt / 100_000:.2f}亿"
    elif amt >= 10_000:
        return f"{amt / 10_000:.2f}万"
    elif amt >= 1_000:
        return f"{amt:.1f}万"
    return f"{amt:.1f}"


def create_stock_table(
    trackers: List[StockDataTracker],
    palette: str = "cn",
    visible_columns: Optional[List[str]] = None,
    monochrome: bool = False,
    is_live: bool = True,
    sort_by: Optional[str] = None,
    reverse: bool = True,
    alerts_triggered: Optional[Dict[str, List[str]]] = None,
) -> Table:
    """Create a high-density, professional Rich Table for stock monitoring with sorting & alert indicators."""
    is_cn = (palette == "cn")
    
    # Sort trackers if requested
    sorted_trackers = list(trackers)
    if sort_by:
        key_map = {
            "change_pct": lambda t: t.change_pct,
            "price": lambda t: t.price,
            "volume": lambda t: t.volume,
            "amount": lambda t: t.amount,
            "amplitude": lambda t: t.amplitude,
            "turnover_rate": lambda t: t.turnover_rate,
            "symbol": lambda t: t.symbol,
            "pe": lambda t: (t.pe or 0.0),
        }
        if sort_by in key_map:
            sorted_trackers.sort(key=key_map[sort_by], reverse=reverse)

    table = Table(
        box=ROUNDED,
        show_header=True,
        header_style="bold bright_white on grey15",
        title_style="bold gold1",
        caption_style="dim white",
        expand=True,
        pad_edge=False,
    )

    # Define all available columns
    all_col_defs = {
        "symbol": ("Symbol", "center", "bold cyan", 9),
        "name": ("Name", "left", "bold white", 14),
        "price": ("Price", "right", "bold", 10),
        "change_pct": ("Change%", "right", "bold", 10),
        "change": ("Change", "right", "dim", 9),
        "amplitude": ("Amp%", "right", "dim", 8),
        "turnover_rate": ("Turnover%", "right", "dim", 10),
        "volume": ("Volume", "right", "dim cyan", 10),
        "amount": ("Amount", "right", "dim yellow", 10),
        "pe": ("P/E", "right", "dim magenta", 7),
        "bollinger": ("Bollinger (%b)", "center", "bold", 14),
        "sparkline": ("Real-time Trend (Sparkline)", "left", "none", 32),
    }

    cols_to_show = visible_columns or list(all_col_defs.keys())

    for col_key in cols_to_show:
        if col_key in all_col_defs:
            title, justify, style, min_w = all_col_defs[col_key]
            # Add sort indicator arrow
            if sort_by == col_key:
                title += " ▼" if reverse else " ▲"
            table.add_column(title, justify=justify, style=style, min_width=min_w)

    up_count = 0
    down_count = 0
    flat_count = 0

    for tr in sorted_trackers:
        chg = tr.change
        chg_pct = tr.change_pct

        if chg > 0.0001:
            up_count += 1
            color_style = "grey70" if monochrome else ("bright_red" if is_cn else "bright_green")
            ansi_arrow = "▲"
        elif chg < -0.0001:
            down_count += 1
            color_style = "grey70" if monochrome else ("bright_green" if is_cn else "bright_red")
            ansi_arrow = "▼"
        else:
            flat_count += 1
            color_style = "grey70" if monochrome else "bright_white"
            ansi_arrow = "-"

        # Technical Indicators
        price_list = list(tr.prices)
        _, _, _, pct_b, _ = compute_bollinger_bands(price_list, window=20)
        bb_badge = "[·····]" if monochrome else render_bollinger_badge(pct_b, palette=palette)

        # Sparkline Curve
        spark_text = sparkline(
            price_list,
            length=12,
            mode="braille",
            palette=palette,
            fill=(not monochrome),
            baseline=tr.prev_close,
            show_dot=True,
            annotate=(not monochrome),
        )

        sym_display = tr.symbol
        if alerts_triggered and tr.symbol in alerts_triggered:
            sym_display = f"🚨 {tr.symbol}"

        row_cells = []
        for col_key in cols_to_show:
            if col_key == "symbol":
                row_cells.append(sym_display)
            elif col_key == "name":
                row_cells.append(tr.name)
            elif col_key == "price":
                row_cells.append(Text(f"{tr.price:.2f}", style=color_style))
            elif col_key == "change_pct":
                row_cells.append(Text(f"{chg_pct:+.2f}% {ansi_arrow}", style=color_style))
            elif col_key == "change":
                row_cells.append(Text(f"{chg:+.2f}", style=color_style))
            elif col_key == "amplitude":
                row_cells.append(f"{tr.amplitude:.2f}%")
            elif col_key == "turnover_rate":
                row_cells.append(f"{tr.turnover_rate:.2f}%")
            elif col_key == "volume":
                row_cells.append(format_volume(tr.volume))
            elif col_key == "amount":
                row_cells.append(format_amount(tr.amount))
            elif col_key == "pe":
                row_cells.append(f"{tr.pe:.1f}" if tr.pe else "-")
            elif col_key == "bollinger":
                row_cells.append(Text.from_ansi(bb_badge))
            elif col_key == "sparkline":
                row_cells.append(Text.from_ansi(spark_text))

        table.add_row(*row_cells)

    # Market Sentiment in Caption
    total = len(sorted_trackers)
    sentiment_str = f"Market: [bold green]▲ {up_count}[/] Up | [bold red]▼ {down_count}[/] Down | [bold white]- {flat_count}[/] Flat (Total: {total})" if not is_cn else f"市场情绪: [bold red]▲ {up_count} 涨[/] | [bold green]▼ {down_count} 跌[/] | [bold white]- {flat_count} 平[/] (自选: {total} 只)"
    source_tag = "[bold green][● LIVE QUOTE (Tencent API)][/]" if is_live else "[bold yellow][○ SIMULATION ENGINE][/]"
    
    sort_info = f" | Sort: [bold cyan]{sort_by or 'default'}[/] ({'DESC' if reverse else 'ASC'})" if sort_by else ""
    table.title = f"⚡ TERM-STOCK-TABLE FINANCIAL TERMINAL ⚡  {source_tag}{sort_info}"
    table.caption = f"{sentiment_str} | [bold cyan]s[/] Sort | [bold green]P[/] Portfolio | [bold magenta]b[/] Boss Key | [bold yellow]q[/] Quit"

    return table
