"""Interactive Textual TUI Application for real-time stock monitoring."""
import asyncio
import sys
from typing import List, Optional, Dict, Any
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Header, Footer, Static, Input, Button, Label, DataTable
from textual.screen import ModalScreen, Screen
from textual.binding import Binding
from textual import work

from .api import StockDataTracker, fetch_live_quotes, fetch_kline
from .config import (
    load_watchlist,
    save_watchlist,
    add_to_watchlist,
    remove_from_watchlist,
    save_note,
    get_symbol_notes,
    load_settings,
    save_settings,
    load_portfolio,
    load_alerts,
    save_alert,
)
from .table import create_stock_table
from .detail import render_stock_detail, period_label, candles_from_prices
from .inline_spark import (
    set_image_enabled,
    terminal_supports_images,
    overlay_begin,
    overlay_end,
    overlay_blank,
    OVERLAY_BLANK_WIDTH,
    _image,
)
from rich.cells import cell_len
from .boss import render_boss_view, PROFILES
from .portfolio import calculate_portfolio_pnl, create_portfolio_table
from .alerts import evaluate_alerts
from .market import render_indices_banner
from .radar import MarketRadarTracker
from .sector import SectorHeatmapTracker
from .backtest import StrategyBacktester
from .themes import ThemeManager, THEMES
from .formula import FormulaManager, CustomFormula


