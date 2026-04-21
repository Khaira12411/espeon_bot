import discord

from utils.loggers.espeon_log import EspeonContext, espeon_log
from utils.loggers.debug_log import debug_log, enable_debug
from utils.listener_func.battle_weakness import weakness_chart
enable_debug(f"{__name__}.test_message_listener")
async def test_message_listener(bot: discord.Client, message: discord.Message):
    if not message.reference or not message.reference.message_id:
        return
    replied_message = await message.channel.fetch_message(message.reference.message_id)
    if not replied_message:
        debug_log(
            f"Failed to fetch replied message with ID {message.reference.message_id} in channel {message.channel.id}"
        )
        return
    replied_message_content = getattr(replied_message, "content", "")
    debug_log(f"Fetched replied message content: '{replied_message_content}'")

    # 💜────────────────────────────────────────────
    #          🧑‍🌾 Message Variables
    # 💜────────────────────────────────────────────
    content = message.content
    first_embed = replied_message.embeds[0] if replied_message.embeds else None
    first_embed_author = (
        first_embed.author.name
        if first_embed and first_embed.author
        else ""
    )
    first_embed_description = (
        first_embed.description
        if first_embed and first_embed.description
        else ""
    )
    first_embed_footer = (
        first_embed.footer.text
        if first_embed and first_embed.footer
        else ""
    )
    first_embed_title = (
        first_embed.title
        if first_embed and first_embed.title
        else ""
    )
    # ✨───────────────────────────────────────────────✨
    # 🪻 Battle Weakness Chart
    # ✨───────────────────────────────────────────────✨
    if first_embed:
        if ":crossed_swords" in first_embed_title and "sent out" in first_embed_description:
            try:
                espeon_log(
                    "info",
                    f"Processing battle weakness for message {replied_message.id} in {replied_message.channel.name}",
                    source="weakness_chart",
                )
                await weakness_chart(bot=bot, message=replied_message)
            except Exception as bw_e:
                espeon_log(
                    "error",
                    f"Battle weakness processing failed for message {replied_message.id} in {replied_message.channel.name}: {bw_e}",
                    source="weakness_chart",
                )
