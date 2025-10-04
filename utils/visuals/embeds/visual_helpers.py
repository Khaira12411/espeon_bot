import random
from datetime import datetime

import discord

from utils.visuals.gif import fetch_pokemon_gif
from utils.visuals.embeds.get_pokemon_gif import get_pokemon_gif


def format_bulletin_desc(*args, key_style_override: str = None) -> str:
    """
    Flexible bulletin formatter.
    - By default, keys are bold.
    - If key_style_override is provided, all keys use that style.
    - Skips any key/value pair where the value is None or empty string.
    """

    def apply_style(text: str, style: str) -> str:
        style = style.lower()
        if style == "bold":
            return f"**{text}**"
        elif style == "italic":
            return f"*{text}*"
        elif style == "underline":
            return f"__{text}__"
        elif style == "strikethrough":
            return f"~~{text}~~"
        elif style == "spoiler":
            return f"||{text}||"
        elif style == "inline_code":
            return f"`{text}`"
        elif style == "code":
            return f"```\n{text}\n```"
        elif style == "bold_upper":
            return f"**{text.upper()}**"
        else:
            return f"**{text}**"  # default bold

    key_style = key_style_override if key_style_override else "bold"

    lines = []
    i = 0
    while i < len(args):
        key = args[i]
        value = args[i + 1] if i + 1 < len(args) else None

        # 🔹 Skip if value is None or empty string
        if value is None or (isinstance(value, str) and value.strip() == ""):
            i += 2
            continue

        formatted_key = apply_style(f"{key}:", key_style)
        lines.append(f"- {formatted_key} {value}")

        i += 2

    return "\n".join(lines)


# 💜 Expanded Espeon palette
ESPEON_PALETTE = {
    "lavender": ["#E6DAF3", "#D8B7DD", "#E0BBE4", "#D2B4DE", "#BB8FCE", "#F4E1F5"],
    "light_purple": ["#D0A9F5", "#CDA4DE", "#AF7AC5", "#C39BD3", "#DAA6F3", "#B39DDB"],
    "dark_purple": ["#9B59B6", "#8E44AD", "#7D3C98", "#6C3483", "#5B2C6F", "#4A235A"],
    "pastel_red": ["#F5B7B1", "#F1948A", "#FADBD8", "#F8C8DC", "#F9E0E3"],
    "pink": ["#FFC0CB", "#FFB6C1", "#FF69B4", "#FF77FF", "#E6ABD2"],
    "magenta": ["#FF00FF", "#D100D1", "#C71585", "#E754E4", "#F012BE"],
}


# ── Core color functions ─────────────────────────────
def get_random_espeon_shade(shade: str = None) -> discord.Colour:
    """Returns a random Espeon-themed color. If shade is None, pick randomly from all shades."""
    if not shade or shade not in ESPEON_PALETTE:
        shade = random.choice(list(ESPEON_PALETTE.keys()))
    color_ints = [int(c.lstrip("#"), 16) for c in ESPEON_PALETTE[shade]]
    return discord.Colour(random.choice(color_ints))


def get_random_espeon_color() -> discord.Colour:
    """Returns any random Espeon color (full palette)."""
    return get_random_espeon_shade()


# ── Convenience shade helpers ─────────────────────────
get_random_lavender = lambda: get_random_espeon_shade("lavender")
get_random_light_purple = lambda: get_random_espeon_shade("light_purple")
get_random_dark_purple = lambda: get_random_espeon_shade("dark_purple")
get_random_pastel_red = lambda: get_random_espeon_shade("pastel_red")
get_random_pink = lambda: get_random_espeon_shade("pink")
get_random_magenta = lambda: get_random_espeon_shade("magenta")


# ── Embed helper ─────────────────────────────
async def design_embed(
    embed: discord.Embed,
    user: discord.User | discord.Member,
    thumbnail_url: str = None,
    image_url: str = None,
    footer_text: str = None,
    pokemon_name: str = None,
    color: discord.Colour | str = None,
) -> discord.Embed:
    """
    Sets the embed's author, thumbnail, image, footer, and optional color.
    - Author text = user's display name
    - Author icon = user's avatar
    - Thumbnail = thumbnail_url or user's avatar
    - Image = image_url if provided
    - Footer = footer_text or user ID
    - Color = Discord Color or Espeon shade string
    """
    avatar_url = user.display_avatar.url
    embed.set_author(name=user.display_name, icon_url=avatar_url)
    embed.timestamp = datetime.now()

    if pokemon_name:
        pokemon_gif = await get_pokemon_gif(pokemon_name)
        if pokemon_gif:
            thumbnail_url = pokemon_gif

    # Set thumbnail
    embed.set_thumbnail(url=thumbnail_url or avatar_url)

    # Set image if provided
    if image_url:
        embed.set_image(url=image_url)

    # Set footer
    embed.set_footer(
        text=footer_text or f"💫 User ID: {user.id}",
        icon_url=(
            getattr(user.guild.icon, "url", None) if hasattr(user, "guild") else None
        ),
    )

    # Set color
    if isinstance(color, str):
        embed.color = get_random_espeon_shade(color)
    elif isinstance(color, discord.Colour):
        embed.color = color
    else:
        embed.color = 11500229

    return embed


import discord

ERROR_LOG_CHANNEL_ID = 1410202143570530375
async def pokemon_embed(
    embed: discord.Embed, pokemon_name: str, bot: discord.Client
) -> discord.Embed:
    """
    Inserts a Pokémon GIF in the embed thumbnail.
    Logs a warning to the botlog if the GIF is invalid or missing.
    """
    # Fetch the Pokémon GIF (assume it returns a URL string or None)
    pokemon_gif = await get_pokemon_gif(pokemon_name)

    if not pokemon_gif or not isinstance(pokemon_gif, str) or not pokemon_gif.strip():
        # Send warning to botlog channel
        botlog_channel = bot.get_channel(ERROR_LOG_CHANNEL_ID)
        if botlog_channel:
            await botlog_channel.send(
                f"⚠️ Pokémon '{pokemon_name}' does not have a proper GIF for the thumbnail."
            )
        return embed  # still return the embed, just without thumbnail

    embed.set_thumbnail(url=pokemon_gif)
    return embed
