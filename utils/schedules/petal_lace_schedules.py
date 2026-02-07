from datetime import datetime

import discord
import pytz

from config.aesthetic import Espeon_Emoji
from config.current_setup import STRAYMONS_GUILD_ID
from config.petal_lace_settings import SERVER_CURRENCY_EMOJI, COLOR, DIVIDER, SERVER_CURRENCY_NAME
from config.straymons_constants import (
    STRAYMONS__EMOJIS,
    STRAYMONS__ROLES,
    STRAYMONS__TEXT_CHANNELS,
)
from utils.database.server_currency import reset_all_balances
from utils.loggers.espeon_log import EspeonContext, espeon_log
from utils.database.server_shop import remove_all_items

async def scheduled_petal_lace_opening(bot: discord.Client):
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

    For this year, we have a brand new shop that just opened up here in Straymons. This magical shop only appears once a year and lasts about a month until it disappears. The shop only accepts special currency called Cherry Pin {SERVER_CURRENCY_EMOJI} to buy wares and that currency only drops if you catch any Pokémon from your `;e cl` event checklist.

    You can purchase as many items as you like until the stocks run out as long as you earn that currency. Some items are said to have more value than the other but have limited stocks, so be sure to grab them before it runs out!

    -# The amount earned are calculated as follows:
    ```Shiny Event - 2 {SERVER_CURRENCY_EMOJI}
    Exclusive Event - 3 {SERVER_CURRENCY_EMOJI}
    Fishing Shiny Event (if any) - 2 {SERVER_CURRENCY_EMOJI}
    Fishing Exclusive Event (if any) - 5 {SERVER_CURRENCY_EMOJI}
    Legendary - 1 Cherry Pin
    Shiny Full Odds - 2 {SERVER_CURRENCY_EMOJI}
    Shiny Legendary Full Odds - 5 {SERVER_CURRENCY_EMOJI}
    Fishing Legendary - 2 {SERVER_CURRENCY_EMOJI}
    Fishing Shiny - 4 {SERVER_CURRENCY_EMOJI}```
    To purchase an item • `/shop buy`
    To view the shop • `/shop view`
    To check your balance • `/balance view`

    There are also hidden quests that the shopkeeper sells. Anyone that can afford it are welcomed to purchase it, but only one person gets to complete the quest and claim the spoils. If you have any questions, do ping Skaia or any staffs online and we'll assist you. Do have fun and spend wisely!

    -# All {charming_hershey_espresso_role.mention} are rewarded 1M {STRAYMONS__EMOJIS.pokecoin} each after the event ends on <t:1766898000:f>. When it does, you will not be able to earn anymore {SERVER_CURRENCY_NAME} and your leftovers will need to be exhausted before they dissappear on <t:1767502800:f>."""

    footer_text = f"Only {SERVER_CURRENCY_NAME} earned after this post are counted."

    embed = discord.Embed(
        description=NEWS_POST_DESC,
        color=COLOR,
        timestamp=datetime.now(),
    )
    embed.set_footer(text=footer_text, icon_url=guild.icon.url if guild.icon else None)
    await news_channel.send(content=content, embed=embed)

    # Reset all user cherry pin balances
    await reset_all_balances(bot)


async def scheduled_petal_lace_event_end(bot: discord.Client):
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
    content = f"{straymons_role.mention} The Petal Lace Shop Event has ended! {Espeon_Emoji.pink_flower_two}"
    title = "🌸 Message from Skaia"
    desc = f"""The event has finally ended! Thank you so much for participating in my last event for the year. It has been a great year for me since I joined Straymons back in January this year and took up the role of making events for everyone. I hope the events that were made are all to your liking!

You cannot gain anymore {SERVER_CURRENCY_NAME} {SERVER_CURRENCY_EMOJI} and you have exactly one week to use it all up until they will disappear on <t:1767502800:f>. I will not be here a lot than usual and I've made my mind to stay and not leave the server or the clan. I will still conduct weekly hunts for you **and** if my life permits me, I can still do events like these every 3 months (March, June, September, December).

Hopefully when I'm able to, I can come down here to say hello and catch up with everyone. But for now, thank you so much for being with me and I can never ask for better clan members than everyone here so thank you thank you thank you! {Espeon_Emoji.hana_hug}"""
    embed = discord.Embed(
        title=title,
        description=desc,
        color=COLOR,
        timestamp=datetime.now(),
    )
    embed.set_footer(
        text="🌸 Wishing everyone a wonderful rest of the year ahead!",
        icon_url=guild.icon.url if guild.icon else None,
    )
    await news_channel.send(content=content, embed=embed)


async def scheduled_petal_lace_shop_clear(
    bot: discord.Client,
):
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
    content = f"{straymons_role.mention} The Petal Lace Shop is now closed! {Espeon_Emoji.pink_flower_two}"
    desc = f"The shop along with any unused {SERVER_CURRENCY_NAME} {SERVER_CURRENCY_EMOJI} have been removed. Thank you so much for your patron!"
    embed = discord.Embed(
        description=desc,
        color=COLOR,
        timestamp=datetime.now(),
    )
    # Send shop closure message
    await news_channel.send(content=content, embed=embed)

    # Reset all user cherry pin balances
    await reset_all_balances(bot)

    # Clear shop
    await remove_all_items(bot)
