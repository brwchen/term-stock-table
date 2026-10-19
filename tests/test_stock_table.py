"""Comprehensive unit tests for term-stock-table."""
import io
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from rich.table import Table

from term_stock_table.api import (
    normalize_symbol_code,
    parse_tencent_line,
    fetch_live_quotes,
    StockDataTracker,
)
from term_stock_table.indicators import (
    compute_sma,
    compute_bollinger_bands,
    render_bollinger_badge,
    compute_rsi,
)
from term_stock_table.config import (
    load_watchlist,
    save_watchlist,
    add_to_watchlist,
    remove_from_watchlist,
    load_notes,
    save_note,
    get_symbol_notes,
    load_settings,
    save_settings,
)
from term_stock_table.table import (
    create_stock_table,
    format_volume,
    format_amount,
)
from term_stock_table.detail import render_stock_detail
from term_stock_table.boss import (
    render_boss_view,
    render_devops_top,
    render_kubectl_pods,
    render_nginx_logs,
    render_monochrome_table,
    PROFILES,
)
from term_stock_table.portfolio import calculate_portfolio_pnl, create_portfolio_table
from term_stock_table.alerts import evaluate_alerts, send_desktop_notification
from term_stock_table.indicators import (
    compute_macd,
    compute_kdj,
    render_candlestick_chart,
    estimate_valuation_percentile,
)
from term_stock_table.market import (
    render_indices_banner,
    simulate_capital_flow,
    render_capital_flow_panel,
)
from term_stock_table.boss import (
    render_boss_view,
    render_devops_top,
    render_kubectl_pods,
    render_nginx_logs,
    render_cpp_build,
    render_git_diff,
    render_python_train,
    render_monochrome_table,
    export_daily_review,
    PROFILES,
)
from term_stock_table.config import (
    load_portfolio,
    save_position,
    remove_position,
    load_alerts,
    save_alert,
    remove_alert,
)
from term_stock_table.cli import main as cli_main


def test_portfolio_and_pnl():
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir)
        with patch("term_stock_table.config.DEFAULT_CONFIG_DIR", test_dir), \
             patch("term_stock_table.config.PORTFOLIO_FILE", test_dir / "portfolio.json"):
            
            assert load_portfolio() == {}
            save_position("600519", 100, 1300.0)
            port = load_portfolio()
            assert "600519" in port
            assert port["600519"]["shares"] == 100
            assert port["600519"]["cost"] == 1300.0

            quotes = [{"symbol": "600519", "name": "贵州茅台", "price": 1350.0, "change": 10.0, "change_pct": 0.75}]
            pnl_data = calculate_portfolio_pnl(quotes, port)
            assert pnl_data["total_market_val"] == 135000.0
            assert pnl_data["total_cost"] == 130000.0
            assert pnl_data["total_float_pnl"] == 5000.0
            assert pnl_data["total_today_pnl"] == 1000.0

            tbl = create_portfolio_table(pnl_data, palette="cn")
            assert isinstance(tbl, Table)

            assert remove_position("600519") is True
            assert remove_position("600519") is False


def test_alerts_and_desktop_notifications():
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir)
        with patch("term_stock_table.config.DEFAULT_CONFIG_DIR", test_dir), \
             patch("term_stock_table.config.ALERTS_FILE", test_dir / "alerts.json"):

            assert load_alerts() == {}
            save_alert("600519", target_high=1400.0, target_low=1200.0, max_change_pct=2.0)
            alerts = load_alerts()
            assert "600519" in alerts

            quotes = [{"symbol": "600519", "name": "贵州茅台", "price": 1450.0, "change_pct": 2.5}]
            with patch("term_stock_table.alerts.send_desktop_notification") as mock_notif:
                triggered = evaluate_alerts(quotes, alerts, trigger_notification=True)
                assert "600519" in triggered
                assert len(triggered["600519"]) == 2  # high target + max change
                assert mock_notif.called

            assert remove_alert("600519") is True
            assert remove_alert("600519") is False

            # Test notification safe run
            send_desktop_notification("Test", "Safe message")


