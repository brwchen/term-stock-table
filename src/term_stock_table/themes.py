"""Theme Ecosystem and Color Palette Presets module.
Provides:
- Bloomberg Terminal Classic (Amber/Orange on Deep Charcoal)
- Tokyo Night (Deep Indigo, Cyan & Neon Pastel)
- Catppuccin Mocha (Smooth Pastel Dark)
- Cyberpunk Neon (Electric Pink & Neon Green)
- Nord Polar (Frost Ice & Polar Night)
- Gruvbox Dark (Warm Retro Earth)
- Standard CN / US Themes
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class ThemeColors:
    """Color styling tokens for terminal components."""
    name: str
    description: str
    up_color: str         # Color when price rises
    down_color: str       # Color when price falls
    flat_color: str       # Color when flat
    header_style: str     # Style for table headers
    border_style: str     # Style for panel / table borders
    title_style: str      # Style for panel titles
    accent_style: str     # Highlight / callout style
    dim_style: str        # Secondary text / timestamp style
    badge_bg: str         # Badge background


THEMES: Dict[str, ThemeColors] = {
    "bloomberg": ThemeColors(
        name="bloomberg",
        description="Bloomberg Classic Terminal (Amber & Charcoal)",
        up_color="bright_green",
        down_color="bright_red",
        flat_color="dark_orange",
        header_style="bold black on dark_orange",
        border_style="dark_orange",
        title_style="bold dark_orange",
        accent_style="bold gold1",
        dim_style="grey62",
        badge_bg="grey15",
    ),
    "tokyonight": ThemeColors(
        name="tokyonight",
        description="Tokyo Night (Midnight Indigo & Pastel)",
        up_color="bright_red",
        down_color="bright_green",
        flat_color="cyan",
        header_style="bold bright_white on color(24)",
        border_style="cyan",
        title_style="bold bright_magenta",
        accent_style="bold deep_sky_blue1",
        dim_style="color(103)",
        badge_bg="color(235)",
    ),
    "catppuccin": ThemeColors(
        name="catppuccin",
        description="Catppuccin Mocha (Soothing Pastel Dark)",
        up_color="color(211)",      # Maroon / Pinkish Red
        down_color="color(120)",     # Mint Green
        flat_color="color(223)",     # Flamingo
        header_style="bold black on color(183)", # Mauve header
        border_style="color(117)",   # Sapphire
        title_style="bold color(219)",
        accent_style="bold color(215)", # Peach
        dim_style="color(244)",
        badge_bg="color(234)",
    ),
    "cyberpunk": ThemeColors(
        name="cyberpunk",
        description="Cyberpunk Neon (Electric Pink & Neon Lime)",
        up_color="bold bright_red",
        down_color="bold bright_green",
        flat_color="bold bright_yellow",
        header_style="bold black on bright_yellow",
        border_style="bright_magenta",
        title_style="bold bright_cyan",
        accent_style="bold bright_magenta",
        dim_style="bright_black",
        badge_bg="black",
    ),
    "nord": ThemeColors(
        name="nord",
        description="Nord Polar (Arctic Frost & Polar Night)",
        up_color="color(167)",       # Aurora Red
        down_color="color(108)",      # Aurora Green
        flat_color="color(110)",      # Frost Cyan
        header_style="bold white on color(24)",
        border_style="color(110)",
        title_style="bold color(117)",
        accent_style="bold color(222)", # Aurora Yellow
        dim_style="color(242)",
        badge_bg="color(236)",
    ),
    "gruvbox": ThemeColors(
        name="gruvbox",
        description="Gruvbox Dark (Warm Retro Earthy Tone)",
        up_color="color(167)",       # Gruvbox Red
        down_color="color(142)",      # Gruvbox Green
        flat_color="color(214)",      # Gruvbox Orange
        header_style="bold black on color(214)",
        border_style="color(172)",
        title_style="bold color(220)",
        accent_style="bold color(208)",
        dim_style="color(243)",
        badge_bg="color(237)",
    ),
    "classic_cn": ThemeColors(
        name="classic_cn",
        description="Classic Chinese Market (Red Up / Green Down)",
        up_color="red",
        down_color="green",
        flat_color="yellow",
        header_style="bold bright_white on dark_blue",
        border_style="bright_blue",
        title_style="bold bright_white",
        accent_style="bold yellow",
        dim_style="dim",
        badge_bg="grey19",
    ),
    "classic_us": ThemeColors(
        name="classic_us",
        description="Classic US Market (Green Up / Red Down)",
        up_color="green",
        down_color="red",
        flat_color="yellow",
        header_style="bold bright_white on dark_blue",
        border_style="bright_blue",
        title_style="bold bright_white",
        accent_style="bold yellow",
        dim_style="dim",
        badge_bg="grey19",
    ),
}


class ThemeManager:
    """Manages active theme and color styling queries."""

    def __init__(self, theme_name: str = "classic_cn"):
        self.set_theme(theme_name)

    def set_theme(self, theme_name: str) -> ThemeColors:
        key = theme_name.lower().replace("-", "_")
        if key in THEMES:
            self.current_theme = THEMES[key]
        elif key == "cn":
            self.current_theme = THEMES["classic_cn"]
        elif key == "us":
            self.current_theme = THEMES["classic_us"]
        else:
            self.current_theme = THEMES["classic_cn"]
        return self.current_theme

    def get_color(self, value: float) -> str:
        """Get positive / negative / flat color based on value."""
        if value > 0:
            return self.current_theme.up_color
        elif value < 0:
            return self.current_theme.down_color
        return self.current_theme.flat_color

    @staticmethod
    def list_themes() -> List[str]:
        return list(THEMES.keys())
