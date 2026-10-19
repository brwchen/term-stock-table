"""Real-time market quote fetcher and realistic offline simulator."""
import math
import json
import random
import threading
import time
import urllib.request
from collections import deque
from typing import Dict, List, Optional, Any, Tuple

DEFAULT_PRESET_SYMBOLS = {
    "600519": {"name": "贵州茅台", "price": 1324.97, "prev_close": 1329.00, "open": 1322.50, "high": 1348.60, "low": 1321.00, "volume": 39729, "amount": 530894.0, "turnover_rate": 0.32, "pe": 20.34, "pb": 6.59, "amplitude": 2.08},
    "000001": {"name": "平安银行", "price": 11.65, "prev_close": 11.50, "open": 11.48, "high": 11.68, "low": 11.41, "volume": 1267793, "amount": 146672.0, "turnover_rate": 0.65, "pe": 4.40, "pb": 0.49, "amplitude": 2.35},
    "300750": {"name": "宁德时代", "price": 267.02, "prev_close": 277.00, "open": 275.00, "high": 275.00, "low": 267.02, "volume": 311460, "amount": 839933.0, "turnover_rate": 0.73, "pe": 14.27, "pb": 3.31, "amplitude": 2.88},
    "AAPL":   {"name": "Apple Inc.", "price": 345.10, "prev_close": 343.46, "open": 340.78, "high": 346.00, "low": 340.12, "volume": 7915573, "amount": 2721349.0, "turnover_rate": 0.05, "pe": 39.58, "pb": 46.26, "amplitude": 1.71},
    "NVDA":   {"name": "NVIDIA Corp.", "price": 217.62, "prev_close": 214.13, "open": 218.10, "high": 218.41, "low": 214.70, "volume": 27918297, "amount": 6045270.0, "turnover_rate": 0.12, "pe": 27.51, "pb": 44.41, "amplitude": 1.73},
    "00700":  {"name": "腾讯控股", "price": 382.40, "prev_close": 380.00, "open": 378.00, "high": 385.00, "low": 376.60, "volume": 15820000, "amount": 604320.0, "turnover_rate": 0.18, "pe": 21.20, "pb": 3.85, "amplitude": 2.21},
    "BABA":   {"name": "阿里巴巴", "price": 88.50, "prev_close": 87.20, "open": 86.80, "high": 89.20, "low": 86.50, "volume": 12450000, "amount": 110182.0, "turnover_rate": 0.45, "pe": 12.80, "pb": 1.35, "amplitude": 3.10},
}


def normalize_symbol_code(symbol: str) -> str:
    """Normalize raw stock symbol into Tencent market quote code."""
    s = symbol.strip().lower()
    if s.startswith(("sh", "sz", "hk", "us")):
        return s
    if s.isdigit():
        if len(s) == 5:
            return "hk" + s
        if s.startswith(("60", "68", "90")):
            return "sh" + s
        elif s.startswith(("00", "30", "20")):
            return "sz" + s
        return "sh" + s
    # US stock ticker
    return "us" + s.upper()


def parse_tencent_line(line: str, code_map: Dict[str, str]) -> Optional[Dict[str, Any]]:
    """Parse single quote line from Tencent Finance."""
    line = line.strip()
    if not line or "=" not in line:
        return None
    var_name, val_str = line.split("=", 1)
    val_str = val_str.strip('"; \n')
    parts = val_str.split("~")
    if len(parts) < 6:
        return None

    q_code = var_name.replace("v_", "").strip()
    orig_sym = code_map.get(q_code, q_code)
    try:
        name = parts[1]
        price = float(parts[3])
        prev_close = float(parts[4]) if float(parts[4]) > 0 else price
        open_p = float(parts[5]) if parts[5] else prev_close
        volume = int(float(parts[6])) if parts[6] else 0

        # Parse 5-level Order Book (Bids & Asks)
        bids = []
        asks = []
        # Bid 1 to 5: [9..18]
        if len(parts) >= 29:
            for idx in range(9, 19, 2):
                if idx + 1 < len(parts) and parts[idx]:
                    bids.append((float(parts[idx]), int(float(parts[idx + 1])) if parts[idx + 1] else 0))
            for idx in range(19, 29, 2):
                if idx + 1 < len(parts) and parts[idx]:
                    asks.append((float(parts[idx]), int(float(parts[idx + 1])) if parts[idx + 1] else 0))

        # Metrics
        change = float(parts[31]) if len(parts) > 31 and parts[31] else (price - prev_close)
        change_pct = float(parts[32]) if len(parts) > 32 and parts[32] else ((price - prev_close) / prev_close * 100 if prev_close else 0.0)
        high = float(parts[33]) if len(parts) > 33 and parts[33] else max(price, open_p)
        low = float(parts[34]) if len(parts) > 34 and parts[34] else min(price, open_p)
        amount = float(parts[37]) if len(parts) > 37 and parts[37] else (price * volume / 10000)
        turnover_rate = float(parts[38]) if len(parts) > 38 and parts[38] else 0.0
        pe = float(parts[39]) if len(parts) > 39 and parts[39] else 0.0
        amplitude = float(parts[43]) if len(parts) > 43 and parts[43] else (((high - low) / prev_close * 100) if prev_close else 0.0)
        pb = float(parts[46]) if len(parts) > 46 and parts[46] else 0.0

        return {
            "symbol": orig_sym,
            "name": name,
            "price": price,
            "prev_close": prev_close,
            "open": open_p,
            "high": high,
            "low": low,
            "change": change,
            "change_pct": change_pct,
            "volume": volume,
            "amount": amount,
            "turnover_rate": turnover_rate,
            "pe": pe,
            "pb": pb,
            "amplitude": amplitude,
            "bids": bids,
            "asks": asks,
            "is_real": True,
        }
    except Exception:
        return None


