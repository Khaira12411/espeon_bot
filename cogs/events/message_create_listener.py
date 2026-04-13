# 🟣────────────────────────────────────────────
#           💜 Message Create Listener Cog 💜
# ─────────────────────────────────────────────

import asyncio

import discord
from discord.ext import commands

from config.current_setup import (
    KHY_USER_ID,
    POKEMEOW_APPLICATION_ID,
    STRAYMONS_GUILD_ID,
)
from config.petal_lace_settings import CHERRY_PIN, COLOR, DIVIDER, SHOP_EVENT
from config.straymons_constants import STRAYMONS__CATEGORIES, STRAYMONS__TEXT_CHANNELS
from utils.listener_func.afk import afk_reply_on_mention
from utils.listener_func.bud_ev_listener import handle_pokemeow_embed_sync
from utils.listener_func.code_claim_listener import handle_code_claim
from utils.listener_func.dex_listener import dex_listener
from utils.listener_func.egg_hatch_listener import egg_hatch_listener_func
from utils.listener_func.ev_tracker_listener import handle_pokemeow_battle_message
from utils.listener_func.market_alert import process_market_alert_message
from utils.listener_func.mr_weakness import mr_weakness_chart
from utils.listener_func.wb_sub import ping_wb_subscribers
from utils.loggers.espeon_log import espeon_log
from utils.quick_codes.petal_lace_event_post import post_news_func
from utils.listener_func.battle_weakness import weakness_chart
MARKETFEED_CHANNELS = {
    STRAYMONS__TEXT_CHANNELS.ic_u_r_s_market_feed,
    STRAYMONS__TEXT_CHANNELS.iiishiny_market_feed,
    STRAYMONS__TEXT_CHANNELS.iil_m_gmax_market_feed,
    STRAYMONS__TEXT_CHANNELS.ivgolden_market_feed,
}
bud_info_trigger = "**Level**:"

triggers = {
    "code_use": "<:checkedbox:752302633141665812> you used a code to claim a :gift:",
}


