from datetime import datetime

import discord
import pytz

from config.aesthetic import Espeon_Emoji
from config.current_setup import STRAYMONS_GUILD_ID
from config.petal_lace_settings import CHERRY_PIN, COLOR, DIVIDER
from config.straymons_constants import (
    STRAYMONS__EMOJIS,
    STRAYMONS__ROLES,
    STRAYMONS__TEXT_CHANNELS,
)
from utils.database.server_currency import reset_all_balances
from utils.loggers.espeon_log import EspeonContext, espeon_log


def is_nov_30_1pm_or_later_manila():
    tz = pytz.timezone("Asia/Manila")
    now = datetime.now(tz)
    target = tz.localize(datetime(now.year, 11, 30, 13, 0, 0))
    return now >= target


async def post_news_func(bot: discord.Client, message: discord.Message):

    if not is_nov_30_1pm_or_later_manila():
        # dont post if before nov 30 1pm manila time
        espeon_log(
            "info",
            "Current time is before Nov 30, 1 PM Manila time. Skipping news post.",
            source="Petal Lace Event Post",
        )
        return

    guild = bot.get_guild(STRAYMONS_GUILD_ID)
    if not guild:
        espeon_log(
            "error",
            "Straymons guild not found when trying to post Petal Lace news.",
            source="Petal Lace Event Post",
        )
        return

    news_channel = guild.get_channel(STRAYMONS__TEXT_CHANNELS.clueberry)

    charming_hershey_espresso_role = guild.get_role(
        STRAYMONS__ROLES.charming_hershey_espresso
    )
    straymons_role = guild.get_role(STRAYMONS__ROLES.straymon)
    content = f"{straymons_role.mention} Petal Lace Shop in now open! {Espeon_Emoji.pink_flower_two}"
    NEWS_POST_DESC = f"""# __Carnivalesque__ {Espeon_Emoji.sakura_moon}
    -# This special event has opened its doors to our {charming_hershey_espresso_role.mention} and all who wish to join during said event!

    For this year, we have a brand new shop that just opened up here in Straymons. This magical shop only appears once a year and lasts about a month until it disappears. The shop only accepts special currency called Cherry Pin {CHERRY_PIN} to buy wares and that currency only drops if you catch any Pokémon from your `;e cl` event checklist.

    You can purchase as many items as you like until the stocks run out as long as you earn that currency. Some items are said to have more value than the other but have limited stocks, so be sure to grab them before it runs out!

    -# The amount earned are calculated as follows:
    ```Shiny Event - 2 {CHERRY_PIN}
    Exclusive Event - 3 {CHERRY_PIN}
    Fishing Shiny Event (if any) - 2 {CHERRY_PIN}
    Fishing Exclusive Event (if any) - 5 {CHERRY_PIN}
    Legendary - 1 Cherry Pin
    Shiny Full Odds - 2 {CHERRY_PIN}
    Shiny Legendary Full Odds - 5 {CHERRY_PIN}
    Fishing Legendary - 2 {CHERRY_PIN}
    Fishing Shiny - 4 {CHERRY_PIN}```
    To purchase an item • `/shop buy`
    To view the shop • `/shop view`
    To check your balance • `/balance view`

    There are also hidden quests that the shopkeeper sells. Anyone that can afford it are welcomed to purchase it, but only one person gets to complete the quest and claim the spoils. If you have any questions, do ping Skaia or any staffs online and we'll assist you. Do have fun and spend wisely!

    -# All {charming_hershey_espresso_role.mention} are rewarded 1M {STRAYMONS__EMOJIS.pokecoin} each after the event."""

    footer_text = "🍒 Only Cherry Pins earned after this post are counted."

    embed = discord.Embed(
        description=NEWS_POST_DESC,
        color=COLOR,
        timestamp=datetime.now(),
    )
    embed.set_footer(text=footer_text, icon_url=guild.icon.url if guild.icon else None)
    await news_channel.send(content=content, embed=embed)

    # Reset all user cherry pin balances
    await reset_all_balances(bot)

    await message.reply(
        f"✅ Successfully posted Petal Lace news in {news_channel.mention} and reset all user Cherry Pin balances."
    )
