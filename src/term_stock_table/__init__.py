"""term-stock-table: Professional real-time terminal stock monitoring table, technical indicators, detail views, and stealth boss mode."""

from .api import StockDataTracker, fetch_live_quotes, normalize_symbol_code
from .indicators import (
    compute_bollinger_bands,
    render_bollinger_badge,
    compute_sma,
    compute_rsi,
    compute_macd,
    compute_kdj,
    render_candlestick_chart,
    estimate_valuation_percentile,
)
from .table import create_stock_table, format_volume, format_amount
from .detail import render_stock_detail
from .boss import render_boss_view, PROFILES, export_daily_review
from .portfolio import calculate_portfolio_pnl, create_portfolio_table
from .alerts import evaluate_alerts, send_desktop_notification
from .market import render_indices_banner, simulate_capital_flow, render_capital_flow_panel
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
    load_portfolio,
    save_position,
    remove_position,
    load_alerts,
    save_alert,
    remove_alert,
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
    "compute_macd",
    "compute_kdj",
    "render_candlestick_chart",
    "estimate_valuation_percentile",
    "create_stock_table",
    "format_volume",
    "format_amount",
    "render_stock_detail",
    "render_boss_view",
    "PROFILES",
    "export_daily_review",
    "calculate_portfolio_pnl",
    "create_portfolio_table",
    "evaluate_alerts",
    "send_desktop_notification",
    "render_indices_banner",
    "simulate_capital_flow",
    "render_capital_flow_panel",
    "load_watchlist",
    "save_watchlist",
    "add_to_watchlist",
    "remove_from_watchlist",
    "load_notes",
    "save_note",
    "get_symbol_notes",
    "load_settings",
    "save_settings",
    "load_portfolio",
    "save_position",
    "remove_position",
    "load_alerts",
    "save_alert",
    "remove_alert",
    "StockTerminalApp",
]