def embed_has_field_name(embed, name_to_match: str) -> bool:
    """
    Returns True if any field name in the embed matches the given string.
    Returns False immediately if the embed has no fields.
    """
    if not hasattr(embed, "fields") or not embed.fields:
        return False
    for field in embed.fields:
        if field.name == name_to_match:
            return True
    return False


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
        # ---- WB SUB PING
        if message.channel.id == STRAYMONS__TEXT_CHANNELS.worldboss_tracker:
            try:
                await ping_wb_subscribers(bot=self.bot, message=message)

            except Exception as e:
                espeon_log(
                    "error",
                    f"WB Sub ping failed for message {message.id}: {e}",
                )
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
        if message.guild and message.guild.id == STRAYMONS_GUILD_ID:
            # ✨───────────────────────────────────────────────✨
            # 🪻 Message Variables
            # ✨───────────────────────────────────────────────✨
            content = message.content
            first_embed = message.embeds[0] if message.embeds else None
            first_embed_author = (
                first_embed.author.name if first_embed and first_embed.author else ""
            )
            first_embed_description = (
                first_embed.description
                if first_embed and first_embed.description
                else ""
            )
            first_embed_footer = (
                first_embed.footer.text if first_embed and first_embed.footer else ""
            )
            first_embed_title = (
                first_embed.title if first_embed and first_embed.title else ""
            )
            # ✨───────────────────────────────────────────────✨
            # 🪻 MARKET ALERT
            # ✨───────────────────────────────────────────────✨
            if message.channel.id in MARKETFEED_CHANNELS:
                try:
                    await process_market_alert_message(
                        self.bot, message, STRAYMONS__CATEGORIES.MONSTREET_EXCHANGE
                    )
                except Exception as ma_e:
                    espeon_log(
                        tag="error",
                        message=f"Market alert processing failed for message {message.id} in {message.channel.name}: {ma_e}",
                        source="process_market_alert_message",
                    )
            """"# ✨───────────────────────────────────────────────✨
            # 🪻 Egg Hatch Listener
            # ✨───────────────────────────────────────────────✨
            if (
                message.embeds
                and message.embeds[0]
                and message.content
                and message.embeds[0].author
                and "hatched an Egg!" in (message.embeds[0].author.name or "")
                and "just hatched a" in message.content
            ):
                try:
                    await egg_hatch_listener_func(bot=self.bot, message=message)
                except Exception as eh_e:
                    espeon_log(
                        "error",
                        f"Egg hatch processing failed for message {message.id} in {message.channel.name}: {eh_e}",
                        source="egg_hatch_listener_func",
                    )"""
            """"# ✨───────────────────────────────────────────────✨
            # 🪻 Code Claim Listener
            # ✨───────────────────────────────────────────────✨
            if (
                message.content
                and triggers["code_use"].lower() in message.content.lower()
            ):
                try:
                    await handle_code_claim(bot=self.bot, message=message)
                except Exception as cc_e:
                    espeon_log(
                        "error",
                        f"Code claim processing failed for message {message.id} in {message.channel.name}: {cc_e}",
                        source="handle_code_claim",
                    )"""
            # ✨───────────────────────────────────────────────✨
            # 🪻 DEX LISTENER
            # ✨───────────────────────────────────────────────✨
            if first_embed:
                if embed_has_field_name(first_embed, "Dex Number"):
                    espeon_log(
                        "info",
                        f"Detected dex command embed with 'Dex Number' field. Triggering dex listener.",
                    )
                    await dex_listener(self.bot, message)
            # ✨───────────────────────────────────────────────✨
            # 🪻 MR WEAKNESS CHART
            # ✨───────────────────────────────────────────────✨
            if message.embeds and message.embeds[0]:
                embed_title = message.embeds[0].title or ""
                if "Wave" in embed_title:
                    try:
                        await mr_weakness_chart(bot=self.bot, message=message)
                    except Exception as mw_e:
                        espeon_log(
                            "error",
                            f"Mr. Weakness processing failed for message {message.id} in {message.channel.name}: {mw_e}",
                            source="mr_weakness_chart",
                        )
            # ✨───────────────────────────────────────────────✨
            # 🪻 Battle Weakness Chart
            # ✨───────────────────────────────────────────────✨
            if message.embeds and message.embeds[0]:
                if ":crossed_swords" in first_embed_title and "sent out" in first_embed_description:
                    try:
                        await weakness_chart(bot=self.bot, message=message)
                    except Exception as bw_e:
                        espeon_log(
                            "error",
                            f"Battle weakness processing failed for message {message.id} in {message.channel.name}: {bw_e}",
                            source="weakness_chart",
                        )
            # ✨───────────────────────────────────────────────✨
            # 🪻 EV TRAINING
            # ✨───────────────────────────────────────────────✨
            if message.content and "won the battle" in message.content:
                try:
                    await handle_pokemeow_battle_message(bot=self.bot, message=message)
                except Exception as ev_e:
                    espeon_log(
                        "error",
                        f"EV Tracker battle processing failed for message {message.id} in {message.channel.name}: {ev_e}",
                        source="handle_pokemeow_battle_message",
                    )
            # ✨───────────────────────────────────────────────✨
            # 🪻 EV TRACKER BUD
            # ✨───────────────────────────────────────────────✨
            if message.embeds and message.embeds[0]:
                embed_description = message.embeds[0].description
                if embed_description and bud_info_trigger in embed_description:
                    try:
                        await handle_pokemeow_embed_sync(bot=self.bot, message=message)
                    except Exception as ev_e:
                        espeon_log(
                            "error",
                            f"EV Tracker sync failed for message {message.id} in {message.channel.name}: {ev_e}",
                            source="handle_pokemeow_embed_sync",
                        )


# 💜────────────────────────────────────────────
#        🛠️ Setup function to add cog to bot
# 💜────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(MessageCreateListener(bot))
