import random
import discord


def get_random_espeon_shade(shade: str = None) -> discord.Colour:
    """
    Returns a random Espeon-themed color.
    If shade is None, randomly selects from all categories:
        - 'lavender'
        - 'light_purple'
        - 'dark_purple'
        - 'pastel_red'
    Otherwise, pick a specific shade category.
    """
    palette = {
        "lavender": ["#E6DAF3", "#D8B7DD", "#E0BBE4", "#D2B4DE", "#BB8FCE"],
        "light_purple": ["#D0A9F5", "#CDA4DE", "#AF7AC5", "#C39BD3"],
        "dark_purple": ["#9B59B6", "#8E44AD", "#7D3C98", "#6C3483"],
        "pastel_red": ["#F5B7B1", "#F1948A", "#FADBD8", "#F8C8DC"],
    }

    if not shade or shade not in palette:
        # pick a random shade category
        shade = random.choice(list(palette.keys()))

    color_ints = [int(c.lstrip("#"), 16) for c in palette[shade]]
    return discord.Colour(random.choice(color_ints))


# 🌟 Convenience wrapper for fully random Espeon palette
def get_random_espeon_color() -> discord.Colour:
    return get_random_espeon_shade()
