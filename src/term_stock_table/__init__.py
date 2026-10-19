"""term-stock-table: Professional real-time terminal stock monitoring table, technical indicators, detail views, and stealth boss mode."""

from .api import StockDataTracker, fetch_live_quotes, normalize_symbol_code
from .indicators import compute_bollinger_bands, render_bollinger_badge, compute_sma, compute_rsi
from .table import create_stock_table, format_volume, format_amount
from .detail import render_stock_detail
from .boss import render_boss_view, PROFILES
from .config import (
    load_watchlist,
    save_watchlist,
    add_to_watchlist,
    remove_from_watchlist,
    load_notes,
    save_note,
    get_symbol_notes,
    load_settings,
    save_settings,
)
from .tui import StockTerminalApp

__version__ = "0.1.0"
__all__ = [
    "StockDataTracker",
    "fetch_live_quotes",
    "normalize_symbol_code",
    "compute_bollinger_bands",
    "render_bollinger_badge",
    "compute_sma",
    "compute_rsi",
    "create_stock_table",
    "format_volume",
    "format_amount",
    "render_stock_detail",
    "render_boss_view",
    "PROFILES",
    "load_watchlist",
    "save_watchlist",
    "add_to_watchlist",
    "remove_from_watchlist",
    "load_notes",
    "save_note",
    "get_symbol_notes",
    "load_settings",
    "save_settings",
    "StockTerminalApp",
]
