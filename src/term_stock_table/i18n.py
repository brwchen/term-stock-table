"""Minimal English / Chinese UI translation layer."""
from typing import Dict

LANGS = ("en", "zh")
_lang = "en"

STRINGS: Dict[str, Dict[str, str]] = {
    "en": {
        "app_title": "term-stock-table (Professional Financial Workstation)",
        "lang_switched": "Language: English",
        # table
        "col_symbol": "Symbol", "col_name": "Name", "col_price": "Price", "col_change_pct": "Change%",
        "col_change": "Change", "col_amplitude": "Amp%", "col_turnover": "Turnover%", "col_volume": "Volume",
        "col_amount": "Amount", "col_pe": "P/E", "col_bollinger": "Bollinger (%b)",
        "col_trend": "Real-time Trend (Sparkline)",
        "tag_live": "● LIVE QUOTE (Tencent API)", "tag_sim": "○ SIMULATION ENGINE",
        "table_title": "TERM-STOCK-TABLE FINANCIAL TERMINAL",
        "sentiment": "Market: [bold green]▲ {up_count} Up[/] | [bold red]▼ {down} Down[/] | [bold white]- {flat} Flat[/] (Total: {total})",
        "sentiment_cn_colors": "Market: [bold red]▲ {up_count} Up[/] | [bold green]▼ {down} Down[/] | [bold white]- {flat} Flat[/] (Total: {total})",
        "caption_keys": "[bold cyan]s[/] Sort | [bold green]P[/] Portfolio | [bold magenta]b[/] Boss Key | [bold cyan]L[/] Language | [bold yellow]q[/] Quit",
        "sort_label": "Sort",
        "desc": "DESC", "asc": "ASC", "default": "default",
        # bindings
        "b_boss": "Boss Key", "b_escape": "Escape", "b_tab": "Next Boss Disguise", "b_enter": "Stock Detail",
        "b_note": "Add Note", "b_alert": "Price Alert", "b_add": "Add Stock", "b_search": "Search/Add",
        "b_delete": "Delete Stock", "b_sort": "Sort Column", "b_reverse": "Reverse Sort",
        "b_themes": "Theme Presets", "b_formulas": "Custom Formulas", "b_radar": "Market Radar",
        "b_sector": "Sector Heatmap", "b_backtest": "Strategy Backtest", "b_portfolio": "Portfolio View",
        "b_palette": "CN/US Palette", "b_lang": "Language 中/EN", "b_quit": "Quit",
        # modals
        "alert_title": "🔔 Set Price Alert for {name} ({symbol})",
        "alert_high": "Target High Price (e.g. 1800.0)", "alert_low": "Stop Low Price (e.g. 1200.0)",
        "alert_pct": "Max Volatility % (e.g. 3.0)",
        "save_alert": "Save Alert (Enter)", "cancel": "Cancel (Esc)", "save": "Save (Enter)", "add": "Add (Enter)",
        "close": "Close (Esc)", "close_enter": "Close (Esc/Enter)", "add_note_btn": "Add Note ('n')",
        "note_title": "📝 Add Investment Note for {name} ({symbol})",
        "add_title": "🔍 Add Stock Symbol (e.g. 600519, 000001, AAPL, NVDA, 00700):",
        "theme_title": "🎨 Choose Color Theme Preset:",
        "formula_title": "📐 Custom Quantitative Formulas:",
        "n_alert_set": "Alert configured for {symbol}!", "n_note_saved": "Note saved for {symbol}!",
        "n_added": "Added {symbol} to watchlist!", "n_exists": "{symbol} already in watchlist.",
        "n_theme": "Theme switched to: {theme}", "n_removed": "Removed {symbol} from watchlist.",
        "n_mode": "Mode: {mode}", "mode_portfolio": "Portfolio Holdings", "mode_watchlist": "Watchlist",
        "n_sorted": "Sorted by: {col}", "n_order": "Order: {order}",
        "order_desc": "Descending (▼)", "order_asc": "Ascending (▲)", "n_palette": "Switched palette to: {palette}",
        # detail
        "p_intraday": "Intraday", "p_m5": "5m", "p_m15": "15m", "p_m30": "30m", "p_m60": "60m",
        "p_day": "Daily", "p_week": "Weekly", "p_month": "Monthly",
        "d_loading": "Loading K-line data...",
        "d_simulated": "Simulated candles (real K-line data unavailable for this period/market)",
        "d_kline": "K-Line",
        "d_volume": "Volume", "d_intraday_volume": "Intraday Volume", "d_curve": "Smooth Price Curve",
        "d_indicators": "Technical & Quant Indicators",
        "d_panel_tech": "📈 Technical Analysis & Curves (click a button or press 1-8 to switch period)",
        "d_panel_book": "📊 5-Level Order Book", "d_panel_flow": "💰 Capital Flow",
        "d_panel_notes": "📝 Investment Notes & Strategy Log (press 'n' to edit)",
        "d_level": "Level", "d_price": "Price", "d_vol_hands": "Vol (Hands)",
        "d_sell": "Sell", "d_buy": "Buy",
        "d_main_net": "Main Net Inflow", "d_super_large": "Super-Large Orders", "d_retail": "Retail Net",
        "d_unit": "×10k",
        "dh_high": "High", "dh_low": "Low", "dh_open": "Open", "dh_prev": "Prev",
        "dh_amp": "Amp", "dh_pe": "P/E", "dh_vol": "Vol", "dh_turn": "Turn", "dh_amt": "Amt",
        "d_avg": "Avg", "d_latest": "Last", "d_book": "Order Book", "d_ticks": "Ticks",
        "d_vol_short": "Vol",
        "d_notes_dt": "Date / Time", "d_notes_tags": "Tags", "d_notes_text": "Investment Logic & Trade Notes",
        "d_no_notes": "No notes recorded yet.",
        "d_no_notes_hint": "Press 'n' in interactive TUI mode to add notes for this stock (e.g. Target price, Stop loss, Catalyst).",
    },
    "zh": {
        "app_title": "term-stock-table（专业金融终端）",
        "lang_switched": "语言：中文",
        "col_symbol": "代码", "col_name": "名称", "col_price": "现价", "col_change_pct": "涨跌幅",
        "col_change": "涨跌额", "col_amplitude": "振幅", "col_turnover": "换手率", "col_volume": "成交量",
        "col_amount": "成交额", "col_pe": "市盈率", "col_bollinger": "布林 (%b)",
        "col_trend": "实时走势",
        "tag_live": "● 实时行情 (腾讯接口)", "tag_sim": "○ 模拟引擎",
        "table_title": "TERM-STOCK-TABLE 金融终端",
        "sentiment": "市场情绪: [bold green]▲ {up_count} 涨[/] | [bold red]▼ {down} 跌[/] | [bold white]- {flat} 平[/] (自选: {total} 只)",
        "sentiment_cn_colors": "市场情绪: [bold red]▲ {up_count} 涨[/] | [bold green]▼ {down} 跌[/] | [bold white]- {flat} 平[/] (自选: {total} 只)",
        "caption_keys": "[bold cyan]s[/] 排序 | [bold green]P[/] 持仓 | [bold magenta]b[/] 老板键 | [bold cyan]L[/] 语言 | [bold yellow]q[/] 退出",
        "sort_label": "排序",
        "desc": "降序", "asc": "升序", "default": "默认",
        "b_boss": "老板键 (摸鱼模式)", "b_escape": "返回", "b_tab": "切换伪装", "b_enter": "股票详情",
        "b_note": "添加笔记", "b_alert": "价格预警", "b_add": "添加股票", "b_search": "搜索/添加",
        "b_delete": "删除股票", "b_sort": "切换排序列", "b_reverse": "反转排序",
        "b_themes": "主题配色", "b_formulas": "自定义公式", "b_radar": "市场雷达",
        "b_sector": "板块热力图", "b_backtest": "策略回测", "b_portfolio": "持仓视图",
        "b_palette": "红涨绿跌/绿涨红跌", "b_lang": "语言 中/EN", "b_quit": "退出",
        "alert_title": "🔔 设置价格预警：{name} ({symbol})",
        "alert_high": "目标高价 (如 1800.0)", "alert_low": "止损低价 (如 1200.0)",
        "alert_pct": "最大波动 % (如 3.0)",
        "save_alert": "保存预警 (Enter)", "cancel": "取消 (Esc)", "save": "保存 (Enter)", "add": "添加 (Enter)",
        "close": "关闭 (Esc)", "close_enter": "关闭 (Esc/Enter)", "add_note_btn": "添加笔记 ('n')",
        "note_title": "📝 添加投资笔记：{name} ({symbol})",
        "add_title": "🔍 添加股票代码 (如 600519, 000001, AAPL, NVDA, 00700):",
        "theme_title": "🎨 选择配色主题:",
        "formula_title": "📐 自定义量化公式:",
        "n_alert_set": "已设置 {symbol} 的预警！", "n_note_saved": "已保存 {symbol} 的笔记！",
        "n_added": "已添加 {symbol} 到自选！", "n_exists": "{symbol} 已在自选中。",
        "n_theme": "主题已切换为: {theme}", "n_removed": "已从自选移除 {symbol}。",
        "n_mode": "模式: {mode}", "mode_portfolio": "持仓", "mode_watchlist": "自选",
        "n_sorted": "排序: {col}", "n_order": "顺序: {order}",
        "order_desc": "降序 (▼)", "order_asc": "升序 (▲)", "n_palette": "配色已切换为: {palette}",
        "p_intraday": "分时", "p_m5": "5分", "p_m15": "15分", "p_m30": "30分", "p_m60": "60分",
        "p_day": "日K", "p_week": "周K", "p_month": "月K",
        "d_loading": "正在加载K线数据...",
        "d_simulated": "模拟K线（该周期/市场暂无真实K线数据）",
        "d_kline": "K线",
        "d_volume": "成交量", "d_intraday_volume": "分时成交量", "d_curve": "平滑价格曲线",
        "d_indicators": "技术与量化指标",
        "d_panel_tech": "📈 技术分析与曲线 (点击按钮或按 1-8 切换周期)",
        "d_panel_book": "📊 五档盘口", "d_panel_flow": "💰 资金流向",
        "d_panel_notes": "📝 投资笔记与策略日志 (按 'n' 编辑)",
        "d_level": "档位", "d_price": "价格", "d_vol_hands": "量 (手)",
        "d_sell": "卖", "d_buy": "买",
        "d_main_net": "主力净流入", "d_super_large": "超大单净额", "d_retail": "散户净额",
        "d_unit": "万",
        "dh_high": "高", "dh_low": "低", "dh_open": "开", "dh_prev": "昨收",
        "dh_amp": "振幅", "dh_pe": "市盈", "dh_vol": "量", "dh_turn": "换", "dh_amt": "额",
        "d_avg": "均价", "d_latest": "最新", "d_book": "五档", "d_ticks": "明细",
        "d_vol_short": "量",
        "d_notes_dt": "日期 / 时间", "d_notes_tags": "标签", "d_notes_text": "投资逻辑与交易笔记",
        "d_no_notes": "暂无笔记。",
        "d_no_notes_hint": "在交互式 TUI 中按 'n' 为该股票添加笔记（如目标价、止损、催化剂）。",
    },
}


def get_lang() -> str:
    return _lang


def set_lang(lang: str) -> str:
    global _lang
    _lang = lang if lang in LANGS else "en"
    return _lang


def toggle_lang() -> str:
    return set_lang("zh" if _lang == "en" else "en")


def t(key: str, **kwargs) -> str:
    text = STRINGS.get(_lang, {}).get(key) or STRINGS["en"].get(key, key)
    return text.format(**kwargs) if kwargs else text