def test_advanced_indicators_macd_kdj_candle():
    prices = [10.0 + (i % 5) for i in range(30)]
    dif, dea, hist = compute_macd(prices)
    assert len(dif) == len(prices)
    assert len(dea) == len(prices)
    assert len(hist) == len(prices)

    k, d, j = compute_kdj(prices)
    assert len(k) == len(prices)
    assert len(d) == len(prices)
    assert len(j) == len(prices)

    candles = [
        {"open": 10.0, "high": 12.0, "low": 9.5, "close": 11.5},
        {"open": 11.5, "high": 13.0, "low": 11.0, "close": 12.8},
        {"open": 12.8, "high": 13.0, "low": 10.0, "close": 10.2},
    ]
    chart = render_candlestick_chart(candles, height=5, palette="cn")
    assert "│" in chart
    assert "█" in chart or "░" in chart

    pct, status, badge = estimate_valuation_percentile(18.5)
    assert 0 <= pct <= 100
    assert "Reasonable" in status or "Fair" in status
    assert "●" in badge


def test_market_indices_and_capital_flow():
    banner = render_indices_banner(palette="cn")
    assert banner is not None

    flow = simulate_capital_flow("600519", 1350.0, 50000)
    assert "super_large" in flow
    assert "main_net" in flow
    panel = render_capital_flow_panel(flow, palette="cn")
    assert panel is not None


def test_boss_modes_and_daily_export():
    assert render_cpp_build() is not None
    assert render_git_diff() is not None
    assert render_python_train() is not None

    trackers = [StockDataTracker("600519"), StockDataTracker("AAPL")]
    notes = {"600519": [{"timestamp": "2026-10-19 12:00:00", "text": "Hold for long term"}]}
    portfolio = {"600519": {"shares": 100, "cost": 1300.0}}
    
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
        tmp_path = f.name
    try:
        report = export_daily_review(trackers, notes, portfolio, output_path=tmp_path)
        assert "Daily Financial Review" in report
        assert "600519" in report
        assert "Hold for long term" in report
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)



def test_normalize_symbol_code():
    assert normalize_symbol_code("600519") == "sh600519"
    assert normalize_symbol_code("688981") == "sh688981"
    assert normalize_symbol_code("000001") == "sz000001"
    assert normalize_symbol_code("300750") == "sz300750"
    assert normalize_symbol_code("00700") == "hk00700"
    assert normalize_symbol_code("aapl") == "usAAPL"
    assert normalize_symbol_code("NVDA") == "usNVDA"
    assert normalize_symbol_code("sh600519") == "sh600519"


def test_parse_tencent_line():
    code_map = {"sh600519": "600519"}
    line = 'v_sh600519="1~贵州茅台~600519~1324.97~1329.00~1322.50~39729~22926~16803~1324.97~11~1324.96~21~1324.90~1~1324.31~1~1324.20~1~1324.99~4~1325.00~19~1325.04~1~1325.05~1~1325.80~1~~20261019161457~-4.03~-0.30~1348.60~1321.00~1324.97/39729/5308935919~39729~530894~0.32~20.34~~1348.60~1321.00~2.08~16563.21~16563.21~6.59~1461.90~1196.10~1.12~9~1336.29~18.60~20.12~~~0.04~530893.5919~264.9940~20~   A~GP-A~-1.79~2.87~3.93~32.41~27.30~1539.98~1151.01~6.52~3.91~5.74~1250081601~1250081601~14.75~-2.64~1250081601~~~-5.56~0.00~~CNY~0~___D__F__N~1326.00~-20~";'
    parsed = parse_tencent_line(line, code_map)
    assert parsed is not None
    assert parsed["symbol"] == "600519"
    assert parsed["name"] == "贵州茅台"
    assert parsed["price"] == 1324.97
    assert parsed["prev_close"] == 1329.00
    assert parsed["change"] == -4.03
    assert parsed["change_pct"] == -0.30
    assert len(parsed["bids"]) > 0
    assert len(parsed["asks"]) > 0

    # Invalid lines
    assert parse_tencent_line("", code_map) is None
    assert parse_tencent_line("invalid", code_map) is None
    assert parse_tencent_line("v_sh123=invalid_parts", code_map) is None


def test_fetch_live_quotes_mocked():
    assert fetch_live_quotes([]) == {}

    mock_resp = MagicMock()
    mock_resp.read.return_value = (
        'v_sh600519="1~贵州茅台~600519~1324.97~1329.00~1322.50~39729~...~32~-0.30~";'
    ).encode("gbk")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        quotes = fetch_live_quotes(["600519"])
        assert "600519" in quotes
        assert quotes["600519"]["price"] == 1324.97

    # Network exception fallback
    with patch("urllib.request.urlopen", side_effect=Exception("Timeout")):
        assert fetch_live_quotes(["600519"]) == {}


