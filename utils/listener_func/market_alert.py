# ────────────────────────────────────────────
#           💜 Market Alert Processor 💜
# ────────────────────────────────────────────

import re

import discord
from discord import Embed

from config.current_setup import STRAYMONS_GUILD_ID, STAFF_SERVER_GUILD_ID
from config.emojis import PokeCoin
from utils.cache.market_alert_cache import market_alert_cache
from utils.loggers.espeon_log import EspeonContext, espeon_log

STAFFMONS_ALLOWED_WEBHOOKS = {
    1407471446023868416,  # Shiny
    1407470834251206677,  # Regular
    1407471147695476776,  # Legendary
    1407471632368402514,  # Golden
}

ALLOWED_WEBHOOKS = {
    1301883013571022892,  # Shiny
    1301882441547513879,  # Regular
    1301882823631966280,  # Legendary
    1301883351359164486,  # Golden
}

# 🔹 Global role cache (guild_id, role_id) -> discord.Role
_role_cache: dict[tuple[int, int], discord.Role] = {}


async def process_market_alert_message(
    bot: discord.Client, message: discord.Message, market_category_id: int
):
    from utils.cache.market_alert_cache import _market_alert_index

    if message.channel.category_id != market_category_id:
        return
    if message.webhook_id not in ALLOWED_WEBHOOKS:
        return
    if not message.embeds:
        return

    embed = message.embeds[0]
    embed_author_name = embed.author.name if embed.author else ""
    match = re.match(r"(.+?)\s+#(\d+)", embed_author_name)
    if not match:
        return

    poke_name = match.group(1)
    poke_dex = int(match.group(2))

    fields = {f.name: f.value for f in embed.fields}
    listed_price_str = re.sub(r"<a?:\w+:\d+>", "", fields.get("Listed Price", "0"))
    match_price = re.search(r"(\d[\d,]*)", listed_price_str)
    listed_price = int(match_price.group(1).replace(",", "")) if match_price else 0

    author_icon_url = embed.author.icon_url if embed.author else None
    # Rebuild index if empty
    if not _market_alert_index:
        _market_alert_index.clear()
        for alert in market_alert_cache:
            # key by pokemon.lower() only, keep list for multiple alerts per Pokémon
            key = alert["pokemon"].lower()
            _market_alert_index.setdefault(key, []).append(alert)

    original_id = fields.get("ID", "0")

    # ✅ O(1) lookup using indexed cache
    alerts_to_check = _market_alert_index.get(poke_name.lower(), [])

    # --- Fallback to linear search if index is empty ---
    if not alerts_to_check:

        alerts_to_check = [
            alert
            for alert in market_alert_cache
            if alert["pokemon"].lower() == poke_name.lower()
        ]

    for alert in alerts_to_check:
        if not alert.get("notify", True):
            continue

        if int(alert["dex_number"]) != poke_dex:
            continue

        if listed_price > alert["max_price"]:
            continue

        # Fetch channel
        channel = bot.get_channel(alert["channel_id"])
        if not channel:
            try:
                channel = await bot.fetch_channel(alert["channel_id"])
            except Exception as e:
                espeon_log(
                    "warn",
                    f"Failed to fetch channel {alert['channel_id']}: {e}",
                    context=EspeonContext.STRAYMONS,
                )
                continue

        # Build embed
        new_embed = discord.Embed(color=embed.color or 0x0855FB)
        if embed.thumbnail:
            new_embed.set_thumbnail(url=embed.thumbnail.url)
        new_embed.set_author(name=embed_author_name, icon_url=author_icon_url)

        # Buy commands
        new_embed.add_field(
            name="Buy Command (iPhone)", value=f"`;m b {original_id}`", inline=False
        )
        new_embed.add_field(
            name="Buy Command (Android)", value=f";m b {original_id}", inline=False
        )

        # Copy & clean other fields
        for name, value in fields.items():
            value_cleaned = re.sub(r"<a?:\w+:\d+>", PokeCoin, value)
            new_embed.add_field(name=name, value=value_cleaned)

        new_embed.set_footer(
            text=(
                embed.footer.text
                if embed.footer
                else "Please check listing before purchase"
            )
        )

        # --- inside your for alert in alerts_to_check loop ---
        content = ""
        if alert.get("role_id"):
            role = None
            # First check Straymons guild
            guild = bot.get_guild(STRAYMONS_GUILD_ID)
            if guild:
                role_key = (guild.id, alert["role_id"])
                role = _role_cache.get(role_key)
                if not role:
                    role = guild.get_role(alert["role_id"])
                    if role:
                        _role_cache[role_key] = role  # cache it

            # Fallback: Staff guild
            if not role:
                staff_guild = bot.get_guild(STAFF_SERVER_GUILD_ID)
                if staff_guild:
                    role_key = (staff_guild.id, alert["role_id"])
                    role = _role_cache.get(role_key)
                    if not role:
                        role = staff_guild.get_role(alert["role_id"])
                        if role:
                            _role_cache[role_key] = role  # cache it

            if role:
                content += role.mention + " "

        content += f"{poke_name} on market for {PokeCoin} {listed_price:,}"
        # Send
        try:
            await channel.send(content=content, embed=new_embed)
            espeon_log(
                "info",
                f"Sent market alert for {poke_name} #{poke_dex} to channel {alert['channel_id']}",
                context=EspeonContext.STRAYMONS,
            )
        except Exception as e:
            espeon_log(
                "error",
                f"Failed to send market alert: {e}",
                context=EspeonContext.STRAYMONS,
            )
