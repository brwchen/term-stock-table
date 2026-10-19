"""Position & Watchlist CSV/JSON Import and Export module.
Supports:
- Importing position records from CSV (Tonghuashun, Xueqiu, or standard format)
- Exporting portfolio and watchlist to CSV or Markdown
"""

from __future__ import annotations

import csv
import json
import io
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

from .portfolio import Position


class PortfolioDataImporter:
    """Handles importing and exporting portfolio data."""

    @staticmethod
    def import_from_csv(csv_content_or_path: str) -> List[Position]:
        """Parse CSV rows into Position instances.
        Supported CSV headers (case-insensitive):
        - symbol, shares, cost_price, name, notes
        - 代码, 持仓数量, 成本价, 股票名称
        """
        content = csv_content_or_path
        if Path(csv_content_or_path).is_file():
            content = Path(csv_content_or_path).read_text(encoding="utf-8")

        positions: List[Position] = []
        reader = csv.DictReader(io.StringIO(content.strip()))

        # Normalize header keys
        for row in reader:
            normalized = {k.strip().lower(): v.strip() for k, v in row.items() if k}

            sym = normalized.get("symbol") or normalized.get("代码") or normalized.get("code") or ""
            name = normalized.get("name") or normalized.get("名称") or normalized.get("股票名称") or ""
            shares_str = normalized.get("shares") or normalized.get("持仓数量") or normalized.get("股数") or "100"
            cost_str = normalized.get("cost_price") or normalized.get("成本价") or normalized.get("买入均价") or "0.0"
            notes = normalized.get("notes") or normalized.get("备注") or ""

            if sym:
                try:
                    shares = int(float(shares_str))
                    cost_p = float(cost_str)
                    positions.append(Position(
                        symbol=sym,
                        name=name or sym,
                        shares=shares,
                        cost_price=cost_p,
                        notes=notes,
                    ))
                except ValueError:
                    continue

        return positions

    @staticmethod
    def export_to_csv(positions: List[Position]) -> str:
        """Export list of positions to CSV string."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["symbol", "name", "shares", "cost_price", "notes"])
        for p in positions:
            writer.writerow([p.symbol, p.name, p.shares, p.cost_price, p.notes])
        return output.getvalue()

    @staticmethod
    def export_to_markdown(positions: List[Position]) -> str:
        """Export portfolio to Markdown table."""
        lines = [
            "# 📊 投资组合持仓明细 (Portfolio Export)",
            "",
            "| 代码 | 名称 | 持仓股数 | 成本均价 | 备注 |",
            "|---|---|---|---|---|",
        ]
        for p in positions:
            lines.append(f"| {p.symbol} | {p.name} | {p.shares:,} | ¥{p.cost_price:.2f} | {p.notes} |")
        lines.append("")
        return "\n".join(lines)
