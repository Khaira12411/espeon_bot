from discord.ext import commands
from utils.essentials.command_group_counter import get_force_commands_to_send
from config.straymons_constants import *
from utils.essentials.command_tracker_helpers import (
    collect_all_commands,
    detect_command_changes,
    load_command_cache,
    save_command_cache,
    send_changelog_embed,
    collect_all_commands_from_cogs,
)
from utils.loggers.espeon_log import espeon_log, EspeonContext

FORCE_COMMAND_CACHE_FILE = "data/force_logged_commands.json"
KNOWN_COMMAND_CACHE_FILE = "data/known_commands.json"

from discord import app_commands


async def auto_log_new_commands(
    bot: commands.Bot,
    label: str = "🌻 Changelog",
    dry_run: bool | None = None,
):
    """💙 Auto-log commands; embeds sent only once per force-true command.
    Group commands and their children are reliably tracked via FORCE_COMMAND_CACHE_FILE.
    """
    espeon_log(
        tag="",
        message="💫 Starting auto-log of commands...",
        context=EspeonContext.STRAYMONS,
        label=label,
    )

    try:
        # Load caches
        known_cache = load_command_cache(KNOWN_COMMAND_CACHE_FILE)

        # Collect all top-level commands to update known_cache silently
        all_commands, force_cache = collect_all_commands_from_cogs(
            bot
        )  # ← use returned force_cache

        # Update known_cache
        for path, cmd_data in all_commands.items():
            extras = cmd_data.get("extras", {}) or {}
            grouped = cmd_data.get("grouped", False)
            category = cmd_data.get("category", "Owner")
            group = cmd_data.get("group")
            subgroup = cmd_data.get("subgroup")
            name = cmd_data.get("name", path.split(" ")[-1])

            # Prefer extras if explicitly provided
            group = extras.get("group", group)
            subgroup = extras.get("subgroup", subgroup)
            name = extras.get("name", name)

            if path not in known_cache:
                known_cache[path] = {
                    "rename_history": [],
                    "grouped": grouped,
                    "category": category,
                    "group": group,
                    "subgroup": subgroup,
                    "name": name,
                }
                espeon_log(
                    tag="",
                    message=f"[KNOWN] Registered new command /{path}",
                    context=EspeonContext.STRAYMONS,
                    label=label,
                )
            else:
                known_cache[path].update(
                    {
                        "grouped": grouped,
                        "category": category,
                        "group": group,
                        "subgroup": subgroup,
                        "name": name,
                    }
                )

        save_command_cache(KNOWN_COMMAND_CACHE_FILE, known_cache)

        # ── Send force-true commands directly from the freshly collected force_cache ──
        for key, cmd_data in force_cache.items():
            full_path = cmd_data.get("_full_path") or key

            # Skip if already sent
            if cmd_data.get("sent", False):
                continue

            category = cmd_data.get("category", "Owner")

            # Channel selection
            channel_map = {
                "staff": STRAYMONS__TEXT_CHANNELS.staff_announcement,
                "owner": STRAYMONS__TEXT_CHANNELS.bot_logs,
            }
            channel_id = channel_map.get(
                category.lower(), STRAYMONS__TEXT_CHANNELS.change_log
            )
            channel = bot.get_channel(channel_id)

            # Detect changes
            changes = detect_command_changes(cmd_data, force_cache)

            # Skip sending if dry run
            if dry_run:
                espeon_log(
                    tag="",
                    message=f"[DRY RUN] Would send force command /{full_path}",
                    context=EspeonContext.STRAYMONS,
                    label=label,
                )
                continue

            # Send embed
            await send_changelog_embed(
                bot, cmd_data, channel, label, extra_changes=changes
            )

            # Mark as sent
            force_cache[key]["sent"] = True
            espeon_log(
                tag="",
                message=f"[SENT] Force command /{full_path} logged successfully",
                context=EspeonContext.STRAYMONS,
                label=label,
            )

        # Save the updated force cache
        save_command_cache(FORCE_COMMAND_CACHE_FILE, force_cache)

        espeon_log(
            tag="",
            message=f"✅ Auto-log completed successfully{' (dry run)' if dry_run else ''}.",
            context=EspeonContext.STRAYMONS,
            label=label,
        )

    except Exception as e:
        espeon_log(
            tag="error",
            message=f"❌ Failed to auto-log commands: {e}",
            context=EspeonContext.STRAYMONS,
            label=label,
            include_trace=True,
            exc=e,
        )
