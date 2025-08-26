import random
import discord

# 💜 Expanded Espeon palette
ESPEON_PALETTE = {
    "lavender": ["#E6DAF3", "#D8B7DD", "#E0BBE4", "#D2B4DE", "#BB8FCE", "#F4E1F5"],
    "light_purple": ["#D0A9F5", "#CDA4DE", "#AF7AC5", "#C39BD3", "#DAA6F3", "#B39DDB"],
    "dark_purple": ["#9B59B6", "#8E44AD", "#7D3C98", "#6C3483", "#5B2C6F", "#4A235A"],
    "pastel_red": ["#F5B7B1", "#F1948A", "#FADBD8", "#F8C8DC", "#F9E0E3"],
    "pink": ["#FFC0CB", "#FFB6C1", "#FF69B4", "#FF77FF", "#FF85D7"],
    "magenta": ["#FF00FF", "#D100D1", "#C71585", "#E754E4", "#F012BE"],
}


# ── Core function ─────────────────────────────
def get_random_espeon_shade(shade: str = None) -> discord.Colour:
    """
    Returns a random Espeon-themed color.
    If shade is None, randomly selects from all categories.
    """
    if not shade or shade not in ESPEON_PALETTE:
        shade = random.choice(list(ESPEON_PALETTE.keys()))
    color_ints = [int(c.lstrip("#"), 16) for c in ESPEON_PALETTE[shade]]
    return discord.Colour(random.choice(color_ints))


# ── Fully random Espeon color ─────────────────
def get_random_espeon_color() -> discord.Colour:
    """Returns any random Espeon color (full palette)."""
    return get_random_espeon_shade()


# ── Specific shade helpers ────────────────────
def get_random_lavender() -> discord.Colour:
    return get_random_espeon_shade("lavender")


def get_random_light_purple() -> discord.Colour:
    return get_random_espeon_shade("light_purple")


def get_random_dark_purple() -> discord.Colour:
    return get_random_espeon_shade("dark_purple")


def get_random_pastel_red() -> discord.Colour:
    return get_random_espeon_shade("pastel_red")


def get_random_pink() -> discord.Colour:
    return get_random_espeon_shade("pink")


def get_random_magenta() -> discord.Colour:
    return get_random_espeon_shade("magenta")
