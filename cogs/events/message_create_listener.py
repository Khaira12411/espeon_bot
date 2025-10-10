# 🟣────────────────────────────────────────────
#           💜 Message Create Listener Cog 💜
# ─────────────────────────────────────────────

import asyncio

import discord
from discord.ext import commands

from config.current_setup import (
    ACTIVE_GUILD_ID,
    POKEMEOW_APPLICATION_ID,
    STAFF_SERVER_GUILD_ID,
    STRAYMONS_GUILD_ID,
)
from config.staffmons_constants import STAFFMONS_CATEGORIES
from config.straymons_constants import STRAYMONS__CATEGORIES, STRAYMONS__TEXT_CHANNELS
from utils.listener_func.afk import afk_reply_on_mention
from utils.listener_func.as_ping import as_rare_ping
from utils.listener_func.bud_ev_listener import handle_pokemeow_embed_sync
from utils.listener_func.ev_tracker_listener import handle_pokemeow_battle_message
from utils.listener_func.market_alert import process_market_alert_message
from utils.listener_func.mr_weakness import mr_weakness_chart
from utils.listener_func.pokemon_timer import *
from utils.listener_func.wb_sub import ping_wb_subscribers
from utils.loggers.espeon_log import espeon_log

MARKETFEED_CHANNELS = {
    STRAYMONS__TEXT_CHANNELS.ic_u_r_s_market_feed,
    STRAYMONS__TEXT_CHANNELS.iiishiny_market_feed,
    STRAYMONS__TEXT_CHANNELS.iil_m_gmax_market_feed,
    STRAYMONS__TEXT_CHANNELS.ivgolden_market_feed,
}
bud_info_trigger = "**Level**:"

class MessageCreateListener(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # 💜 Helper: Retry Discord calls on 503
    async def retry_discord_call(self, func, *args, retries=3, delay=2, **kwargs):
        for attempt in range(1, retries + 1):
            try:
                return await func(*args, **kwargs)
            except discord.HTTPException as e:
                if e.status == 503:
                    espeon_log(
                        "warn",
                        f"HTTP 503 error on attempt {attempt}. Retrying in {delay}s...",
                        source="MessageCreateListener",
                    )
                    if attempt < retries:
                        await asyncio.sleep(delay)
                        continue
                    else:
                        raise
                else:
                    raise

    # 💜────────────────────────────────────────────
    #           👂 Message Listener Event
    # 💜────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        try:
            # ---- WB SUB PING
            if message.channel.id == STRAYMONS__TEXT_CHANNELS.worldboss_tracker:
                try:
                    await ping_wb_subscribers(bot=self.bot, message=message)

                except Exception as e:
                    import traceback

                    print(f"[WB SUB PING ERROR] Failed to ping subscribers: {e}")
                    traceback.print_exc()
            # 🚫 Ignore bots except PokéMeow, but allow webhooks
            if (
                message.author.bot
                and message.author.id != POKEMEOW_APPLICATION_ID
                and not message.webhook_id
            ):
                return
            # ---- afk reply
            try:
                await afk_reply_on_mention(message)
            except Exception as afk_e:
                espeon_log(
                    "error",
                    f"AFK reply failed for message {message.id}: {afk_e}",
                    source="MessageCreateListener",
                )

            # --- Weakness chart processing (Active + Staff Guilds) ---
            if message.guild and message.guild.id in (
                ACTIVE_GUILD_ID,
                STAFF_SERVER_GUILD_ID,
                STRAYMONS_GUILD_ID,
            ):
                # ✨───────────────────────────────────────────────✨
                # 🪻 MR WEAKNESS CHART
                # ✨───────────────────────────────────────────────✨
                if message.embeds and message.embeds[0]:
                    embed_title = message.embeds[0].title or ""
                    if "Wave" in embed_title:
                        await mr_weakness_chart(bot=self.bot, message=message)

                # ✨───────────────────────────────────────────────✨
                # 🪻 EV TRAINING
                # ✨───────────────────────────────────────────────✨
                if message.content and "won the battle" in message.content:
                    await handle_pokemeow_battle_message(bot=self.bot, message=message)

                # ✨───────────────────────────────────────────────✨
                # 🪻 EV TRACKER BUD
                # ✨───────────────────────────────────────────────✨
                if message.embeds and message.embeds[0]:
                    embed_description = message.embeds[0].description
                    if embed_description and bud_info_trigger in embed_description:
                        await handle_pokemeow_embed_sync(bot=self.bot, message=message)

                # ✨───────────────────────────────────────────────✨
                # 🪻 MARKET ALERT
                # ✨───────────────────────────────────────────────✨
                if (
                    message.guild
                    and message.guild.id == STRAYMONS_GUILD_ID
                    and message.channel.id in MARKETFEED_CHANNELS
                ):
                    await process_market_alert_message(
                        self.bot, message, STRAYMONS__CATEGORIES.MONSTREET_EXCHANGE
                    )

        except Exception as e:
            espeon_log(
                "critical",
                f"Unhandled exception in on_message: {e}",
                include_trace=True,
                source="MessageCreateListener",
            )


# 💜────────────────────────────────────────────
#        🛠️ Setup function to add cog to bot
# 💜────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(MessageCreateListener(bot))
