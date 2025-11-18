# ────────────────────────────────────────────
#           💜 Market Alert Processor 💜
# ────────────────────────────────────────────

import re

import discord
from discord import Embed

from config.current_setup import STAFF_SERVER_GUILD_ID, STRAYMONS_GUILD_ID
from config.emojis import PokeCoin
from config.paldea_galar_dict import (
    Legendary_icon_url,
    get_rarity_by_color,
    icon_url_map,
    paldean_mons,
)
from config.straymons_constants import (
    STRAYMONS__EMOJIS,
    STRAYMONS__ROLES,
    STRAYMONS__TEXT_CHANNELS,
)
from utils.cache.cache_list import _market_alert_index, _role_cache, market_alert_cache
from utils.loggers.espeon_log import EspeonContext, espeon_log

ALLOWED_WEBHOOKS = {
    1301883013571022892,  # Shiny
    1301882441547513879,  # Regular
    1301882823631966280,  # Legendary
    1301883351359164486,  # Golden
}

SNIPE_MAP = {
    "common": {"role": STRAYMONS__ROLES.basic_snipe},
    "uncommon": {"role": STRAYMONS__ROLES.basic_snipe},
    "rare": {"role": STRAYMONS__ROLES.basic_snipe},
    "superrare": {"role": STRAYMONS__ROLES.super_rare_snipe},
    "legendary": {"role": STRAYMONS__ROLES.legendary_snipe},
    "shiny": {"role": STRAYMONS__ROLES.shiny_snipe},
    "golden": {"role": STRAYMONS__ROLES.golden_snipe},
    "gmax": {"role": STRAYMONS__ROLES.gmax_snipe},
    "mega": {"role": STRAYMONS__ROLES.mega_snipe},
    "event_exclusive": {"role": STRAYMONS__ROLES.event_exclusive_snipe},
}
PRE_MEGA_LIST = [
    "Venusaur",
    "Charizard",
    "Blastoise",
    "Beedrill",
    "Pidgeot",
    "Alakazam",
    "Slowbro",
    "Gengar",
    "Kangaskhan",
    "Pinsir",
    "Gyarados",
    "Aerodactyl",
    "Mewtwo",
    "Ampharos",
    "Scizor",
    "Heracross",
    "Houndoom",
    "Tyranitar",
    "Sceptile",
    "Blaziken",
    "Swampert",
    "Gardevoir",
    "Sableye",
    "Mawile",
    "Aggron",
    "Medicham",
    "Manectric",
    "Sharpedo",
    "Camerupt",
    "Altaria",
    "Banette",
    "Absol",
    "Glalie",
    "Salamence",
    "Metagross",
    "Latias",
    "Latios",
    "Rayquaza",
    "Lopunny",
    "Garchomp",
    "Lucario",
    "Abomasnow",
    "Gallade",
    "Audino",
    "Diancie",
]

processed_market_feed_message_ids = set()
processed_snipe_ids = set()


async def snipe_handler(
    bot: discord.Client,
    poke_name: str,
    listed_price: int,
    id: str,
    lowest_market: int,
    amount: int,
    listing_seen: str,
    message: discord.Message,
    embed: discord.Embed,
):
    embed_color = embed.color.value
    rarity = get_rarity_by_color(embed_color)
    second_snipe_rarity_role = None
    if poke_name.title() in PRE_MEGA_LIST and (rarity != "shiny" and rarity != "mega"):
        second_rarity_role_id = STRAYMONS__ROLES.premega_snipe
        second_snipe_rarity_role = message.guild.get_role(second_rarity_role_id)

    elif rarity == "unknown":
        if "shiny" in poke_name.lower():
            rarity = "shiny"
        elif "mega" in poke_name.lower():
            rarity = "mega"
        elif "gigantamax-" in poke_name.lower() or "eternamax-" in poke_name.lower():
            rarity = "gmax"
        elif embed.author and embed.author.icon_url == Legendary_icon_url:
            rarity = "legendary"
    elif rarity == "event_exclusive":
        icon_url = embed.author.icon_url
        if poke_name.title() in paldean_mons:
            second_rarity_role_id = STRAYMONS__ROLES.paldean_snipe
            second_snipe_rarity_role = message.guild.get_role(second_rarity_role_id)
        else:
            second_snipe_rarity = icon_url_map.get(icon_url)
            if second_snipe_rarity:
                second_rarity_role_id = SNIPE_MAP.get(second_snipe_rarity, {}).get(
                    "role"
                )
                if second_rarity_role_id:
                    second_snipe_rarity_role = message.guild.get_role(
                        second_rarity_role_id
                    )

    ping_role_id = SNIPE_MAP.get(rarity, {}).get("role")
    if ping_role_id:
        guild = message.guild
        role = guild.get_role(ping_role_id)
        snipe_channel = guild.get_channel(STRAYMONS__TEXT_CHANNELS.market_snipe)
        # snipe_channel = guild.get_channel(STRAYMONS__TEXT_CHANNELS.test_snipe)
        if role and snipe_channel:
            display_pokemon_name = poke_name.title()
            if second_snipe_rarity_role:
                content = content = (
                    f"{role.mention} {second_snipe_rarity_role.mention} {display_pokemon_name} listed for {PokeCoin} {listed_price:,} each"
                )
            else:
                content = f"{role.mention} {display_pokemon_name} listed for {PokeCoin} {listed_price:,} each"

            # Check if lowest market is int or "?"
            if isinstance(lowest_market, int):
                lowest_market_str = f"{PokeCoin} {lowest_market:,}"
            else:
                lowest_market_str = f"{PokeCoin} {lowest_market}"

            # Build embed
            snipe_embed = Embed(color=embed.color or 0x0855FB)
            if embed.thumbnail:
                snipe_embed.set_thumbnail(url=embed.thumbnail.url)
            snipe_embed.set_author(
                name=embed.author.name, icon_url=embed.author.icon_url
            )
            snipe_embed.add_field(
                name="Buy Command (Android)", value=f";m b {id}", inline=False
            )
            snipe_embed.add_field(
                name="Buy Command (iPhone)", value=f"`;m b {id}`", inline=False
            )
            snipe_embed.add_field(name="ID", value=id, inline=True)
            snipe_embed.add_field(
                name="Listed Price", value=f"{PokeCoin} {listed_price:,}", inline=True
            )
            snipe_embed.add_field(name="Amount", value=amount, inline=True)
            snipe_embed.add_field(
                name="Lowest Market", value=lowest_market_str, inline=True
            )
            snipe_embed.add_field(name="Listing Seen", value=listing_seen, inline=True)
            snipe_embed.set_footer(
                text="Please check listing before purchase. 🪻",
                icon_url=message.guild.icon.url,
            )
            await snipe_channel.send(content=content, embed=snipe_embed)
            espeon_log(
                "sent",
                f"Sent snipe alert for {display_pokemon_name} to channel {snipe_channel.id}",
                context=EspeonContext.STRAYMONS,
            )


