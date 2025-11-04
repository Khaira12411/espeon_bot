import asyncio
import json
from pathlib import Path

from discord import app_commands

from utils.loggers.espeon_log import EspeonContext, espeon_log

FORCE_COMMAND_CACHE_FILE = "data/force_logged_commands.json"
KNOWN_COMMAND_CACHE_FILE = "data/known_commands.json"
LOG_GROUP_COMMANDS_STATUS = False

def log_command_group_counter(group: app_commands.Group):
    """
    Logs a visually enhanced one-line summary of a staff command group.

    Example output:
    💙🎐 Staff Command Group 🎐💙 top:1/9 | warning 🔹 3, channel 🔹 2, view 🔹 3
    """


    # Count top-level commands (excluding subgroups)
    top_count = sum(1 for c in group.commands if not isinstance(c, app_commands.Group))
    total_commands = top_count

    # Count commands per subgroup
    subgroup_counts = []
    for cmd in group.commands:
        if isinstance(cmd, app_commands.Group):
            count = sum(
                1 for c in cmd.commands if not isinstance(c, app_commands.Group)
            )
            subgroup_counts.append(f"{cmd.name} ❣ {count}")
            total_commands += count

    # Only add " | " if there are subgroups
    summary = f"top:{top_count}/{total_commands}"
    if subgroup_counts:
        summary += " | " + ", ".join(subgroup_counts)

    espeon_log(
        tag="",
        message=summary,
        context=EspeonContext.ESPEON,
        label=f"🌟  {group.name.capitalize()} Command Group",
    )


def log_command_group_full_paths(group: app_commands.Group, top_prefix: str = None):
    """
    Logs all commands in a group, including nested subgroups, with full top-level path.
    Example: /staff echo, /staff warning add
    """
    top_prefix = top_prefix or group.name  # Use group name if no top_prefix provided

    def gather_commands(cmd_group: app_commands.Group, parent_path=""):
        commands_list = []
        for cmd in cmd_group.commands:
            cmd_path = f"{parent_path} {cmd.name}".strip()
            if isinstance(cmd, app_commands.Group):
                # Recurse into subgroup
                commands_list.extend(gather_commands(cmd, cmd_path))
            else:
                # Prepend the top-level prefix
                full_cmd_path = f"{top_prefix} {cmd_path}".strip()
                commands_list.append(f"/{full_cmd_path}")
        return commands_list

    all_commands = gather_commands(group, "")
    summary = f"{top_prefix.capitalize()} commands ({len(all_commands)}): " + ", ".join(
        all_commands
    )

    espeon_log(
        tag="",
        message=summary,
        context=EspeonContext.ESPEON,
        label="🌟  Command Group",
    )


import json
import unicodedata


def sanitize_for_cache(s: str) -> str:
    """
    Normalize string to remove fancy accents and special Unicode characters
    that might break downstream JSON or processing.
    Keeps normal letters, numbers, and basic punctuation.
    """
    if not s:
        return s
    # NFKD normalization, then encode to ASCII ignoring errors, then decode back
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")


# ----------------------------📌 Safe Force Command Embed ----------------------------
from pathlib import Path

from utils.loggers.espeon_log import EspeonContext, espeon_log


# ----------------------------📌 Force Commands ----------------------------
def get_force_commands_to_send(
    all_commands: dict, force_cache_file: str = FORCE_COMMAND_CACHE_FILE
) -> list[dict]:
    """
    Returns a list of force-true command dicts that haven't been sent yet.
    Recursively handles subgroups and constructs full paths for proper logging.
    """

    # Load existing force cache
    if Path(force_cache_file).exists():
        with open(force_cache_file, "r", encoding="utf-8") as f:
            try:
                force_cache = json.load(f)
            except json.JSONDecodeError:
                force_cache = {}
    else:
        force_cache = {}

    commands_to_send = []

    def gather_command(cmd_path: str, cmd_data: dict):
        extras = cmd_data.get("extras", {}) or {}
        force_true = extras.get("force_true", False)

        espeon_log(
            message=f"Checking command: {cmd_path}, force_true={force_true}",
            context=EspeonContext.STRAYMONS,
            tag="info",
        )

        if not force_true:
            espeon_log(
                message=f"Skipping {cmd_path} because force_true is False",
                context=EspeonContext.STRAYMONS,
                tag="skip",
            )
            return

        # Build full path
        group = cmd_data.get("group")
        subgroup = cmd_data.get("subgroup")
        name = cmd_data.get("name", cmd_path.split()[-1])
        full_path_parts = [p for p in [group, subgroup, name] if p]
        full_path = " ".join(full_path_parts).lower()

        espeon_log(
            message=f"Full path: {full_path}",
            context=EspeonContext.STRAYMONS,
            tag="info",
        )

        # Skip if already sent
        if force_cache.get(full_path, {}).get("sent"):
            espeon_log(
                message=f"Skipping {full_path} because it is already sent",
                context=EspeonContext.STRAYMONS,
                tag="skip",
            )
            return

        # Attach full path for embed and sanitize description
        cmd_dict = cmd_data.copy()
        cmd_dict["_full_path"] = full_path
        if "description" in cmd_dict:
            cmd_dict["description"] = sanitize_for_cache(cmd_dict["description"])
        commands_to_send.append(cmd_dict)

        espeon_log(
            message=f"Adding {full_path} to commands_to_send (description sanitized)",
            context=EspeonContext.STRAYMONS,
            tag="sent",
        )

    # Recursively process commands and subgroups
    def process_group(prefix: str, commands: dict):
        for path, cmd_data in commands.items():
            full_path = f"{prefix} {path}".strip() if prefix else path

            # If this command is a "group", recurse
            if cmd_data.get("grouped"):
                subgroup_commands = cmd_data.get("subcommands", {})
                process_group(full_path, subgroup_commands)

            # Always gather the current command itself
            gather_command(full_path, cmd_data)

    process_group("", all_commands)

    espeon_log(
        message=f"Total commands to send: {len(commands_to_send)}",
        context=EspeonContext.STRAYMONS,
        tag="info",
    )
    return commands_to_send


