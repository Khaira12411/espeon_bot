import discord

from config.emojis import PokeCoin  # your coin emoji
from utils.group_func.market_alert.db_func.market_alert_db_func import fetch_user_alerts


# 🟪────────────────────────────────────────────
#   Mine Market Alerts
# 🟪────────────────────────────────────────────
async def mine_market_alerts_func(bot, user_id: int) -> discord.Embed:
    """
    Fetch and display all market alerts owned by a user in a cute styled embed.
    """
    alerts = await fetch_user_alerts(bot, user_id)

    if not alerts:
        return discord.Embed(
            title="💜 No Market Alerts",
            description="You don’t have any active market alerts right now.\n"
            "Use `/market-alert add` to create one ✨",
            color=0xAA88FF,
        )

    embed = discord.Embed(
        title="💜 Your Market Alerts",
        description="Here’s a list of your current market alerts:\n",
        color=0xAA88FF,
    )

    for alert in alerts:
        role_mention = f"<@&{alert['role_id']}>" if alert.get("role_id") else "None"
        notify_status = "✅ Enabled" if alert.get("notify", True) else "❌ Disabled"

        embed.add_field(
            name=f"✨ {alert['pokemon'].title()} (Dex #{alert['dex_number']})",
            value=(
                f"> - **Max Price:** {PokeCoin} {alert['max_price']:,}\n"
                f"> - **Channel:** <#{alert['channel_id']}>\n"
                f"> - **Role:** {role_mention}\n"
                f"> - **Notify:** {notify_status}"
            ),
            inline=False,
        )

    embed.set_footer(
        text="💜 Use /market-alert remove or /market-alert toggle to manage these alerts!"
    )

    return embed
