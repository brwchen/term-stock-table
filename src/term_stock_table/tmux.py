"""Tmux Multi-Pane Trading Floor Workstation Layout Generator module.
Provides:
- 4-Pane split layout: Left (Watchlist), Top-Right (Radar), Mid-Right (Intraday/Sector), Bottom-Right (Tick Tape)
- Automated Tmux session bootstrap and bash script generation
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import List, Optional

from rich.panel import Panel
from rich.text import Text


class TmuxLayoutGenerator:
    """Generates and executes multi-pane Tmux trading room sessions."""

    def __init__(self, session_name: str = "stk-trading", symbols: Optional[List[str]] = None):
        self.session_name = session_name
        self.symbols = symbols or ["600519", "300750", "002594", "AAPL", "NVDA", "00700"]

    def generate_shell_script(self, active_symbol: str = "600519") -> str:
        """Generate ready-to-run bash script for multi-pane tmux workstation."""
        sym_str = ",".join(self.symbols)
        lines = [
            "#!/usr/bin/env bash",
            f"# Tmux 4-Pane Terminal Financial Workstation (Auto-generated)",
            f"SESSION=\"{self.session_name}\"",
            "",
            "# Check if session exists and kill if requested",
            "tmux has-session -t $SESSION 2>/dev/null",
            "if [ $? -eq 0 ]; then",
            "  tmux kill-session -t $SESSION",
            "fi",
            "",
            "# 1. Create main session with Left Pane (Watchlist Table)",
            f"tmux new-session -d -s $SESSION -n 'TradeStation' \"stk --symbols {sym_str} --watch --interval 1.0\"",
            "",
            "# 2. Split vertically for Right Column",
            "tmux split-window -h -t $SESSION:0.0 -p 50",
            "",
            "# 3. Run Top-Right (Market Radar)",
            "tmux send-keys -t $SESSION:0.1 'stk --radar' C-m",
            "",
            "# 4. Split Right Column horizontally for Mid-Right (Sector Heatmap / Intraday)",
            "tmux split-window -v -t $SESSION:0.1 -p 60",
            f"tmux send-keys -t $SESSION:0.2 'stk --intraday {active_symbol}' C-m",
            "",
            "# 5. Split Bottom for Tick Tape",
            "tmux split-window -v -t $SESSION:0.2 -p 45",
            f"tmux send-keys -t $SESSION:0.3 'stk --tape {active_symbol}' C-m",
            "",
            "# Focus on Left Watchlist pane and attach",
            "tmux select-pane -t $SESSION:0.0",
            "tmux attach-session -t $SESSION",
        ]
        return "\n".join(lines)

    def launch(self, active_symbol: str = "600519", dry_run: bool = False) -> str:
        """Launch the tmux session or output script."""
        script_code = self.generate_shell_script(active_symbol)
        if dry_run or not self._is_tmux_available():
            return script_code

        script_path = Path("/tmp/launch_stk_tmux.sh")
        script_path.write_text(script_code, encoding="utf-8")
        os.chmod(script_path, 0o755)
        subprocess.run(["bash", str(script_path)])
        return script_code

    @staticmethod
    def _is_tmux_available() -> bool:
        try:
            res = subprocess.run(["which", "tmux"], capture_output=True)
            return res.returncode == 0
        except Exception:
            return False

    def render_preview_panel(self) -> Panel:
        """Render Rich panel previewing the 4-pane layout map."""
        txt = Text.from_markup(
            f"[bold cyan]┌─────────────────────────┬─────────────────────────┐[/]\n"
            f"[bold cyan]│[/] [bold yellow]Pane 1 (Left 50%):[/]      [bold cyan]│[/] [bold yellow]Pane 2 (Top-Right):[/]     [bold cyan]│[/]\n"
            f"[bold cyan]│[/] • Real-Time Watchlist    [bold cyan]│[/] • Market Breadth Radar   [bold cyan]│[/]\n"
            f"[bold cyan]│[/] • Bollinger Bands Badge  [bold cyan]│[/] • Connect Capital Flow   [bold cyan]│[/]\n"
            f"[bold cyan]│[/] • Vector Sparklines      [bold cyan]├─────────────────────────┤[/]\n"
            f"[bold cyan]│[/] • PnL & Quant Columns    [bold cyan]│[/] [bold yellow]Pane 3 (Mid-Right):[/]     [bold cyan]│[/]\n"
            f"[bold cyan]│[/]                         [bold cyan]│[/] • Intraday VWAP Curve    [bold cyan]│[/]\n"
            f"[bold cyan]│[/]                         [bold cyan]├─────────────────────────┤[/]\n"
            f"[bold cyan]│[/]                         [bold cyan]│[/] [bold yellow]Pane 4 (Bottom-Right):[/]  [bold cyan]│[/]\n"
            f"[bold cyan]│[/]                         [bold cyan]│[/] • Real-Time Tick Tape    [bold cyan]│[/]\n"
            f"[bold cyan]└─────────────────────────┴─────────────────────────┘[/]\n\n"
            f"[bold green]Command:[/] [bold white]stk tmux-launch [symbol][/] [dim](or stk --tmux-layout)[/]"
        )
        return Panel(
            txt,
            title="[bold yellow]🖥️ Tmux 4-Pane 交易室分屏布局预览 (Multi-Pane Trading Station)[/]",
            border_style="yellow",
            padding=(0, 1),
        )
