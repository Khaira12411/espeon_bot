# 🟣────────────────────────────────────────────
#           💜 Market Alert Brain (Pretty Defer) 💜
# 🟣────────────────────────────────────────────

import asyncio
from datetime import datetime
from typing import Optional

import discord

from config.aesthetic import *
from config.emojis import PokeCoin
from utils.essentials.loader import pretty_defer  # <- your new defer wrapper
from utils.group_func.market_alert.db_func.market_alert_counter import *
from utils.group_func.market_alert.db_func.market_alert_db_func import insert_name_alert
from utils.group_func.market_alert.parsers import (
    parse_special_mega_input,
    resolve_pokemon_input,
)
from utils.loggers.espeon_log import espeon_log
from utils.misc.number_parser import parse_compact_number
from utils.misc.string_parser import parse_prefix
from utils.visuals.embeds.get_log_channel import get_log_channel
from utils.visuals.embeds.visual_helpers import design_embed, format_bulletin_desc


# 🤍━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   ✨ Espeon Core Function › Market Alert Add ✨
# 🤍━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def add_market_alert_func(
    bot,
    interaction: discord.Interaction,
    pokemon: str,
    max_price: str,
    channel: discord.TextChannel,
    role: Optional[discord.Role] = None,
    mobile_role_input: Optional[str] = None,
    notify: bool = True,
):
    """
    Market alert workflow using pretty_defer:
    - Immediate loader with safe edits
    - Updates steps live
    - Sends final confirmation embed
    """
    from utils.cache.market_alert_cache import insert_alert, load_market_alert_cache

    user = interaction.user
    user_id = user.id
    log_channel = get_log_channel(bot=bot)

    # 💜 Start loader
    loader = await pretty_defer(
        interaction, content="Espeon is thinking...", ephemeral=False
    )

    # 💜 Validate price
    parsed_price = parse_compact_number(str(max_price))
    if not parsed_price:
        await loader.stop(
            content="❌ Invalid max price format! Use e.g. 1k, 1.5m, 2000"
        )
        return
    max_price = int(parsed_price)

    alerts_counter = await get_alerts_row(bot=bot, user_id=user_id)
    if not alerts_counter:
        await loader.stop(content="❌ Do `/market-alert register` first!")
        return

    total_alerts = alerts_counter["total_alerts"]
    alerts_used = alerts_counter["alerts_used"]

    if total_alerts == alerts_used:
        await loader.stop(
            content=f"❌ You have used up all of your {total_alerts} market alerts"
        )
        return

    # 💜 Normalize role
    role_obj = role
    role_id = None
    role_mention = ""
    if mobile_role_input:
        try:
            mobile_id = int(mobile_role_input.strip().strip("<@&>"))
            role_obj = interaction.guild.get_role(mobile_id)
            if role_obj is None:
                raise ValueError(f"Role ID {mobile_id} not found in guild.")
        except Exception as e:
            await loader.stop(
                content=f"❌ Invalid mobile role input: {e}",
            )
            return
    if role_obj:
        role_id = role_obj.id
        role_mention = f" <@&{role_id}>"

    pokemon_title = pokemon.title()

    try:
        # 🔹 Step 1: Resolve Pokemon
        await loader.edit(content="Resolving Pokemon...")
        if pokemon.isdigit():
            if len(pokemon) == 4 and not pokemon.startswith(("1", "7", "9")):
                raise ValueError("Invalid 4-digit Dex number.")
            target_name, dex_number = resolve_pokemon_input(pokemon)
        elif any(
            pokemon_title.startswith(f"{prefix}Mega ")
            for prefix in ["", "Shiny ", "Golden "]
        ):
            dex_number = parse_special_mega_input(pokemon)
            target_name = pokemon_title
        else:
            target_name, dex_number = resolve_pokemon_input(pokemon)

        # 🔹 Step 2: Validate max price
        await loader.edit(content="Validating max price...")
        max_price_int = int(max_price)

        # 🔹 Step 3: Insert into DB
        await loader.edit(content="Inserting alert into DB...")
        await insert_name_alert(
            bot,
            user_id,
            target_name,
            dex_number,
            max_price_int,
            channel.id,
            role_id,
            notify,
        )
        alert_entry = {
            "pokemon": target_name.lower(),
            "dex_number": dex_number,
            "max_price": max_price_int,
            "channel_id": channel.id,
            "role_id": role_id,
            "notify": notify,
            "user_id": user_id,
        }
        # 🔹 Step 4: Refresh cache
        await loader.edit(content="Adding alert to cache...")
        insert_alert(alert=alert_entry)

        # 🔹 Step 5: Increment alerts used
        await loader.edit(content="Finalizing...")
        status = await use_market_alert(bot=bot, user=user)

    except Exception as e:
        espeon_log("critical", f"Market alert failed: {e}", source="MarketAlert", exc=e)
        await loader.stop(
            content=f"❌ Market alert Add failed: {e}",
        )
        return

    clan_staff = interaction.guild.get_role(STRAYMONS__ROLES.clan_staff)
    is_staff = clan_staff in user.roles or interaction.guild.id == STAFF_SERVER_GUILD_ID
    target_name = target_name.title()
    target_name = parse_prefix(target_name)
    desc_lines = [
        f"- **Member:** {user.mention}",
        f"- **Pokemon:** {target_name} #{dex_number}",
        f"- **Max Price:** {PokeCoin} {max_price_int:,}",
        f"- **Channel:** {channel.mention}",
    ]
    if role_id:
        desc_lines.append(f"- **Role:** {role_mention}")

    full_desc = "\n".join(desc_lines)

    # 💜 Build final confirmation embed

    user_embed = discord.Embed(
        title=f"{Espeon_Emoji.purple_candy} Market Alert Added!",
        description=f"{status['message']}\n{full_desc}",
    )

    footer_text = "You'll be notified when a Pokemon matches your alert 💜"
    user_embed = await design_embed(
        embed=user_embed,
        user=user,
        pokemon_name=target_name,
        footer_text=footer_text,
    )

    if log_channel:
        desc_lines = [
            f"{status['message']}\n" f"- **Member:** {user.mention}",
            f"- **Pokemon:** {target_name} #{dex_number}",
            f"- **Max Price:** {PokeCoin} {max_price_int:,}",
            f"- **Channel:** {channel.mention}",
        ]
        if role_id:
            desc_lines.append(f"- **Role:** {role_mention}")

        full_desc = "\n".join(desc_lines)
        log_embed = discord.Embed(
            title=f"{Espeon_Emoji.purple_candy} Market Alert Created",
            description=full_desc,
            color=0xFF99FF,
            timestamp=datetime.now(),
        )
        log_embed = await design_embed(
            embed=log_embed, user=user, pokemon_name=target_name
        )

    # 💜 Stop loader and show final embed
    await loader.stop(embed=user_embed, delete=False)

    # 💜 Log to staff channel
    try:
        espeon_log(
            "sent",
            f"Market alert created for {target_name} @ {max_price_int}",
            source="MarketAlert",
        )
        if log_channel:
            await log_channel.send(embed=log_embed)
    except Exception as e:
        espeon_log(
            "error",
            f"Failed to send final embed: {e}",
            source="MarketAlert",
            exc=e,
            include_trace=True,
        )
