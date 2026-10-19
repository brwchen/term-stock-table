"""Portfolio and PnL calculation and rendering engine."""
from typing import Dict, List, Any, Optional
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.box import ROUNDED

from .config import load_portfolio
from .table import format_amount


def calculate_portfolio_pnl(quotes: List[Dict[str, Any]], portfolio: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Calculate portfolio position metrics, floating PnL, today PnL, and totals.
    """
    if portfolio is None:
        portfolio = load_portfolio()
    
    quote_map = {q["symbol"].upper(): q for q in quotes}
    
    positions_detail = []
    total_market_val = 0.0
    total_cost = 0.0
    total_float_pnl = 0.0
    total_today_pnl = 0.0
    
    for sym, pos in portfolio.items():
        shares = float(pos.get("shares", 0))
        cost_price = float(pos.get("cost", 0))
        currency = pos.get("currency", "CNY")
        
        quote = quote_map.get(sym.upper())
        if quote:
            current_price = float(quote.get("price", cost_price))
            change = float(quote.get("change", 0.0))
            change_pct = float(quote.get("change_pct", 0.0))
            name = quote.get("name", sym)
        else:
            current_price = cost_price
            change = 0.0
            change_pct = 0.0
            name = sym
        
        market_val = shares * current_price
        cost_val = shares * cost_price
        float_pnl = market_val - cost_val
        float_pnl_pct = (float_pnl / cost_val * 100.0) if cost_val > 0 else 0.0
        today_pnl = shares * change
        
        total_market_val += market_val
        total_cost += cost_val
        total_float_pnl += float_pnl
        total_today_pnl += today_pnl
        
        positions_detail.append({
            "symbol": sym,
            "name": name,
            "shares": shares,
            "cost_price": cost_price,
            "current_price": current_price,
            "change": change,
            "change_pct": change_pct,
            "cost_val": cost_val,
            "market_val": market_val,
            "float_pnl": float_pnl,
            "float_pnl_pct": float_pnl_pct,
            "today_pnl": today_pnl,
            "currency": currency,
        })
    
    total_pnl_pct = (total_float_pnl / total_cost * 100.0) if total_cost > 0 else 0.0
    today_pnl_pct = (total_today_pnl / (total_market_val - total_today_pnl) * 100.0) if (total_market_val - total_today_pnl) > 0 else 0.0
    
    return {
        "positions": positions_detail,
        "total_market_val": total_market_val,
        "total_cost": total_cost,
        "total_float_pnl": total_float_pnl,
        "total_pnl_pct": total_pnl_pct,
        "total_today_pnl": total_today_pnl,
        "today_pnl_pct": today_pnl_pct,
    }


def create_portfolio_table(
    portfolio_data: Dict[str, Any],
    palette: str = "cn",
) -> Table:
    """
    Render a Rich Table summarizing portfolio holdings and real-time PnL.
    """
    up_color = "red" if palette == "cn" else "green"
    down_color = "green" if palette == "cn" else "red"
    
    table = Table(
        title="💼 PORTFOLIO & ASSET VALUATION MONITOR",
        box=ROUNDED,
        header_style="bold cyan",
        title_style="bold yellow",
        expand=True,
    )
    
    table.add_column("Symbol", justify="left", style="cyan", no_wrap=True)
    table.add_column("Name", justify="left", style="white", no_wrap=True)
    table.add_column("Shares", justify="right", style="bright_white")
    table.add_column("Cost Price", justify="right", style="bright_white")
    table.add_column("Current Price", justify="right", style="bold")
    table.add_column("Market Value", justify="right", style="bold white")
    table.add_column("Today PnL", justify="right")
    table.add_column("Float PnL (¥/$)", justify="right")
    table.add_column("Return %", justify="right", style="bold")
    
    positions = portfolio_data.get("positions", [])
    if not positions:
        table.add_row(
            "[dim]No positions[/dim]",
            "[dim]Add via 'stk --position <sym> <shares> <cost>'[/dim]",
            "-", "-", "-", "-", "-", "-", "-"
        )
        return table
    
    for p in positions:
        pnl = p["float_pnl"]
        pnl_pct = p["float_pnl_pct"]
        today_pnl = p["today_pnl"]
        
        # Color coding
        pnl_color = up_color if pnl > 0 else (down_color if pnl < 0 else "white")
        pnl_sign = "+" if pnl > 0 else ""
        
        today_color = up_color if today_pnl > 0 else (down_color if today_pnl < 0 else "white")
        today_sign = "+" if today_pnl > 0 else ""
        
        table.add_row(
            p["symbol"],
            p["name"],
            f"{p['shares']:,.0f}" if p['shares'].is_integer() else f"{p['shares']:,.2f}",
            f"{p['cost_price']:,.2f}",
            f"[{pnl_color}]{p['current_price']:,.2f}[/{pnl_color}]",
            f"{p['market_val']:,.2f}",
            f"[{today_color}]{today_sign}{today_pnl:,.2f}[/{today_color}]",
            f"[{pnl_color}]{pnl_sign}{pnl:,.2f}[/{pnl_color}]",
            f"[{pnl_color}]{pnl_sign}{pnl_pct:.2f}%[/{pnl_color}]",
        )
        
    return table
