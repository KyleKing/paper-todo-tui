import os
from dataclasses import dataclass
from enum import StrEnum


class ThemeMode(StrEnum):
    DARK = "dark"
    LIGHT = "light"


@dataclass(frozen=True)
class CatppuccinPalette:
    base: str
    surface: str
    overlay: str
    text: str
    subtext: str
    green: str
    blue: str
    yellow: str
    red: str
    mauve: str


MACCHIATO = CatppuccinPalette(
    base="#24273a",
    surface="#363a4f",
    overlay="#494d64",
    text="#cad3f5",
    subtext="#a5adcb",
    green="#a6da95",
    blue="#8aadf4",
    yellow="#eed49f",
    red="#ed8796",
    mauve="#c6a0f6",
)

LATTE = CatppuccinPalette(
    base="#faf4ed",
    surface="#f2e9e1",
    overlay="#dcd0c5",
    text="#575279",
    subtext="#797593",
    green="#56949f",
    blue="#286983",
    yellow="#ea9d34",
    red="#b4637a",
    mauve="#907aa9",
)

PALETTES = {
    ThemeMode.DARK: MACCHIATO,
    ThemeMode.LIGHT: LATTE,
}


def _detect_terminal_theme() -> ThemeMode | None:
    if (colorfgbg := os.environ.get("COLORFGBG")):
        parts = colorfgbg.split(";")
        if len(parts) >= 2:
            try:
                bg = int(parts[-1])
                if bg in (0, 8):
                    return ThemeMode.DARK
                if bg in (7, 15):
                    return ThemeMode.LIGHT
            except ValueError:
                pass

    if os.environ.get("TERM_PROGRAM") in ("iTerm.app", "Apple_Terminal", "Hyper", "WezTerm"):
        return ThemeMode.DARK

    return None


def detect_system_theme() -> ThemeMode:
    if (env_scheme := os.environ.get("COLORSCHEME")):
        return ThemeMode.LIGHT if "light" in env_scheme.lower() else ThemeMode.DARK

    if (terminal_theme := _detect_terminal_theme()):
        return terminal_theme

    return ThemeMode.DARK


def get_palette(mode: ThemeMode) -> CatppuccinPalette:
    return PALETTES[mode]
