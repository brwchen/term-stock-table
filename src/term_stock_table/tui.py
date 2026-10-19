"""Interactive Textual TUI Application for real-time stock monitoring."""
import asyncio
from typing import List, Optional, Dict, Any
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Header, Footer, Static, Input, Button, Label, DataTable
from textual.screen import ModalScreen, Screen
from textual.binding import Binding
from textual import work

from .api import StockDataTracker, fetch_live_quotes
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
from .detail import render_stock_detail
from .boss import render_boss_view, PROFILES
from .portfolio import calculate_portfolio_pnl, create_portfolio_table
from .alerts import evaluate_alerts
from .market import render_indices_banner
from .radar import MarketRadarTracker
from .sector import SectorHeatmapTracker
from .backtest import StrategyBacktester


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


class DetailModal(ModalScreen[None]):
    """Modal screen for comprehensive stock detail view."""

    def __init__(self, tracker: StockDataTracker, palette: str = "cn"):
        super().__init__()
        self.tracker = tracker
        self.palette = palette
        self.show_candle = False

    def compose(self) -> ComposeResult:
        with Vertical(id="detail-container"):
            yield Static(id="detail-view")
            with Horizontal(id="detail-footer"):
                yield Button("K-Line / Sparkline ('k')", id="detail-candle-btn", variant="warning")
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
            show_candlestick=self.show_candle,
        )
        self.query_one("#detail-view", Static).update(layout)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "detail-note-btn":
            self.app.push_screen(NoteModal(self.tracker.symbol, self.tracker.name))
        elif event.button.id == "detail-candle-btn":
            self.show_candle = not self.show_candle
            self.update_content()
        else:
            self.dismiss()

    def key_escape(self) -> None:
        self.dismiss()

    def key_enter(self) -> None:
        self.dismiss()

    def key_n(self) -> None:
        self.app.push_screen(NoteModal(self.tracker.symbol, self.tracker.name))

    def key_k(self) -> None:
        self.show_candle = not self.show_candle
        self.update_content()


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
        Binding("n", "add_note", "Add Note"),
        Binding("l", "set_alert", "Price Alert"),
        Binding("a", "add_stock", "Add Stock"),
        Binding("slash", "add_stock", "Search/Add"),
        Binding("d", "delete_stock", "Delete Stock"),
        Binding("s", "cycle_sort", "Sort Column"),
        Binding("r", "reverse_sort", "Reverse Sort"),
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
        use_real_data: bool = True,
        refresh_interval: float = 1.0,
    ):
        super().__init__()
        self.symbols_list = symbols or load_watchlist()
        self.palette = palette
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
            tbl = create_stock_table(
                self.trackers,
                palette=self.palette,
                monochrome=False,
                is_live=self.is_live,
                sort_by=sort_col,
                reverse=self.sort_descending,
                alerts_triggered=self.alerts_triggered,
            )
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