def test_stock_data_tracker():
    tr = StockDataTracker("600519")
    assert tr.symbol == "600519"
    assert tr.name == "贵州茅台"
    assert len(tr.prices) > 0

    # Test simulation tick
    old_len = len(tr.prices)
    tr.tick_simulation()
    assert len(tr.prices) == old_len
    assert len(tr.bids) == 5
    assert len(tr.asks) == 5

    # Test update from quote
    mock_quote = {
        "name": "贵州茅台",
        "price": 1330.00,
        "prev_close": 1329.00,
        "open": 1325.00,
        "high": 1335.00,
        "low": 1320.00,
        "volume": 50000,
        "amount": 600000.0,
        "turnover_rate": 0.45,
        "pe": 21.0,
        "pb": 6.8,
        "amplitude": 1.2,
        "bids": [(1329.5, 100)],
        "asks": [(1330.5, 200)],
    }
    tr.update_from_quote(mock_quote)
    assert tr.price == 1330.00
    assert tr.change == 1.00
    assert round(tr.change_pct, 2) == 0.08
    assert tr.is_real is True


def test_indicators_sma_and_bollinger():
    assert compute_sma([], 5) == []
    assert compute_sma([10, 20], 0) == []
    sma = compute_sma([10, 20, 30, 40, 50], 3)
    assert sma[0] is None
    assert sma[2] == 20.0
    assert sma[4] == 40.0

    # Bollinger Bands
    assert compute_bollinger_bands([]) == (None, None, None, None, None)
    assert compute_bollinger_bands([10]) == (None, None, None, None, None)

    prices = [10.0 + i for i in range(25)]
    upper, mid, lower, pct_b, b_width = compute_bollinger_bands(prices, window=20)
    assert upper > mid > lower
    assert pct_b is not None
    assert b_width > 0

    # Bollinger Badge
    assert render_bollinger_badge(None) == "[-----]"
    assert "▶" in render_bollinger_badge(1.2, palette="cn")
    assert "◀" in render_bollinger_badge(-0.2, palette="cn")
    assert "●" in render_bollinger_badge(0.5, palette="cn")
    assert "●" in render_bollinger_badge(0.9, palette="us")
    assert "●" in render_bollinger_badge(0.1, palette="us")


def test_indicators_rsi():
    assert compute_rsi([]) == []
    assert compute_rsi([10]) == [50.0]
    prices = [10, 12, 11, 14, 15, 13, 16, 18, 17, 19, 20, 22, 21, 23, 25, 24]
    rsi = compute_rsi(prices, period=5)
    assert len(rsi) == len(prices)
    assert 0 <= rsi[-1] <= 100


def test_format_helpers():
    assert format_volume(120_000_000) == "1.20亿"
    assert format_volume(50_000) == "5.00万"
    assert format_volume(800) == "800"

    assert format_amount(250_000) == "2.50亿"
    assert format_amount(25_000) == "2.50万"
    assert format_amount(5_000) == "5000.0万"
    assert format_amount(500) == "500.0"


def test_config_watchlist_and_notes():
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir)
        with patch("term_stock_table.config.DEFAULT_CONFIG_DIR", test_dir), \
             patch("term_stock_table.config.WATCHLIST_FILE", test_dir / "watchlist.json"), \
             patch("term_stock_table.config.NOTES_FILE", test_dir / "notes.json"), \
             patch("term_stock_table.config.SETTINGS_FILE", test_dir / "settings.json"):

            # Watchlist tests
            wl = load_watchlist()
            assert len(wl) > 0
            assert add_to_watchlist("TSLA") is True
            assert add_to_watchlist("TSLA") is False  # duplicate
            assert "TSLA" in load_watchlist()
            assert remove_from_watchlist("TSLA") is True
            assert "TSLA" not in load_watchlist()

            # Notes tests
            assert load_notes() == {}
            save_note("600519", "Target price 1800", tags=["core"])
            notes_600519 = get_symbol_notes("600519")
            assert len(notes_600519) == 1
            assert notes_600519[0]["text"] == "Target price 1800"

            # Settings tests
            s = load_settings()
            assert s["palette"] == "cn"
            s["palette"] = "us"
            save_settings(s)
            assert load_settings()["palette"] == "us"


