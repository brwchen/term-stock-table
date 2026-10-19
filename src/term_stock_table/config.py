"""Configuration, watchlist, notes, and user settings persistence."""
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

DEFAULT_CONFIG_DIR = Path.home() / ".term_stock"
WATCHLIST_FILE = DEFAULT_CONFIG_DIR / "watchlist.json"
NOTES_FILE = DEFAULT_CONFIG_DIR / "notes.json"
SETTINGS_FILE = DEFAULT_CONFIG_DIR / "settings.json"
PORTFOLIO_FILE = DEFAULT_CONFIG_DIR / "portfolio.json"
ALERTS_FILE = DEFAULT_CONFIG_DIR / "alerts.json"

DEFAULT_WATCHLIST = [
    "600519",  # 贵州茅台
    "000001",  # 平安银行
    "300750",  # 宁德时代
    "AAPL",    # 苹果
    "NVDA",    # 英伟达
    "00700",   # 腾讯控股
    "BABA",    # 阿里巴巴
]

DEFAULT_SETTINGS = {
    "palette": "cn",  # "cn" (Red up/Green down) or "us" (Green up/Red down)
    "refresh_interval": 1.0,
    "sparkline_length": 14,
    "default_boss_profile": "devops",  # "devops", "nginx", "monochrome"
    "visible_columns": [
        "symbol", "name", "price", "change_pct", "change",
        "amplitude", "turnover_rate", "volume", "amount", "pe",
        "bollinger", "sparkline"
    ],
}


def ensure_config_dir():
    """Ensure configuration directory exists."""
    DEFAULT_CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_watchlist() -> List[str]:
    """Load stock watchlist from disk or return default."""
    ensure_config_dir()
    if WATCHLIST_FILE.exists():
        try:
            with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and data:
                    return data
        except Exception:
            pass
    return list(DEFAULT_WATCHLIST)


def save_watchlist(watchlist: List[str]) -> None:
    """Save stock watchlist to disk."""
    ensure_config_dir()
    with open(WATCHLIST_FILE, "w", encoding="utf-8") as f:
        json.dump(watchlist, f, ensure_ascii=False, indent=2)


def add_to_watchlist(symbol: str) -> bool:
    """Add a symbol to watchlist if not already present."""
    wl = load_watchlist()
    s_clean = symbol.strip().upper()
    if s_clean and s_clean not in [x.upper() for x in wl]:
        wl.append(s_clean)
        save_watchlist(wl)
        return True
    return False


def remove_from_watchlist(symbol: str) -> bool:
    """Remove a symbol from watchlist."""
    wl = load_watchlist()
    s_clean = symbol.strip().upper()
    new_wl = [x for x in wl if x.upper() != s_clean]
    if len(new_wl) != len(wl):
        save_watchlist(new_wl)
        return True
    return False


def load_notes() -> Dict[str, List[Dict[str, Any]]]:
    """Load all stock investment notes."""
    ensure_config_dir()
    if NOTES_FILE.exists():
        try:
            with open(NOTES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_note(symbol: str, note_text: str, tags: Optional[List[str]] = None) -> None:
    """Add or append an investment note for a stock symbol."""
    notes = load_notes()
    s_clean = symbol.strip().upper()
    import datetime
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = {
        "timestamp": now_str,
        "text": note_text.strip(),
        "tags": tags or ["default"],
    }
    if s_clean not in notes:
        notes[s_clean] = []
    notes[s_clean].insert(0, entry)  # Prepend newest
    ensure_config_dir()
    with open(NOTES_FILE, "w", encoding="utf-8") as f:
        json.dump(notes, f, ensure_ascii=False, indent=2)


def get_symbol_notes(symbol: str) -> List[Dict[str, Any]]:
    """Get all notes for a specific stock."""
    notes = load_notes()
    return notes.get(symbol.strip().upper(), [])


def load_settings() -> Dict[str, Any]:
    """Load user settings."""
    ensure_config_dir()
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                s = json.load(f)
                merged = dict(DEFAULT_SETTINGS)
                merged.update(s)
                return merged
        except Exception:
            pass
    return dict(DEFAULT_SETTINGS)


def save_settings(settings: Dict[str, Any]) -> None:
    """Save user settings."""
    ensure_config_dir()
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)


def load_portfolio() -> Dict[str, Dict[str, Any]]:
    """Load user portfolio positions."""
    ensure_config_dir()
    if PORTFOLIO_FILE.exists():
        try:
            with open(PORTFOLIO_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_position(symbol: str, shares: float, cost: float, currency: str = "CNY") -> None:
    """Add or update a portfolio position."""
    portfolio = load_portfolio()
    s_clean = symbol.strip().upper()
    portfolio[s_clean] = {
        "shares": float(shares),
        "cost": float(cost),
        "currency": currency.upper(),
    }
    ensure_config_dir()
    with open(PORTFOLIO_FILE, "w", encoding="utf-8") as f:
        json.dump(portfolio, f, ensure_ascii=False, indent=2)


def remove_position(symbol: str) -> bool:
    """Remove a position from portfolio."""
    portfolio = load_portfolio()
    s_clean = symbol.strip().upper()
    if s_clean in portfolio:
        del portfolio[s_clean]
        ensure_config_dir()
        with open(PORTFOLIO_FILE, "w", encoding="utf-8") as f:
            json.dump(portfolio, f, ensure_ascii=False, indent=2)
        return True
    return False


def load_alerts() -> Dict[str, Dict[str, Any]]:
    """Load price and volatility alert thresholds."""
    ensure_config_dir()
    if ALERTS_FILE.exists():
        try:
            with open(ALERTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_alert(
    symbol: str,
    target_high: Optional[float] = None,
    target_low: Optional[float] = None,
    max_change_pct: Optional[float] = None,
) -> None:
    """Add or update price alert configuration for a stock symbol."""
    alerts = load_alerts()
    s_clean = symbol.strip().upper()
    current = alerts.get(s_clean, {})
    if target_high is not None:
        current["target_high"] = float(target_high)
    if target_low is not None:
        current["target_low"] = float(target_low)
    if max_change_pct is not None:
        current["max_change_pct"] = float(max_change_pct)
    current["enabled"] = True
    alerts[s_clean] = current
    ensure_config_dir()
    with open(ALERTS_FILE, "w", encoding="utf-8") as f:
        json.dump(alerts, f, ensure_ascii=False, indent=2)


def remove_alert(symbol: str) -> bool:
    """Remove an alert for a stock symbol."""
    alerts = load_alerts()
    s_clean = symbol.strip().upper()
    if s_clean in alerts:
        del alerts[s_clean]
        ensure_config_dir()
        with open(ALERTS_FILE, "w", encoding="utf-8") as f:
            json.dump(alerts, f, ensure_ascii=False, indent=2)
        return True
    return False

