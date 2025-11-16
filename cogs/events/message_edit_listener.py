import discord
from discord.ext import commands

from config.current_setup import POKEMEOW_APPLICATION_ID, STRAYMONS_GUILD_ID
from config.paldea_galar_dict import rarity_meta
from utils.listener_func.event_checklist_caught import event_checklist_caught
from utils.loggers.espeon_log import espeon_log

SHINY_COLOR = 16751052
EVENT_EXCLUSIVE_COLOR = 16751052
VALID_COLOR = [SHINY_COLOR, EVENT_EXCLUSIVE_COLOR]
LOW_RARITY_COLORS = [
    rarity_meta["rare"]["color"],
    rarity_meta["superrare"]["color"],
    rarity_meta["common"]["color"],
    rarity_meta["uncommon"]["color"],
]


class MessageEditListener(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):

        # Only process in straymons server and avoid dms
        if after.guild is None or after.guild.id != STRAYMONS_GUILD_ID:
            return

        # 🚫 Ignore bots except PokéMeow
        if (
            after.author.bot
            and after.author.id != POKEMEOW_APPLICATION_ID
            and not after.webhook_id
        ):
            return

        embed = after.embeds[0] if after.embeds else None
        embed_desc = embed.description if embed else ""
        embed_color = embed.color.value if embed else None

        # 💜────────────────────────────────────────────
        #           👂 Event Checklist Caught (Debug)
        # 💜────────────────────────────────────────────
        if embed and embed_color not in LOW_RARITY_COLORS:
            if "You caught" in embed_desc:
                espeon_log(
                    "info",
                    f"Detected edited message with rare catch embed in {after.channel.name}, processing...",
                    source="Message Edit Listener",
                )
                await event_checklist_caught(
                    bot=self.bot,
                    before_message=before,
                    after_message=after,
                )


async def setup(bot: commands.Bot):
    await bot.add_cog(MessageEditListener(bot))
