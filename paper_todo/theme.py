import os
import subprocess
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
    base="#eff1f5",
    surface="#e6e9ef",
    overlay="#ccd0da",
    text="#4c4f69",
    subtext="#6c6f85",
    green="#40a02b",
    blue="#1e66f5",
    yellow="#df8e1d",
    red="#d20f39",
    mauve="#8839ef",
)

PALETTES = {
    ThemeMode.DARK: MACCHIATO,
    ThemeMode.LIGHT: LATTE,
}


def _detect_macos_theme() -> ThemeMode | None:
    try:
        result = subprocess.run(
            ["defaults", "read", "-g", "AppleInterfaceStyle"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0 and "dark" in result.stdout.lower():
            return ThemeMode.DARK
        return ThemeMode.LIGHT
    except (FileNotFoundError, OSError):
        return None


def detect_system_theme() -> ThemeMode:
    if (env_scheme := os.environ.get("COLORSCHEME")):
        return ThemeMode.LIGHT if "light" in env_scheme.lower() else ThemeMode.DARK

    if (macos_theme := _detect_macos_theme()):
        return macos_theme

    return ThemeMode.DARK


def get_palette(mode: ThemeMode) -> CatppuccinPalette:
    return PALETTES[mode]
