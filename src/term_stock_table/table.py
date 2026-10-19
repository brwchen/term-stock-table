"""Rich table generator for professional terminal stock monitoring."""
from typing import List, Optional, Dict, Any
from rich.table import Table
from rich.style import Style
from rich.text import Text
from .i18n import t
from rich.box import ROUNDED, HEAVY_EDGE, SIMPLE
from .api import StockDataTracker
from .inline_spark import smart_spark
from . import inline_spark as _isp
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


SORT_KEYS = {
    "change_pct": lambda t: t.change_pct,
    "price": lambda t: t.price,
    "volume": lambda t: t.volume,
    "amount": lambda t: t.amount,
    "amplitude": lambda t: t.amplitude,
    "turnover_rate": lambda t: t.turnover_rate,
    "symbol": lambda t: t.symbol,
    "pe": lambda t: (t.pe or 0.0),
}


def sort_trackers(trackers: List[StockDataTracker], sort_by: Optional[str] = None, reverse: bool = True) -> List[StockDataTracker]:
    """Return trackers in the order the table displays them."""
    ordered = list(trackers)
    if sort_by in SORT_KEYS:
        ordered.sort(key=SORT_KEYS[sort_by], reverse=reverse)
    return ordered


def create_stock_table(
    trackers: List[StockDataTracker],
    palette: str = "cn",
    visible_columns: Optional[List[str]] = None,
    monochrome: bool = False,
    is_live: bool = True,
    sort_by: Optional[str] = None,
    reverse: bool = True,
    alerts_triggered: Optional[Dict[str, List[str]]] = None,
    selected_symbol: Optional[str] = None,
) -> Table:
    """Create a high-density, professional Rich Table for stock monitoring with sorting & alert indicators."""
    is_cn = (palette == "cn")
    spark_rows = 1 if _isp.OVERLAY_QUEUE is not None else 2
    sorted_trackers = sort_trackers(trackers, sort_by, reverse)

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
        "symbol": (t("col_symbol"), "center", "bold cyan", 9),
        "name": (t("col_name"), "left", "bold white", 14),
        "price": (t("col_price"), "right", "bold", 10),
        "change_pct": (t("col_change_pct"), "right", "bold", 10),
        "change": (t("col_change"), "right", "dim", 9),
        "amplitude": (t("col_amplitude"), "right", "dim", 8),
        "turnover_rate": (t("col_turnover"), "right", "dim", 10),
        "volume": (t("col_volume"), "right", "dim cyan", 10),
        "amount": (t("col_amount"), "right", "dim yellow", 10),
        "pe": (t("col_pe"), "right", "dim magenta", 7),
        "bollinger": (t("col_bollinger"), "center", "bold", 14),
        "sparkline": (t("col_trend"), "left", "none", 32),
    }

    cols_to_show = visible_columns or list(all_col_defs.keys())

    for col_key in cols_to_show:
        if col_key in all_col_defs:
            title, justify, style, min_w = all_col_defs[col_key]
            # Add sort indicator arrow
            if sort_by == col_key:
                title += " ▼" if reverse else " ▲"
            table.add_column(title, justify=justify, style=style, min_width=min_w, vertical="middle")

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
        note = None
        if not monochrome and len(price_list) >= 2:
            note = Text(f"[{tr.price:.2f} {tr.change_pct:+.2f}%]", style=color_style)
        spark_text = smart_spark(
            price_list, 20, palette, note, rows=spark_rows, fill=True, up=(tr.change_pct >= 0), show_dot=False
        )

        sym_display = tr.symbol
        if alerts_triggered and tr.symbol in alerts_triggered:
            sym_display = f"🚨 {tr.symbol}"

        click_style = Style(meta={"@click": f"app.open_detail('{tr.symbol}')"})
        row_cells = []
        for col_key in cols_to_show:
            if col_key == "symbol":
                row_cells.append(Text(sym_display, style=click_style))
            elif col_key == "name":
                row_cells.append(Text(tr.name, style=click_style))
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
                row_cells.append(spark_text)

        table.add_row(*row_cells, style="on grey23" if tr.symbol == selected_symbol else None)

    # Market Sentiment in Caption
    total = len(sorted_trackers)
    sentiment_key = "sentiment_cn_colors" if is_cn else "sentiment"
    sentiment_str = t(sentiment_key, up_count=up_count, down=down_count, flat=flat_count, total=len(sorted_trackers))
    tag = t("tag_live") if is_live else t("tag_sim")
    source_tag = f"[bold green][{tag}][/]" if is_live else f"[bold yellow][{tag}][/]"

    sort_info = f" | {t('sort_label')}: [bold cyan]{sort_by or t('default')}[/] ({t('desc') if reverse else t('asc')})" if sort_by else ""
    table.title = f"⚡ {t('table_title')} ⚡  {source_tag}{sort_info}"
    table.caption = f"{sentiment_str} | {t('caption_keys')}"

    return table
