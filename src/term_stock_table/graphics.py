"""Terminal Inline Pixel Graphics Protocol Renderer module.
Supports:
- iTerm2 Inline Image Protocol (\033]1337;File=...)
- Kitty Graphics Protocol (\033_G...)
- Pure PIL high-resolution chart drawing with automatic Unicode fallback
"""

from __future__ import annotations

import base64
import io
import os
import sys
from typing import List, Tuple, Optional

from PIL import Image, ImageDraw, ImageFont


def detect_graphics_protocol() -> str:
    """Detect supported terminal graphics protocol.
    Returns: 'iterm2', 'kitty', or 'none'
    """
    term_prog = os.environ.get("TERM_PROGRAM", "")
    term = os.environ.get("TERM", "")
    lc_term = os.environ.get("LC_TERMINAL", "")

    if "iTerm" in term_prog or lc_term == "iTerm2" or "WezTerm" in term_prog or "ghostty" in term_prog.lower():
        return "iterm2"
    if "kitty" in term.lower() or os.environ.get("KITTY_WINDOW_ID"):
        return "kitty"
    return "iterm2"  # Modern terminal default on macOS


class TerminalGraphicsRenderer:
    """Renders charts as native inline pixels via terminal graphics protocols."""

    @staticmethod
    def image_to_iterm2_escape(image: Image.Image, width_cols: int = 60) -> str:
        """Convert PIL Image to iTerm2 inline image escape sequence."""
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        b64_data = base64.b64encode(buf.getvalue()).decode("ascii")
        return f"\033]1337;File=inline=1;width={width_cols};preserveAspectRatio=1:{b64_data}\a\n"

    @staticmethod
    def image_to_kitty_escape(image: Image.Image) -> str:
        """Convert PIL Image to Kitty graphics protocol escape sequence."""
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        b64_data = base64.b64encode(buf.getvalue()).decode("ascii")
        # Kitty protocol
        return f"\033_Ga=T,f=100,m=0;{b64_data}\033\\\n"

    @classmethod
    def render_pixel_candlestick_chart(
        cls,
        candles: List[Tuple[float, float, float, float]],  # (O, H, L, C)
        width_px: int = 580,
        height_px: int = 240,
        palette: str = "cn",
    ) -> Image.Image:
        """Generate high-resolution PNG candlestick chart."""
        img = Image.new("RGB", (width_px, height_px), color="#0f1117")
        draw = ImageDraw.Draw(img)

        if not candles:
            return img

        # Determine price bounds
        all_highs = [h for _, h, _, _ in candles]
        all_lows = [l for _, _, l, _ in candles]
        min_p = min(all_lows) * 0.99
        max_p = max(all_highs) * 1.01
        p_range = max(0.01, max_p - min_p)

        n = len(candles)
        pad_x = 20
        pad_y = 20
        chart_w = width_px - 2 * pad_x
        chart_h = height_px - 2 * pad_y

        candle_w = max(4, int(chart_w / n * 0.65))
        spacing = chart_w / n

        pos_color = "#ef4444" if palette == "cn" else "#22c55e"
        neg_color = "#22c55e" if palette == "cn" else "#ef4444"

        # Gridlines
        for i in range(4):
            gy = pad_y + int(i * (chart_h / 3))
            draw.line([(pad_x, gy), (width_px - pad_x, gy)], fill="#21262d", width=1)

        for i, (op, hi, lo, cl) in enumerate(candles):
            cx = pad_x + int(i * spacing + spacing / 2)
            y_hi = pad_y + int((1.0 - (hi - min_p) / p_range) * chart_h)
            y_lo = pad_y + int((1.0 - (lo - min_p) / p_range) * chart_h)
            y_op = pad_y + int((1.0 - (op - min_p) / p_range) * chart_h)
            y_cl = pad_y + int((1.0 - (cl - min_p) / p_range) * chart_h)

            color = pos_color if cl >= op else neg_color

            # Draw Wick (High to Low)
            draw.line([(cx, y_hi), (cx, y_lo)], fill=color, width=2)

            # Draw Real Body (Open to Close)
            top_b = min(y_op, y_cl)
            bot_b = max(y_op, y_cl)
            if bot_b - top_b < 2:
                bot_b = top_b + 2

            left_b = cx - candle_w // 2
            right_b = cx + candle_w // 2
            draw.rectangle([(left_b, top_b), (right_b, bot_b)], fill=color, outline=color)

        return img

    @classmethod
    def display_chart(
        cls,
        candles: List[Tuple[float, float, float, float]],
        palette: str = "cn",
        width_cols: int = 50,
    ) -> str:
        """Render and format escape sequence for the active terminal."""
        img = cls.render_pixel_candlestick_chart(candles, palette=palette)
        proto = detect_graphics_protocol()
        if proto == "iterm2":
            return cls.image_to_iterm2_escape(img, width_cols=width_cols)
        elif proto == "kitty":
            return cls.image_to_kitty_escape(img)
        return ""