def fetch_live_quotes(symbols: List[str], timeout: float = 2.0) -> Dict[str, Dict[str, Any]]:
    """Fetch live market quotes from Tencent Finance API."""
    if not symbols:
        return {}
    code_map = {normalize_symbol_code(s): s for s in symbols}
    q_str = ",".join(code_map.keys())
    url = f"http://qt.gtimg.cn/q={q_str}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (term-stock-table/0.1.0)"})

    results: Dict[str, Dict[str, Any]] = {}
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content = resp.read().decode("gbk", errors="ignore")
            for line in content.split(";"):
                parsed = parse_tencent_line(line, code_map)
                if parsed:
                    results[parsed["symbol"]] = parsed
    except Exception:
        pass
    return results


def fetch_intraday_series(symbol: str, timeout: float = 4.0) -> List[Tuple[float, int]]:
    """Fetch today's 1-minute (price, per-minute volume) series from Tencent; [] if unavailable."""
    code = normalize_symbol_code(symbol)
    url = f"https://web.ifzq.gtimg.cn/appstock/app/minute/query?code={code}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (term-stock-table)"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8", errors="ignore"))
        rows = next(iter(payload["data"].values()))["data"]["data"]
    except Exception:
        return []
    series: List[Tuple[float, int]] = []
    prev_cum = 0
    for row in rows:
        parts = row.split()
        if len(parts) < 3:
            continue
        try:
            price, cum = float(parts[1]), int(float(parts[2]))
        except ValueError:
            continue
        series.append((price, max(0, cum - prev_cum)))
        prev_cum = cum
    return series


