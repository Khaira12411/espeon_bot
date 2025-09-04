import asyncio
from typing import Any, Callable, Coroutine, List

import discord

from config.aesthetic import Espeon_Emoji
from utils.loggers.espeon_log import espeon_log, EspeonContext


async def pretty_defer(
    interaction: discord.Interaction,
    content: str = "Please wait while Espeon thinks...",
    embed: discord.Embed | None = None,
    ephemeral: bool = True,
):
    """
    Defer an interaction with a styled loading message.
    Returns a handle for safely editing or stopping the message later.
    """

    # 🟣────────────────────────────────────────────
    #         💜 Pretty Defer Handle Class 💜
    # 🟣────────────────────────────────────────────
    class PrettyDeferHandle:
        def __init__(self, interaction: discord.Interaction, message: discord.Message):
            self.interaction = interaction
            self.message = message

        async def edit(
            self,
            content: str | None = None,
            embed: discord.Embed | None = None,
            view: discord.ui.View | None = None,
        ):
            """Edit the loader safely with new content/embed/view."""
            if not self.message:
                return
            try:
                kwargs = {}
                if content is not None:
                    kwargs["content"] = f"{Espeon_Emoji.heart_loading} {content}"
                if embed is not None:
                    kwargs["embed"] = embed
                if view is not None:
                    kwargs["view"] = view
                if kwargs:
                    await self.message.edit(**kwargs)
                    espeon_log(
                        "cmd",
                        f"Loader edited → {content or 'embed/view'}",
                        context=EspeonContext.ESPEON,
                    )
            except discord.NotFound:
                try:
                    await self.interaction.followup.send(
                        content=content, embed=embed, view=view, ephemeral=ephemeral
                    )
                except Exception as e:
                    espeon_log(
                        "error",
                        f"Failed to send followup edit: {e}",
                        exc=e,
                        context=EspeonContext.ESPEON,
                    )

        async def stop(
            self,
            content: str | None = None,
            embed: discord.Embed | None = None,
            view: discord.ui.View | None = None,
            delete: bool = False,
        ):
            """Stop the loader: optionally edit final message or delete."""
            if not self.message:
                return
            try:
                if content or embed or view:
                    await self.message.edit(content=content, embed=embed, view=view)
                    espeon_log(
                        "cmd",
                        f"Loader stopped → {content or 'embed/view'}",
                        context=EspeonContext.ESPEON,
                    )
                if delete:
                    await self.message.delete()
                    espeon_log(
                        "cmd", "Loader message deleted", context=EspeonContext.ESPEON
                    )
            except discord.NotFound:
                espeon_log(
                    "warn",
                    "Loader message not found when stopping",
                    context=EspeonContext.ESPEON,
                )
            except Exception as e:
                espeon_log(
                    "error",
                    f"Failed to stop loader: {e}",
                    exc=e,
                    context=EspeonContext.ESPEON,
                )

    # 🟣────────────────────────────────────────────
    #         💜 Send Initial Loader 💜
    # 🟣────────────────────────────────────────────
    msg_content = f"{Espeon_Emoji.heart_loading} {content}"
    try:
        if not interaction.response.is_done():
            await interaction.response.send_message(
                content=msg_content, embed=embed, ephemeral=ephemeral
            )
            msg = await interaction.original_response()
        else:
            msg = await interaction.followup.send(
                content=msg_content, embed=embed, ephemeral=ephemeral
            )
        espeon_log(
            "cmd",
            f"Loader started for {interaction.user}",
            context=EspeonContext.ESPEON,
        )
    except Exception as e:
        espeon_log(
            "error", f"Failed to start loader: {e}", exc=e, context=EspeonContext.ESPEON
        )
        raise

    return PrettyDeferHandle(interaction, msg)
