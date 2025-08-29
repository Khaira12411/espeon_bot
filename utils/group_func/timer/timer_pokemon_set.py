# 🟣────────────────────────────────────────────
#        💜 Timer Pokémon Function 💜
# ─────────────────────────────────────────────
from datetime import datetime

import discord
from discord.ext import commands

from utils.group_func.timer.timer_db_func import set_timer
from utils.loggers.espeon_log import EspeonContext, espeon_log
from utils.visuals.embeds.visual_helpers import set_embed_user_context


async def timer_pokemon_set_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
    mode: str,
):
    from utils.cache.timers_cache import load_timer_cache

    # 🐾 Grab the user info
    user = interaction.user
    user_id = user.id
    user_name = user.name

    # 💾 Update the Pokémon timer setting in DB
    await set_timer(bot=bot, user_id=user_id, pokemon_setting=mode, user_name=user_name)
    espeon_log(
        tag="db",
        message=f"Set Pokémon timer for {user} to {mode}",
        context=EspeonContext.STRAYMONS,
    )

    # 🌸 Prepare confirmation embed
    embed = discord.Embed(
        title="💜 Timer Setting Updated",
        description=f"Pokémon: **{mode}**",
        color=discord.Color.purple(),
        timestamp=datetime.now(),
    )
    embed = set_embed_user_context(embed=embed, user=user)
    # ✨ Send as ephemeral interaction response
    try:
        if interaction.response.is_done():
            # 🔁 If already responded, use followup
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)
        espeon_log(
            tag="info",
            message=f"Sent Pokémon timer confirmation to {user}",
            context=EspeonContext.STRAYMONS,
        )
        await load_timer_cache(bot)

    except Exception as e:
        # ⚠️ Log any errors
        espeon_log(
            tag="error",
            message=f"Failed to send Pokémon timer confirmation for {user_id}: {e}",
            context=EspeonContext.STRAYMONS,
        )