def test_table_and_detail_rendering():
    trackers = [StockDataTracker("600519"), StockDataTracker("AAPL")]
    
    # CN Palette Table
    table_cn = create_stock_table(trackers, palette="cn", monochrome=False, is_live=True)
    assert isinstance(table_cn, Table)

    # US Palette Table
    table_us = create_stock_table(trackers, palette="us", monochrome=False, is_live=False)
    assert isinstance(table_us, Table)

    # Monochrome Table
    table_mono = create_stock_table(trackers, monochrome=True)
    assert isinstance(table_mono, Table)

    # Stock Detail View Layout
    layout = render_stock_detail(trackers[0], palette="cn")
    assert layout is not None


def test_boss_mode_profiles():
    for prof in PROFILES:
        res = render_boss_view(prof, trackers=[StockDataTracker("600519")])
        assert res is not None

    assert render_devops_top() is not None
    assert render_kubectl_pods() is not None
    assert render_nginx_logs() is not None
    assert render_monochrome_table([StockDataTracker("600519")]) is not None


def test_cli_commands():
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir)
        with patch("term_stock_table.config.DEFAULT_CONFIG_DIR", test_dir), \
             patch("term_stock_table.config.WATCHLIST_FILE", test_dir / "watchlist.json"), \
             patch("term_stock_table.config.NOTES_FILE", test_dir / "notes.json"), \
             patch("term_stock_table.cli.StockTerminalApp"):

            # CLI --add and --list
            with patch.object(sys, "argv", ["stk", "--add", "TSLA"]):
                with patch("sys.stdout", new_callable=io.StringIO):
                    cli_main()

            with patch.object(sys, "argv", ["stk", "--list"]):
                with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                    cli_main()
                    assert "TSLA" in mock_out.getvalue()

            # CLI --remove
            with patch.object(sys, "argv", ["stk", "--remove", "TSLA"]):
                with patch("sys.stdout", new_callable=io.StringIO):
                    cli_main()

            # CLI --note and --notes
            with patch.object(sys, "argv", ["stk", "--note", "600519", "Buy dip"]):
                with patch("sys.stdout", new_callable=io.StringIO):
                    cli_main()

            with patch.object(sys, "argv", ["stk", "--notes"]):
                with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                    cli_main()
                    assert "Buy dip" in mock_out.getvalue()

            # CLI --detail
            with patch.object(sys, "argv", ["stk", "--detail", "600519", "--sim"]):
                with patch("sys.stdout", new_callable=io.StringIO):
                    cli_main()

            # CLI --boss
            with patch.object(sys, "argv", ["stk", "--boss", "--boss-profile", "kubectl"]):
                with patch("sys.stdout", new_callable=io.StringIO):
                    cli_main()

            # CLI --indices
            with patch.object(sys, "argv", ["stk", "--indices"]):
                with patch("sys.stdout", new_callable=io.StringIO):
                    cli_main()

            # CLI --position and --portfolio
            with patch.object(sys, "argv", ["stk", "--position", "600519", "100", "1350.0"]):
                with patch("sys.stdout", new_callable=io.StringIO):
                    cli_main()

            with patch.object(sys, "argv", ["stk", "--portfolio", "--sim"]):
                with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                    cli_main()
                    assert "PORTFOLIO" in mock_out.getvalue()

            with patch.object(sys, "argv", ["stk", "--remove-position", "600519"]):
                with patch("sys.stdout", new_callable=io.StringIO):
                    cli_main()

            # CLI --alert and --alerts
            with patch.object(sys, "argv", ["stk", "--alert", "600519", "high=1800", "low=1200", "pct=3.0"]):
                with patch("sys.stdout", new_callable=io.StringIO):
                    cli_main()

            with patch.object(sys, "argv", ["stk", "--alerts"]):
                with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                    cli_main()
                    assert "600519" in mock_out.getvalue()

            with patch.object(sys, "argv", ["stk", "--remove-alert", "600519"]):
                with patch("sys.stdout", new_callable=io.StringIO):
                    cli_main()

            # CLI --export-daily
            with patch.object(sys, "argv", ["stk", "--export-daily", "test_report.md", "--sim"]):
                with patch("sys.stdout", new_callable=io.StringIO):
                    cli_main()

            # CLI --print snapshot with sorting
            with patch.object(sys, "argv", ["stk", "--print", "--sim", "--sort", "change_pct", "--asc"]):
                with patch("sys.stdout", new_callable=io.StringIO):
                    cli_main()

            # CLI --watch mock
            with patch("term_stock_table.cli.Live") as mock_live_cls:
                mock_instance = MagicMock()
                mock_live_cls.return_value.__enter__.return_value = mock_instance
                with patch("term_stock_table.cli.time.sleep", side_effect=KeyboardInterrupt), \
                     patch("time.sleep", side_effect=KeyboardInterrupt):
                    with patch.object(sys, "argv", ["stk", "--watch", "--sim", "--interval", "0.1"]):
                        with patch("sys.stdout", new_callable=io.StringIO):
                            cli_main()


