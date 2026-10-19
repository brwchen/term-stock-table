"""Fundamental Valuation, DuPont Analysis, and Dragon-Tiger (龙虎榜) module.
Provides:
- DuPont Analysis (ROE, 净利率, 周转率, 权益乘数)
- Financial Health & Growth metrics (营收同比, 扣非净利同比, 资产负债率)
- Dragon-Tiger seat dynamics (机构专用席位, 知名游资买卖明细)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from rich.console import Console, Group
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.columns import Columns


@dataclass
class DuPontMetrics:
    """DuPont identity breakdown."""
    roe: float = 24.8           # Return on Equity %
    net_profit_margin: float = 21.2  # 销售净利率 %
    asset_turnover: float = 0.85     # 总资产周转率 (times/year)
    equity_multiplier: float = 1.38  # 权益乘数 (杠杆倍数)
    rev_yoy_pct: float = +28.5       # 营业收入同比增长 %
    net_profit_yoy: float = +32.1    # 归母净利润同比增长 %
    debt_to_assets: float = 27.5     # 资产负债率 %
    operating_cash_flow_b: float = 48.2  # 经营性现金流 (亿)


@dataclass
class DragonTigerSeat:
    """Dragon-Tiger List (龙虎榜) seat."""
    seat_name: str
    buy_amount_m: float   # in Millions CNY
    sell_amount_m: float  # in Millions CNY
    net_amount_m: float   # in Millions CNY
    seat_type: str = "机构专用"  # "机构专用", "顶级游资", "北向专用", "散户大本营"


class FundamentalAnalyzer:
    """Renders DuPont analysis panels and Dragon-Tiger seat breakdown."""

    def __init__(self, symbol: str, name: str, palette: str = "cn"):
        self.symbol = symbol
        self.name = name
        self.palette = palette
        self.dupont = DuPontMetrics()
        self.seats = self._get_mock_seats()

    def _get_mock_seats(self) -> List[DragonTigerSeat]:
        return [
            DragonTigerSeat("机构专用 (Seat 1)", 128.5, 12.0, +116.5, "机构专用"),
            DragonTigerSeat("机构专用 (Seat 2)", 85.2, 0.0, +85.2, "机构专用"),
            DragonTigerSeat("中信证券北京呼家楼", 64.0, 15.2, +48.8, "顶级游资"),
            DragonTigerSeat("国泰君安上海江苏路", 42.1, 28.5, +13.6, "顶级游资"),
            DragonTigerSeat("东方财富拉萨团结路", 25.4, 68.2, -42.8, "散户大本营"),
        ]

    def render_dupont_panel(self) -> Panel:
        """Render DuPont financial identity breakdown."""
        d = self.dupont
        pos_color = "red" if self.palette == "cn" else "green"

        grid = Table.grid(padding=(0, 2))
        grid.add_column()
        grid.add_column()

        col1 = Text.from_markup(
            f"[bold]杜邦分解核心 (DuPont Identity):[/]\n"
            f"• [bold white]净资产收益率 (ROE):[/] [bold yellow]{d.roe:.2f}%[/]\n"
            f"  ═ [dim]销售净利率:[/] [bold cyan]{d.net_profit_margin:.1f}%[/] ×\n"
            f"    [dim]总资产周转率:[/] [bold cyan]{d.asset_turnover:.2f}次[/] ×\n"
            f"    [dim]权益乘数(杠杆):[/] [bold cyan]{d.equity_multiplier:.2f}倍[/]\n"
            f"• [bold white]质量评价:[/] [bold green]高盈利能力 + 低财务杠杆优质标的[/]"
        )

        col2 = Text.from_markup(
            f"[bold]成长性与财务健康度:[/] \n"
            f"• [dim]营收同比增长:[/] [{pos_color}]+{d.rev_yoy_pct:.1f}%[/]\n"
            f"• [dim]归母净利同比:[/] [{pos_color}]+{d.net_profit_yoy:.1f}%[/]\n"
            f"• [dim]资产负债率:[/]   [bold white]{d.debt_to_assets:.1f}%[/] [dim](偿债能力稳健)[/]\n"
            f"• [dim]经营现金净流:[/] [bold yellow]+{d.operating_cash_flow_b:.1f} 亿元[/]\n"
            f"• [dim]毛利率水平:[/]   [bold cyan]42.8%[/]"
        )

        grid.add_row(col1, col2)
        return Panel(
            grid,
            title=f"[bold bright_white]📊 {self.name} ({self.symbol}) 杜邦财报基本面透视 (DuPont Fundamentals)[/]",
            border_style="bright_blue",
            padding=(0, 1),
        )

    def render_dragon_tiger_table(self) -> Table:
        """Render Dragon-Tiger seat ranking table."""
        table = Table(
            title=f"🐉 龙虎榜席位动向 (Dragon-Tiger Seat Analysis: {self.name})",
            title_style="bold yellow",
            header_style="bold bright_white on dark_blue",
            border_style="yellow",
            expand=True,
            show_edge=True,
        )
        table.add_column("席位名称", justify="left", width=22)
        table.add_column("席位类型", justify="center", width=12)
        table.add_column("买入额(万元)", justify="right", width=14)
        table.add_column("卖出额(万元)", justify="right", width=14)
        table.add_column("净买入(万元)", justify="right", width=14)

        pos_color = "red" if self.palette == "cn" else "green"
        neg_color = "green" if self.palette == "cn" else "red"

        for s in self.seats:
            is_pos = s.net_amount_m >= 0
            n_col = pos_color if is_pos else neg_color
            sign = "+" if is_pos else ""

            type_col = "bold magenta" if "机构" in s.seat_type else "bold yellow" if "游资" in s.seat_type else "dim"

            table.add_row(
                f"[bold white]{s.seat_name}[/]",
                f"[{type_col}]{s.seat_type}[/]",
                f"[yellow]{s.buy_amount_m * 100:>10,.1f}[/]",
                f"[dim]{s.sell_amount_m * 100:>10,.1f}[/]",
                f"[{n_col} bold]{sign}{s.net_amount_m * 100:>10,.1f}[/]",
            )
        return table