# ----------------------------📌 Cache Logging ----------------------------
async def log_command_group_full_paths_to_cache(
    bot, group: app_commands.Group, known_cache: dict = None
):
    """
    Logs all commands in a group (including nested subgroups) with full paths.
    Updates KNOWN_COMMAND_CACHE_FILE and FORCE_COMMAND_CACHE_FILE for force-true commands.
    Only writes to files if there are actual changes.
    """
    # Don't log if disabled
    if not LOG_GROUP_COMMANDS_STATUS:
        return
    
    # Quick one-line summary of the group
    log_command_group_counter(group)

    # --- Load known cache ---
    if known_cache is None:
        known_cache = {}
        if Path(KNOWN_COMMAND_CACHE_FILE).exists():
            try:
                with open(KNOWN_COMMAND_CACHE_FILE, "r", encoding="utf-8") as f:
                    known_cache = json.load(f)
            except json.JSONDecodeError:
                pass

    # Take snapshot to compare later
    old_known_cache = known_cache.copy()

    # --- Load force cache ---
    force_cache = {}
    if Path(FORCE_COMMAND_CACHE_FILE).exists():
        try:
            with open(FORCE_COMMAND_CACHE_FILE, "r", encoding="utf-8") as f:
                force_cache = json.load(f)
        except json.JSONDecodeError:
            pass

    old_force_cache = force_cache.copy()
    added_any = False

    # Recursive function to gather commands
    async def gather_commands(cmd_group: app_commands.Group, parent_path=""):
        nonlocal added_any
        for cmd in cmd_group.commands:
            cmd_path = f"{parent_path} {cmd.name}".strip()
            if isinstance(cmd, app_commands.Group):
                await gather_commands(cmd, cmd_path)
            else:
                full_cmd_path = f"{group.name} {cmd_path}".strip().lower()
                extras = getattr(cmd, "extras", {}) or {}

                # --- Update known cache ---
                if full_cmd_path not in known_cache:
                    parts = full_cmd_path.split(" ")
                    group_name = parts[0]
                    subgroup_name = " ".join(parts[1:-1]) if len(parts) > 2 else None
                    cmd_name = parts[-1]

                    known_cache[full_cmd_path] = {
                        "rename_history": [],
                        "grouped": bool(group.name),
                        "category": extras.get("category", "Public"),
                        "group": group_name,
                        "subgroup": subgroup_name,
                        "name": cmd_name,
                    }
                    added_any = True

                    espeon_log(
                        message=f"Added {full_cmd_path} to known cache",
                        context=EspeonContext.STRAYMONS,
                        tag="sent",
                    )

                # --- Update force cache if force_true ---
                if extras.get("force_true"):
                    if full_cmd_path not in force_cache:
                        force_cache[full_cmd_path] = known_cache[full_cmd_path].copy()
                        force_cache[full_cmd_path]["sent"] = False
                        force_cache[full_cmd_path]["_full_path"] = full_cmd_path
                        # sanitize description to prevent JSON corruption
                        raw_desc = getattr(cmd, "description", "")
                        force_cache[full_cmd_path]["description"] = sanitize_for_cache(
                            raw_desc
                        )

                        espeon_log(
                            message=f"Added {full_cmd_path} to force cache (sanitized description)",
                            context=EspeonContext.STRAYMONS,
                            tag="sent",
                        )

    await gather_commands(group, "")

    # --- Save caches only if changed ---
    if known_cache != old_known_cache:
        with open(KNOWN_COMMAND_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(known_cache, f, indent=2, ensure_ascii=False)
            espeon_log(
                message="Known command cache updated",
                context=EspeonContext.STRAYMONS,
                tag="db",
            )

    if force_cache != old_force_cache:
        with open(FORCE_COMMAND_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(force_cache, f, indent=2, ensure_ascii=False)
            espeon_log(
                message="Force command cache updated",
                context=EspeonContext.STRAYMONS,
                tag="db",
            )
