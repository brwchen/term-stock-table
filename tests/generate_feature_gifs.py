"""Generate high-density terminal showcase GIFs using Pillow and Rich rendering."""
import os
import io
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from rich.console import Console

from term_stock_table.api import StockDataTracker
from term_stock_table.table import create_stock_table
from term_stock_table.portfolio import calculate_portfolio_pnl, create_portfolio_table
from term_stock_table.detail import render_stock_detail
from term_stock_table.boss import render_boss_view, PROFILES
from term_stock_table.market import render_indices_banner
from term_stock_table.radar import MarketRadarTracker
from term_stock_table.sector import SectorHeatmapTracker
from term_stock_table.tick import IntradayChartRenderer, ChipProfileRenderer, TickTapeRenderer
from term_stock_table.fundamentals import FundamentalAnalyzer
from term_stock_table.backtest import StrategyBacktester

ASSETS_DIR = Path("/Users/xchen17/term-stock-table/assets")
FEATURES_DIR = ASSETS_DIR / "features"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)
FEATURES_DIR.mkdir(parents=True, exist_ok=True)


def get_font(size=14):
    font_paths = [
        "/System/Library/Fonts/SFNSMono.ttf",
        "/System/Library/Fonts/Monaco.ttf",
        "/System/Library/Fonts/Menlo.ttc",
        "/System/Library/Fonts/Supplemental/Courier New.ttf",
    ]
    for p in font_paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def renderable_to_image(renderable, width_chars=110, font_size=14, bg_color="#0d1117"):
    import tempfile
    import subprocess

    console = Console(
        width=width_chars,
        record=True,
        color_system="truecolor",
    )
    console.print(renderable)
    svg_str = console.export_svg(title="term-stock-table")

    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f_svg:
        f_svg.write(svg_str.encode("utf-8"))
        svg_path = f_svg.name

    png_path = svg_path.replace(".svg", ".png")
    try:
        subprocess.run(["rsvg-convert", svg_path, "-o", png_path], check=True, capture_output=True)
        img = Image.open(png_path).convert("RGB")
        return img
    finally:
        if os.path.exists(svg_path):
            os.remove(svg_path)
        if os.path.exists(png_path):
            os.remove(png_path)


def normalize_frames(frames, bg_color=(13, 17, 23)):
    if not frames:
        return []
    max_w = max(img.width for img in frames)
    max_h = max(img.height for img in frames)
    normalized = []
    for img in frames:
        canvas = Image.new("RGB", (max_w, max_h), bg_color)
        canvas.paste(img, (0, 0))
        normalized.append(canvas)
    return normalized


def save_gif(frames, path, duration=450):
    norm = normalize_frames(frames)
    if norm:
        norm[0].save(
            path,
            save_all=True,
            append_images=norm[1:],
            duration=duration,
            loop=0,
            optimize=True,
        )


