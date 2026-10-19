"""Interactive Textual TUI Application for real-time stock monitoring."""
import asyncio
import dataclasses
import sys
from typing import List, Optional, Dict, Any
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal, VerticalScroll, ScrollableContainer
from textual.geometry import Region
from textual.widgets import Header, Footer, Static, Input, Button, Label, DataTable
from textual.screen import ModalScreen, Screen
from textual.binding import Binding
from textual.scrollbar import ScrollBar, ScrollBarRender
from rich.segment import Segment, Segments
from rich.style import Style as RichStyle
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
from .table import create_stock_table, sort_trackers
from .i18n import t, set_lang, toggle_lang, get_lang
from .detail import render_detail_header, render_detail_body, period_label, candles_from_prices
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
            yield Label(t("alert_title", name=self.stock_name, symbol=self.symbol), id="alert-title")
            yield Input(placeholder=t("alert_high"), id="high-input")
            yield Input(placeholder=t("alert_low"), id="low-input")
            yield Input(placeholder=t("alert_pct"), id="pct-input")
            with Horizontal(id="alert-buttons"):
                yield Button(t("save_alert"), variant="primary", id="save-alert-btn")
                yield Button(t("cancel"), variant="default", id="cancel-alert-btn")

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
            self.app.notify(t("n_alert_set", symbol=self.symbol))
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
            yield Label(t("note_title", name=self.stock_name, symbol=self.symbol), id="note-title")
            yield Input(placeholder="e.g. Target price 1800, stop loss 1250, wait for Q3 earnings...", id="note-input")
            with Horizontal(id="note-buttons"):
                yield Button(t("save"), variant="primary", id="save-btn")
                yield Button(t("cancel"), variant="default", id="cancel-btn")

    def on_mount(self) -> None:
        self.query_one(Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        if text:
            save_note(self.symbol, text, tags=["manual", "trade"])
            self.app.notify(t("n_note_saved", symbol=self.symbol))
        self.dismiss()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-btn":
            inp = self.query_one(Input)
            if inp.value.strip():
                save_note(self.symbol, inp.value.strip(), tags=["manual", "trade"])
                self.app.notify(t("n_note_saved", symbol=self.symbol))
            self.dismiss()
        else:
            self.dismiss()


class AddStockModal(ModalScreen[None]):
    """Modal dialog for adding new stock to watchlist."""

    def compose(self) -> ComposeResult:
        with Vertical(id="add-dialog"):
            yield Label(t("add_title"), id="add-title")
            yield Input(placeholder="Enter stock code...", id="add-input")
            with Horizontal(id="add-buttons"):
                yield Button(t("add"), variant="primary", id="add-btn")
                yield Button(t("cancel"), variant="default", id="cancel-btn")

    def on_mount(self) -> None:
        self.query_one(Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        sym = event.value.strip().upper()
        if sym:
            if add_to_watchlist(sym):
                self.app.notify(t("n_added", symbol=sym))
            else:
                self.app.notify(t("n_exists", symbol=sym), severity="warning")
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


class ThinScrollBarRender(ScrollBarRender):
    """Hairline scrollbar: a one-eighth-cell thumb on a blank track."""

    @classmethod
    def render_bar(cls, size=25, virtual_size=50, window_size=20, position=0,
                   thickness=1, vertical=True, back_color=None, bar_color=None):
        glyph = "▕" if vertical else "▁"
        width = 1 if not vertical else max(1, thickness)
        grab = {"@mouse.down": "grab"}
        if not (window_size and size and virtual_size and size != virtual_size):
            return Segments([Segment(" " * width, RichStyle(bgcolor=back_color)) for _ in range(size)], new_lines=vertical)
        thumb = max(1, round(size * window_size / virtual_size))
        span = max(1, virtual_size - window_size)
        start = round((size - thumb) * min(1.0, position / span))
        segs = []
        for i in range(size):
            if start <= i < start + thumb:
                segs.append(Segment(glyph * width, RichStyle(color=bar_color, bgcolor=back_color, meta=grab)))
            else:
                segs.append(Segment(" " * width, RichStyle(bgcolor=back_color)))
        return Segments(segs, new_lines=vertical)


ScrollBar.renderer = ThinScrollBarRender


class DetailScroll(ScrollableContainer, can_focus=False):
    """Scroll container for modal content; keys are handled by the modal."""


class ScrollKeysMixin:
    """Keyboard scrolling for the detail-style view inside a modal."""

    SCROLL_BINDINGS = [
        Binding("q", "app.quit", "Quit"),
        Binding("up", "scroll_view('up')", show=False),
        Binding("down", "scroll_view('down')", show=False),
        Binding("left", "scroll_view('left')", show=False),
        Binding("right", "scroll_view('right')", show=False),
        Binding("pageup", "scroll_view('page_up')", show=False),
        Binding("pagedown", "scroll_view('page_down')", show=False),
        Binding("home", "scroll_view('home')", show=False),
        Binding("end", "scroll_view('end')", show=False),
    ]

    def action_scroll_view(self, direction: str) -> None:
        view = self.query_one("#detail-scroll")
        getattr(view, f"scroll_{direction}")(animate=True, duration=0.15, easing="out_cubic")


class RadarModal(ScrollKeysMixin, ModalScreen[None]):
    """Modal screen for market sentiment and anomaly radar."""

    BINDINGS = ScrollKeysMixin.SCROLL_BINDINGS

    def __init__(self, palette: str = "cn"):
        super().__init__()
        self.palette = palette

    def compose(self) -> ComposeResult:
        radar = MarketRadarTracker(palette=self.palette)
        with Vertical(id="detail-container"):
            with DetailScroll(id="detail-scroll"):
                yield Static(radar.render_full_radar_view(), id="detail-view")
            with Horizontal(id="detail-footer"):
                yield Button(t("close"), id="close-radar-btn", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss()

    def key_escape(self) -> None:
        self.dismiss()


class SectorModal(ScrollKeysMixin, ModalScreen[None]):
    """Modal screen for sector heatmap and rankings."""

    BINDINGS = ScrollKeysMixin.SCROLL_BINDINGS

    def __init__(self, palette: str = "cn"):
        super().__init__()
        self.palette = palette

    def compose(self) -> ComposeResult:
        sec = SectorHeatmapTracker(palette=self.palette)
        with Vertical(id="detail-container"):
            with DetailScroll(id="detail-scroll"):
                yield Static(sec.render_full_sector_view(), id="detail-view")
            with Horizontal(id="detail-footer"):
                yield Button(t("close"), id="close-sector-btn", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss()

    def key_escape(self) -> None:
        self.dismiss()


class BacktestModal(ScrollKeysMixin, ModalScreen[None]):
    """Modal screen for strategy backtesting."""

    BINDINGS = ScrollKeysMixin.SCROLL_BINDINGS

    def __init__(self, tracker: StockDataTracker, palette: str = "cn"):
        super().__init__()
        self.tracker = tracker
        self.palette = palette

    def compose(self) -> ComposeResult:
        bt = StrategyBacktester(self.tracker.symbol, self.tracker.name, palette=self.palette)
        with Vertical(id="detail-container"):
            with DetailScroll(id="detail-scroll"):
                yield Static(bt.render_backtest_panel(), id="detail-view")
            with Horizontal(id="detail-footer"):
                yield Button(t("close"), id="close-bt-btn", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss()

    def key_escape(self) -> None:
        self.dismiss()


class ThemeModal(ScrollKeysMixin, ModalScreen[None]):
    """Modal screen for selecting theme presets."""

    BINDINGS = ScrollKeysMixin.SCROLL_BINDINGS

    def compose(self) -> ComposeResult:
        with Vertical(id="alert-dialog"):
            yield Label(t("theme_title"), id="alert-title")
            for key, th in THEMES.items():
                yield Button(f"{key.upper()} - {th.description}", id=f"theme-{key}", variant="default")
            yield Button(t("close"), id="close-theme-btn", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id and event.button.id.startswith("theme-"):
            theme_key = event.button.id.replace("theme-", "")
            self.app.theme_manager.set_theme(theme_key)
            self.app.notify(t("n_theme", theme=theme_key.upper()))
            self.app.update_view()
            self.dismiss()
        else:
            self.dismiss()

    def key_escape(self) -> None:
        self.dismiss()


class FormulaModal(ScrollKeysMixin, ModalScreen[None]):
    """Modal screen for custom indicator formulas."""

    BINDINGS = ScrollKeysMixin.SCROLL_BINDINGS

    def compose(self) -> ComposeResult:
        formulas = FormulaManager.load_formulas()
        with Vertical(id="alert-dialog"):
            yield Label(t("formula_title"), id="alert-title")
            for name, f in formulas.items():
                yield Label(f"• [bold cyan]{name}:[/] [yellow]{f.expression}[/] - [dim]{f.description}[/]")
            yield Button(t("close"), id="close-formula-btn", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss()

    def key_escape(self) -> None:
        self.dismiss()


class DetailModal(ScrollKeysMixin, ModalScreen[None]):
    """Modal screen for comprehensive stock detail view with switchable chart periods."""

    BINDINGS = ScrollKeysMixin.SCROLL_BINDINGS

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
            yield Static(id="detail-header")
            with Horizontal(id="detail-periods"):
                for i, p in enumerate(self.PERIODS, 1):
                    yield Button(f"{period_label(p)} {i}", id=f"period-{p}", variant="default")
            with DetailScroll(id="detail-scroll"):
                yield Static(id="detail-view")
            with Horizontal(id="detail-footer"):
                yield Button(t("add_note_btn"), id="detail-note-btn", variant="primary")
                yield Button(t("close_enter"), id="detail-close-btn", variant="default")

    def on_mount(self) -> None:
        self.update_content()

    def update_content(self) -> None:
        notes = get_symbol_notes(self.tracker.symbol)
        self.query_one("#detail-header", Static).update(render_detail_header(self.tracker, self.palette))
        layout = render_detail_body(
            self.tracker,
            palette=self.palette,
            notes=notes,
            period=self.period,
            candles=self.kline_cache.get(self.period),
            period_note=self.kline_note.get(self.period, ""),
        )
        self.query_one("#detail-view", Static).update(layout)
        for p in self.PERIODS:
            self.query_one(f"#period-{p}", Button).set_class(p == self.period, "active")

    def set_period(self, period: str) -> None:
        self.period = period
        if period != "intraday" and period not in self.kline_cache:
            self.kline_note[period] = t("d_loading")
            self.run_worker(lambda: self.load_kline(period), thread=True, exclusive=True, group="kline")
        self.update_content()

    def load_kline(self, period: str) -> None:
        candles: List[Dict[str, Any]] = []
        note = ""
        if getattr(self.app, "use_real_data", False):
            candles = fetch_kline(self.tracker.symbol, period)
        if not candles:
            candles = candles_from_prices(list(self.tracker.prices))
            note = t("d_simulated")
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


class MainScroll(VerticalScroll, can_focus=False):
    """Scrollable container that leaves arrow keys to the stock selection bindings."""


class StockTerminalApp(App):
    """Main Textual TUI Application for term-stock-table."""

    CSS = """
    * {
        scrollbar-size: 1 1;
        scrollbar-background: #0f1117;
        scrollbar-background-hover: #0f1117;
        scrollbar-background-active: #0f1117;
        scrollbar-color: #3b4252;
        scrollbar-color-hover: #5e6a82;
        scrollbar-color-active: #81a1c1;
        scrollbar-corner-color: #0f1117;
    }
    Screen {
        background: #0f1117;
    }
    Footer {
        overflow: hidden hidden;
        scrollbar-size: 0 0;
    }
    #main-scroll {
        width: 100%;
        height: 1fr;
        overflow-x: auto;
        overflow-y: auto;
    }
    #main-table-view {
        width: 100%;
        height: auto;
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
        padding: 0 1;
        align: center middle;
    }
    #detail-scroll {
        width: 100%;
        height: 1fr;
    }
    #detail-view {
        width: 100%;
        height: auto;
    }
    #detail-header {
        height: auto;
    }
    #detail-periods {
        height: 1;
        align: left middle;
        overflow: hidden hidden;
    }
    #detail-periods Button {
        background: #1f2937;
        color: #cbd5e1;
        text-style: none;
    }
    #detail-periods Button.active {
        background: #dc2626;
        color: white;
        text-style: bold;
    }
    #detail-periods Button:hover {
        background: #374151;
    }
    #detail-footer {
        height: 1;
        align: right middle;
        overflow: hidden hidden;
    }
    #detail-periods Button, #detail-footer Button {
        height: 1;
        min-width: 0;
        border: none;
        padding: 0;
        margin: 0 1 0 0;
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
        Binding("b", "toggle_boss", "Boss Key", priority=True),
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
        Binding("L", "toggle_language", "Language 中/EN"),
        Binding("q", "quit", "Quit"),
    ]

    BINDING_LABELS = {
        ("b", "toggle_boss"): "b_boss", ("escape", "handle_escape"): "b_escape",
        ("tab", "cycle_boss_profile"): "b_tab", ("enter", "show_detail"): "b_enter",
        ("n", "add_note"): "b_note", ("l", "set_alert"): "b_alert", ("a", "add_stock"): "b_add",
        ("slash", "add_stock"): "b_search", ("d", "delete_stock"): "b_delete",
        ("s", "cycle_sort"): "b_sort", ("r", "reverse_sort"): "b_reverse",
        ("T", "show_themes"): "b_themes", ("F", "show_formulas"): "b_formulas",
        ("R", "show_radar"): "b_radar", ("S", "show_sector"): "b_sector",
        ("B", "show_backtest"): "b_backtest", ("P", "toggle_portfolio"): "b_portfolio",
        ("p", "toggle_palette"): "b_palette", ("L", "toggle_language"): "b_lang",
        ("q", "quit"): "b_quit",
    }

    def __init__(
        self,
        symbols: Optional[List[str]] = None,
        palette: str = "cn",
        theme: str = "classic_cn",
        use_real_data: bool = True,
        refresh_interval: float = 1.0,
        lang: Optional[str] = None,
    ):
        super().__init__()
        set_lang(lang or load_settings().get("language", "en"))
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
        self.selected_symbol: Optional[str] = None
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
        with MainScroll(id="main-scroll"):
            yield Static(id="main-table-view")
        yield Footer()

    def on_mount(self) -> None:
        self.apply_language()
        self.update_view()
        self.set_interval(self.refresh_interval, self.refresh_market_data)
        if self.overlay_enabled:
            self.install_overlay_hook()

    def apply_language(self) -> None:
        """Retitle the app and footer bindings in the active language."""
        self.title = t("app_title")
        for key, bindings in self._bindings.key_to_bindings.items():
            for i, binding in enumerate(bindings):
                label = self.BINDING_LABELS.get((binding.key, binding.action))
                if label:
                    bindings[i] = dataclasses.replace(binding, description=t(label))
        self.refresh_bindings()

    def action_toggle_language(self) -> None:
        """Switch UI language between English and Chinese and persist the choice."""
        lang = toggle_lang()
        settings = load_settings()
        settings["language"] = lang
        save_settings(settings)
        self.apply_language()
        self.update_view()
        self.notify(t("lang_switched"))

    def install_overlay_hook(self) -> None:
        """Append smooth term-sparkline images to every frame so they never get erased."""
        driver = self._driver
        orig_write = driver.write

        def write(data: str) -> None:
            orig_write(data + (self.overlay_payload() if len(data) > 40 else ""))

        driver.write = write

    TABLE_HEADER_LINES = 4

    @property
    def row_height(self) -> int:
        return 1 if self.overlay_enabled else 2

    def hidden_rows_above(self) -> int:
        """Rows scrolled out of view above the viewport (so images map to the right stock)."""
        if not self.overlay_enabled:
            return 0
        scroll_y = int(self.query_one("#main-scroll").scroll_y)
        return max(0, scroll_y - self.TABLE_HEADER_LINES) // self.row_height

    def scroll_to_selected(self) -> None:
        """Keep the highlighted row inside the visible viewport."""
        if self.is_boss_mode or self.is_portfolio_mode:
            return
        scroll = self.query_one("#main-scroll")
        if self.selected_index == 0:
            scroll.scroll_home(animate=True, duration=0.15, easing="out_cubic")
            return
        y = self.TABLE_HEADER_LINES + self.selected_index * self.row_height
        scroll.scroll_to_region(Region(0, y, 1, self.row_height), animate=True, duration=0.15, easing="out_cubic")

    def overlay_payload(self) -> str:
        if not self.overlay_items or len(self.screen_stack) > 1:
            return ""
        try:
            strips = self.screen._compositor.render_strips()
        except Exception:
            return ""
        blank = overlay_blank(OVERLAY_BLANK_WIDTH)
        out = ["\x1b7"]
        idx = self.hidden_rows_above()
        first = idx
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
        return "".join(out) if idx > first else ""

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

    def fit_table_width(self, widget: Static, tbl) -> None:
        """Let the table keep its natural minimum width so narrow terminals scroll horizontally."""
        try:
            from rich.measure import Measurement
            natural = sum((c.min_width or 0) for c in tbl.columns) + 3 * len(tbl.columns) + 1
            needed = max(natural, Measurement.get(self.console, self.console.options, tbl).minimum) + 2
            avail = self.query_one("#main-scroll").size.width
            widget.styles.width = max(needed, avail) if avail else "100%"
        except Exception:
            widget.styles.width = "100%"

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
                selected_symbol=self.current_tracker().symbol if self.trackers else None,
            )
            overlay_end()
            self.overlay_items = queue or []
            view_widget.update(tbl)
            self.fit_table_width(view_widget, tbl)

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
        self.notify(t("n_mode", mode=t("mode_portfolio") if self.is_portfolio_mode else t("mode_watchlist")))
        self.update_view()

    def action_cycle_sort(self) -> None:
        """Cycle sorting column."""
        self.sort_col_idx = (self.sort_col_idx + 1) % len(self.sort_columns)
        curr = self.sort_columns[self.sort_col_idx] or "Default"
        self.notify(t("n_sorted", col=curr.upper()))
        self.update_view()

    def action_reverse_sort(self) -> None:
        """Reverse sorting order."""
        self.sort_descending = not self.sort_descending
        self.notify(t("n_order", order=t("order_desc") if self.sort_descending else t("order_asc")))
        self.update_view()

    def action_open_detail(self, symbol: str) -> None:
        """Open the detail view for a clicked symbol/name cell."""
        if len(self.screen_stack) > 1:
            return
        for i, tr in enumerate(self.ordered_trackers()):
            if tr.symbol == symbol:
                self.selected_index = i
                self.selected_symbol = symbol
                self.push_screen(DetailModal(tr, palette=self.palette))
                return

    def action_show_detail(self) -> None:
        """Show detail view for highlighted stock."""
        if self.trackers:
            tr = self.current_tracker()
            self.push_screen(DetailModal(tr, palette=self.palette))

    def action_add_note(self) -> None:
        """Open note editor for current stock."""
        if self.trackers:
            tr = self.current_tracker()
            self.push_screen(NoteModal(tr.symbol, tr.name))

    def action_set_alert(self) -> None:
        """Open alert configuration modal."""
        if self.trackers:
            tr = self.current_tracker()
            self.push_screen(AlertModal(tr.symbol, tr.name))

    def action_add_stock(self) -> None:
        """Open add stock modal."""
        self.push_screen(AddStockModal())

    def action_delete_stock(self) -> None:
        """Delete currently selected stock."""
        if self.trackers:
            tr = self.current_tracker()
            remove_from_watchlist(tr.symbol)
            self.notify(t("n_removed", symbol=tr.symbol))
            self.refresh_trackers_from_disk()

    def ordered_trackers(self) -> List[StockDataTracker]:
        return sort_trackers(self.trackers, self.sort_columns[self.sort_col_idx], self.sort_descending)

    def current_tracker(self) -> StockDataTracker:
        """Highlighted stock; follows its symbol when live data re-sorts the table."""
        ordered = self.ordered_trackers()
        for i, tr in enumerate(ordered):
            if tr.symbol == self.selected_symbol:
                self.selected_index = i
                return tr
        tr = ordered[self.selected_index % len(ordered)]
        self.selected_symbol = tr.symbol
        return tr

    def move_selection(self, index: int) -> None:
        if self.trackers:
            self.current_tracker()
            ordered = self.ordered_trackers()
            self.selected_index = index % len(ordered)
            self.selected_symbol = ordered[self.selected_index].symbol
            self.update_view()
            self.call_after_refresh(self.scroll_to_selected)

    def action_cursor_down(self) -> None:
        """Vim 'j' / Down: Move highlighted stock selection down."""
        self.move_selection(self.selected_index + 1)

    def action_cursor_up(self) -> None:
        """Vim 'k' / Up: Move highlighted stock selection up."""
        self.move_selection(self.selected_index - 1)

    def action_cursor_top(self) -> None:
        """Vim 'g' / Home: Jump to first stock."""
        self.move_selection(0)

    def action_cursor_bottom(self) -> None:
        """Vim 'G' / End: Jump to last stock."""
        self.move_selection(len(self.trackers) - 1)

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
            tr = self.current_tracker()
            self.push_screen(BacktestModal(tr, palette=self.palette))

    def action_toggle_palette(self) -> None:
        """Toggle between CN (Red Up) and US (Green Up) color palettes."""
        self.palette = "us" if self.palette == "cn" else "cn"
        self.notify(t("n_palette", palette=self.palette.upper()))
        self.update_view()
