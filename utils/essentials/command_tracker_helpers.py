# ─────────────────────────────────────────────
#   💙 Helpers for auto command logging (Fixed)
# ─────────────────────────────────────────────
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict

import discord
from discord import app_commands
from discord.ext import commands

from config.aesthetic import *
from utils.loggers.espeon_log import EspeonContext, espeon_log


# ── JSON helpers ─────────────────────────────
def load_command_cache(path: str) -> dict:
    if os.path.exists(path):
        with open(path, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}


def save_command_cache(path: str, data: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ── Flatten tree commands ─────────────────────
def flatten_commands(commands_list, parent_name="") -> list[app_commands.Command]:
    flattened = []
    for cmd in commands_list:
        if isinstance(cmd, app_commands.Group):
            # recurse into group commands
            new_parent = f"{parent_name} {cmd.name}".strip()
            flattened.extend(flatten_commands(cmd.commands, new_parent))
        else:
            # store full path
            cmd._full_path = (
                f"{parent_name} {cmd.name}".strip() if parent_name else cmd.name
            )
            flattened.append(cmd)
    return flattened


# ── Gather commands from app_commands.Group ──
def gather_group_commands(cmd_group: app_commands.Group, parent_path=""):
    """Recursively gather commands from groups (all, not just force_true)"""
    result = []
    for cmd in cmd_group.commands:
        full_path = f"{parent_path} {cmd.name}".strip()
        cmd._full_path = full_path
        result.append(cmd)
        if isinstance(cmd, app_commands.Group):
            result.extend(gather_group_commands(cmd, full_path))
    return result


# ── Collect all force_true commands ──────────
def collect_force_true_commands(bot: commands.Bot):
    """Collect all commands with force_true=True (including groups, both cog and bot.tree)."""
    commands_found = []

    # ── From cogs ─────────────────────────────
    for cog in bot.cogs.values():
        for attr_name in dir(cog):
            attr = getattr(cog, attr_name)
            if isinstance(attr, (commands.Command, commands.HybridCommand)):
                extras = getattr(attr, "extras", {})
                if extras.get("force_true"):
                    attr._full_path = attr.name
                    commands_found.append(attr)
            elif isinstance(attr, app_commands.Group):
                commands_found.extend(
                    [
                        c
                        for c in gather_group_commands(attr, parent_path=attr.name)
                        if getattr(c, "extras", {}).get("force_true")
                    ]
                )

    # ── From bot.tree (slash commands not in cogs) ─
    for cmd in flatten_commands(bot.tree.get_commands()):
        extras = getattr(cmd, "extras", {})
        if extras.get("force_true"):
            commands_found.append(cmd)

    # ── Deduplicate just in case ───────────────
    return deduplicate_commands(commands_found)


# ── Remove duplicates safely ──────────────────
def deduplicate_commands(commands: list):
    seen, unique = set(), []
    for cmd in commands:
        path = getattr(cmd, "_full_path", None) or getattr(cmd, "name", None)
        if not path:
            continue
        if path not in seen:
            unique.append(cmd)
            seen.add(path)
    return unique


# ── Change detection (renamed + grouped) ─────
def detect_command_changes(cmd, cache_data: dict):
    """Check if a command was renamed or grouped since the last run."""
    # Determine extras
    if isinstance(cmd, dict):
        extras = cmd.get("extras", {})
        path = cmd.get("_full_path") or cmd.get("name", "unknown_command")
    else:
        extras = getattr(cmd, "extras", {})
        path = getattr(cmd, "_full_path", getattr(cmd, "name", "unknown_command"))

    changes = []

    # Initialize cache entry if missing
    if path not in cache_data:
        cache_data[path] = {"rename_history": [], "grouped": False}

    # Check for renamed commands
    renamed_val = extras.get("renamed")
    if renamed_val and renamed_val not in cache_data[path]["rename_history"]:
        changes.append(f"renamed → {renamed_val}")
        cache_data[path]["rename_history"].append(renamed_val)

    # Check for grouped changes
    grouped_val = extras.get("grouped")
    if grouped_val is not None and grouped_val != cache_data[path].get("grouped"):
        changes.append(f"grouped → {grouped_val}")
        cache_data[path]["grouped"] = grouped_val

    return changes


# ── Embed sender ─────────────────────────────
# ── Embed sender ─────────────────────────────
async def send_changelog_embed(bot, cmd_data: dict, channel, label, extra_changes=None):
    """Send a changelog embed using full command path from dict."""
    command_path = cmd_data.get("_full_path") or cmd_data.get("name", "unknown")
    category = cmd_data.get("category", "Owner").capitalize()
    description = cmd_data.get("description", "No description provided.")

    embed = discord.Embed(
        title=f"{Espeon_Emoji.purple_heart_two} New Command Update!",
        description=f"/{command_path}",
        color=8207512,
        timestamp=datetime.now(),
    )
    embed.add_field(
        name=f"{Espeon_Emoji.purple_flower} Description",
        value=description,
        inline=False,
    )
    embed.add_field(
        name=f"{Espeon_Emoji.purple_candy} Category", value=category, inline=True
    )

    if extra_changes:
        embed.add_field(
            name="✨ Changes",
            value="\n".join(f"- {c}" for c in extra_changes),
            inline=False,
        )

    bot_avatar = getattr(bot.user, "display_avatar", None)
    icon_url = bot_avatar.url if bot_avatar else None
    embed.set_author(name="Straymons Changelog", icon_url=icon_url)
    embed.set_footer(text="Auto-generated changelog")
    embed.set_image(url=Esepon_Divider.purple_moon)
    embed.set_thumbnail(url=Espeon_Thumbnail.note)

    if channel:
        await channel.send(embed=embed)
        channel_name = getattr(channel, "name", "(missing channel)")
        espeon_log(
            tag="sent",
            message=f"Logged update for /{command_path} to {channel_name}",
            context=EspeonContext.STRAYMONS,
            label=label,
        )
    else:
        espeon_log(
            tag="warn",
            message=f"Could not find channel for /{command_path}",
            context=EspeonContext.STRAYMONS,
            label=label,
        )


EXCLUDED_COMMAND_MODULES = [
    "cogs.commands.market_alert_group",
    "cogs.commands.ev_tracker_group",
]

KNOWN_COMMAND_CACHE_FILE = "data/known_commands.json"
FORCE_COMMAND_CACHE_FILE = "data/force_logged_commands.json"


def is_excluded_command(cmd_obj) -> bool:
    """Check if command comes from an excluded module path."""
    callback = getattr(cmd_obj, "callback", None) or getattr(cmd_obj, "_callback", None)
    if callback and hasattr(callback, "__module__"):
        return any(
            callback.__module__.startswith(path) for path in EXCLUDED_COMMAND_MODULES
        )
    return False


def collect_all_commands(bot: commands.Bot, label: str = "🌻 Changelog"):
    """Collect all standalone top-level commands AND push force_true commands to force cache."""
    known_cache = load_command_cache(KNOWN_COMMAND_CACHE_FILE)
    force_cache = load_command_cache(FORCE_COMMAND_CACHE_FILE)

    command_dict = {}
    seen_paths = set()

    # ── Helper to add commands to known + force cache
    def register_command(cmd):
        full_path = getattr(cmd, "_full_path", cmd.name)
        key = full_path.lower()
        if key in seen_paths:
            return
        seen_paths.add(key)

        extras = getattr(cmd, "extras", {}) or {}
        command_dict[full_path] = {
            "rename_history": [],
            "grouped": extras.get("grouped", False),
            "category": extras.get("category", "Public"),
            "group": None,
            "subgroup": None,
            "name": full_path.split(" ")[-1],
        }

        # Add to force cache if force_true
        if extras.get("force_true"):
            if full_path not in force_cache:
                force_cache[full_path] = command_dict[full_path].copy()
                force_cache[full_path].update(
                    {
                        "sent": False,
                        "_full_path": full_path,
                        "description": getattr(cmd, "description", ""),
                    }
                )

    # ── Phase 1: Collect all cog commands
    for cog in bot.cogs.values():
        for attr_name in dir(cog):
            attr = getattr(cog, attr_name)
            if isinstance(
                attr, (commands.Command, commands.HybridCommand, app_commands.Command)
            ):
                register_command(attr)
            elif isinstance(attr, app_commands.Group):
                for cmd in gather_group_commands(attr, parent_path=attr.name):
                    register_command(cmd)

    # ── Phase 2: Collect bot.tree commands not in cogs
    for cmd in flatten_commands(bot.tree.get_commands()):
        register_command(cmd)

    # ── Phase 3: Update known_cache
    for path, data in command_dict.items():
        if path not in known_cache:
            known_cache[path] = data
        else:
            known_cache[path].update(data)

    # ── Save caches
    save_command_cache(KNOWN_COMMAND_CACHE_FILE, known_cache)
    save_command_cache(FORCE_COMMAND_CACHE_FILE, force_cache)

    espeon_log(
        tag="",
        message=f"Collected {len(command_dict)} commands; force cache now has {len(force_cache)} commands",
        context=EspeonContext.STRAYMONS,
        label=label,
    )

    return command_dict, force_cache


def collect_all_commands_from_cogs(bot: commands.Bot, label: str = "🌻 Changelog"):
    """Collect all commands from cogs using metadata (extras) only."""
    known_cache = load_command_cache(KNOWN_COMMAND_CACHE_FILE)
    force_cache = load_command_cache(FORCE_COMMAND_CACHE_FILE)
    command_dict = {}
    seen_paths = set()

    for cog in bot.cogs.values():
        for attr_name in dir(cog):
            attr = getattr(cog, attr_name)

            # ── Command / HybridCommand / app_commands.Command ──
            if isinstance(
                attr, (commands.Command, commands.HybridCommand, app_commands.Command)
            ):
                extras = getattr(attr, "extras", {}) or {}
                full_path = getattr(attr, "_full_path", attr.name)
                key = full_path.lower()

                if is_excluded_command(attr) or key in seen_paths:
                    continue

                seen_paths.add(key)
                command_dict[full_path] = {
                    "rename_history": [],
                    "grouped": extras.get("grouped", False),
                    "category": extras.get("category", "Public"),
                    "group": None,
                    "subgroup": None,
                    "name": full_path.split(" ")[-1],
                }

                # ── Add to force cache if force_true
                if extras.get("force_true"):
                    if full_path not in force_cache:
                        force_cache[full_path] = command_dict[full_path].copy()
                        force_cache[full_path].update(
                            {
                                "sent": False,
                                "_full_path": full_path,
                                "description": getattr(attr, "description", ""),
                            }
                        )

            # ── Handle app_commands.Group ──
            elif isinstance(attr, app_commands.Group):
                for subcmd in gather_group_commands(attr, parent_path=attr.name):
                    extras = getattr(subcmd, "extras", {}) or {}
                    full_path = getattr(subcmd, "_full_path", subcmd.name)
                    key = full_path.lower()

                    if is_excluded_command(subcmd) or key in seen_paths:
                        continue

                    seen_paths.add(key)
                    command_dict[full_path] = {
                        "rename_history": [],
                        "grouped": extras.get("grouped", False),
                        "category": extras.get("category", "Public"),
                        "group": None,
                        "subgroup": None,
                        "name": full_path.split(" ")[-1],
                    }

                    if extras.get("force_true"):
                        if full_path not in force_cache:
                            force_cache[full_path] = command_dict[full_path].copy()
                            force_cache[full_path].update(
                                {
                                    "sent": False,
                                    "_full_path": full_path,
                                    "description": getattr(subcmd, "description", ""),
                                }
                            )

    # ── Update known cache before saving ──
    for path, data in command_dict.items():
        if path not in known_cache:
            known_cache[path] = data
        else:
            known_cache[path].update(data)

    # ── Ensure folders exist ──
    os.makedirs(os.path.dirname(KNOWN_COMMAND_CACHE_FILE), exist_ok=True)
    os.makedirs(os.path.dirname(FORCE_COMMAND_CACHE_FILE), exist_ok=True)

    # ── Save caches ──

    save_command_cache(KNOWN_COMMAND_CACHE_FILE, known_cache)
    save_command_cache(FORCE_COMMAND_CACHE_FILE, force_cache)

    espeon_log(
        tag="",
        message=f"Collected {len(command_dict)} commands; force cache now has {len(force_cache)} commands",
        context=EspeonContext.STRAYMONS,
        label=label,
    )

    return command_dict, force_cache
