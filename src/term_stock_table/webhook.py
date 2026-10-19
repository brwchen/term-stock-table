"""Multi-channel Webhook Alert Dispatcher module.
Supports:
- Feishu / Lark Webhook (飞书机器人)
- DingTalk Webhook (钉钉机器人)
- WeCom Webhook (企业微信机器人)
- Telegram Bot API
- Slack Incoming Webhook
- Generic Custom JSON Webhook
"""

from __future__ import annotations

import json
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Dict, Any, Optional

from rich.console import Console
from rich.panel import Panel
from rich.text import Text


@dataclass
class WebhookConfig:
    """Webhook channel configuration."""
    channel_type: str = "generic"  # "feishu", "dingtalk", "wecom", "slack", "telegram", "generic"
    url: str = ""
    token: str = ""
    chat_id: str = ""
    enabled: bool = False


class WebhookDispatcher:
    """Dispatches formatted alert messages to webhook channels."""

    def __init__(self, config: Optional[WebhookConfig] = None):
        self.config = config or WebhookConfig()

    def send_alert_message(self, title: str, content: str) -> bool:
        """Send formatted alert payload to configured endpoint."""
        if not self.config.url and not self.config.token:
            return False

        payload: Dict[str, Any] = {}
        ch = self.config.channel_type.lower()

        if ch in ("feishu", "lark"):
            payload = {
                "msg_type": "text",
                "content": {"text": f"🚨 【Term Stock Alert】{title}\n\n{content}"}
            }
        elif ch == "dingtalk":
            payload = {
                "msg_type": "text",
                "text": {"content": f"🚨 【Term Stock Alert】{title}\n\n{content}"}
            }
        elif ch == "wecom":
            payload = {
                "msgtype": "text",
                "text": {"content": f"🚨 【Term Stock Alert】{title}\n\n{content}"}
            }
        elif ch == "slack":
            payload = {
                "text": f"🚨 *{title}*\n```{content}```"
            }
        elif ch == "telegram":
            url = f"https://api.telegram.org/bot{self.config.token}/sendMessage"
            payload = {
                "chat_id": self.config.chat_id,
                "text": f"🚨 *{title}*\n{content}",
                "parse_mode": "Markdown"
            }
            return self._http_post(url, payload)
        else:  # Generic
            payload = {
                "title": title,
                "message": content,
                "source": "term-stock-table",
            }

        return self._http_post(self.config.url, payload)

    def _http_post(self, url: str, payload: Dict[str, Any]) -> bool:
        """Execute HTTP POST with JSON data."""
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json", "User-Agent": "TermStockTable/0.1.0"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status in (200, 201, 204)
        except Exception:
            return False

    def render_test_preview(self, title: str, content: str) -> Panel:
        """Render Rich panel simulating the sent webhook payload."""
        txt = Text.from_markup(
            f"[bold]渠道类型:[/] [bold cyan]{self.config.channel_type.upper()}[/]\n"
            f"[bold]目标终端:[/] [dim]{self.config.url or 'Mock Test Endpoint'}[/]\n"
            f"[bold]通知标题:[/] [bold yellow]🚨 {title}[/]\n"
            f"[bold]通知内容:[/]\n[bright_white]{content}[/]"
        )
        return Panel(
            txt,
            title="[bold green]📡 Webhook 机器人告警推送预览 (Webhook Dispatch Preview)[/]",
            border_style="green",
            padding=(0, 1),
        )
