"""Experiment A: paint iTerm2 inline images over a blank trend column after each Textual frame.

Run: python -m term_stock_table.exp_overlay   (iTerm2 / WezTerm only, q to quit)
"""
import sys

from rich.cells import cell_len
from rich.table import Table
from rich.text import Text
from textual.app import App, ComposeResult
from textual.widgets import Static

from .api import StockDataTracker
from .inline_spark import _image

SYMBOLS = ["600519", "000001", "300750", "AAPL", "NVDA", "00700", "BABA"]
SPARK_W = 24
BLANK = "\u2800" * SPARK_W


class OverlayDemo(App):
    BINDINGS = [("q", "quit", "Quit")]
    CSS = "Screen { background: #0f1117; } #t { padding: 1 2; }"

    def __init__(self) -> None:
        super().__init__()
        self.trackers = [StockDataTracker(s) for s in SYMBOLS]

    def compose(self) -> ComposeResult:
        yield Static(id="t")

    def on_mount(self) -> None:
        self.set_interval(1.0, self.tick)
        self.tick()

    def tick(self) -> None:
        table = Table(title="Experiment A: image overlay (q to quit)", expand=False)
        for col in ("Symbol", "Name", "Price", "Change%", "Trend"):
            table.add_column(col, vertical="middle")
        for tr in self.trackers:
            tr.tick_simulation()
            style = "bright_red" if tr.change_pct >= 0 else "bright_green"
            table.add_row(tr.symbol, tr.name, f"{tr.price:.2f}", Text(f"{tr.change_pct:+.2f}%", style=style), Text(BLANK))
        self.query_one("#t", Static).update(table)
        self.set_timer(0.12, self.paint_images)

    def paint_images(self) -> None:
        strips = self.screen._compositor.render_strips()
        out = ["\x1b7"]
        idx = 0
        for y, strip in enumerate(strips):
            text = strip.text
            x = text.find(BLANK)
            if x < 0 or idx >= len(self.trackers):
                continue
            tr = self.trackers[idx]
            idx += 1
            img = _image(tuple(tr.prices), SPARK_W, "cn", (("fill", False), ("show_dot", False)))
            out.append(f"\x1b[{y + 1};{cell_len(text[:x]) + 1}H{img}")
        out.append("\x1b8")
        sys.__stdout__.write("".join(out))
        sys.__stdout__.flush()


def main() -> None:
    OverlayDemo().run()


if __name__ == "__main__":
    main()