def generate_all_gifs():
    symbols = ["600519", "000001", "300750", "AAPL", "NVDA", "00700", "BABA"]
    trackers = [StockDataTracker(s) for s in symbols]

    # 1. Watchlist Overview GIF
    print("Generating watchlist_overview.gif...")
    frames = []
    for _ in range(8):
        for tr in trackers:
            tr.tick_simulation()
        tbl = create_stock_table(trackers, palette="cn", is_live=True)
        img = renderable_to_image(tbl)
        frames.append(img)
    save_gif(frames, FEATURES_DIR / "watchlist_overview.gif", duration=400)

    # 2. Portfolio PnL Tracker GIF
    print("Generating portfolio_pnl_tracker.gif...")
    frames = []
    portfolio = {
        "600519": {"shares": 200, "cost": 1320.0},
        "000001": {"shares": 5000, "cost": 11.20},
        "AAPL": {"shares": 100, "cost": 220.0},
        "NVDA": {"shares": 150, "cost": 125.0},
    }
    for _ in range(6):
        for tr in trackers:
            tr.tick_simulation()
        p_data = calculate_portfolio_pnl([tr.to_dict() for tr in trackers], portfolio)
        tbl = create_portfolio_table(p_data, palette="cn")
        frames.append(renderable_to_image(tbl))
    save_gif(frames, FEATURES_DIR / "portfolio_pnl_tracker.gif", duration=450)

    # 3. Stock Detail & K-Line GIF
    print("Generating stock_detail_view.gif...")
    frames = []
    tr_detail = StockDataTracker("600519")
    for i in range(6):
        tr_detail.tick_simulation()
        layout = render_stock_detail(tr_detail, palette="cn", show_candlestick=(i % 2 == 1))
        frames.append(renderable_to_image(layout, width_chars=110))
    save_gif(frames, FEATURES_DIR / "stock_detail_view.gif", duration=600)

    # 4. Boss Mode Camouflage Matrix GIF
    print("Generating boss_mode_stealth.gif...")
    frames = []
    for prof in ["devops", "kubectl", "cpp", "git", "python", "nginx"]:
        view = render_boss_view(prof, trackers=trackers)
        frames.append(renderable_to_image(view))
    save_gif(frames, FEATURES_DIR / "boss_mode_stealth.gif", duration=650)

    # 5. Bollinger and Indicators GIF
    print("Generating bollinger_and_indicators.gif...")
    frames = []
    for _ in range(6):
        for tr in trackers:
            tr.tick_simulation()
        tbl = create_stock_table(trackers, palette="cn", sort_by="change_pct", reverse=True)
        frames.append(renderable_to_image(tbl))
    save_gif(frames, FEATURES_DIR / "bollinger_and_indicators.gif", duration=450)

    # 6. Market Radar & Live Anomaly GIF
    print("Generating radar_and_anomalies.gif...")
    radar_frames = []
    radar = MarketRadarTracker(palette="cn")
    for _ in range(5):
        radar_frames.append(renderable_to_image(radar.render_full_radar_view(), width_chars=110))
    save_gif(radar_frames, FEATURES_DIR / "radar_and_anomalies.gif", duration=500)

    # 7. Sector Heatmap & Inflow Matrix GIF
    print("Generating sector_heatmap_matrix.gif...")
    sec_frames = []
    sec = SectorHeatmapTracker(palette="cn")
    for _ in range(5):
        sec_frames.append(renderable_to_image(sec.render_full_sector_view(), width_chars=110))
    save_gif(sec_frames, FEATURES_DIR / "sector_heatmap_matrix.gif", duration=500)

    # 8. Intraday VWAP & Chip Distribution GIF
    print("Generating intraday_and_chips.gif...")
    intra_frames = []
    intra = IntradayChartRenderer("600519", "贵州茅台", 1680.0, palette="cn")
    chip = ChipProfileRenderer(1688.0, palette="cn")
    tape = TickTapeRenderer(1688.0, palette="cn")
    intra_frames.append(renderable_to_image(intra.render_intraday_panel(), width_chars=110))
    intra_frames.append(renderable_to_image(intra.render_intraday_panel(), width_chars=110))
    intra_frames.append(renderable_to_image(chip.render_chip_panel(), width_chars=110))
    intra_frames.append(renderable_to_image(tape.render_tape_table(), width_chars=110))
    save_gif(intra_frames, FEATURES_DIR / "intraday_and_chips.gif", duration=600)

    # 9. Main Terminal Demo GIF
    print("Generating demo.gif...")
    demo_frames = []
    # Scene A: Watchlist
    for _ in range(3):
        for tr in trackers:
            tr.tick_simulation()
        demo_frames.append(renderable_to_image(create_stock_table(trackers, palette="cn")))
    # Scene B: Radar & Sentiment
    demo_frames.append(renderable_to_image(radar.render_full_radar_view(), width_chars=110))
    # Scene C: Sector Heatmap
    demo_frames.append(renderable_to_image(sec.render_full_sector_view(), width_chars=110))
    # Scene D: Portfolio
    p_data = calculate_portfolio_pnl([tr.to_dict() for tr in trackers], portfolio)
    demo_frames.append(renderable_to_image(create_portfolio_table(p_data, palette="cn")))
    # Scene E: Stock Detail & Candlestick
    demo_frames.append(renderable_to_image(render_stock_detail(trackers[0], palette="cn", show_candlestick=False), width_chars=110))
    demo_frames.append(renderable_to_image(render_stock_detail(trackers[0], palette="cn", show_candlestick=True), width_chars=110))
    # Scene F: Boss Mode Camouflage
    demo_frames.append(renderable_to_image(render_boss_view("neovim")))
    demo_frames.append(renderable_to_image(render_boss_view("cpp")))
    
    save_gif(demo_frames, ASSETS_DIR / "demo.gif", duration=550)
    print("All GIFs generated successfully!")


if __name__ == "__main__":
    generate_all_gifs()
