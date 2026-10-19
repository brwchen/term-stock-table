"""Experiment B: native Textual rows with textual-image widgets for the trend column.

Run: python -m term_stock_table.exp_textual_image   (needs `pip install textual-image`, q to quit)
"""
import base64
import io

from PIL import Image as PILImage
from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Label, Static
from textual_image.widget import AutoImage

from .api import StockDataTracker
from .inline_spark import _image

SYMBOLS = ["600519", "000001", "300750", "AAPL", "NVDA", "00700", "BABA"]
SPARK_W = 24


def spark_pil(tr: StockDataTracker) -> PILImage.Image:
    escape = _image(tuple(tr.prices), SPARK_W, "cn", (("fill", False), ("show_dot", False)))
    payload = escape.split(":", 1)[1].rstrip("\x07")
    return PILImage.open(io.BytesIO(base64.b64decode(payload))).convert("RGBA")


class TextualImageDemo(App):
    BINDINGS = [("q", "quit", "Quit")]
    CSS = """
    Screen { background: #0f1117; }
    .row { height: 2; padding: 0 1; }
    .c1 { width: 10; } .c2 { width: 14; } .c3 { width: 12; } .c4 { width: 12; }
    .spark { width: 24; height: 2; }
    """

    def __init__(self) -> None:
        super().__init__()
        self.trackers = [StockDataTracker(s) for s in SYMBOLS]
        self.price_labels = {}
        self.change_labels = {}
        self.images = {}

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("Experiment B: textual-image widgets (q to quit)")
            for tr in self.trackers:
                with Horizontal(classes="row"):
                    yield Static(tr.symbol, classes="c1")
                    yield Static(tr.name, classes="c2")
                    self.price_labels[tr.symbol] = Static("", classes="c3")
                    yield self.price_labels[tr.symbol]
                    self.change_labels[tr.symbol] = Static("", classes="c4")
                    yield self.change_labels[tr.symbol]
                    self.images[tr.symbol] = AutoImage(spark_pil(tr), classes="spark")
                    yield self.images[tr.symbol]

    def on_mount(self) -> None:
        self.set_interval(1.0, self.tick)

    def tick(self) -> None:
        for tr in self.trackers:
            tr.tick_simulation()
            style = "bright_red" if tr.change_pct >= 0 else "bright_green"
            self.price_labels[tr.symbol].update(f"{tr.price:.2f}")
            self.change_labels[tr.symbol].update(Text(f"{tr.change_pct:+.2f}%", style=style))
            self.images[tr.symbol].image = spark_pil(tr)


def main() -> None:
    TextualImageDemo().run()


if __name__ == "__main__":
    main()
