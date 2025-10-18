# 🟪────────────────────────────────────────────
#                  Rare Ping Function
#      Handles rare & auto-spawn notifications
# 🟪────────────────────────────────────────────

import re

import discord

from config.paldea_galar_dict import *
from config.staffmons_constants import STAFFMONS__TEXT_CHANNELS, STAFFMONS_ROLES
from utils.loggers.espeon_log import espeon_log  # Using Espeon logs

# The Discord role ID for the auto-spawn mention role
AUTO_SPAWN_ROLE_ID = STAFFMONS_ROLES.as_spawn
RARE_SPAWNS_CHANNEL_ID = STAFFMONS__TEXT_CHANNELS.rare_spawn

# Colors corresponding to special rare/legendary Pokemon embed colors
LEGENDARY_COLORS = {
    rarity_meta["legendary"]["color"],
    rarity_meta["shiny"]["color"],
    rarity_meta["golden"]["color"],
}


async def as_rare_ping(bot: discord.Client, message: discord.Message):
    # 🟪──────────────── Entry / Early Checks ────────────────
    if message.edited_at or not message.embeds:
        return

    embed = message.embeds[0]
    if not (embed.title and "A wild" in embed.title):
        return

    # 🟪──────────────── Parse Rarity & Dex ────────────────
    dex_number = None
    rarity_key = "unknown"
    rarity_info = rarity_meta.get("unknown", {})
    rarity_color = rarity_info["color"]

    rarity_emoji_match = re.search(r"<:([a-zA-Z0-9_]+):\d+>", embed.title)
    if rarity_emoji_match:
        raw_rarity_key = rarity_emoji_match.group(1).lower()
        rarity_key_map = {
            "common": "common",
            "uncommon": "uncommon",
            "rare": "rare",
            "superrare": "superrare",
            "legendary": "legendary",
            "shiny": "shiny",
            "golden": "golden",
        }
        rarity_key = rarity_key_map.get(raw_rarity_key, "unknown")
        rarity_info = rarity_meta.get(rarity_key, rarity_meta["unknown"])

    dex_match = re.search(r"<:([0-9]+):\d+>", embed.title)
    if dex_match:
        dex_number = int(dex_match.group(1))

    pokemon_name = paldea_galar_dict.get(dex_number) or dex.get(
        dex_number, "Unknown Pokemon"
    )
    shiny_text = "shiny " if rarity_key == "shiny" else ""
    is_paldean = dex_number and dex_number in paldea_galar_dict
    is_legendary = embed.color and embed.color.value in LEGENDARY_COLORS

    # 🟪──────────────── Non-Rare AS Ping ────────────────
    if not (is_paldean or is_legendary):
        AUTO_SPAWN_ROLE_MENTION = f"<@&{AUTO_SPAWN_ROLE_ID}>"
        content = f"{AUTO_SPAWN_ROLE_MENTION} A wild {rarity_info.get('emoji', '❓')} **{pokemon_name}** has appeared!"

        channel = bot.get_channel(STAFFMONS__TEXT_CHANNELS.hall)
        if channel:
            await channel.send(content)
            espeon_log("sent", "AS ping sent successfully.", label="SENT")
        else:
            espeon_log("error", "AS ping channel not found.", label="ERROR")
        return

    # 🟪──────────────── Rare Spawn Ping ────────────────
    mention_role = f"<@&{STAFFMONS_ROLES.as_rare_spawn}>"
    content = f"{mention_role} A wild {shiny_text}{rarity_info.get('emoji', '❓')} **{pokemon_name}** has appeared!"

    channel = bot.get_channel(STAFFMONS__TEXT_CHANNELS.hall)
    if channel:
        await channel.send(content)
        espeon_log("sent", "Rare spawn ping sent successfully.", label="SENT")
    else:
        espeon_log("error", "Rare spawn ping channel not found.", label="ERROR")

    # 🟪──────────────── Send Rare Spawn Embed ────────────────
    message_link = f"https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}"
    desc = f"### {rarity_info['emoji']} {pokemon_name} #{dex_number}\n- [Jump to Message]({message_link})"
    rare_spawn_embed = discord.Embed(
        title="A Pokemon has spawned", description=desc, color=rarity_color
    )

    # 🟪──────────────── Embed GIF & Footer ────────────────
    gif_name = paldea_galar_dict.get(dex_number) or dex.get(dex_number)
    gif_url = f"https://play.pokemonshowdown.com/sprites/xyani/{gif_name.lower()}.gif?quality=lossless"
    rare_spawn_embed.set_image(url=gif_url)
    rare_spawn_embed.set_footer(
        text=f"Spawned in {message.guild.name}", icon_url=message.guild.icon.url
    )

    rare_spawn_channel = message.guild.get_channel(RARE_SPAWNS_CHANNEL_ID)
    if rare_spawn_channel:
        await rare_spawn_channel.send(embed=rare_spawn_embed)
        espeon_log("sent", "Rare spawn embed sent successfully.", label="SENT")
    else:
        espeon_log("error", "Rare spawn embed channel not found.", label="ERROR")