def test_tui_app_actions():
    from term_stock_table.tui import StockTerminalApp, NoteModal, AddStockModal, DetailModal

    app = StockTerminalApp(symbols=["600519", "AAPL"], palette="cn", use_real_data=False)
    
    # Test boss mode toggling
    assert app.is_boss_mode is False
    app.action_toggle_boss()
    assert app.is_boss_mode is True
    app.action_cycle_boss_profile()
    assert app.boss_profile_idx == 1
    app.action_toggle_boss()
    assert app.is_boss_mode is False

    # Test palette toggle
    assert app.palette == "cn"
    app.action_toggle_palette()
    assert app.palette == "us"

    # Test market data refresh (simulated)
    app.refresh_market_data()
    assert len(app.trackers) == 2

    # Test market data refresh (real data mocked)
    app.use_real_data = True
    mock_quotes = {
        "600519": {"name": "贵州茅台", "price": 1335.0, "prev_close": 1329.0},
    }
    with patch("term_stock_table.tui.fetch_live_quotes", return_value=mock_quotes):
        app.refresh_market_data()
        assert app.is_live is True
        assert app.trackers[0].price == 1335.0

    # Test modals
    note_modal = NoteModal("600519", "贵州茅台")
    assert note_modal.symbol == "600519"

    add_modal = AddStockModal()
    assert add_modal is not None

    detail_modal = DetailModal(app.trackers[0], palette="cn")
    assert detail_modal.tracker.symbol == "600519"


def test_radar_and_anomaly():
    from term_stock_table.radar import MarketRadarTracker, MarketSentiment, AnomalyEvent

    radar = MarketRadarTracker(palette="cn")
    panel = radar.get_sentiment_panel()
    assert panel is not None

    tbl = radar.get_anomaly_table()
    assert tbl is not None

    full_view = radar.render_full_radar_view()
    assert full_view is not None

    ev = AnomalyEvent("14:30:00", "300750", "宁德时代", "🚀 火箭发射", 258.4, +4.82, 3850, "急拉")
    txt_cn = ev.to_colored_text("cn")
    txt_us = ev.to_colored_text("us")
    assert "300750" in txt_cn.plain
    assert "300750" in txt_us.plain


def test_intraday_chips_and_tape():
    from term_stock_table.tick import IntradayChartRenderer, ChipProfileRenderer, TickTapeRenderer

    # Intraday
    intra = IntradayChartRenderer("600519", "贵州茅台", 1680.0, palette="cn")
    panel = intra.render_intraday_panel()
    assert panel is not None

    # Chips
    chip = ChipProfileRenderer(1688.0, palette="cn")
    c_panel = chip.render_chip_panel()
    assert c_panel is not None
    assert 0 <= chip.chip_data.profit_ratio <= 100

    # Tape
    tape = TickTapeRenderer(1688.0, palette="cn")
    t_table = tape.render_tape_table()
    assert t_table is not None
    assert len(tape.ticks) > 0


def test_sector_heatmap():
    from term_stock_table.sector import SectorHeatmapTracker

    sec = SectorHeatmapTracker(palette="cn")
    matrix = sec.render_heatmap_matrix()
    assert matrix is not None

    tbl = sec.render_sector_table()
    assert tbl is not None

    full = sec.render_full_sector_view()
    assert full is not None


def test_fundamentals_and_dragon_tiger():
    from term_stock_table.fundamentals import FundamentalAnalyzer

    fa = FundamentalAnalyzer("600519", "贵州茅台", palette="cn")
    d_panel = fa.render_dupont_panel()
    assert d_panel is not None

    dt_tbl = fa.render_dragon_tiger_table()
    assert dt_tbl is not None
    assert len(fa.seats) > 0


