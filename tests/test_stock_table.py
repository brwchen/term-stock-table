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
from term_stock_table.cli import main as cli_main


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
             patch("term_stock_table.config.NOTES_FILE", test_dir / "notes.json"):

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

            # CLI --print snapshot
            with patch.object(sys, "argv", ["stk", "--print", "--sim"]):
                with patch("sys.stdout", new_callable=io.StringIO):
                    cli_main()

            # CLI --watch mock
            with patch.object(sys, "argv", ["stk", "--watch", "--sim", "--interval", "0.1"]):
                with patch("time.sleep", side_effect=KeyboardInterrupt):
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

