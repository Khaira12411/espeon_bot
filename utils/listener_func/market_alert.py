# ────────────────────────────────────────────
#           💜 Market Alert Processor 💜
# ────────────────────────────────────────────

import re

import discord
from discord import Embed

from config.current_setup import STRAYMONS_GUILD_ID
from config.emojis import PokeCoin
from utils.cache.market_alert_cache import market_alert_cache
from utils.loggers.espeon_log import EspeonContext, espeon_log

# MeowHelper webhook ID
MEOWHELPER_WEBHOOK_ID = 1407470834251206677
MEW_BOT_ID = 1407471147695476776
ALLOWED_WEBHOOKS = {
    1407471446023868416,  # Shiny 1407471446023868416
    1407470834251206677,  # Regular 1407470834251206677
    1407471147695476776,  # Legendary 1407471147695476776
    1407471632368402514,  # Golden 1407471632368402514
}
#ALLOWED_WEBHOOKS = {MEOWHELPER_WEBHOOK_ID, MEW_BOT_ID}


async def process_market_alert_message(
    bot: discord.Client,
    message: discord.Message,
    market_category_id: int,
):
    """
    Process MeowHelper market embeds and send alerts to users.
    Only logs crucial errors/warnings.
    """

    # Only process messages in the correct category
    if message.channel.category_id != market_category_id:
        return

    # Only process messages from allowed webhooks
    if message.webhook_id not in ALLOWED_WEBHOOKS:
        return

    if not message.embeds:
        return

    embed = message.embeds[0]

    # Parse Pokémon name & Dex from embed author field
    embed_author_name = embed.author.name if embed.author else ""
    match = re.match(r"(.+?)\s+#(\d+)", embed_author_name)
    if not match:
        return

    poke_name = match.group(1)
    poke_dex = int(match.group(2))

    # Parse listed price
    fields = {f.name: f.value for f in embed.fields}
    listed_price_str = fields.get("Listed Price", "0")
    listed_price_str = re.sub(r"<a?:\w+:\d+>", "", listed_price_str)
    match_price = re.search(r"(\d[\d,]*)", listed_price_str)
    listed_price = int(match_price.group(1).replace(",", "")) if match_price else 0

    author_icon_url = embed.author.icon_url if embed.author else None
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
                    color=embed.color or 0x0855FB,
                )

                if embed.thumbnail:
                    new_embed.set_thumbnail(url=embed.thumbnail.url)

                new_embed.set_author(name=embed_author_name, icon_url=author_icon_url)

                # Add Buy Command fields
                new_embed.add_field(
                    name="Buy Command (iPhone)",
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
                    else:
                        guild = bot.get_guild(STRAYMONS_GUILD_ID)
                        if guild:
                            role = guild.get_role(alert["role_id"])
                            content += role.mention + " "

                content += f"{poke_name} on market for {PokeCoin} {listed_price:,}"

                # Send alert
                try:
                    await channel.send(content=content, embed=new_embed)
                except Exception as e:
                    espeon_log(
                        "error",
                        f"Failed to send market alert: {e}",
                        context=EspeonContext.STRAYMONS,
                    )
