# 🟣────────────────────────────────────────────
#           💜 Market Alert Brain 💜
# ─────────────────────────────────────────────

from datetime import datetime

import discord

from config.aesthetic import *
from config.emojis import PokeCoin
from utils.group_func.market_alert.db_func.market_alert_counter import *
from utils.group_func.market_alert.db_func.market_alert_db_func import insert_name_alert
from utils.group_func.market_alert.parsers import (
    parse_special_mega_input,
    resolve_pokemon_input,
)
from utils.loggers.espeon_log import espeon_log
from utils.visuals.embeds.get_log_channel import get_log_channel
from utils.visuals.embeds.visual_helpers import design_embed


async def add_market_alert_func(
    bot,
    interaction: discord.Interaction,
    pokemon: str,
    max_price: int,
    channel: discord.TextChannel,
    role: discord.Role | None = None,
    notify: bool = True,
):
    """
    Full market alert workflow:
    Resolves Pokémon → validates → inserts DB → refreshes cache → sends embeds.
    """
    from utils.cache.market_alert_cache import load_market_alert_cache

    # 💜 Step 0.5: Defer the interaction so we have more time
    try:
        await interaction.response.defer(ephemeral=True)
    except Exception as e:
        espeon_log(
            "warn",
            f"Failed to defer interaction (might have been already responded): {e}",
            source="MarketAlert",
        )
    user = interaction.user
    role_id = role.id if role else None
    user_id = interaction.user.id

    # 💜 Step 1: Start process
    espeon_log(
        "ready",
        f"Starting market alert creation for user {user_id}",
        source="MarketAlert",
    )

    # fetch current alert status
    await get_market_alert_status(bot=bot, user=user)
    log_channel = get_log_channel(bot=bot)

    pokemon_title = pokemon.title()

    # 🔎 Step 2: Resolve Pokémon
    try:
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
    except Exception as e:
        espeon_log(
            "critical",
            f"Failed to resolve Pokémon: {e}",
            source="MarketAlert",
            exc=e,
            include_trace=True,
        )
        await interaction.response.send_message(
            f"❌ Could not resolve Pokémon '{pokemon}': {e}", ephemeral=True
        )
        return

    # 💜 Step 3: Validate max price
    try:
        max_price = int(max_price)
    except ValueError:
        espeon_log("critical", f"Invalid max_price={max_price}", source="MarketAlert")
        await interaction.response.send_message(
            "❌ Max price must be an integer.", ephemeral=True
        )
        return

    # 💜 Step 4: Insert into DB
    try:
        await insert_name_alert(
            bot,
            user_id,
            target_name,
            dex_number,
            max_price,
            channel.id,
            role_id,
            notify,
        )
    except Exception as e:
        espeon_log(
            "critical",
            f"Failed DB insert: {e}",
            source="MarketAlert",
            exc=e,
            include_trace=True,
        )
        await interaction.response.send_message(
            f"❌ Failed to insert market alert: {e}", ephemeral=True
        )
        return

    # 💜 Step 5: Refresh cache
    try:
        await load_market_alert_cache(bot)
    except Exception as e:
        espeon_log(
            "warn",
            f"Cache refresh failed: {e}",
            source="MarketAlert",
            exc=e,
            include_trace=True,
        )

    # 💜 Step 6: Increment alerts_used and get status
    status = await use_market_alert(bot=bot, user=user)
    target_name = target_name.title()
    # 💜 Step 7: Build user embed
    role_mention = f" <@&{role_id}>" if role_id else ""
    user_embed = discord.Embed(
        title="💜 Market Alert Added!",
        description=f"{status['message']}{role_mention}",
        color=0xFF99FF,
    )
    user_embed.add_field(
        name="Pokémon", value=f"{target_name} #{dex_number}", inline=False
    )
    user_embed.add_field(
        name="Max Price", value=f"{PokeCoin} {max_price:,}", inline=False
    )
    user_embed.add_field(name="Channel", value=f"<#{channel.id}>", inline=False)
    if role_id:
        user_embed.add_field(name="Role", value=f"{role_mention}", inline=False)
    user_embed.set_footer(
        text="You'll be notified when a Pokémon matches your alert 💜"
    )
    clan_staff = interaction.guild.get_role(STRAYMONS__ROLES.clan_staff)
    is_staff = False
    if clan_staff in user.roles or interaction.guild.id == STAFF_SERVER_GUILD_ID:
        is_staff = True

    # 💜 Step 8: Build log embed

    if log_channel:
        # Base description
        desc_lines = [
            f"- Member: {user.mention}",
            f"- Pokemon Added: {target_name.title()} #{dex_number}",
            f"- Max Price: {PokeCoin} {max_price:,}",
            f"- Channel: {channel.mention}",
        ]
        if role_id:
            desc_lines.append(f"- Role: {role_mention}")
        # Append Alerts Usage if user is not staff
        if not is_staff:
            desc_lines.append(
                f"- Alerts Usage: Used {status['alerts_used']} / Total {status['total_alerts']} ({status['alerts_left']} left)"
            )

        # Join all lines
        full_desc = "\n".join(desc_lines)

        log_embed = discord.Embed(
            title=f"{Espeon_Emoji.purple_candy} Market Alert Created",
            description=full_desc,
            color=0xFF99FF,
            timestamp=datetime.now(),
        )

        log_embed = design_embed(embed=log_embed, user=user)

    # 💜 Step 9: Send embeds
    # 💜 Step 9: Send embeds using followup
    try:
        await interaction.followup.send(embed=user_embed, ephemeral=True)
        espeon_log(
            "sent",
            f"Market alert created for {target_name} @ {max_price}",
            source="MarketAlert",
        )
        if log_channel:
            await log_channel.send(embed=log_embed)
    except Exception as e:
        espeon_log(
            "error",
            f"Failed to send embed(s): {e}",
            source="MarketAlert",
            exc=e,
            include_trace=True,
        )
