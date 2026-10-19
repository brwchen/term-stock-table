"""Sector & Industry Heatmap and Leaderboard module.
Provides:
- Industry & Concept sector rankings and net capital inflow
- Terminal Unicode matrix heatmap with dynamic color intensity
- Sector drill-down into top leading stocks
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from rich.console import Console, Group
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.columns import Columns

from .inline_spark import smart_spark


@dataclass
class SectorInfo:
    """Sector data item."""
    name: str
    change_pct: float
    net_inflow_billion: float  # Capital net inflow (Billions CNY)
    leader_symbol: str
    leader_name: str
    leader_pct: float
    component_count: int = 45
    trend_history: List[float] = field(default_factory=list)


class SectorHeatmapTracker:
    """Tracks sector performance and generates terminal visual heatmaps."""

    def __init__(self, palette: str = "cn"):
        self.palette = palette
        self.sectors = self._get_default_sectors()

    def _get_default_sectors(self) -> List[SectorInfo]:
        return [
            SectorInfo("半导体/芯片", +4.25, +38.5, "688981", "中芯国际", +6.82, 92, [1.1, 1.8, 2.5, 3.2, 4.25]),
            SectorInfo("人工智能/CPO", +3.80, +26.4, "300308", "中际旭创", +7.45, 68, [0.8, 1.5, 2.1, 3.1, 3.80]),
            SectorInfo("新能源汽车", +2.65, +18.2, "002594", "比亚迪", +4.10, 115, [0.4, 0.9, 1.8, 2.2, 2.65]),
            SectorInfo("电池/储能", +2.10, +12.0, "300750", "宁德时代", +3.25, 84, [0.2, 0.8, 1.2, 1.9, 2.10]),
            SectorInfo("消费电子", +1.85, +8.4, "002475", "立讯精密", +2.80, 76, [0.1, 0.5, 1.1, 1.4, 1.85]),
            SectorInfo("生物医药", +0.95, +4.2, "600276", "恒瑞医药", +1.85, 142, [-0.2, 0.1, 0.4, 0.7, 0.95]),
            SectorInfo("白酒/食品", +0.45, +1.5, "600519", "贵州茅台", +0.85, 48, [-0.5, -0.2, 0.1, 0.3, 0.45]),
            SectorInfo("银行/金融", -0.35, -5.2, "601398", "工商银行", -0.42, 42, [0.1, 0.0, -0.2, -0.3, -0.35]),
            SectorInfo("煤炭开采", -1.15, -12.4, "601088", "中国神华", -1.45, 36, [-0.3, -0.6, -0.8, -1.0, -1.15]),
            SectorInfo("房地产", -1.80, -18.6, "000002", "万科A", -2.35, 78, [-0.5, -0.9, -1.2, -1.5, -1.80]),
        ]

    def render_heatmap_matrix(self) -> Panel:
        """Render a graphical sector heatmap block matrix."""
        pos_color = "red" if self.palette == "cn" else "green"
        neg_color = "green" if self.palette == "cn" else "red"

        cards = []
        for s in self.sectors:
            is_pos = s.change_pct >= 0
            p_color = pos_color if is_pos else neg_color
            sign = "+" if is_pos else ""

            # Heat intensity background or border
            intensity = min(5, int(abs(s.change_pct) * 1.2))
            heat_dots = "🔥" * intensity if is_pos else "❄️" * intensity

            card_text = (
                f"[bold white]{s.name}[/]\n"
                f"[{p_color} bold]{sign}{s.change_pct:.2f}%[/]\n"
                f"[dim]净流入: [yellow]{s.net_inflow_billion:+.1f}亿[/][/]\n"
                f"[dim]领涨: {s.leader_name} ([{p_color}]{s.leader_pct:+.1f}%[/])[/]"
            )
            border_style = p_color if abs(s.change_pct) >= 1.5 else "dim"
            cards.append(Panel(Text.from_markup(card_text), border_style=border_style, width=22))

        cols = Columns(cards, equal=True, expand=False)
        return Panel(
            cols,
            title="[bold yellow]🗺️ 行业与概念板块热力图 (Sector Heatmap Matrix)[/]",
            border_style="yellow",
            padding=(0, 1),
        )

    def render_sector_table(self) -> Table:
        """Render sector ranking and capital inflow table."""
        table = Table(
            title="📊 行业板块涨跌榜与主力资金流向 (Sector Inflow Ranking)",
            title_style="bold cyan",
            header_style="bold bright_white on dark_blue",
            border_style="bright_blue",
            expand=True,
            show_edge=True,
        )
        table.add_column("排名", justify="center", width=6)
        table.add_column("行业板块", justify="left", width=14)
        table.add_column("涨跌幅", justify="right", width=10)
        table.add_column("主力净流入", justify="right", width=12)
        table.add_column("领涨龙头股", justify="left", width=18)
        table.add_column("龙头涨幅", justify="right", width=10)
        table.add_column("日内走势", justify="center", width=12)

        pos_color = "red" if self.palette == "cn" else "green"
        neg_color = "green" if self.palette == "cn" else "red"

        # Sort by change_pct descending
        sorted_sectors = sorted(self.sectors, key=lambda x: x.change_pct, reverse=True)

        for i, s in enumerate(sorted_sectors, 1):
            is_pos = s.change_pct >= 0
            p_col = pos_color if is_pos else neg_color
            sign = "+" if is_pos else ""

            lead_pos = s.leader_pct >= 0
            l_col = pos_color if lead_pos else neg_color
            l_sign = "+" if lead_pos else ""

            spark = smart_spark(s.trend_history or [], 12, self.palette)

            table.add_row(
                f"[bold cyan]#{i}[/]",
                f"[bold white]{s.name}[/]",
                f"[{p_col} bold]{sign}{s.change_pct:.2f}%[/]",
                f"[yellow]{s.net_inflow_billion:+.1f} 亿[/]",
                f"{s.leader_name} ([dim]{s.leader_symbol}[/])",
                f"[{l_col}]{l_sign}{s.leader_pct:.2f}%[/]",
                spark,
            )
        return table

    def render_full_sector_view(self) -> Group:
        return Group(
            self.render_heatmap_matrix(),
            Text(""),
            self.render_sector_table(),
        )
