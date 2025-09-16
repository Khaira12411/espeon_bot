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
    Returns a handle for safely editing, stopping, or completing the message.
    """

    class PrettyDeferHandle:
        def __init__(self, interaction: discord.Interaction, message: discord.Message):
            self.interaction = interaction
            self.message = message
            self.stopped = False

        async def _resolve_message(self) -> discord.Message | None:
            """Ensure we always have the original message if possible."""
            if self.message:
                return self.message
            try:
                self.message = await self.interaction.original_response()
                return self.message
            except Exception:
                return None

        async def edit(
            self,
            content: str | None = None,
            embed: discord.Embed | None = None,
            view: discord.ui.View | None = None,
        ):
            if self.stopped:
                return
            msg = await self._resolve_message()
            if not msg:
                try:
                    self.message = await self.interaction.followup.send(
                        content=(
                            f"{Espeon_Emoji.heart_loading} {content}"
                            if content
                            else None
                        ),
                        embed=embed,
                        view=view,
                        ephemeral=ephemeral,
                    )
                except Exception as e:
                    espeon_log(
                        "error",
                        f"Failed to send followup edit: {e}",
                        exc=e,
                        context=EspeonContext.ESPEON,
                    )
                return
            kwargs = {
                k: v
                for k, v in {
                    "content": (
                        f"{Espeon_Emoji.heart_loading} {content}" if content else None
                    ),
                    "embed": embed,
                    "view": view,
                }.items()
                if v is not None
            }
            try:
                if kwargs:
                    await msg.edit(**kwargs)
                    espeon_log(
                        "cmd",
                        f"Loader edited → {content or 'embed/view'}",
                        context=EspeonContext.ESPEON,
                    )
            except discord.NotFound:
                pass

        async def stop(
            self,
            content: str | None = None,
            embed: discord.Embed | None = None,
            view: discord.ui.View | None = None,
            delete: bool = False,
        ):
            if self.stopped:
                return
            self.stopped = True
            msg = await self._resolve_message()
            if not msg:
                return
            try:
                if content or embed or view:
                    await msg.edit(content=content, embed=embed, view=view)
                    espeon_log(
                        "cmd",
                        f"Loader stopped → {content or 'embed/view'}",
                        context=EspeonContext.ESPEON,
                    )
                if delete:
                    await msg.delete()
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

        async def success(
            self,
            content: str | None = "Done!",
            embed: discord.Embed | None = None,
            view: discord.ui.View | None = None,
            ephemeral: bool | None = None,
            override_public: bool = False,
            delete: bool = False,
        ):
            """Mark interaction as completed; always tries to edit original response first."""
            if self.stopped:
                return
            self.stopped = True
            msg = await self._resolve_message()
            final_ephemeral = ephemeral if ephemeral is not None else True
            content_with_emoji = (
                f"{Espeon_Emoji.purple_check3} {content}" if content else None
            )

            try:
                if delete and msg:
                    await msg.delete()
                    return

                # --- Always try to edit the original message first ---
                if msg:
                    try:
                        await msg.edit(
                            content=content_with_emoji, embed=embed, view=view
                        )
                        return
                    except Exception:
                        pass  # fallback if edit fails

                # --- Fallbacks ---
                if final_ephemeral and not override_public:
                    await self.interaction.followup.send(
                        content=content_with_emoji,
                        embed=embed,
                        view=view,
                        ephemeral=True,
                    )
                else:
                    if override_public and msg:
                        try:
                            await msg.delete()
                        except Exception:
                            pass
                    if getattr(self.interaction, "channel", None):
                        await self.interaction.channel.send(
                            content=content_with_emoji, embed=embed, view=view
                        )
            except Exception as e:
                espeon_log(
                    "error",
                    f"[pretty_defer.success] Failed to send success: {e}",
                    exc=e,
                    context=EspeonContext.ESPEON,
                )

        async def error(
            self,
            content: str = "An error occurred.",
            embed: discord.Embed | None = None,
        ):
            if self.stopped:
                return
            self.stopped = True
            content_with_emoji = f"{Espeon_Emoji.error} {content}"
            msg = await self._resolve_message()
            try:
                if msg:
                    await msg.edit(content=content_with_emoji, embed=embed)
                else:
                    await self.interaction.followup.send(
                        content=content_with_emoji, embed=embed, ephemeral=True
                    )
            except Exception as e:
                espeon_log(
                    "error",
                    f"Failed to send error: {e}",
                    exc=e,
                    context=EspeonContext.ESPEON,
                )

    # ----------------- Send initial loader -----------------
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


# ╭───────────────────────────────╮
#   🌊 Standalone Pretty Error Helper
# ╰───────────────────────────────╯
async def pretty_error(
    interaction: discord.Interaction,
    content: str = "An error occurred.",
    embed: discord.Embed | None = None,
):
    """Send a standalone ephemeral error using Espeon style."""
    content_with_emoji = f"{Espeon_Emoji.error} {content}"
    try:
        if not interaction.response.is_done():
            await interaction.response.send_message(
                content=content_with_emoji, embed=embed, ephemeral=True
            )
        else:
            await interaction.followup.send(
                content=content_with_emoji, embed=embed, ephemeral=True
            )
    except Exception as e:
        espeon_log(
            "error",
            f"[pretty_error] Failed to send error: {e}",
            exc=e,
            context=EspeonContext.ESPEON,
        )
