"""Command Line Interface for term-stock-table."""
import argparse
import sys
import time
from rich.console import Console
from rich.live import Live

from .api import StockDataTracker, fetch_live_quotes
from .config import (
    load_watchlist,
    add_to_watchlist,
    remove_from_watchlist,
    save_note,
    load_notes,
    get_symbol_notes,
    load_portfolio,
    save_position,
    remove_position,
    load_alerts,
    save_alert,
    remove_alert,
)
from .table import create_stock_table
from .detail import render_stock_detail
from .boss import render_boss_view, PROFILES, export_daily_review
from .portfolio import calculate_portfolio_pnl, create_portfolio_table, Position
from .alerts import evaluate_alerts
from .market import render_indices_banner
from .radar import MarketRadarTracker
from .tick import IntradayChartRenderer, ChipProfileRenderer, TickTapeRenderer
from .sector import SectorHeatmapTracker
from .fundamentals import FundamentalAnalyzer
from .backtest import StrategyBacktester
from .statusline import StatuslineFormatter
from .importer import PortfolioDataImporter
from .webhook import WebhookDispatcher, WebhookConfig
from .tui import StockTerminalApp


def main():
    parser = argparse.ArgumentParser(
        prog="stk",
        description="Professional real-time terminal stock monitoring table, technical indicators, detail views, and stealth boss mode."
    )
    parser.add_argument(
        "--version", "-v",
        action="version",
        version="term-stock-table 0.1.0"
    )
    parser.add_argument(
        "--symbols", "-s",
        type=str,
        default=None,
        help="Comma-separated stock symbols (e.g. 600519,AAPL,NVDA,00700)"
    )
    parser.add_argument(
        "--palette", "-p",
        choices=["cn", "us"],
        default="cn",
        help="Market color palette ('cn': Red up/Green down, 'us': Green up/Red down)"
    )
    parser.add_argument(
        "--print",
        action="store_true",
        help="Print single static Rich table snapshot to stdout and exit"
    )
    parser.add_argument(
        "--watch", "-w",
        action="store_true",
        help="Run live refreshing terminal loop (Rich Live mode)"
    )
    parser.add_argument(
        "--interval", "-i",
        type=float,
        default=1.0,
        help="Refresh interval in seconds (default: 1.0)"
    )
    parser.add_argument(
        "--sim",
        action="store_true",
        help="Force offline simulation engine instead of live quote API"
    )
    parser.add_argument(
        "--sort",
        choices=["change_pct", "price", "volume", "amount", "amplitude", "turnover_rate", "symbol", "pe"],
        default=None,
        help="Sort table by specific column"
    )
    parser.add_argument(
        "--asc",
        action="store_true",
        help="Sort in ascending order (default is descending)"
    )
    parser.add_argument(
        "--indices",
        action="store_true",
        help="Display global major indices overview banner"
    )
    parser.add_argument(
        "--radar", "-r",
        action="store_true",
        help="Display market breadth sentiment & live anomaly radar"
    )
    parser.add_argument(
        "--sector",
        action="store_true",
        help="Display industry & concept sector heatmap and inflow rankings"
    )
    parser.add_argument(
        "--intraday",
        type=str,
        metavar="SYMBOL",
        help="Display intraday price chart with VWAP line and time axis"
    )
    parser.add_argument(
        "--chips",
        type=str,
        metavar="SYMBOL",
        help="Display chip cost volume profile and profit ratio"
    )
    parser.add_argument(
        "--tape",
        type=str,
        metavar="SYMBOL",
        help="Display real-time tick-by-tick trade tape"
    )
    parser.add_argument(
        "--dupont",
        type=str,
        metavar="SYMBOL",
        help="Display DuPont financial analysis and Dragon-Tiger seat dynamics"
    )
    parser.add_argument(
        "--backtest",
        type=str,
        metavar="SYMBOL",
        help="Run quantitative strategy backtest and render terminal equity curve"
    )
    parser.add_argument(
        "--statusline", "--tmux",
        action="store_true",
        help="Output single-line compact ticker for Tmux/WezTerm status bar"
    )
    parser.add_argument(
        "--import-csv",
        type=str,
        metavar="FILEPATH",
        help="Import portfolio position records from CSV file"
    )
    parser.add_argument(
        "--export-csv",
        nargs="?",
        const="portfolio_export.csv",
        metavar="FILEPATH",
        help="Export current portfolio positions to CSV file"
    )
    parser.add_argument(
        "--webhook-test",
        action="store_true",
        help="Test dispatching a sample alert notification via Webhook"
    )
    parser.add_argument(
        "--portfolio",
        action="store_true",
        help="View portfolio asset valuation and real-time floating PnL table"
    )
    parser.add_argument(
        "--position",
        nargs=3,
        metavar=("SYMBOL", "SHARES", "COST"),
        help="Set or update portfolio position (e.g. --position 600519 100 1350.0)"
    )
    parser.add_argument(
        "--remove-position",
        type=str,
        metavar="SYMBOL",
        help="Remove symbol position from portfolio"
    )
    parser.add_argument(
        "--alert",
        nargs="+",
        metavar=("SYMBOL", "PARAMS"),
        help="Set price alert: --alert SYMBOL [high=VAL] [low=VAL] [pct=VAL]"
    )
    parser.add_argument(
        "--alerts",
        action="store_true",
        help="View all configured price and volatility alerts"
    )
    parser.add_argument(
        "--remove-alert",
        type=str,
        metavar="SYMBOL",
        help="Remove price alert for a symbol"
    )
    parser.add_argument(
        "--export-daily",
        nargs="?",
        const="daily_review.md",
        metavar="FILEPATH",
        help="Export comprehensive daily review markdown report"
    )
    parser.add_argument(
        "--boss", "-b",
        action="store_true",
        help="Launch directly in Boss Mode (摸鱼伪装模式)"
    )
    parser.add_argument(
        "--boss-profile",
        choices=PROFILES,
        default="devops",
        help="Camouflage profile for Boss Mode ('devops', 'kubectl', 'nginx', 'cpp', 'git', 'python', 'monochrome')"
    )
    parser.add_argument(
        "--add",
        type=str,
        metavar="SYMBOL",
        help="Add symbol to persistent watchlist"
    )
    parser.add_argument(
        "--remove",
        type=str,
        metavar="SYMBOL",
        help="Remove symbol from persistent watchlist"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all symbols in persistent watchlist"
    )
    parser.add_argument(
        "--note",
        nargs=2,
        metavar=("SYMBOL", "TEXT"),
        help="Add investment note for a stock symbol"
    )
    parser.add_argument(
        "--notes",
        nargs="?",
        const="__ALL__",
        metavar="SYMBOL",
        help="View notes for specific symbol or all symbols"
    )
    parser.add_argument(
        "--detail", "-d",
        type=str,
        metavar="SYMBOL",
        help="View full detail page for a single stock symbol"
    )

    args = parser.parse_args()
    console = Console()

    # 1. Indices Banner & Radar & Sector
    if args.indices:
        banner = render_indices_banner(palette=args.palette)
        console.print(banner)
        return

    if args.radar:
        radar = MarketRadarTracker(palette=args.palette)
        console.print(radar.render_full_radar_view())
        return

    if args.sector:
        sec = SectorHeatmapTracker(palette=args.palette)
        console.print(sec.render_full_sector_view())
        return

    if args.intraday:
        tr = StockDataTracker(args.intraday)
        renderer = IntradayChartRenderer(tr.symbol, tr.name, tr.prev_close, palette=args.palette)
        console.print(renderer.render_intraday_panel())
        return

    if args.chips:
        tr = StockDataTracker(args.chips)
        chip_rend = ChipProfileRenderer(tr.price, palette=args.palette)
        console.print(chip_rend.render_chip_panel())
        return

    if args.tape:
        tr = StockDataTracker(args.tape)
        tape_rend = TickTapeRenderer(tr.price, palette=args.palette)
        console.print(tape_rend.render_tape_table())
        return

    if args.dupont:
        tr = StockDataTracker(args.dupont)
        fa = FundamentalAnalyzer(tr.symbol, tr.name, palette=args.palette)
        console.print(fa.render_dupont_panel())
        console.print("")
        console.print(fa.render_dragon_tiger_table())
        return

    if args.backtest:
        tr = StockDataTracker(args.backtest)
        bt = StrategyBacktester(tr.symbol, tr.name, palette=args.palette)
        console.print(bt.render_backtest_panel())
        return

    if args.import_csv:
        imported = PortfolioDataImporter.import_from_csv(args.import_csv)
        for pos in imported:
            save_position(pos.symbol, pos.shares, pos.cost_price, notes=pos.notes)
        console.print(f"[bold green]✓ Imported {len(imported)} positions from {args.import_csv}[/]")
        return

    if args.export_csv:
        port = load_portfolio()
        positions = [
            Position(sym, sym, data.get("shares", 0), data.get("cost", 0.0), notes=data.get("notes", ""))
            for sym, data in port.items()
        ]
        csv_str = PortfolioDataImporter.export_to_csv(positions)
        with open(args.export_csv, "w", encoding="utf-8") as f:
            f.write(csv_str)
        console.print(f"[bold green]✓ Exported {len(positions)} positions to {args.export_csv}[/]")
        return

    if args.webhook_test:
        dispatcher = WebhookDispatcher()
        preview = dispatcher.render_test_preview(
            "宁德时代 (300750) 突破预警",
            "现价 258.40 (+4.82%) 突破目标阻力价位 255.00，量比放大 2.4倍！"
        )
        console.print(preview)
        return

    if args.statusline:
        symbols_list = args.symbols.split(",") if args.symbols else load_watchlist()
        trackers_list = [StockDataTracker(s) for s in symbols_list]
        fmt = StatuslineFormatter(trackers_list, palette=args.palette)
        line = fmt.format_statusline(symbols_list, use_ansi=True)
        print(line)
        return

    # 2. Watchlist operations
    if args.add:
        if add_to_watchlist(args.add):
            console.print(f"[bold green]✓ Added {args.add.upper()} to watchlist.[/]")
        else:
            console.print(f"[yellow]! {args.add.upper()} is already in watchlist.[/]")
        return

    if args.remove:
        if remove_from_watchlist(args.remove):
            console.print(f"[bold green]✓ Removed {args.remove.upper()} from watchlist.[/]")
        else:
            console.print(f"[yellow]! {args.remove.upper()} not found in watchlist.[/]")
        return

    if args.list:
        wl = load_watchlist()
        console.print(f"[bold cyan]Persistent Watchlist ({len(wl)} items):[/] {', '.join(wl)}")
        return

    # 3. Position and Portfolio operations
    if args.position:
        sym, shares, cost = args.position
        save_position(sym, float(shares), float(cost))
        console.print(f"[bold green]✓ Portfolio Position Saved:[/] {sym.upper()} - {shares} shares @ ¥{float(cost):.2f}")
        return

    if args.remove_position:
        if remove_position(args.remove_position):
            console.print(f"[bold green]✓ Position removed for {args.remove_position.upper()}.[/]")
        else:
            console.print(f"[yellow]! No position found for {args.remove_position.upper()}.[/]")
        return

    if args.portfolio:
        port = load_portfolio()
        symbols = list(port.keys()) or load_watchlist()
        quotes_dict = {}
        if not args.sim and symbols:
            quotes_dict = fetch_live_quotes(symbols, timeout=2.0)
        quotes_list = []
        for s in symbols:
            if s in quotes_dict:
                quotes_list.append(quotes_dict[s])
            else:
                tr = StockDataTracker(s)
                quotes_list.append(tr.to_dict())
        p_data = calculate_portfolio_pnl(quotes_list, port)
        table = create_portfolio_table(p_data, palette=args.palette)
        console.print(table)
        return

    # 4. Alerts operations
    if args.alert:
        sym = args.alert[0]
        high_val, low_val, pct_val = None, None, None
        for item in args.alert[1:]:
            if item.startswith("high=") or item.startswith(">"):
                high_val = float(item.split("=")[-1].replace(">", ""))
            elif item.startswith("low=") or item.startswith("<"):
                low_val = float(item.split("=")[-1].replace("<", ""))
            elif item.startswith("pct=") or item.startswith("%"):
                pct_val = float(item.split("=")[-1].replace("%", ""))
            elif item.replace(".", "", 1).isdigit():
                high_val = float(item)
        save_alert(sym, target_high=high_val, target_low=low_val, max_change_pct=pct_val)
        console.print(f"[bold green]✓ Alert saved for {sym.upper()}:[/] High={high_val}, Low={low_val}, Volatility={pct_val}%")
        return

    if args.alerts:
        all_alerts = load_alerts()
        if not all_alerts:
            console.print("[dim]No price alerts configured.[/]")
        else:
            console.print("[bold gold1]🔔 Configured Price & Volatility Alerts:[/]")
            for sym, cfg in all_alerts.items():
                h = cfg.get('target_high', '-')
                l = cfg.get('target_low', '-')
                p = cfg.get('max_change_pct', '-')
                console.print(f"  • [bold cyan]{sym}[/]: High ≥ {h} | Low ≤ {l} | ±Change ≥ {p}%")
        return

    if args.remove_alert:
        if remove_alert(args.remove_alert):
            console.print(f"[bold green]✓ Alert removed for {args.remove_alert.upper()}.[/]")
        else:
            console.print(f"[yellow]! No alert found for {args.remove_alert.upper()}.[/]")
        return

    # 5. Notes operations
    if args.note:
        sym, text = args.note
        save_note(sym, text, tags=["cli"])
        console.print(f"[bold green]✓ Note saved for {sym.upper()}:[/] {text}")
        return

    if args.notes:
        all_notes = load_notes()
        if args.notes == "__ALL__":
            if not all_notes:
                console.print("[dim]No notes recorded yet.[/]")
            else:
                for sym, entries in all_notes.items():
                    console.print(f"\n[bold gold1]📝 Notes for {sym}:[/]")
                    for e in entries:
                        console.print(f"  • [{e.get('timestamp')}] {e.get('text')}")
        else:
            sym_entries = get_symbol_notes(args.notes)
            if not sym_entries:
                console.print(f"[dim]No notes for {args.notes.upper()}.[/]")
            else:
                console.print(f"[bold gold1]📝 Notes for {args.notes.upper()}:[/]")
                for e in sym_entries:
                    console.print(f"  • [{e.get('timestamp')}] {e.get('text')}")
        return

    # 6. Stock Detail View
    if args.detail:
        tracker = StockDataTracker(args.detail)
        if not args.sim:
            quotes = fetch_live_quotes([tracker.symbol], timeout=2.0)
            if quotes and tracker.symbol in quotes:
                tracker.update_from_quote(quotes[tracker.symbol])
        layout = render_stock_detail(tracker, palette=args.palette)
        console.print(layout)
        return

    # 7. Boss Mode Standalone
    if args.boss:
        view = render_boss_view(args.boss_profile)
        console.print(view)
        return

    # Resolve active symbols
    symbols_list = args.symbols.split(",") if args.symbols else load_watchlist()
    trackers = [StockDataTracker(s) for s in symbols_list]

    # Fetch quotes if live mode
    is_live = False
    if not args.sim:
        quotes = fetch_live_quotes(symbols_list, timeout=2.0)
        if quotes:
            is_live = True
            for tr in trackers:
                if tr.symbol in quotes:
                    tr.update_from_quote(quotes[tr.symbol])

    # 8. Export Daily Review Report
    if args.export_daily:
        notes = load_notes()
        portfolio = load_portfolio()
        report = export_daily_review(trackers, notes, portfolio, output_path=args.export_daily)
        console.print(f"[bold green]✓ Daily Review report exported to {args.export_daily}[/]")
        return

    # 9. Print Snapshot Mode
    if args.print:
        # Check alerts
        triggered = evaluate_alerts([tr.to_dict() for tr in trackers], trigger_notification=False)
        table = create_stock_table(
            trackers,
            palette=args.palette,
            is_live=is_live,
            sort_by=args.sort,
            reverse=(not args.asc),
            alerts_triggered=triggered,
        )
        console.print(table)
        return

    # 10. Live Watch Loop Mode (Rich Live)
    if args.watch:
        try:
            with Live(console=console, screen=True, refresh_per_second=int(1 / max(0.1, args.interval))) as live:
                while True:
                    is_live = False
                    if not args.sim:
                        quotes = fetch_live_quotes(symbols_list, timeout=1.5)
                        if quotes:
                            is_live = True
                            for tr in trackers:
                                if tr.symbol in quotes:
                                    tr.update_from_quote(quotes[tr.symbol])
                                else:
                                    tr.tick_simulation()
                        else:
                            for tr in trackers:
                                tr.tick_simulation()
                    else:
                        for tr in trackers:
                            tr.tick_simulation()

                    triggered = evaluate_alerts([tr.to_dict() for tr in trackers], trigger_notification=True)
                    tbl = create_stock_table(
                        trackers,
                        palette=args.palette,
                        is_live=is_live,
                        sort_by=args.sort,
                        reverse=(not args.asc),
                        alerts_triggered=triggered,
                    )
                    live.update(tbl)
                    time.sleep(args.interval)
        except KeyboardInterrupt:
            pass
        return

    # 11. Default Interactive TUI Mode (Textual)
    app = StockTerminalApp(
        symbols=symbols_list,
        palette=args.palette,
        use_real_data=(not args.sim),
        refresh_interval=args.interval,
    )
    app.run()



if __name__ == "__main__":
    main()
