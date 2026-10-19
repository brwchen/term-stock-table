"""Stable aliases that stand in for stock names in the Boss Key view."""
from typing import Dict

SERVICE_REGISTRY: Dict[str, str] = {}


def _initials(name: str) -> str:
    """Pinyin initials for Chinese names, leading letters for Latin names."""
    try:
        from pypinyin import Style, lazy_pinyin
        parts = lazy_pinyin(name, style=Style.FIRST_LETTER, errors=lambda chunk: [chunk])
    except ImportError:
        parts = [c for c in name if c.isascii()]
    letters = "".join(c for c in "".join(parts).lower() if c.isalnum())
    return letters[:5]


def service_name(symbol: str, name: str = "") -> str:
    """Stable per-session alias derived from the stock name initials."""
    if symbol not in SERVICE_REGISTRY:
        base = _initials(name) or f"{len(SERVICE_REGISTRY) + 1}"
        alias, n = f"svc-{base}", 2
        while alias in SERVICE_REGISTRY.values():
            alias, n = f"svc-{base}{n}", n + 1
        SERVICE_REGISTRY[symbol] = alias
    return SERVICE_REGISTRY[symbol]
