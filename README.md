# term-stock-table 📊

> Professional terminal financial workstation: real-time stock watchlist, Bollinger Bands & quant indicators, stock detail views, persistent trade notes, and stealth Boss Mode.

Built on top of [`term-sparkline`](https://github.com/brwchen/term-sparkline) for high-density inline vector sparklines and tick badges.

<p align="center">
  <img src="assets/demo.gif" alt="term-stock-table Real-Time Terminal Demo" width="720"/>
</p>

---

## ✨ Features

- **Professional Financial Columns & Real-time Feeds**:
  - Live quote integration via high-speed API (A-Shares, HK, US stocks) with seamless offline simulation fallback.
  - Multi-market unified tickers: `600519` (Moutai), `000001` (Ping An), `300750` (CATL), `00700` (Tencent), `AAPL`, `NVDA`.
  - Comprehensive metrics: `Price`, `Change%`, `Change`, `Amplitude%`, `Turnover%`, `Volume`, `Turnover Amount`, `P/E`, `P/B`.
- **Bollinger Bands & Quant Indicators**:
  - Compact Bollinger Bands %b position badge: `[··●··]` (Mid), `[····▶]` (Overbought), `[◀····]` (Oversold).
  - Built-in Moving Averages (MA5, MA10, MA20), RSI(14), and Price-Volume dual-axis curves.
  - Inline high-definition Sparkline curves with end-point dots and price change badges.
- **Stock Detail View & 5-Level Order Book (五档盘口)**:
  - Deep-dive view with intraday tick curves, technical analysis, and real-time Bid/Ask five-tier order depth.
- **Persistent Investment Journal & Strategy Notes**:
  - Record target prices, stop-loss levels, and trade rationales directly from terminal (stored locally in `~/.term_stock/notes.json`).
- **Stealth Boss Mode (摸鱼神器 / Boss Key)**:
  - Press `b` or `ESC` to instantly camouflage into real-time system monitoring or backend logs:
    - **DevOps Profile**: Linux `top` / `htop` dynamic process table.
    - **Kubernetes Profile**: `kubectl get pods -A` cluster status.
    - **Nginx Profile**: `tail -f /var/log/nginx/access.log` HTTP stream.
    - **Monochrome Profile**: Grayscale neutral sensor telemetry table without market colors.
- **Dual Runtime Architecture**:
  - **Interactive TUI** (`stk`): Full-featured Textual terminal dashboard with keyboard shortcuts.
  - **CLI Pipeline** (`stk --print` / `stk --watch`): Snapshot Rich tables for scripts, cron jobs, and tmux status bars.

---

## 📦 Installation

```bash
pip install term-stock-table
```

*(Includes `term-sparkline`, `rich`, and `textual` out of the box).*

---

## 🚀 Quick Start

### 1. Launch Interactive Financial Terminal (TUI)

```bash
# Launch default watchlist dashboard
stk

# Or track specific symbols
stk --symbols 600519,000001,300750,AAPL,NVDA,00700
```

### 2. Print Snapshot Table (CLI Mode)

```bash
# Fast print to terminal (ideal for tmux / i3 status)
stk --print

# US Market Green-Up/Red-Down Palette
stk --print --palette us
```

### 3. Quick Detail View & Investment Notes

```bash
# Open single stock detail view
stk --detail 600519

# Add an investment note from CLI
stk --note 600519 "Target price 1800, stop loss 1250, wait for Q3 earnings"

# View all saved investment notes
stk --notes
```

### 4. Direct Boss Mode Launch

```bash
# Start directly in stealth camouflage mode
stk --boss --boss-profile kubectl
```

---

## ⌨️ Interactive TUI Keybindings

| Key | Action | Description |
|:---:|:---|:---|
| <kbd>b</kbd> / <kbd>ESC</kbd> | **Boss Key (摸鱼模式)** | Instantly toggles camouflage profile (top, kubectl, nginx, mono) |
| <kbd>Tab</kbd> | **Next Boss Profile** | Cycles camouflage disguise (DevOps → Kubernetes → Nginx → Monochrome) |
| <kbd>Enter</kbd> | **Stock Detail View** | Opens deep detail page (OHLC, Indicators, 5-Level Order Book, Notes) |
| <kbd>n</kbd> | **Add Note** | Opens note editor modal for the current stock |
| <kbd>a</kbd> / <kbd>/</kbd> | **Add Stock** | Search and add stock symbol to persistent watchlist |
| <kbd>d</kbd> | **Delete Stock** | Remove highlighted stock from watchlist |
| <kbd>p</kbd> | **Toggle Palette** | Switch between CN (Red ▲) and US (Green ▲) palettes |
| <kbd>q</kbd> | **Quit** | Exit application |

---

## 🎨 Visual Showcase & Feature Matrix

### 1. Watchlist Overview & Live Streaming
> High-density real-time financial monitoring with automatic CN/US market color schemes, volume formatting, and inline Sparklines.
<p align="center">
  <img src="assets/features/watchlist_overview.gif" alt="Watchlist Overview" width="680"/>
</p>

---

### 2. Bollinger Bands Position Matrix (%b)
> Intuitive `%b` position badges mapping whether prices are riding the upper band, oscillating in the middle, or oversold below the lower band.
<p align="center">
  <img src="assets/features/bollinger_and_indicators.gif" alt="Bollinger Bands Indicators" width="680"/>
</p>

---

### 3. Stock Detail View & 5-Level Order Book
> Multi-panel stock analysis workstation with intraday Price+Volume combo curves, MA/RSI indicators, and real-time Bid/Ask depth.
<p align="center">
  <img src="assets/features/stock_detail_view.gif" alt="Stock Detail View" width="680"/>
</p>

---

### 4. Persistent Investment Notes & Trade Journal
> Built-in trade notebook for tracking catalysts, entry/exit criteria, and thesis validation without leaving the terminal.
<p align="center">
  <img src="assets/features/investment_notes.gif" alt="Investment Notes" width="680"/>
</p>

---

### 5. Stealth Boss Mode (One-Key Camouflage)
> Millisecond-level one-key disguise into Linux `top`, `kubectl get pods`, or `nginx access.log` streams.
<p align="center">
  <img src="assets/features/boss_mode_stealth.gif" alt="Boss Mode Stealth" width="680"/>
</p>

---

### 6. Watchlist Search & CLI Management
> Fast CLI commands for managing persistent stock watchlists (`stk --add`, `stk --remove`, `stk --list`).
<p align="center">
  <img src="assets/features/watchlist_management.gif" alt="Watchlist Management" width="680"/>
</p>

---

## 🗺️ Architecture & Component Map

| Module / Component | File | Description |
|:---|:---|:---|
| `api.py` | Core Data | Real-time quote fetcher (Tencent API) & offline Geometric Random Walk simulator |
| `indicators.py` | Analytics | Bollinger Bands (%b, bandwidth), SMA (5/10/20), RSI(14), and badge renderers |
| `config.py` | Storage | Persistent Watchlist, Notes, and Settings in `~/.term_stock/` |
| `table.py` | UI Engine | Professional Rich Table generator with customizable columns & sparklines |
| `detail.py` | Detail View | Multi-panel stock detail layout (Combo chart, 5-level order book, Notes panel) |
| `boss.py` | Privacy | Boss mode camouflage engines (`devops`, `kubectl`, `nginx`, `monochrome`) |
| `tui.py` | Interactive | Textual reactive application with modals, timers, and keybindings |
| `cli.py` | CLI Interface | Dual-mode CLI entrypoint (`stk` / `stock-table`) |

---

## 📄 License

MIT © [brwchen](https://github.com/brwchen)