class StockDataTracker:
    """Tracks historical series, intraday ticks, indicators, and live quotes."""

    def __init__(self, symbol: str, history_len: int = 200):
        self.symbol = symbol.strip().upper()
        self.history_len = history_len
        self.prices: deque = deque(maxlen=history_len)
        self.volumes: deque = deque(maxlen=history_len)
        self.highs: deque = deque(maxlen=history_len)
        self.lows: deque = deque(maxlen=history_len)

        # Seed initial data
        preset = DEFAULT_PRESET_SYMBOLS.get(self.symbol, {
            "name": self.symbol,
            "price": 100.0,
            "prev_close": 100.0,
            "open": 99.5,
            "high": 102.0,
            "low": 98.5,
            "volume": 20000,
            "amount": 2000.0,
            "turnover_rate": 0.5,
            "pe": 15.0,
            "pb": 1.5,
            "amplitude": 3.5,
        })

        self.name = preset["name"]
        self.price = preset["price"]
        self.prev_close = preset["prev_close"]
        self.open = preset["open"]
        self.high = preset["high"]
        self.low = preset["low"]
        self.volume = preset["volume"]
        self.amount = preset["amount"]
        self.turnover_rate = preset["turnover_rate"]
        self.pe = preset["pe"]
        self.pb = preset["pb"]
        self.amplitude = preset["amplitude"]
        self.bids: List[Tuple[float, int]] = []
        self.asks: List[Tuple[float, int]] = []
        self.is_real = False

        # Seed rolling history as a minute-like random walk that ends at the quoted price
        end_price, walk, p = self.price, [], self.price
        for _ in range(history_len):
            p = max(0.01, p + (random.random() - 0.5) * (p * 0.0015))
            walk.append(p)
        shift = end_price - walk[-1]
        v = max(100, int(self.volume / max(1, history_len)))
        for p in walk:
            p = max(0.01, p + shift)
            v = max(100, int(v * (1.0 + (random.random() - 0.5) * 0.3)))
            self.prices.append(p)
            self.volumes.append(v)
            self.highs.append(p * 1.0005)
            self.lows.append(p * 0.9995)
        self.price = self.prices[-1]
        self.minute_mode = False
        self._backfill_started = False
        self._bucket = 0
        self._cum_volume = 0

    def _backfill_intraday(self) -> None:
        series = fetch_intraday_series(self.symbol)
        if len(series) < 2:
            return
        series = series[-self.history_len:]
        self.prices.clear()
        self.volumes.clear()
        self.highs.clear()
        self.lows.clear()
        for price, vol in series:
            self.prices.append(price)
            self.volumes.append(vol)
            self.highs.append(price)
            self.lows.append(price)
        self._bucket = int(time.time() // 60)
        self._cum_volume = self.volume
        self.minute_mode = True

    def update_from_quote(self, quote: Dict[str, Any]):
        """Update tracker state with real live market quote."""
        self.name = quote.get("name", self.name)
        self.price = quote.get("price", self.price)
        self.prev_close = quote.get("prev_close", self.prev_close)
        self.open = quote.get("open", self.open)
        self.high = quote.get("high", self.high)
        self.low = quote.get("low", self.low)
        self.volume = quote.get("volume", self.volume)
        self.amount = quote.get("amount", self.amount)
        self.turnover_rate = quote.get("turnover_rate", self.turnover_rate)
        self.pe = quote.get("pe", self.pe)
        self.pb = quote.get("pb", self.pb)
        self.amplitude = quote.get("amplitude", self.amplitude)
        if quote.get("bids"):
            self.bids = quote["bids"]
        if quote.get("asks"):
            self.asks = quote["asks"]
        first_quote = not self.is_real
        self.is_real = True

        if first_quote and not self._backfill_started:
            self._backfill_started = True
            threading.Thread(target=self._backfill_intraday, daemon=True).start()

        if self.minute_mode:
            bucket = int(time.time() // 60)
            if bucket != self._bucket:
                self._bucket = bucket
                self.prices.append(self.price)
                self.volumes.append(max(0, self.volume - self._cum_volume))
                self.highs.append(self.price)
                self.lows.append(self.price)
                self._cum_volume = self.volume
            elif self.prices:
                self.prices[-1] = self.price
                self.highs[-1] = max(self.highs[-1], self.price)
                self.lows[-1] = min(self.lows[-1], self.price)
            return

        self.prices.append(self.price)
        self.volumes.append(self.volume)
        self.highs.append(self.high)
        self.lows.append(self.low)

    def tick_simulation(self):
        """Simulate realistic tick movement when offline."""
        delta = (random.random() - 0.48) * (self.price * 0.004)
        self.price = max(0.01, self.price + delta)
        self.high = max(self.high, self.price)
        self.low = min(self.low, self.price)
        self.volume = max(100, int(self.volume + random.randint(10, 500)))
        self.amount = round(self.amount + self.price * 0.05, 2)
        self.prices.append(self.price)
        self.volumes.append(self.volume)

        # Generate realistic 5-level order book
        spread = max(0.01, round(self.price * 0.001, 2))
        self.bids = [
            (round(self.price - (i * spread), 2), random.randint(50, 2000))
            for i in range(1, 6)
        ]
        self.asks = [
            (round(self.price + (i * spread), 2), random.randint(50, 2000))
            for i in range(1, 6)
        ]

    @property
    def change(self) -> float:
        return self.price - self.prev_close

    @property
    def change_pct(self) -> float:
        return (self.change / self.prev_close * 100.0) if self.prev_close else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert tracker status to dictionary representation."""
        return {
            "symbol": self.symbol,
            "name": self.name,
            "price": self.price,
            "prev_close": self.prev_close,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "change": self.change,
            "change_pct": self.change_pct,
            "volume": self.volume,
            "amount": self.amount,
            "turnover_rate": self.turnover_rate,
            "pe": self.pe,
            "pb": self.pb,
            "amplitude": self.amplitude,
            "bids": list(self.bids),
            "asks": list(self.asks),
            "is_real": self.is_real,
        }