def test_strategy_backtester():
    from term_stock_table.backtest import StrategyBacktester

    bt = StrategyBacktester("300750", "宁德时代", palette="cn")
    res = bt.run_sma_cross_strategy(fast_period=5, slow_period=20)
    assert res.total_trades >= 0
    assert len(res.strategy_curve) > 0

    panel = bt.render_backtest_panel(res)
    assert panel is not None


def test_webhook_dispatcher():
    from term_stock_table.webhook import WebhookDispatcher, WebhookConfig

    cfg = WebhookConfig(channel_type="feishu", url="https://open.feishu.cn/mock", enabled=True)
    dispatcher = WebhookDispatcher(cfg)

    preview = dispatcher.render_test_preview("突破告警", "宁德时代突破255")
    assert preview is not None

    # Test disabled/empty send
    d_empty = WebhookDispatcher(WebhookConfig())
    assert d_empty.send_alert_message("title", "content") is False


def test_portfolio_importer_exporter():
    from term_stock_table.importer import PortfolioDataImporter
    from term_stock_table.portfolio import Position

    sample_csv = "symbol,name,shares,cost_price,notes\n600519,贵州茅台,100,1420.50,核心持仓\n300750,宁德时代,300,240.00,新能源"
    positions = PortfolioDataImporter.import_from_csv(sample_csv)
    assert len(positions) == 2
    assert positions[0].symbol == "600519"
    assert positions[0].shares == 100
    assert positions[0].cost_price == 1420.50

    exported_csv = PortfolioDataImporter.export_to_csv(positions)
    assert "600519" in exported_csv

    exported_md = PortfolioDataImporter.export_to_markdown(positions)
    assert "贵州茅台" in exported_md


def test_statusline_formatter():
    from term_stock_table.statusline import StatuslineFormatter

    tracker = StockDataTracker("600519")
    fmt = StatuslineFormatter(tracker, palette="cn")

    ansi_line = fmt.format_statusline(["600519"], use_ansi=True)
    assert "贵州茅台" in ansi_line
    assert "\033[" in ansi_line

    plain_line = fmt.format_statusline(["600519"], use_ansi=False)
    assert "贵州茅台" in plain_line
    assert "\033[" not in plain_line


def test_extended_cli_and_boss():
    from term_stock_table.boss import render_neovim_buffer, render_gdb_debugger

    assert render_neovim_buffer() is not None
    assert render_gdb_debugger() is not None

    # Test extended CLI flags
    with patch.object(sys, "argv", ["stk", "--radar"]):
        with patch("sys.stdout", new_callable=io.StringIO):
            cli_main()

    with patch.object(sys, "argv", ["stk", "--sector"]):
        with patch("sys.stdout", new_callable=io.StringIO):
            cli_main()

    with patch.object(sys, "argv", ["stk", "--intraday", "600519"]):
        with patch("sys.stdout", new_callable=io.StringIO):
            cli_main()

    with patch.object(sys, "argv", ["stk", "--chips", "600519"]):
        with patch("sys.stdout", new_callable=io.StringIO):
            cli_main()

    with patch.object(sys, "argv", ["stk", "--tape", "600519"]):
        with patch("sys.stdout", new_callable=io.StringIO):
            cli_main()

    with patch.object(sys, "argv", ["stk", "--dupont", "600519"]):
        with patch("sys.stdout", new_callable=io.StringIO):
            cli_main()

    with patch.object(sys, "argv", ["stk", "--backtest", "300750"]):
        with patch("sys.stdout", new_callable=io.StringIO):
            cli_main()

    with patch.object(sys, "argv", ["stk", "--statusline"]):
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            cli_main()
            assert len(mock_out.getvalue()) > 0

    with patch.object(sys, "argv", ["stk", "--webhook-test"]):
        with patch("sys.stdout", new_callable=io.StringIO):
            cli_main()


def test_theme_manager():
    from term_stock_table.themes import ThemeManager, THEMES

    tm = ThemeManager("bloomberg")
    assert tm.current_theme.name == "bloomberg"
    assert tm.get_color(+1.5) == tm.current_theme.up_color
    assert tm.get_color(-1.5) == tm.current_theme.down_color

    for th in THEMES.keys():
        tm.set_theme(th)
        assert tm.current_theme.name == th

    assert "tokyonight" in ThemeManager.list_themes()


