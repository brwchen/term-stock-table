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


def compute_macd(
    prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9
) -> Tuple[List[float], List[float], List[float]]:
    """
    Compute MACD (DIF, DEA, MACD Histogram).
    """
    if not prices:
        return ([], [], [])
    
    # Calculate EMA
    def calc_ema(series: List[float], span: int) -> List[float]:
        alpha = 2.0 / (span + 1.0)
        ema = [series[0]]
        for val in series[1:]:
            ema.append(alpha * val + (1.0 - alpha) * ema[-1])
        return ema

    ema_fast = calc_ema(prices, fast)
    ema_slow = calc_ema(prices, slow)
    
    dif = [f - s for f, s in zip(ema_fast, ema_slow)]
    dea = calc_ema(dif, signal)
    hist = [(d - a) * 2.0 for d, a in zip(dif, dea)]
    
    return (dif, dea, hist)


def compute_kdj(
    closes: List[float],
    highs: Optional[List[float]] = None,
    lows: Optional[List[float]] = None,
    n: int = 9,
    m1: int = 3,
    m2: int = 3,
) -> Tuple[List[float], List[float], List[float]]:
    """
    Compute Stochastic Oscillator (KDJ).
    """
    if not closes:
        return ([], [], [])
    
    if highs is None:
        highs = [c * 1.01 for c in closes]
    if lows is None:
        lows = [c * 0.99 for c in closes]
        
    k_vals: List[float] = []
    d_vals: List[float] = []
    j_vals: List[float] = []
    
    k_prev = 50.0
    d_prev = 50.0
    
    for i in range(len(closes)):
        start_idx = max(0, i - n + 1)
        period_low = min(lows[start_idx : i + 1])
        period_high = max(highs[start_idx : i + 1])
        
        if period_high > period_low:
            rsv = (closes[i] - period_low) / (period_high - period_low) * 100.0
        else:
            rsv = 50.0
            
        k = (2.0 / 3.0) * k_prev + (1.0 / 3.0) * rsv
        d = (2.0 / 3.0) * d_prev + (1.0 / 3.0) * k
        j = 3.0 * k - 2.0 * d
        
        k_vals.append(k)
        d_vals.append(d)
        j_vals.append(j)
        
        k_prev = k
        d_prev = d
        
    return (k_vals, d_vals, j_vals)


def render_candlestick_chart(
    candles: List[Dict[str, float]],
    height: int = 7,
    palette: str = "cn",
    gap: int = 0,
) -> str:
    """
    Render a character-based ASCII/Unicode candlestick chart.
    Each candle has 'open', 'high', 'low', 'close'.
    """
    if not candles:
        return "[dim]No candle data[/dim]"
        
    is_cn = (palette == "cn")
    up_col = "\033[31m" if is_cn else "\033[32m"
    down_col = "\033[32m" if is_cn else "\033[31m"
    rst = "\033[0m"
    
    all_highs = [c["high"] for c in candles]
    all_lows = [c["low"] for c in candles]
    min_val = min(all_lows)
    max_val = max(all_highs)
    val_range = max(max_val - min_val, 0.001)
    
    def val_to_y(v: float) -> int:
        return int(round((v - min_val) / val_range * (height - 1)))
    
    # Grid of characters and colors
    num_candles = len(candles)
    grid = [[" " for _ in range(num_candles)] for _ in range(height)]
    color_grid = [["" for _ in range(num_candles)] for _ in range(height)]
    
    for x, c in enumerate(candles):
        o, h, l, cl = c["open"], c["high"], c["low"], c["close"]
        is_up = (cl >= o)
        col = up_col if is_up else down_col
        
        y_low = val_to_y(l)
        y_high = val_to_y(h)
        y_open = val_to_y(o)
        y_close = val_to_y(cl)
        
        y_body_low = min(y_open, y_close)
        y_body_high = max(y_open, y_close)
        
        for y in range(y_low, y_high + 1):
            if y < 0 or y >= height:
                continue
            if y_body_low <= y <= y_body_high:
                grid[y][x] = "█" if is_up else "░"
            else:
                grid[y][x] = "│"
            color_grid[y][x] = col

    lines = []
    for y in reversed(range(height)):
        row_str = ""
        for x in range(num_candles):
            c_char = grid[y][x]
            c_color = color_grid[y][x]
            if c_color:
                row_str += f"{c_color}{c_char}{rst}"
            else:
                row_str += c_char
            row_str += " " * gap
        price_level = min_val + (y / (height - 1)) * val_range
        lines.append(f"{price_level:>8.2f} │ {row_str}")
        
    return "\n".join(lines)


def estimate_valuation_percentile(pe: Optional[float]) -> Tuple[float, str, str]:
    """
    Estimate valuation percentile (0-100%) and classification.
    Returns: (percentile, description, badge)
    """
    if pe is None or pe <= 0:
        return (50.0, "N/A (Loss/No Data)", "[dim][-----][/dim]")
        
    # Standard market valuation bell curve estimation
    if pe < 10.0:
        pct = max(5.0, pe * 1.5)
        status = "Deep Value / Undervalued"
        badge = "[bold cyan][●····][/bold cyan]"
    elif pe < 20.0:
        pct = 15.0 + (pe - 10.0) * 2.0
        status = "Reasonable / Fair Value"
        badge = "[bold green][·●···][/bold green]"
    elif pe < 40.0:
        pct = 35.0 + (pe - 20.0) * 1.8
        status = "Growth / Moderately High"
        badge = "[bold yellow][··●··][/bold yellow]"
    elif pe < 80.0:
        pct = 70.0 + (pe - 40.0) * 0.5
        status = "High Valuation / Premium"
        badge = "[bold red][···●·][/bold red]"
    else:
        pct = 95.0
        status = "Extreme Bubble / Speculative"
        badge = "[bold magenta][····●][/bold magenta]"
        
    return (pct, status, badge)