async def process_market_alert_message(
    bot: discord.Client, message: discord.Message, market_category_id: int
):

    if message.channel.category_id != market_category_id:
        return
    if message.webhook_id not in ALLOWED_WEBHOOKS:
        return
    if not message.embeds:
        return

    if message.id in processed_market_feed_message_ids:
        return
    processed_market_feed_message_ids.add(message.id)

    for embed in message.embeds:
        embed_author_name = embed.author.name if embed.author else ""
        match = re.match(r"(.+?)\s+#(\d+)", embed_author_name)
        if not match:
            continue

        poke_name = match.group(1)
        poke_dex = int(match.group(2))

        fields = {f.name: f.value for f in embed.fields}
        listed_price_str = re.sub(r"<a?:\w+:\d+>", "", fields.get("Listed Price", "0"))
        match_price = re.search(r"(\d[\d,]*)", listed_price_str)
        listed_price = int(match_price.group(1).replace(",", "")) if match_price else 0
        lowest_market_str = re.sub(
            r"<a?:\w+:\d+>", "", fields.get("Lowest Market", "0")
        )
        lowest_market_match = re.search(r"(\d[\d,]*)", lowest_market_str)
        lowest_market = (
            int(lowest_market_match.group(1).replace(",", ""))
            if lowest_market_match
            else 0
        )
        listing_seen = fields.get("Listing Seen", "N/A")
        amount = fields.get("Amount", "1")

        author_icon_url = embed.author.icon_url if embed.author else None
        # Rebuild index if empty
        if not _market_alert_index:
            _market_alert_index.clear()
            for alert in market_alert_cache:
                # key by pokemon.lower() only, keep list for multiple alerts per Pokemon
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

        # Snipe detection: only process unprocessed IDs
        if original_id not in processed_snipe_ids:
            processed_snipe_ids.add(original_id)
            if lowest_market > 0 and listed_price <= lowest_market * 0.7:
                espeon_log(
                    "info",
                    f"Detected snipe listing for {poke_name} #{poke_dex} at {listed_price} (lowest market: {lowest_market})",
                    context=EspeonContext.STRAYMONS,
                )
                await snipe_handler(
                    bot,
                    poke_name,
                    listed_price,
                    original_id,
                    lowest_market,
                    amount,
                    listing_seen,
                    message,
                    embed,
                )
            elif lowest_market == 0:
                espeon_log(
                    "info",
                    f"Detected snipe listing for {poke_name} #{poke_dex} at {listed_price} (lowest market unknown)",
                    context=EspeonContext.STRAYMONS,
                )
                lowest_market = "?"
                await snipe_handler(
                    bot,
                    poke_name,
                    listed_price,
                    original_id,
                    lowest_market,
                    amount,
                    listing_seen,
                    message,
                    embed,
                )

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
                name="Buy Command (Android)", value=f";m b {original_id}", inline=False
            )
            new_embed.add_field(
                name="Buy Command (iPhone)", value=f"`;m b {original_id}`", inline=False
            )

            # Copy & clean other fields
            for name, value in fields.items():
                value_cleaned = re.sub(r"<a?:\w+:\d+>", PokeCoin, value)
                new_embed.add_field(name=name, value=value_cleaned)

            new_embed.set_footer(
                text="Please check listing before purchase. 🪻",
                icon_url=message.guild.icon.url,
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
