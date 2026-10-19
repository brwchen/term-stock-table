"""Intraday Chart (Price + VWAP), Volume Profile (Chip Distribution), and Tick Tape module.
Provides:
- High-definition Intraday Minutely Chart (Current Price Line vs VWAP Mean Line + Volume)
- Chip Volume Distribution (获利比例, 筹码集中度, 成本分布直方图)
- Tick-by-tick Trade Tape (实时逐笔成交明细: 买盘/卖盘/大单标记)
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Any, Optional

from rich.console import Console, Group
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.columns import Columns

from term_sparkline import sparkline


@dataclass
class TickRecord:
    """Single tick trade."""
    time_str: str
    price: float
    volume_lots: int
    direction: str  # "B" (Buy), "S" (Sell), "M" (Neutral)
    is_large: bool = False


@dataclass
class ChipDistribution:
    """Chip volume distribution (筹码分布 / Cost Volume Profile)."""
    profit_ratio: float = 78.4  # % of shares currently in profit
    avg_cost: float = 175.20   # Average cost basis
    concentration_90: float = 8.5  # 90% concentration width percentage
    range_90_low: float = 162.00
    range_90_high: float = 188.50
    price_levels: List[Tuple[float, float]] = field(default_factory=list)  # (price, volume_weight)


class IntradayChartRenderer:
    """Renders high-definition intraday price chart with VWAP line."""

    def __init__(
        self,
        symbol: str,
        name: str,
        pre_close: float,
        prices: Optional[List[float]] = None,
        volumes: Optional[List[int]] = None,
        palette: str = "cn",
    ):
        self.symbol = symbol
        self.name = name
        self.pre_close = pre_close
        self.palette = palette

        if prices is None:
            # Generate realistic intraday random walk around pre_close
            self.prices, self.vwap, self.volumes = self._generate_mock_intraday(pre_close)
        else:
            self.prices = prices
            self.volumes = volumes or [random.randint(100, 5000) for _ in prices]
            self.vwap = self._calculate_vwap(self.prices, self.volumes)

    def _generate_mock_intraday(self, base_price: float) -> Tuple[List[float], List[float], List[int]]:
        """Generate 30 intraday snapshots (representing 9:30 to 15:00)."""
        pts = 30
        curr = base_price * (1.0 + random.uniform(-0.01, 0.02))
        price_list = []
        vol_list = []
        cumulative_val = 0.0
        cumulative_vol = 0
        vwap_list = []

        for _ in range(pts):
            step = random.uniform(-0.005, 0.006) * base_price
            curr = max(base_price * 0.9, min(base_price * 1.1, curr + step))
            vol = random.randint(300, 8000)
            price_list.append(round(curr, 2))
            vol_list.append(vol)

            cumulative_val += curr * vol
            cumulative_vol += vol
            vwap_list.append(round(cumulative_val / cumulative_vol, 2))

        return price_list, vwap_list, vol_list

    def _calculate_vwap(self, prices: List[float], volumes: List[int]) -> List[float]:
        vwap = []
        cum_val = 0.0
        cum_vol = 0
        for p, v in zip(prices, volumes):
            cum_val += p * v
            cum_vol += max(1, v)
            vwap.append(round(cum_val / cum_vol, 2))
        return vwap

    def render_intraday_panel(self, height: int = 10, width: int = 56) -> Panel:
        """Render ASCII/Unicode terminal intraday graph."""
        pos_color = "red" if self.palette == "cn" else "green"
        neg_color = "green" if self.palette == "cn" else "red"

        min_p = min(min(self.prices), self.pre_close * 0.98)
        max_p = max(max(self.prices), self.pre_close * 1.02)
        p_range = max(0.01, max_p - min_p)

        grid = [[" " for _ in range(width)] for _ in range(height)]
        pre_close_y = int((1.0 - (self.pre_close - min_p) / p_range) * (height - 1))
        pre_close_y = max(0, min(height - 1, pre_close_y))

        # Draw baseline pre_close
        for x in range(width):
            grid[pre_close_y][x] = "┄"

        step_x = len(self.prices) / width if width > 0 else 1

        # Plot Price line (█ / ●) and VWAP (· / ─)
        for x in range(width):
            idx = min(len(self.prices) - 1, int(x * step_x))
            p = self.prices[idx]
            v_p = self.vwap[idx]

            y_p = int((1.0 - (p - min_p) / p_range) * (height - 1))
            y_p = max(0, min(height - 1, y_p))

            y_v = int((1.0 - (v_p - min_p) / p_range) * (height - 1))
            y_v = max(0, min(height - 1, y_v))

            if y_p == y_v:
                grid[y_p][x] = "◈"
            else:
                grid[y_v][x] = "═"
                grid[y_p][x] = "●"

        # Format output lines with price labels
        lines = []
        for y, row_chars in enumerate(grid):
            p_val = max_p - (y / (height - 1)) * p_range
            pct = ((p_val - self.pre_close) / self.pre_close) * 100
            p_style = pos_color if p_val >= self.pre_close else neg_color
            sign = "+" if pct >= 0 else ""

            row_str = "".join(row_chars)
            # Highlight tokens
            row_str = row_str.replace("●", f"[{p_style}]●[/]")
            row_str = row_str.replace("═", "[yellow]═[/]")
            row_str = row_str.replace("◈", "[bold cyan]◈[/]")
            row_str = row_str.replace("┄", "[dim]┄[/]")

            lbl = f"[{p_style}]{p_val:>7.2f} ({sign}{pct:>5.1f}%)[/]"
            lines.append(f"{lbl} │{row_str}│")

        # Time axis
        time_bar = " 09:30" + " " * (width - 24) + "11:30/13:00" + " " * (width - 38) + "15:00"
        lines.append(f"{' ' * 16} └{'─' * width}┘")
        lines.append(f"{' ' * 16}  {time_bar}")

        curr_p = self.prices[-1]
        curr_pct = ((curr_p - self.pre_close) / self.pre_close) * 100
        sign = "+" if curr_pct >= 0 else ""
        c_col = pos_color if curr_pct >= 0 else neg_color

        content = "\n".join(lines)
        legend = f"图例: [{c_col}]● 现价 {curr_p:.2f} ({sign}{curr_pct:.2f}%)[/]  [yellow]═ 分时均线(VWAP) {self.vwap[-1]:.2f}[/]  [dim]┄ 昨收 {self.pre_close:.2f}[/]"

        return Panel(
            Group(Text.from_markup(content), Text.from_markup("\n" + legend)),
            title=f"[bold bright_white]📈 {self.name} ({self.symbol}) 分时走势与均线 (Intraday & VWAP)[/]",
            border_style="bright_blue",
            padding=(0, 1),
        )


class ChipProfileRenderer:
    """Renders Chip Volume Distribution (筹码分布) and statistics."""

    def __init__(self, current_price: float, palette: str = "cn"):
        self.current_price = current_price
        self.palette = palette
        self.chip_data = self._calculate_chip_distribution(current_price)

    def _calculate_chip_distribution(self, current_price: float) -> ChipDistribution:
        """Simulate realistic multi-peak chip volume distribution."""
        levels = []
        low_p = current_price * 0.85
        high_p = current_price * 1.15
        steps = 12
        step_val = (high_p - low_p) / steps

        # Generate Gaussian-like dual cost peaks
        peak1 = current_price * 0.94
        peak2 = current_price * 1.03

        profit_sum = 0.0
        total_vol = 0.0

        for i in range(steps):
            p = low_p + i * step_val
            # Gaussian bell curves around peak1 and peak2
            w1 = math.exp(-((p - peak1) ** 2) / (2 * (current_price * 0.04) ** 2))
            w2 = 0.7 * math.exp(-((p - peak2) ** 2) / (2 * (current_price * 0.03) ** 2))
            weight = max(0.05, w1 + w2 + random.uniform(0.02, 0.08))

            levels.append((p, weight))
            total_vol += weight
            if p <= current_price:
                profit_sum += weight

        profit_ratio = (profit_sum / total_vol) * 100 if total_vol else 50.0
        avg_cost = sum(p * w for p, w in levels) / total_vol if total_vol else current_price

        return ChipDistribution(
            profit_ratio=round(profit_ratio, 1),
            avg_cost=round(avg_cost, 2),
            concentration_90=round(8.6, 1),
            range_90_low=round(current_price * 0.91, 2),
            range_90_high=round(current_price * 1.06, 2),
            price_levels=levels,
        )

    def render_chip_panel(self) -> Panel:
        """Render Rich panel showing chip histogram and key metrics."""
        cd = self.chip_data
        pos_color = "red" if self.palette == "cn" else "green"
        neg_color = "green" if self.palette == "cn" else "red"

        # Find max level weight for bar scaling
        max_w = max((w for _, w in cd.price_levels), default=1.0)
        bar_max_len = 18

        lines = []
        for p, w in reversed(cd.price_levels):
            bar_len = int((w / max_w) * bar_max_len)
            bar_len = max(1, min(bar_max_len, bar_len))

            is_profit = p <= self.current_price
            bar_col = pos_color if is_profit else neg_color
            bar_char = "█" * bar_len

            curr_marker = " ◀现价" if abs(p - self.current_price) < ((cd.price_levels[1][0] - cd.price_levels[0][0]) / 2) else ""
            lines.append(f" {p:>7.2f} │[{bar_col}]{bar_char:<18}[/] [bold yellow]{curr_marker}[/]")

        chart_text = "\n".join(lines)

        stat_col = pos_color if cd.profit_ratio >= 50 else neg_color
        stats = Text.from_markup(
            f"[bold]获利盘比例:[/] [{stat_col}]{cd.profit_ratio}%[/]\n"
            f"[bold]平均持仓成本:[/] [bold yellow]{cd.avg_cost:.2f}[/]\n"
            f"[bold]90% 筹码集中度:[/] [bold cyan]{cd.concentration_90}%[/]\n"
            f"[bold]90% 筹码区间:[/] [dim]{cd.range_90_low:.2f} - {cd.range_90_high:.2f}[/]\n"
            f"[bold]形态特征:[/] [bold white]单峰密集 获利盘主导[/]"
        )

        grid = Table.grid(padding=(0, 2))
        grid.add_column()
        grid.add_column()
        grid.add_row(Text.from_markup(chart_text), stats)

        return Panel(
            grid,
            title="[bold yellow]🎯 筹码分布图 (Cost Volume Profile)[/]",
            border_style="yellow",
            padding=(0, 1),
        )


class TickTapeRenderer:
    """Renders real-time tick-by-tick order tape (逐笔成交明细)."""

    def __init__(self, current_price: float, palette: str = "cn"):
        self.current_price = current_price
        self.palette = palette
        self.ticks = self._generate_mock_ticks(current_price)

    def _generate_mock_ticks(self, current_price: float, count: int = 8) -> List[TickRecord]:
        ticks = []
        dirs = ["B", "S", "M"]
        weights = [0.55, 0.40, 0.05]

        for i in range(count):
            d = random.choices(dirs, weights=weights)[0]
            delta = random.choice([-0.05, 0.0, 0.0, +0.05])
            p = round(current_price + delta, 2)
            vol = random.choice([20, 50, 120, 250, 500, 1200, 2800])
            is_large = vol >= 1000
            ticks.append(TickRecord(
                time_str=f"14:{50+i//2:02d}:{random.randint(10,59):02d}",
                price=p,
                volume_lots=vol,
                direction=d,
                is_large=is_large,
            ))
        return ticks

    def render_tape_table(self) -> Table:
        table = Table(
            title="⚡ 逐笔成交明细 (Tick Tape)",
            title_style="bold cyan",
            header_style="bold bright_white on dark_blue",
            border_style="blue",
            expand=True,
            show_edge=True,
        )
        table.add_column("时间", justify="center", width=9)
        table.add_column("成交价", justify="right", width=9)
        table.add_column("手数", justify="right", width=8)
        table.add_column("盘口性质", justify="center", width=10)
        table.add_column("资金性质", justify="left")

        pos_color = "red" if self.palette == "cn" else "green"
        neg_color = "green" if self.palette == "cn" else "red"

        for t in self.ticks:
            if t.direction == "B":
                dir_label = f"[{pos_color}]主动买盘 (B)[/]"
            elif t.direction == "S":
                dir_label = f"[{neg_color}]主动卖盘 (S)[/]"
            else:
                dir_label = "[dim]中性平盘 (M)[/]"

            tag = "[bold yellow]🔥 主力大单[/]" if t.is_large else "[dim]普通散单[/]"

            table.add_row(
                f"[dim]{t.time_str}[/]",
                f"[bold white]{t.price:.2f}[/]",
                f"[magenta]{t.volume_lots:,}[/]",
                dir_label,
                tag,
            )
        return table
