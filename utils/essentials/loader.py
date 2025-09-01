import asyncio
from typing import Any, Callable, Coroutine, List

import discord

from config.aesthetic import Espeon_Emoji
from utils.loggers.espeon_log import espeon_log


async def pretty_defer(
    interaction: discord.Interaction,
    content: str = "Please wait while Espeon thinks...",
    embed: discord.Embed | None = None,
    ephemeral: bool = True,
):
    """
    Defer an interaction with a loading message.
    Returns a handle for safely editing or stopping the message later.
    """

    class PrettyDeferHandle:
        def __init__(self, interaction: discord.Interaction, message: discord.Message):
            self.interaction = interaction
            self.message = message

        async def edit(
            self, content: str | None = None, embed: discord.Embed | None = None
        ):
            """Edit the loader safely."""
            if not self.message:
                return
            try:
                kwargs = {}
                if content is not None:
                    kwargs["content"] = f"{Espeon_Emoji.heart_loading} {content}"
                if embed is not None:
                    kwargs["embed"] = embed
                if kwargs:
                    await self.message.edit(**kwargs)
            except discord.NotFound:
                await self.interaction.followup.send(
                    content=content, embed=embed, ephemeral=ephemeral
                )

        async def stop(
            self,
            content: str | None = None,
            embed: discord.Embed | None = None,
            delete: bool = False,
        ):
            """Stop the loader: optionally edit final message or delete."""
            if not self.message:
                return
            try:
                if content or embed:
                    await self.message.edit(content=content, embed=embed)
                if delete:
                    await self.message.delete()
            except discord.NotFound:
                pass

    # 💜 Send initial loader
    msg_content = f"{Espeon_Emoji.heart_loading} {content}"
    if not interaction.response.is_done():
        await interaction.response.send_message(
            content=msg_content, embed=embed, ephemeral=ephemeral
        )
        msg = await interaction.original_response()
    else:
        msg = await interaction.followup.send(
            content=msg_content, embed=embed, ephemeral=ephemeral
        )

    return PrettyDeferHandle(interaction, msg)

