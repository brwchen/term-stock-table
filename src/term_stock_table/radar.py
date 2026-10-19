"""Market Breadth Sentiment, Capital Flow, and Real-time Anomaly Radar module.
Provides:
- Market breadth sentiment (Up/Down ratio, Limit-up/Limit-down count, Volume comparison)
- Northbound / Southbound (HK-SH-SZ Connect) net flow and intraday curve
- Live ticker anomaly radar (Rocket surge, Dump dive, Heavy buy/sell blocks, Limit break)
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional

from rich.console import Console, Group
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.columns import Columns

from .inline_spark import smart_spark, labeled


@dataclass
class MarketSentiment:
    """Snapshot of overall market sentiment."""
    up_count: int = 2840
    down_count: int = 1950
    flat_count: int = 310
    limit_up: int = 58
    limit_down: int = 6
    total_volume_billions: float = 1128.5  # In Billions CNY
    volume_change_pct: float = +8.4  # vs yesterday same time
    sentiment_score: int = 68  # 0 to 100
    sentiment_label: str = "偏多 / Bullish"
    northbound_net_billion: float = +42.8  # Northbound net inflow (HK -> CN)
    southbound_net_billion: float = +28.5  # Southbound net inflow (CN -> HK)
    northbound_curve: List[float] = field(default_factory=lambda: [
        0.0, 5.2, 12.1, 18.4, 15.2, 22.0, 28.5, 34.2, 32.1, 38.0, 42.8
    ])
    southbound_curve: List[float] = field(default_factory=lambda: [
        0.0, 3.1, 8.4, 12.0, 16.5, 18.2, 21.0, 24.5, 26.8, 27.2, 28.5
    ])


@dataclass
class AnomalyEvent:
    """Real-time market anomaly signal."""
    timestamp: str
    symbol: str
    name: str
    event_type: str  # "🚀 火箭发射", "💥 盘中跳水", "💰 大单买入", "📉 大单卖出", "⚡ 封涨停", "⚠️ 炸板"
    price: float
    change_pct: float
    volume_lots: int  # in lots (手)
    details: str

    def to_colored_text(self, palette: str = "cn") -> Text:
        txt = Text()
        txt.append(f"[{self.timestamp}] ", style="dim")
        txt.append(f"{self.symbol:<8} ", style="bold cyan")
        txt.append(f"{self.name:<6} ", style="bold white")

        # Color based on event type
        is_pos = "发射" in self.event_type or "买入" in self.event_type or "封涨停" in self.event_type
        if palette == "cn":
            ev_style = "bold red" if is_pos else "bold green"
        else:
            ev_style = "bold green" if is_pos else "bold red"

        txt.append(f"{self.event_type:<8} ", style=ev_style)
        txt.append(f"{self.price:>7.2f} ", style="bold yellow")
        pct_sign = "+" if self.change_pct > 0 else ""
        txt.append(f"({pct_sign}{self.change_pct:.2f}%) ", style=ev_style)
        txt.append(f"成交: {self.volume_lots:,}手 ", style="magenta")
        txt.append(f"{self.details}", style="dim")
        return txt


class MarketRadarTracker:
    """Generates and tracks market sentiment and live anomaly events."""

    def __init__(self, palette: str = "cn"):
        self.palette = palette
        self.sentiment = MarketSentiment()
        self.anomaly_log: List[AnomalyEvent] = []
        self._init_mock_anomalies()

    def _init_mock_anomalies(self) -> None:
        """Seed sample anomaly events."""
        now = datetime.now().strftime("%H:%M:%S")
        samples = [
            AnomalyEvent(now, "300750", "宁德时代", "🚀 火箭发射", 258.40, +4.82, 3850, "1分钟快速拉升 1.8%"),
            AnomalyEvent(now, "600519", "贵州茅台", "💰 大单买入", 1688.00, +2.15, 1200, "主力单笔成交 2.02 亿元"),
            AnomalyEvent(now, "002594", "比亚迪", "⚡ 封涨停", 298.50, +10.00, 15400, "封单 4.2 亿元封死涨停"),
            AnomalyEvent(now, "000001", "平安银行", "💰 大单买入", 11.24, +1.26, 45000, "万手大单连续扫盘"),
            AnomalyEvent(now, "688981", "中芯国际", "🚀 火箭发射", 98.60, +5.12, 8200, "半导体板块脉冲拉升"),
            AnomalyEvent(now, "002230", "科大讯飞", "⚠️ 炸板", 48.90, +8.80, 12800, "开板回落 成交放大"),
        ]
        self.anomaly_log = samples

    def get_sentiment_panel(self) -> Panel:
        """Render market sentiment summary panel."""
        s = self.sentiment
        pos_color = "red" if self.palette == "cn" else "green"
        neg_color = "green" if self.palette == "cn" else "red"

        # Up/Down visual bar
        total_stocks = s.up_count + s.down_count + s.flat_count
        up_ratio = s.up_count / total_stocks if total_stocks else 0.5
        bar_len = 24
        up_blocks = int(bar_len * up_ratio)
        down_blocks = bar_len - up_blocks
        up_bar = f"[{pos_color}]{'█' * up_blocks}[/][{neg_color}]{'█' * down_blocks}[/]"

        # Sparklines for capital flow
        nb_spark = smart_spark(s.northbound_curve, 12, self.palette)
        sb_spark = smart_spark(s.southbound_curve, 12, self.palette)

        grid = Table.grid(padding=(0, 2))
        grid.add_column(justify="left")
        grid.add_column(justify="left")
        grid.add_column(justify="left")

        col1 = Text.from_markup(
            f"[bold]全市场情绪:[/] [bold yellow]{s.sentiment_score}分[/] ([bold cyan]{s.sentiment_label}[/])\n"
            f"[bold]涨跌分布:[/] [{pos_color}]涨 {s.up_count}[/] : [dim]平 {s.flat_count}[/] : [{neg_color}]跌 {s.down_count}[/]\n"
            f"[bold]力量对比:[/] {up_bar} [bold]涨停:[{pos_color}]{s.limit_up}[/] 跌停:[{neg_color}]{s.limit_down}[/]"
        )

        vol_sign = "+" if s.volume_change_pct > 0 else ""
        vol_col = pos_color if s.volume_change_pct > 0 else neg_color
        col2 = Text.from_markup(
            f"[bold]两市成交额:[/] [bold yellow]{s.total_volume_billions:.1f} 亿元[/]\n"
            f"[bold]量能对比:[/] [{vol_col}]{vol_sign}{s.volume_change_pct:.1f}% 同比放量[/]\n"
            f"[bold]赚钱效应:[/] [bold cyan]{(s.up_count / total_stocks * 100):.1f}% 胜率[/]"
        )

        col3 = Group(
            labeled(Text.from_markup(f"[bold]北向资金 (沪深股通):[/] [{pos_color}]+{s.northbound_net_billion:.1f}亿[/]"), nb_spark, 12),
            labeled(Text.from_markup(f"[bold]南向资金 (港股通):[/]   [{pos_color}]+{s.southbound_net_billion:.1f}亿[/]"), sb_spark, 12),
            Text.from_markup("[bold]外资风向:[/] [bold green]净流入加仓[/]"),
        )

        grid.add_row(col1, col2, col3)
        return Panel(
            grid,
            title="[bold cyan]🌐 全市场情绪晴雨表 & 互联互通资金流 (Market Breadth & Connect Flow)[/]",
            border_style="cyan",
            padding=(0, 1),
        )

    def get_anomaly_table(self, max_items: int = 6) -> Table:
        """Render recent anomaly alert table."""
        table = Table(
            title="⚡ 盘中实时异动扫描雷达 (Live Anomaly Radar)",
            title_style="bold yellow",
            header_style="bold bright_white on dark_blue",
            border_style="bright_blue",
            expand=True,
            show_edge=True,
        )
        table.add_column("时间", justify="center", width=10)
        table.add_column("代码", justify="center", width=8)
        table.add_column("名称", justify="left", width=10)
        table.add_column("异动类型", justify="center", width=12)
        table.add_column("现价", justify="right", width=9)
        table.add_column("涨跌幅", justify="right", width=9)
        table.add_column("异动单量", justify="right", width=12)
        table.add_column("异动详情", justify="left")

        pos_color = "red" if self.palette == "cn" else "green"
        neg_color = "green" if self.palette == "cn" else "red"

        for ev in self.anomaly_log[:max_items]:
            is_pos = "发射" in ev.event_type or "买入" in ev.event_type or "封涨停" in ev.event_type
            ev_col = pos_color if is_pos else neg_color
            pct_sign = "+" if ev.change_pct > 0 else ""

            table.add_row(
                f"[dim]{ev.timestamp}[/]",
                f"[bold cyan]{ev.symbol}[/]",
                f"[bold white]{ev.name}[/]",
                f"[{ev_col}]{ev.event_type}[/]",
                f"[bold yellow]{ev.price:.2f}[/]",
                f"[{ev_col}]{pct_sign}{ev.change_pct:.2f}%[/]",
                f"[magenta]{ev.volume_lots:,}手[/]",
                f"[dim]{ev.details}[/]",
            )
        return table

    def render_full_radar_view(self) -> Group:
        """Render complete radar panel combining sentiment and anomaly stream."""
        return Group(
            self.get_sentiment_panel(),
            Text(""),
            self.get_anomaly_table(),
        )
