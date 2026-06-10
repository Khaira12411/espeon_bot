import discord
from discord import app_commands
from discord.ext import commands

from config.straymons_constants import STRAYMONS__ROLES, STRAYMONS__TEXT_CHANNELS, ERI_USER_ID, HANA_USER_ID
from config.wb_constants import *
from utils.database.personal_channel import *
from utils.visuals.embeds.visual_helpers import design_embed, format_bulletin_desc
from utils.essentials.loader import pretty_defer
from utils.loggers.espeon_log import espeon_log, EspeonContext
from utils.group_func.wb_sub.wb_sub_embed import create_wb_embed



# 💜────────────────────────────────────────────
#   🟣 Add WB Subscription
# 💜────────────────────────────────────────────
async def wb_sub_add_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
    boss_name: str,
    variant: str,
    mode: str,
):
    from utils.group_func.wb_sub.wb_sync import sync_upsert_wb_ping

    handler = await pretty_defer(
        interaction=interaction,
        content=f"Processing your {boss_name} subscription...",
        ephemeral=False,
    )

    try:
        user = interaction.user
        guild = interaction.guild

        # Normalize variant/mode
        variant = variant.lower()
        mode = mode.lower()

        # Default channel is off-topic
        ping_channel_id = STRAYMONS__TEXT_CHANNELS.off_topic

        # If user has straymon role, try to fetch personal channel
        straymon_role = guild.get_role(STRAYMONS__ROLES.straymon)
        if straymon_role in user.roles:
            member_channel_id = await get_registered_personal_channel(
                bot=bot, user_id=user.id
            )
            if member_channel_id:
                ping_channel_id = member_channel_id
        if user.id == ERI_USER_ID:
            ping_channel_id = STRAYMONS__TEXT_CHANNELS.play_2
        elif user.id == HANA_USER_ID:
            ping_channel_id = STRAYMONS__TEXT_CHANNELS.play_1
            
        # Insert/update subscription
        await sync_upsert_wb_ping(
            bot=bot,
            user_id=user.id,
            user_name=user.display_name,
            variant=variant,
            boss_name=boss_name.lower(),
            mode=mode,
            channel_id=ping_channel_id,
        )

        # 📦 Create User Embed via helper
        embed = create_wb_embed(
            user=user,
            guild=guild,
            boss_name=boss_name,
            variant=variant,
            mode=mode,
            action="added",
        )
        await handler.success(content="", embed=embed)

        # 📦 Send Log Embed
        log_embed = embed.copy()
        log_embed.set_footer(text=f"User ID: {user.id}", icon_url=guild.icon.url)
        log_channel = guild.get_channel(STRAYMONS__TEXT_CHANNELS.server_logs)
        if log_channel:
            await log_channel.send(embed=log_embed)

        # 💠 Espeon Log
        espeon_log(
            tag="db",
            message=(
                f"💜 WB Sub Added | User: {user.display_name} ({user.id}) "
                f"| Boss: {boss_name.title()} | Variant: {variant} | Mode: {mode}"
            ),
            label="💠 WB SUB",
            context=EspeonContext.STRAYMONS,
        )

    except Exception as e:
        espeon_log(
            tag="error",
            message=f"❌ Failed to add WB Sub for {interaction.user.id}: {e}",
            exc=e,
            label="💠 WB SUB",
            context=EspeonContext.STRAYMONS,
        )
