"""Technical indicators and visual badges for stock analysis."""
import math
from typing import List, Tuple, Optional, Dict, Any


def compute_sma(prices: List[float], window: int) -> List[Optional[float]]:
    """Compute Simple Moving Average."""
    if not prices or window <= 0:
        return []
    res: List[Optional[float]] = []
    for i in range(len(prices)):
        if i + 1 < window:
            res.append(None)
        else:
            subset = prices[i + 1 - window : i + 1]
            res.append(sum(subset) / window)
    return res


def compute_bollinger_bands(
    prices: List[float], window: int = 20, num_std: float = 2.0
) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[float], Optional[float]]:
    """
    Calculate Bollinger Bands for price series.
    Returns: (Upper Band, Middle SMA, Lower Band, %b, Bandwidth)
    """
    if not prices or len(prices) < 2:
        return (None, None, None, None, None)

    w = min(window, len(prices))
    subset = prices[-w:]
    middle = sum(subset) / w

    variance = sum((p - middle) ** 2 for p in subset) / (w - 1 if w > 1 else 1)
    std_dev = math.sqrt(variance)

    upper = middle + num_std * std_dev
    lower = middle - num_std * std_dev

    last_price = prices[-1]
    band_range = upper - lower
    percent_b = ((last_price - lower) / band_range) if band_range > 0 else 0.5
    bandwidth = ((upper - lower) / middle * 100.0) if middle > 0 else 0.0

    return (upper, middle, lower, percent_b, bandwidth)


def render_bollinger_badge(percent_b: Optional[float], palette: str = "cn") -> str:
    """Render compact, intuitive visual badge for Bollinger %b position."""
    if percent_b is None:
        return "[-----]"

    is_cn = (palette == "cn")
    col_up = "\033[31m" if is_cn else "\033[32m"
    col_down = "\033[32m" if is_cn else "\033[31m"
    rst = "\033[0m"

    if percent_b > 1.0:
        return f"{col_up}[····▶]{rst}"  # Above Upper (Overbought)
    elif percent_b >= 0.8:
        return f"{col_up}[···●·]{rst}"  # Upper Band
    elif percent_b >= 0.6:
        return f"[··●··]"                # Mid-Upper
    elif percent_b >= 0.4:
        return f"[··●··]"                # Neutral
    elif percent_b >= 0.2:
        return f"[·●···]"                # Mid-Lower
    elif percent_b >= 0.0:
        return f"{col_down}[●····]{rst}"  # Lower Band
    else:
        return f"{col_down}[◀····]{rst}"  # Below Lower (Oversold)


def compute_rsi(prices: List[float], period: int = 14) -> List[float]:
    """Compute Relative Strength Index (RSI)."""
    if not prices or len(prices) < 2:
        return [50.0] * len(prices)
    gains: List[float] = [0.0]
    losses: List[float] = [0.0]
    for i in range(1, len(prices)):
        diff = prices[i] - prices[i - 1]
        gains.append(max(0.0, diff))
        losses.append(max(0.0, -diff))

    rsi_values: List[float] = []
    for i in range(len(prices)):
        if i < period:
            rsi_values.append(50.0)
            continue
        avg_gain = sum(gains[i - period + 1 : i + 1]) / period
        avg_loss = sum(losses[i - period + 1 : i + 1]) / period
        if avg_loss == 0:
            rsi_values.append(100.0)
        else:
            rs = avg_gain / avg_loss
            rsi_values.append(100.0 - (100.0 / (1.0 + rs)))
    return rsi_values
