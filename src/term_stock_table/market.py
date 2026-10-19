"""Global indices overview and capital flow analysis engine."""
from typing import Dict, List, Any, Optional
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.columns import Columns
from rich.box import ROUNDED, SIMPLE


MAJOR_INDICES = [
    {"symbol": "sh000001", "name": "上证指数", "price": 3386.42, "change": 18.25, "change_pct": 0.54},
    {"symbol": "sz399001", "name": "深证成指", "price": 10842.18, "change": -22.10, "change_pct": -0.20},
    {"symbol": "sz399006", "name": "创业板指", "price": 2218.60, "change": 12.45, "change_pct": 0.56},
    {"symbol": "r_hkHSI",   "name": "恒生指数", "price": 20820.50, "change": 145.20, "change_pct": 0.70},
    {"symbol": "us.IXIC",   "name": "纳斯达克", "price": 18415.30, "change": 128.40, "change_pct": 0.70},
    {"symbol": "us.INX",    "name": "标普500",  "price": 5864.20, "change": 22.15, "change_pct": 0.38},
]


def render_indices_banner(palette: str = "cn", indices: Optional[List[Dict[str, Any]]] = None) -> Table:
    """Render a horizontal bar of major market indices."""
    if indices is None:
        indices = MAJOR_INDICES
        
    is_cn = (palette == "cn")
    up_color = "red" if is_cn else "green"
    down_color = "green" if is_cn else "red"
    
    table = Table(box=SIMPLE, show_header=False, pad_edge=False, expand=True)
    for _ in indices:
        table.add_column(justify="center")
        
    cells = []
    for idx in indices:
        chg_pct = idx["change_pct"]
        color = up_color if chg_pct > 0 else (down_color if chg_pct < 0 else "white")
        arrow = "▲" if chg_pct > 0 else ("▼" if chg_pct < 0 else "-")
        sign = "+" if chg_pct > 0 else ""
        
        content = (
            f"[bold cyan]{idx['name']}[/]\n"
            f"[{color}]{idx['price']:,.2f}[/{color}]\n"
            f"[{color}]{sign}{chg_pct:.2f}% {arrow}[/{color}]"
        )
        cells.append(content)
        
    table.add_row(*cells)
    return table


def simulate_capital_flow(symbol: str, price: float, volume: int) -> Dict[str, Any]:
    """
    Compute / model multi-tier capital flow:
    - Super Large Order (超大单)
    - Large Order (大单)
    - Medium Order (中单)
    - Small Order (小单)
    """
    total_val = (price * volume * 100) if volume > 0 else 50_000_000.0
    
    # Proportions based on symbol hash for stable realistic simulation
    h = sum(ord(c) for c in symbol) % 100
    
    super_large_net = (h - 48) * 0.01 * total_val * 0.35
    large_net = (h - 52) * 0.01 * total_val * 0.30
    med_net = (45 - h) * 0.01 * total_val * 0.20
    small_net = (50 - h) * 0.01 * total_val * 0.15
    
    main_net = super_large_net + large_net
    retail_net = med_net + small_net
    
    return {
        "super_large": super_large_net,
        "large": large_net,
        "medium": med_net,
        "small": small_net,
        "main_net": main_net,
        "retail_net": retail_net,
    }


def render_capital_flow_panel(flow: Dict[str, Any], palette: str = "cn") -> Panel:
    """Render a visual capital flow breakdown table panel."""
    is_cn = (palette == "cn")
    up_color = "red" if is_cn else "green"
    down_color = "green" if is_cn else "red"
    
    table = Table(box=ROUNDED, expand=True, show_header=True, header_style="bold cyan")
    table.add_column("Order Tier", justify="left")
    table.add_column("Net Flow (万元)", justify="right")
    table.add_column("Visual Flow Bar", justify="left")
    
    def fmt_flow_row(tier_name: str, amt: float):
        amt_wan = amt / 10_000.0
        color = up_color if amt > 0 else (down_color if amt < 0 else "white")
        sign = "+" if amt > 0 else ""
        
        # Bar length
        bars = int(min(abs(amt_wan) / 500.0, 15))
        bar_char = "█" * max(1, bars)
        bar_str = f"[{color}]{bar_char}[/{color}]" if amt > 0 else f"[{color}]{bar_char}[/{color}]"
        
        return (tier_name, f"[{color}]{sign}{amt_wan:,.1f}[/{color}]", bar_str)
        
    table.add_row(*fmt_flow_row("超大单 (Super Large)", flow["super_large"]))
    table.add_row(*fmt_flow_row("大单 (Large Order)", flow["large"]))
    table.add_row(*fmt_flow_row("中单 (Medium Order)", flow["medium"]))
    table.add_row(*fmt_flow_row("小单 (Small Order)", flow["small"]))
    
    main_val = flow["main_net"] / 10_000.0
    main_col = up_color if main_val > 0 else down_color
    main_sign = "+" if main_val > 0 else ""
    
    title = f"💰 主力资金净流入: [{main_col}]{main_sign}{main_val:,.1f} 万元[/{main_col}]"
    return Panel(table, title=title, box=ROUNDED, border_style="cyan")