class AlertModal(ModalScreen[None]):
    """Modal dialog for configuring price and volatility alerts."""

    def __init__(self, symbol: str, name: str):
        super().__init__()
        self.symbol = symbol
        self.stock_name = name

    def compose(self) -> ComposeResult:
        with Vertical(id="alert-dialog"):
            yield Label(f"🔔 Set Price Alert for {self.stock_name} ({self.symbol})", id="alert-title")
            yield Input(placeholder="Target High Price (e.g. 1800.0)", id="high-input")
            yield Input(placeholder="Stop Low Price (e.g. 1200.0)", id="low-input")
            yield Input(placeholder="Max Volatility % (e.g. 3.0)", id="pct-input")
            with Horizontal(id="alert-buttons"):
                yield Button("Save Alert (Enter)", variant="primary", id="save-alert-btn")
                yield Button("Cancel (Esc)", variant="default", id="cancel-alert-btn")

    def on_mount(self) -> None:
        self.query_one("#high-input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-alert-btn":
            h_text = self.query_one("#high-input", Input).value.strip()
            l_text = self.query_one("#low-input", Input).value.strip()
            p_text = self.query_one("#pct-input", Input).value.strip()
            
            high_val = float(h_text) if h_text else None
            low_val = float(l_text) if l_text else None
            pct_val = float(p_text) if p_text else None
            
            save_alert(self.symbol, target_high=high_val, target_low=low_val, max_change_pct=pct_val)
            self.app.notify(f"Alert configured for {self.symbol}!")
            self.dismiss()
        else:
            self.dismiss()


class NoteModal(ModalScreen[None]):
    """Modal dialog for writing investment notes."""

    def __init__(self, symbol: str, name: str):
        super().__init__()
        self.symbol = symbol
        self.stock_name = name

    def compose(self) -> ComposeResult:
        with Vertical(id="note-dialog"):
            yield Label(f"📝 Add Investment Note for {self.stock_name} ({self.symbol})", id="note-title")
            yield Input(placeholder="e.g. Target price 1800, stop loss 1250, wait for Q3 earnings...", id="note-input")
            with Horizontal(id="note-buttons"):
                yield Button("Save (Enter)", variant="primary", id="save-btn")
                yield Button("Cancel (Esc)", variant="default", id="cancel-btn")

    def on_mount(self) -> None:
        self.query_one(Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        if text:
            save_note(self.symbol, text, tags=["manual", "trade"])
            self.app.notify(f"Note saved for {self.symbol}!")
        self.dismiss()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-btn":
            inp = self.query_one(Input)
            if inp.value.strip():
                save_note(self.symbol, inp.value.strip(), tags=["manual", "trade"])
                self.app.notify(f"Note saved for {self.symbol}!")
            self.dismiss()
        else:
            self.dismiss()


class AddStockModal(ModalScreen[None]):
    """Modal dialog for adding new stock to watchlist."""

    def compose(self) -> ComposeResult:
        with Vertical(id="add-dialog"):
            yield Label("🔍 Add Stock Symbol (e.g. 600519, 000001, AAPL, NVDA, 00700):", id="add-title")
            yield Input(placeholder="Enter stock code...", id="add-input")
            with Horizontal(id="add-buttons"):
                yield Button("Add (Enter)", variant="primary", id="add-btn")
                yield Button("Cancel (Esc)", variant="default", id="cancel-btn")

    def on_mount(self) -> None:
        self.query_one(Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        sym = event.value.strip().upper()
        if sym:
            if add_to_watchlist(sym):
                self.app.notify(f"Added {sym} to watchlist!")
            else:
                self.app.notify(f"{sym} already in watchlist.", severity="warning")
            self.app.refresh_trackers_from_disk()
        self.dismiss()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "add-btn":
            inp = self.query_one(Input)
            sym = inp.value.strip().upper()
            if sym:
                add_to_watchlist(sym)
                self.app.refresh_trackers_from_disk()
            self.dismiss()
        else:
            self.dismiss()


class RadarModal(ModalScreen[None]):
    """Modal screen for market sentiment and anomaly radar."""

    def __init__(self, palette: str = "cn"):
        super().__init__()
        self.palette = palette

    def compose(self) -> ComposeResult:
        radar = MarketRadarTracker(palette=self.palette)
        with Vertical(id="detail-container"):
            yield Static(radar.render_full_radar_view(), id="detail-view")
            with Horizontal(id="detail-footer"):
                yield Button("Close (Esc)", id="close-radar-btn", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss()

    def key_escape(self) -> None:
        self.dismiss()


class SectorModal(ModalScreen[None]):
    """Modal screen for sector heatmap and rankings."""

    def __init__(self, palette: str = "cn"):
        super().__init__()
        self.palette = palette

    def compose(self) -> ComposeResult:
        sec = SectorHeatmapTracker(palette=self.palette)
        with Vertical(id="detail-container"):
            yield Static(sec.render_full_sector_view(), id="detail-view")
            with Horizontal(id="detail-footer"):
                yield Button("Close (Esc)", id="close-sector-btn", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss()

    def key_escape(self) -> None:
        self.dismiss()


class BacktestModal(ModalScreen[None]):
    """Modal screen for strategy backtesting."""

    def __init__(self, tracker: StockDataTracker, palette: str = "cn"):
        super().__init__()
        self.tracker = tracker
        self.palette = palette

    def compose(self) -> ComposeResult:
        bt = StrategyBacktester(self.tracker.symbol, self.tracker.name, palette=self.palette)
        with Vertical(id="detail-container"):
            yield Static(bt.render_backtest_panel(), id="detail-view")
            with Horizontal(id="detail-footer"):
                yield Button("Close (Esc)", id="close-bt-btn", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss()

    def key_escape(self) -> None:
        self.dismiss()


class ThemeModal(ModalScreen[None]):
    """Modal screen for selecting theme presets."""

    def compose(self) -> ComposeResult:
        with Vertical(id="alert-dialog"):
            yield Label("🎨 Choose Color Theme Preset:", id="alert-title")
            for key, th in THEMES.items():
                yield Button(f"{key.upper()} - {th.description}", id=f"theme-{key}", variant="default")
            yield Button("Close (Esc)", id="close-theme-btn", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id and event.button.id.startswith("theme-"):
            theme_key = event.button.id.replace("theme-", "")
            self.app.theme_manager.set_theme(theme_key)
            self.app.notify(f"Theme switched to: {theme_key.upper()}")
            self.app.update_view()
            self.dismiss()
        else:
            self.dismiss()

    def key_escape(self) -> None:
        self.dismiss()


class FormulaModal(ModalScreen[None]):
    """Modal screen for custom indicator formulas."""

    def compose(self) -> ComposeResult:
        formulas = FormulaManager.load_formulas()
        with Vertical(id="alert-dialog"):
            yield Label("📐 Custom Quantitative Formulas:", id="alert-title")
            for name, f in formulas.items():
                yield Label(f"• [bold cyan]{name}:[/] [yellow]{f.expression}[/] - [dim]{f.description}[/]")
            yield Button("Close (Esc)", id="close-formula-btn", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss()

    def key_escape(self) -> None:
        self.dismiss()


class DetailModal(ModalScreen[None]):
    """Modal screen for comprehensive stock detail view with switchable chart periods."""

    PERIODS = ["intraday", "m5", "m15", "m30", "m60", "day", "week", "month"]

    def __init__(self, tracker: StockDataTracker, palette: str = "cn"):
        super().__init__()
        self.tracker = tracker
        self.palette = palette
        self.period = "intraday"
        self.kline_cache: Dict[str, List[Dict[str, Any]]] = {}
        self.kline_note: Dict[str, str] = {}

    def compose(self) -> ComposeResult:
        with Vertical(id="detail-container"):
            yield Static(id="detail-view")
            with Horizontal(id="detail-periods"):
                for i, p in enumerate(self.PERIODS, 1):
                    yield Button(f"{period_label(p)} ({i})", id=f"period-{p}", variant="default")
            with Horizontal(id="detail-footer"):
                yield Button("Add Note ('n')", id="detail-note-btn", variant="primary")
                yield Button("Close (Esc/Enter)", id="detail-close-btn", variant="default")

    def on_mount(self) -> None:
        self.update_content()

    def update_content(self) -> None:
        notes = get_symbol_notes(self.tracker.symbol)
        layout = render_stock_detail(
            self.tracker,
            palette=self.palette,
            notes=notes,
            period=self.period,
            candles=self.kline_cache.get(self.period),
            period_note=self.kline_note.get(self.period, ""),
        )
        self.query_one("#detail-view", Static).update(layout)
        for p in self.PERIODS:
            self.query_one(f"#period-{p}", Button).variant = "warning" if p == self.period else "default"

    def set_period(self, period: str) -> None:
        self.period = period
        if period != "intraday" and period not in self.kline_cache:
            self.kline_note[period] = "Loading K-line data..."
            self.run_worker(lambda: self.load_kline(period), thread=True, exclusive=True, group="kline")
        self.update_content()

    def load_kline(self, period: str) -> None:
        candles: List[Dict[str, Any]] = []
        note = ""
        if getattr(self.app, "use_real_data", False):
            candles = fetch_kline(self.tracker.symbol, period)
        if not candles:
            candles = candles_from_prices(list(self.tracker.prices))
            note = "Simulated candles (real K-line data unavailable for this period/market)"
        self.kline_cache[period] = candles
        self.kline_note[period] = note
        self.app.call_from_thread(self.update_content)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        if bid.startswith("period-"):
            self.set_period(bid[len("period-"):])
        elif bid == "detail-note-btn":
            self.app.push_screen(NoteModal(self.tracker.symbol, self.tracker.name))
        else:
            self.dismiss()

    def on_key(self, event) -> None:
        if event.key in {str(i) for i in range(1, len(self.PERIODS) + 1)}:
            self.set_period(self.PERIODS[int(event.key) - 1])
            event.stop()

    def key_escape(self) -> None:
        self.dismiss()

    def key_enter(self) -> None:
        self.dismiss()

    def key_n(self) -> None:
        self.app.push_screen(NoteModal(self.tracker.symbol, self.tracker.name))

    def key_k(self) -> None:
        nxt = (self.PERIODS.index(self.period) + 1) % len(self.PERIODS)
        self.set_period(self.PERIODS[nxt])


class StockTerminalApp(App):
    """Main Textual TUI Application for term-stock-table."""

    CSS = """
    Screen {
        background: #0f1117;
    }
    #main-table-view {
        width: 100%;
        height: 100%;
        padding: 0 1;
    }
    #note-dialog, #add-dialog, #alert-dialog {
        padding: 1 2;
        background: #1a202c;
        border: solid $primary;
        width: 60;
        height: auto;
        align: center middle;
    }
    #detail-container {
        width: 95%;
        height: 95%;
        background: #0f1117;
        border: solid $accent;
        padding: 1;
        align: center middle;
    }
    #detail-view {
        width: 100%;
        height: 1fr;
    }
    #detail-periods {
        height: 3;
        align: center middle;
    }
    #detail-footer {
        height: 3;
        align: right middle;
    }
    #note-buttons, #add-buttons, #alert-buttons {
        margin-top: 1;
        align: right middle;
    }
    Button {
        margin-left: 1;
    }
    """

    BINDINGS = [
        Binding("b", "toggle_boss", "Boss Key (摸鱼模式)", priority=True),
        Binding("escape", "handle_escape", "Escape", priority=True),
        Binding("tab", "cycle_boss_profile", "Next Boss Disguise"),
        Binding("enter", "show_detail", "Stock Detail"),
        Binding("j", "cursor_down", "Next Row (Vim)", show=False),
        Binding("k", "cursor_up", "Prev Row (Vim)", show=False),
        Binding("down", "cursor_down", "Down", show=False),
        Binding("up", "cursor_up", "Up", show=False),
        Binding("g", "cursor_top", "Top", show=False),
        Binding("G", "cursor_bottom", "Bottom", show=False),
        Binding("n", "add_note", "Add Note"),
        Binding("l", "set_alert", "Price Alert"),
        Binding("a", "add_stock", "Add Stock"),
        Binding("slash", "add_stock", "Search/Add"),
        Binding("d", "delete_stock", "Delete Stock"),
        Binding("s", "cycle_sort", "Sort Column"),
        Binding("r", "reverse_sort", "Reverse Sort"),
        Binding("T", "show_themes", "Theme Presets"),
        Binding("F", "show_formulas", "Custom Formulas"),
        Binding("R", "show_radar", "Market Radar"),
        Binding("S", "show_sector", "Sector Heatmap"),
        Binding("B", "show_backtest", "Strategy Backtest"),
        Binding("P", "toggle_portfolio", "Portfolio View"),
        Binding("p", "toggle_palette", "CN/US Palette"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(
        self,
        symbols: Optional[List[str]] = None,
        palette: str = "cn",
        theme: str = "classic_cn",
        use_real_data: bool = True,
        refresh_interval: float = 1.0,
    ):
        super().__init__()
        set_image_enabled(False)
        self.overlay_enabled = sys.stdout.isatty() and terminal_supports_images()
        self.overlay_items: list = []
        self.symbols_list = symbols or load_watchlist()
        self.palette = palette
        self.theme_manager = ThemeManager(theme or palette)
        self.use_real_data = use_real_data
        self.refresh_interval = refresh_interval
        self.trackers: List[StockDataTracker] = [
            StockDataTracker(sym) for sym in self.symbols_list
        ]
        self.selected_index: int = 0
        self.is_boss_mode: bool = False
        self.is_portfolio_mode: bool = False
        self.boss_profile_idx: int = 0
        self.sort_columns = [None, "change_pct", "price", "volume", "amount", "amplitude", "pe"]
        self.sort_col_idx: int = 0
        self.sort_descending: bool = True
        self.is_live: bool = False
        self.alerts_triggered: Dict[str, List[str]] = {}

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static(id="main-table-view")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "term-stock-table (Professional Financial Workstation)"
        self.update_view()
        self.set_interval(self.refresh_interval, self.refresh_market_data)
        if self.overlay_enabled:
            self.install_overlay_hook()

    def install_overlay_hook(self) -> None:
        """Append smooth term-sparkline images to every frame so they never get erased."""
        driver = self._driver
        orig_write = driver.write

        def write(data: str) -> None:
            orig_write(data + (self.overlay_payload() if len(data) > 40 else ""))

        driver.write = write

    def overlay_payload(self) -> str:
        if not self.overlay_items or len(self.screen_stack) > 1:
            return ""
        try:
            strips = self.screen._compositor.render_strips()
        except Exception:
            return ""
        blank = overlay_blank(OVERLAY_BLANK_WIDTH)
        out = ["\x1b7"]
        idx = 0
        for y, strip in enumerate(strips):
            text = strip.text
            x = text.find(blank)
            if x < 0 or idx >= len(self.overlay_items):
                continue
            data, length, palette = self.overlay_items[idx]
            idx += 1
            img = _image(tuple(data), length, palette, (("fill", False), ("show_dot", False)))
            out.append(f"\x1b[{y + 1};{cell_len(text[:x]) + 1}H{img}")
        out.append("\x1b8")
        return "".join(out) if idx else ""

    def refresh_trackers_from_disk(self) -> None:
        """Reload watchlist from disk."""
        self.symbols_list = load_watchlist()
        existing = {tr.symbol: tr for tr in self.trackers}
        new_trackers = []
        for s in self.symbols_list:
            s_clean = s.strip().upper()
            if s_clean in existing:
                new_trackers.append(existing[s_clean])
            else:
                new_trackers.append(StockDataTracker(s_clean))
        self.trackers = new_trackers
        self.update_view()

    def refresh_market_data(self) -> None:
        """Fetch quotes or step simulation and redraw table."""
        if not self.trackers:
            return

        if self.use_real_data:
            symbols = [tr.symbol for tr in self.trackers]
            quotes = fetch_live_quotes(symbols, timeout=1.5)
            if quotes:
                self.is_live = True
                for tr in self.trackers:
                    if tr.symbol in quotes:
                        tr.update_from_quote(quotes[tr.symbol])
                    else:
                        tr.tick_simulation()
            else:
                self.is_live = False
                for tr in self.trackers:
                    tr.tick_simulation()
        else:
            self.is_live = False
            for tr in self.trackers:
                tr.tick_simulation()

        # Check alerts
        quotes_dict_list = [tr.to_dict() for tr in self.trackers]
        self.alerts_triggered = evaluate_alerts(quotes_dict_list, trigger_notification=True)

        self.update_view()

    def update_view(self) -> None:
        """Render main stock table, Portfolio view, or Boss mode camouflage."""
        try:
            view_widget = self.query_one("#main-table-view", Static)
        except Exception:
            return

        self.overlay_items = []
        if self.is_boss_mode:
            prof = PROFILES[self.boss_profile_idx % len(PROFILES)]
            renderable = render_boss_view(prof, trackers=self.trackers)
            view_widget.update(renderable)
        elif self.is_portfolio_mode:
            port = load_portfolio()
            p_data = calculate_portfolio_pnl([tr.to_dict() for tr in self.trackers], port)
            tbl = create_portfolio_table(p_data, palette=self.palette)
            view_widget.update(tbl)
        else:
            sort_col = self.sort_columns[self.sort_col_idx]
            queue = overlay_begin() if self.overlay_enabled else None
            tbl = create_stock_table(
                self.trackers,
                palette=self.palette,
                monochrome=False,
                is_live=self.is_live,
                sort_by=sort_col,
                reverse=self.sort_descending,
                alerts_triggered=self.alerts_triggered,
            )
            overlay_end()
            self.overlay_items = queue or []
            view_widget.update(tbl)

    def action_toggle_boss(self) -> None:
        """Instantly toggle Boss Mode disguise."""
        self.is_boss_mode = not self.is_boss_mode
        self.update_view()

    def action_handle_escape(self) -> None:
        """Escape toggles boss mode or closes active modal."""
        if self.screen_stack and len(self.screen_stack) > 1:
            self.pop_screen()
        else:
            self.action_toggle_boss()

    def action_cycle_boss_profile(self) -> None:
        """Cycle through Boss mode profiles."""
        if self.is_boss_mode:
            self.boss_profile_idx = (self.boss_profile_idx + 1) % len(PROFILES)
            self.update_view()

    def action_toggle_portfolio(self) -> None:
        """Toggle between Watchlist and Portfolio asset view."""
        self.is_portfolio_mode = not self.is_portfolio_mode
        self.notify(f"Mode: {'Portfolio Holdings' if self.is_portfolio_mode else 'Watchlist'}")
        self.update_view()

    def action_cycle_sort(self) -> None:
        """Cycle sorting column."""
        self.sort_col_idx = (self.sort_col_idx + 1) % len(self.sort_columns)
        curr = self.sort_columns[self.sort_col_idx] or "Default"
        self.notify(f"Sorted by: {curr.upper()}")
        self.update_view()

    def action_reverse_sort(self) -> None:
        """Reverse sorting order."""
        self.sort_descending = not self.sort_descending
        self.notify(f"Order: {'Descending (▼)' if self.sort_descending else 'Ascending (▲)'}")
        self.update_view()

    def action_show_detail(self) -> None:
        """Show detail view for highlighted stock."""
        if self.trackers:
            tr = self.trackers[self.selected_index % len(self.trackers)]
            self.push_screen(DetailModal(tr, palette=self.palette))

    def action_add_note(self) -> None:
        """Open note editor for current stock."""
        if self.trackers:
            tr = self.trackers[self.selected_index % len(self.trackers)]
            self.push_screen(NoteModal(tr.symbol, tr.name))

    def action_set_alert(self) -> None:
        """Open alert configuration modal."""
        if self.trackers:
            tr = self.trackers[self.selected_index % len(self.trackers)]
            self.push_screen(AlertModal(tr.symbol, tr.name))

    def action_add_stock(self) -> None:
        """Open add stock modal."""
        self.push_screen(AddStockModal())

    def action_delete_stock(self) -> None:
        """Delete currently selected stock."""
        if self.trackers:
            tr = self.trackers[self.selected_index % len(self.trackers)]
            remove_from_watchlist(tr.symbol)
            self.notify(f"Removed {tr.symbol} from watchlist.")
            self.refresh_trackers_from_disk()

    def action_cursor_down(self) -> None:
        """Vim 'j' / Down: Move highlighted stock selection down."""
        if self.trackers:
            self.selected_index = (self.selected_index + 1) % len(self.trackers)
            tr = self.trackers[self.selected_index]
            self.notify(f"Selected: {tr.name} ({tr.symbol})")

    def action_cursor_up(self) -> None:
        """Vim 'k' / Up: Move highlighted stock selection up."""
        if self.trackers:
            self.selected_index = (self.selected_index - 1) % len(self.trackers)
            tr = self.trackers[self.selected_index]
            self.notify(f"Selected: {tr.name} ({tr.symbol})")

    def action_cursor_top(self) -> None:
        """Vim 'g' / Home: Jump to first stock."""
        if self.trackers:
            self.selected_index = 0
            tr = self.trackers[0]
            self.notify(f"Selected (Top): {tr.name} ({tr.symbol})")

    def action_cursor_bottom(self) -> None:
        """Vim 'G' / End: Jump to last stock."""
        if self.trackers:
            self.selected_index = len(self.trackers) - 1
            tr = self.trackers[-1]
            self.notify(f"Selected (Bottom): {tr.name} ({tr.symbol})")

    def action_show_themes(self) -> None:
        """Open theme preset switcher modal."""
        self.push_screen(ThemeModal())

    def action_show_formulas(self) -> None:
        """Open custom formulas modal."""
        self.push_screen(FormulaModal())

    def action_show_radar(self) -> None:
        """Open market sentiment and anomaly radar modal."""
        self.push_screen(RadarModal(palette=self.palette))

    def action_show_sector(self) -> None:
        """Open sector heatmap and rankings modal."""
        self.push_screen(SectorModal(palette=self.palette))

    def action_show_backtest(self) -> None:
        """Open strategy backtest modal for current stock."""
        if self.trackers:
            tr = self.trackers[self.selected_index % len(self.trackers)]
            self.push_screen(BacktestModal(tr, palette=self.palette))

    def action_toggle_palette(self) -> None:
        """Toggle between CN (Red Up) and US (Green Up) color palettes."""
        self.palette = "us" if self.palette == "cn" else "cn"
        self.notify(f"Switched palette to: {self.palette.upper()}")
        self.update_view()
