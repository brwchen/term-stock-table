"""Tmux, WezTerm, and iTerm2 Statusline Output module.
Provides:
- Ultra-compact single-line stock ticker statusline generator
- ANSI / Powerline / Plain text format options for embedding in terminal status bars
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional
from .api import StockDataTracker


class StatuslineFormatter:
    """Formats stock watchlist or positions into a compact statusline string."""

    def __init__(self, trackers: Optional[Any] = None, palette: str = "cn"):
        self.trackers = trackers
        self.palette = palette

    def format_statusline(
        self,
        symbols: Optional[List[str]] = None,
        separator: str = " │ ",
        use_ansi: bool = True,
        show_spark: bool = True,
    ) -> str:
        """Generate a single-line ticker string.
        Example: 📈 贵州茅台 1688.00(+2.15%) │ 宁德时代 258.40(+4.82%) │ 比亚迪 298.50(+10.0%)
        """
        tracker_list = []
        if isinstance(self.trackers, list):
            tracker_list = self.trackers
        elif isinstance(self.trackers, StockDataTracker):
            tracker_list = [self.trackers]
        elif symbols:
            tracker_list = [StockDataTracker(s) for s in symbols]
        else:
            tracker_list = [StockDataTracker("600519"), StockDataTracker("300750"), StockDataTracker("002594")]

        if symbols:
            target_symbols = {s.upper() for s in symbols}
            tracker_list = [s for s in tracker_list if s.symbol.upper() in target_symbols or s.name in target_symbols]

        items = []
        for s in tracker_list:
            pct_sign = "+" if s.change_pct >= 0 else ""
            pct_str = f"{pct_sign}{s.change_pct:.2f}%"

            if use_ansi:
                # ANSI colors: Red for up in CN, Green for down
                if self.palette == "cn":
                    color_code = "\033[31m" if s.change_pct >= 0 else "\033[32m"
                else:
                    color_code = "\033[32m" if s.change_pct >= 0 else "\033[31m"
                reset_code = "\033[0m"

                item = f"{s.name} {s.price:.2f}({color_code}{pct_str}{reset_code})"
            else:
                item = f"{s.name} {s.price:.2f}({pct_str})"

            items.append(item)

        prefix = "📈 " if use_ansi else ""
        return prefix + separator.join(items)