def test_formula_engine():
    from term_stock_table.formula import FormulaManager, CustomFormula, SafeFormulaEvaluator

    ctx = {"OPEN": 100.0, "HIGH": 110.0, "LOW": 95.0, "CLOSE": 105.0, "VOL": 5000, "PRE_CLOSE": 100.0}
    evaluator = SafeFormulaEvaluator(ctx, price_history=[90.0, 95.0, 100.0, 105.0])

    assert evaluator.evaluate("HIGH - LOW") == 15.0
    assert evaluator.evaluate("(HIGH + LOW + CLOSE) / 3") == 103.33333333333333
    assert evaluator.evaluate("MA(CLOSE, 3)") == 100.0
    assert evaluator.evaluate("ABS(-10)") == 10.0

    # Test formula manager
    formulas = FormulaManager.load_formulas()
    assert "TYPICAL_PRICE" in formulas
    tr = StockDataTracker("600519")
    val = FormulaManager.evaluate_tracker(formulas["TYPICAL_PRICE"], tr)
    assert val > 0


def test_tmux_layout_generator():
    from term_stock_table.tmux import TmuxLayoutGenerator

    gen = TmuxLayoutGenerator("test-session", symbols=["600519", "AAPL"])
    script = gen.generate_shell_script()
    assert "tmux" in script
    assert "600519" in script
    assert gen.render_preview_panel() is not None


def test_terminal_graphics():
    from term_stock_table.graphics import TerminalGraphicsRenderer, detect_graphics_protocol

    candles = [(100.0, 105.0, 98.0, 103.0), (103.0, 108.0, 101.0, 107.0)]
    img = TerminalGraphicsRenderer.render_pixel_candlestick_chart(candles)
    assert img.size == (580, 240)

    iterm_seq = TerminalGraphicsRenderer.image_to_iterm2_escape(img)
    assert "\033]1337;File=inline=1" in iterm_seq

    kitty_seq = TerminalGraphicsRenderer.image_to_kitty_escape(img)
    assert "\033_Ga=T" in kitty_seq

    proto = detect_graphics_protocol()
    assert proto in ("iterm2", "kitty", "none")


def test_tui_vim_and_theme_modals():
    from term_stock_table.tui import StockTerminalApp, ThemeModal, FormulaModal

    app = StockTerminalApp(symbols=["600519", "000001", "300750"], theme="tokyonight", use_real_data=False)
    assert app.selected_index == 0

    # Vim j / k
    app.action_cursor_down()
    assert app.selected_index == 1
    app.action_cursor_up()
    assert app.selected_index == 0

    # Vim g / G
    app.action_cursor_bottom()
    assert app.selected_index == 2
    app.action_cursor_top()
    assert app.selected_index == 0

    # Theme and Formula modals
    thm_modal = ThemeModal()
    assert thm_modal is not None
    form_modal = FormulaModal()
    assert form_modal is not None


def test_extended_dim56_cli_commands():
    from term_stock_table.cli import main as cli_main

    with patch.object(sys, "argv", ["stk", "--tmux-layout"]):
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            cli_main()
            assert "Tmux" in mock_out.getvalue()

    with patch.object(sys, "argv", ["stk", "--pixel-chart", "600519", "--sim"]):
        with patch("sys.stdout", new_callable=io.StringIO):
            cli_main()

    with patch.object(sys, "argv", ["stk", "--formula", "TYPICAL_PRICE", "--symbols", "600519"]):
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            cli_main()
            assert "TYPICAL_PRICE" in mock_out.getvalue()





def test_intraday_series_parsing(monkeypatch):
    import io
    import json
    from term_stock_table import api

    payload = {"data": {"sh600519": {"data": {"data": ["0930 10.0 100 1.0", "0931 10.5 250 2.0"]}}}}

    class FakeResp(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(api.urllib.request, "urlopen", lambda *a, **k: FakeResp(json.dumps(payload).encode()))
    assert api.fetch_intraday_series("600519") == [(10.0, 100), (10.5, 150)]


def test_tracker_default_history_and_curve_keeps_spike():
    from term_stock_table.api import StockDataTracker
    from term_stock_table.inline_spark import braille_curve

    tr = StockDataTracker("AAPL")
    assert len(tr.prices) == 200 and tr.prices[-1] == tr.price
    data = [100.0] * 200
    data[100] = 110.0
    flat = braille_curve([100.0] * 200, 8, 1).plain
    assert braille_curve(data, 8, 1).plain != flat
