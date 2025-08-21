# ────────────────────────────────────────────
#           💜 Market Alert Processor 💜
# ────────────────────────────────────────────

import re

import discord
from discord import Embed

from config.emojis import PokeCoin  # your PokeCoin emoji/string
from utils.cache.market_alert_cache import market_alert_cache
from utils.loggers.espeon_log import EspeonContext, espeon_log

# MeowHelper webhook ID
MEOWHELPER_WEBHOOK_ID = 1407470834251206677  # Replace with your webhook ID


async def process_market_alert_message(
    bot: discord.Client,
    message: discord.Message,
    market_category_id: int,
):
    """
    Process MeowHelper market embeds and send alerts to users.
    """

    # Only process messages in the correct category
    if message.channel.category_id != market_category_id:
        return

    # Only process messages from MeowHelper webhook
    if message.webhook_id != MEOWHELPER_WEBHOOK_ID:
        return

    if not message.embeds:
        return

    embed = message.embeds[0]

    # Parse Pokémon name & Dex from embed author field
    embed_author_name = embed.author.name if embed.author else ""
    match = re.match(r"(.+?)\s+#(\d+)", embed_author_name)
    if not match:
        espeon_log(
            "skip",
            f"Embed author '{embed_author_name}' did not match pattern",
            context=EspeonContext.STRAYMONS,
        )
        return

    poke_name = match.group(1)
    poke_dex = int(match.group(2))

    # Parse listed price (remove emoji first, handle commas)
    fields = {f.name: f.value for f in embed.fields}
    listed_price_str = fields.get("Listed Price", "0")
    listed_price_str = re.sub(r"<a?:\w+:\d+>", "", listed_price_str)
    match_price = re.search(r"(\d[\d,]*)", listed_price_str)
    listed_price = int(match_price.group(1).replace(",", "")) if match_price else 0

    # Get author icon URL for alert embed
    author_icon_url = embed.author.icon_url if embed.author else None
    """espeon_log(
        "db",
        f"Embed author icon URL: {author_icon_url}",
        context=EspeonContext.STRAYMONS,
    )"""

    # Get the original ID field for Buy Command
    original_id = fields.get("ID", "0")

    # Iterate through cache and send alerts
    for alert in market_alert_cache:
        if not alert.get("notify", True):
            continue

        alert_dex = int(alert["dex_number"])

        if alert["pokemon_name"].lower() == poke_name.lower() or alert_dex == poke_dex:
            if listed_price <= alert["max_price"]:
                # Get the channel
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

                # Build alert embed
                new_embed = Embed(
                    title=embed_author_name,
                    color=0x0855FB,
                )

                # Copy original embed thumbnail if it exists
                if embed.thumbnail:
                    new_embed.set_thumbnail(url=embed.thumbnail.url)

                # Copy original author icon
                new_embed.set_author(name=embed_author_name, icon_url=author_icon_url)

                # Add Buy Command field at the top
                new_embed.add_field(
                    name="Buy Command (Iphone)",
                    value=f"`;m b {original_id}`",
                    inline=False,
                )
                new_embed.add_field(
                    name="Buy Command (Android)",
                    value=f";m b {original_id}",
                    inline=False,
                )
                # Replace custom emojis in other fields
                for name, value in fields.items():
                    value_cleaned = re.sub(r"<a?:\w+:\d+>", PokeCoin, value)
                    new_embed.add_field(name=name, value=value_cleaned)

                # Set footer
                new_embed.set_footer(
                    text=(
                        embed.footer.text
                        if embed.footer
                        else "Please check listing before purchase"
                    )
                )

                # Build content message
                content = ""
                if alert.get("role_id"):
                    role = message.guild.get_role(alert["role_id"])
                    if role:
                        content += role.mention + " "
                content += f"{poke_name} on market for {PokeCoin} {listed_price:,}"

                # Send alert
                try:
                    await channel.send(content=content, embed=new_embed)
                    espeon_log(
                        "sent",
                        f"Sent market alert for {poke_name} to channel {channel}",
                        context=EspeonContext.STRAYMONS,
                    )
                except Exception as e:
                    espeon_log(
                        "error",
                        f"Failed to send market alert: {e}",
                        context=EspeonContext.STRAYMONS,
                    )
