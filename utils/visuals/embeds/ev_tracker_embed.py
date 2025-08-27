import discord


def build_ev_tracker_embed(
    tracked_data: dict,
    evs: dict,
    goals: dict = None,
    guild: discord.Guild = None,
    user_id: int = None,
    title_prefix: str = " EV Tracker 💜",
    winner_name: str = None,
    summary_lines: list[str] = None,
    use_progress_bar: bool = False,
    max_total_evs: int = 510,
    line_separator: str = "----------------------------------------------------------",  # separator between stat lines
) -> discord.Embed:
    """
    Build a flexible EV tracker embed with spacing and line separators.
    The title prefix is now included in the author name instead of the embed title.
    """

    if goals is None:
        goals = tracked_data.get("goals", {})

    stats_order = ["hp", "atk", "spa", "def", "spd", "spe"]
    total_current = sum(evs.get(s, 0) for s in stats_order)
    display_total_current = min(total_current, max_total_evs)

    # Mini progress bar helper
    def ev_bar(current, max_val=252, length=5):
        filled = int(round(length * current / max_val))
        return "💜" * filled + "▫️" * (length - filled)

    # Build 3-per-line stats with optional progress bar
    stats_lines = []
    line = []
    all_completed = True

    for i, stat in enumerate(stats_order, start=1):
        if stat in evs:
            current = evs[stat]
            goal = goals.get(stat, 252 if goals else "–")

            if current >= 252:
                completed = "✅💖"
            elif goal != "–" and isinstance(goal, int) and current >= goal:
                completed = "✅"
            else:
                completed = "❌" if goal != "–" else ""
                all_completed = False

            line.append(
                f"**{stat.upper()}**"
                + (f" {ev_bar(current)}" if use_progress_bar else "")
                + f" {current}/{goal} {completed}"
            )

            if i % 3 == 0:
                stats_lines.append(" |  ".join(line))
                line = []

    if line:
        stats_lines.append(" |  ".join(line))  # append remaining stats

    # Add separator between lines
    stats_str = f"\n{line_separator}\n".join(stats_lines)

    # Build description with spacing
    description = (
        f"## **{tracked_data['pokemon']} #{tracked_data.get('dex_number')}**\n"
        f"### **Total EVs:** {display_total_current}/{max_total_evs}\n\n"
        f"{stats_str}"
    )

    embed = discord.Embed(
        description=description,
        color=0xFF99FF,
    )

    # Set author with title prefix next to username
    member = guild.get_member(user_id) if guild else None
    avatar_url = member.display_avatar.url if member else None
    embed.set_author(
        name=f"{winner_name or tracked_data['user_name']}'s {title_prefix}",
        icon_url=avatar_url,
    )

    if all_completed and goals:
        embed.set_footer(
            text="🎉 All goals completed! Use /ev-tracker reset to track a new Pokémon."
        )

    if summary_lines:
        embed.add_field(
            name="🔄 Updated Stats", value="\n".join(summary_lines), inline=False
        )

    return embed
