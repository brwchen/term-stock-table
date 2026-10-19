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
)
from .table import create_stock_table
from .detail import render_stock_detail
from .boss import render_boss_view, PROFILES
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
        "--boss", "-b",
        action="store_true",
        help="Launch directly in Boss Mode (摸鱼伪装模式)"
    )
    parser.add_argument(
        "--boss-profile",
        choices=PROFILES,
        default="devops",
        help="Camouflage profile for Boss Mode ('devops', 'kubectl', 'nginx', 'monochrome')"
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

    # 1. Watchlist operations
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

    # 2. Notes operations
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

    # 3. Stock Detail View
    if args.detail:
        tracker = StockDataTracker(args.detail)
        if not args.sim:
            quotes = fetch_live_quotes([tracker.symbol], timeout=2.0)
            if quotes and tracker.symbol in quotes:
                tracker.update_from_quote(quotes[tracker.symbol])
        layout = render_stock_detail(tracker, palette=args.palette)
        console.print(layout)
        return

    # 4. Boss Mode Standalone
    if args.boss:
        view = render_boss_view(args.boss_profile)
        console.print(view)
        return

    # Resolve active symbols
    symbols_list = args.symbols.split(",") if args.symbols else load_watchlist()
    trackers = [StockDataTracker(s) for s in symbols_list]

    # 5. Print Snapshot Mode
    if args.print:
        is_live = False
        if not args.sim:
            quotes = fetch_live_quotes(symbols_list, timeout=2.0)
            if quotes:
                is_live = True
                for tr in trackers:
                    if tr.symbol in quotes:
                        tr.update_from_quote(quotes[tr.symbol])
        table = create_stock_table(trackers, palette=args.palette, is_live=is_live)
        console.print(table)
        return

    # 6. Live Watch Loop Mode (Rich Live)
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

                    tbl = create_stock_table(trackers, palette=args.palette, is_live=is_live)
                    live.update(tbl)
                    time.sleep(args.interval)
        except KeyboardInterrupt:
            pass
        return

    # 7. Default Interactive TUI Mode (Textual)
    app = StockTerminalApp(
        symbols=symbols_list,
        palette=args.palette,
        use_real_data=(not args.sim),
        refresh_interval=args.interval,
    )
    app.run()


if __name__ == "__main__":
    main()
