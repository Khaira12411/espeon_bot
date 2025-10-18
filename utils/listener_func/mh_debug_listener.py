# 🟣────────────────────────────────────────────
#           💜 Market Alert Processor (Fixed) 💜
# ─────────────────────────────────────────────

import re

import discord

from utils.cache.market_alert_cache import market_alert_cache

MEOWHELPER_NAME = "MeowHelper Market"


async def process_market_alert_message(
    bot: discord.Client,
    message: discord.Message,
    market_category_id: int,
):
    """
    Processes MeowHelper market embeds and sends alerts to users
    whose alerts match the Pokemon name/Dex and price.
    """

    print(
        f"[DEBUG] Received message: author={message.author}, webhook_id={message.webhook_id}, channel={message.channel}"
    )

    # ── Only process messages in the market category ──
    if message.channel.category_id != market_category_id:
        print(f"[DEBUG] Skipping: wrong category {message.channel.category_id}")
        return

    # ── Detect MeowHelper webhook by name only ──
    if message.author.name != MEOWHELPER_NAME:
        print(f"[DEBUG] Skipping: not MeowHelper ({message.author.name})")
        return

    if not message.embeds:
        print("[DEBUG] Skipping: no embeds found")
        return

    embed = message.embeds[0]

    # ── Parse Pokemon name & Dex from embed author field ──
    embed_author_name = embed.author.name if embed.author else ""
    match = re.match(r"(.+?)\s+#(\d+)", embed_author_name)
    if not match:
        print(
            f"[DEBUG] Skipping embed: author '{embed_author_name}' did not match pattern"
        )
        return

    poke_name = match.group(1)
    poke_dex = int(match.group(2))
    print(f"[DEBUG] Parsed Pokemon: {poke_name} (Dex #{poke_dex})")

    # ── Parse listed price ──
    fields = {f.name: f.value for f in embed.fields}
    listed_price_str = fields.get("Listed Price", "0")
    try:
        listed_price = int("".join(filter(str.isdigit, listed_price_str)))
    except Exception as e:
        print(f"[DEBUG] Failed to parse listed price '{listed_price_str}': {e}")
        return
    print(f"[DEBUG] Listed price: {listed_price}")

    # ── Check against alerts in cache ──
    for alert in market_alert_cache:
        print(f"[DEBUG] Checking alert: {alert}")
        if not alert.get("notify", True):
            print("[DEBUG] Skipping alert: notify=False")
            continue

        # Match by name or Dex
        if (alert["pokemon_name"].lower() == poke_name.lower()) or (
            alert["dex_number"] == poke_dex
        ):
            print(f"[DEBUG] Alert matched: {poke_name} / Dex #{poke_dex}")
            if listed_price <= alert["max_price"]:
                channel = bot.get_channel(alert["channel_id"])
                if not channel:
                    print(f"[DEBUG] Target channel not found: {alert['channel_id']}")
                    continue

                new_embed = discord.Embed(
                    title=embed_author_name,
                    color=0x0855FB,
                    description=f"Listed for {listed_price:,} PokeCoin",
                )
                new_embed.set_footer(
                    text=(
                        embed.footer.text
                        if embed.footer
                        else "Please check listing before purchase"
                    )
                )

                for name, value in fields.items():
                    new_embed.add_field(name=name, value=value)

                content = f"<@&{alert['role_id']}>" if alert.get("role_id") else None
                print(f"[DEBUG] Sending alert to {channel}: content={content}")
                await channel.send(content=content, embed=new_embed)
            else:
                print(f"[DEBUG] Price {listed_price} exceeds max {alert['max_price']}")
        else:
            print(f"[DEBUG] Alert did not match: {alert['pokemon']} vs {poke_name}")
