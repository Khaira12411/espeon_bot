import re

import discord
from discord.ext import commands

from config.current_setup import CC_GUILD_ID
from config.paldea_galar_dict import legendary_mons, rarity_meta
from config.petal_lace_settings import CHERRY_PIN, COLOR, DIVIDER
from utils.cache.cache_list import user_balance_cache
from utils.database.server_currency import (
    get_user_balance,
    update_user_balance,
    upsert_user_balance,
)
from utils.essentials.pokemon_reply import get_pokemeow_reply_member
from utils.loggers.espeon_log import espeon_log

# key = embed_color
SHINY_COLOR = 16751052
LEGENDARY_COLOR = 10487800
EVENT_EXCLUSIVE_COLOR = 16751052
FISHING_COLOR = 8900346
processed_rare_catches = set()
VALID_COLOR = [SHINY_COLOR, EVENT_EXCLUSIVE_COLOR]

LOW_RARITY_COLORS = [
    rarity_meta["rare"]["color"],
    rarity_meta["superrare"]["color"],
    rarity_meta["common"]["color"],
    rarity_meta["uncommon"]["color"],
]

POINT_MAP = {
    "legendary": {"points": 1, "context": "Legendary"},
    "fishing_legendary": {"points": 3, "context": "Fishing Legendary"},
    "fishing_shiny": {"points": 5, "context": "Fishing Shiny"},
    "fishing_exclusive_checklist": {
        "points": 2,
        "context": "Fishing Exclusive Checklist",
    },
    "fishing_shiny_exclusive_checklist": {
        "points": 5,
        "context": "Fishing Shiny Exclusive Checklist",
    },
    "event_shiny": {"points": 2, "context": "Shiny Checklist"},
    "event_exclusive": {"points": 3, "context": "Event Exclusive Checklist"},
    "full_odds_shiny": {"points": 2, "context": "Shiny Full-Odds"},
    "shiny_legendary_full_odds": {"points": 5, "context": "Shiny Legendary Full-Odds"},
}
TEST_BOT_LOG_ID = 1220786187401302036
FISHING_EXCLUSIVE_MON = ["Paldean-Wooper"]
SHINY_FISHIN_EXCLUSIVE_MON = ["Shiny Paldean-Wooper"]


# ❀─────────────────────────────────────────❀
#      💖  Extract Rarity from Footer
# ❀─────────────────────────────────────────❀
def extract_rarity_from_footer(footer_text: str) -> str:
    # Extract rarity from embed footer
    rarity_match = re.search(r"Rarity:\s*([A-Za-z]+)", footer_text)
    if rarity_match:
        rarity = rarity_match.group(1).strip().lower().replace(" ", "")
        espeon_log(
            "info",
            f"Extracted rarity from footer: {rarity}",
            source="Event Checklist Caught",
        )
        return rarity
    else:
        espeon_log(
            "info",
            f"Could not extract rarity from footer: {footer_text}",
            source="Event Checklist Caught",
        )
        return None


async def add_points_to_user(
    bot: discord.Client,
    user: discord.Member,
    points: int,
    display_pokemon_name: str,
    message: discord.Message,
    catch_type: str,
):
    """Add points to user's balance."""
    user_id = user.id
    user_name = user.name
    current_balance = user_balance_cache.get(user_id)

    # If user not in cache, upsert to database
    if current_balance is None:
        await upsert_user_balance(bot, user_id, user_name, points)
        new_balance = points
        espeon_log(
            "info",
            f"User '{user_name}' not in cache. Upserted with initial points: {points}",
            source="Event Checklist Caught",
        )
    else:
        new_balance = current_balance["cherry_pin_balance"] + points
        await update_user_balance(
            bot=bot,
            user_id=user_id,
            user_name=user_name,
            new_balance=new_balance,
        )
        espeon_log(
            "info",
            f"Added {points} points to user '{user_name}'. New balance: {new_balance}",
            source="Event Checklist Caught",
        )
    # Send confirmation message
    embed = discord.Embed(
        title="🎉 Points Awarded!",
        description=(
            f"You have been awarded {points} points for catching {display_pokemon_name}!\n"
            f"**Catch Type:** {catch_type}\n"
            f"**New Balance:** {new_balance} {CHERRY_PIN}"
        ),
        color=0x00FF00,
    )
    embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
    if message.embeds and message.embeds[0].image:
        embed.set_thumbnail(url=message.embeds[0].image.url)
    await message.channel.send(content=user.mention, embed=embed)

async def event_checklist_caught(
    bot: discord.Client,
    before_message: discord.Message,
    after_message: discord.Message,
):
    embed = after_message.embeds[0]
    if not embed:
        return

    embed_color = embed.color.value
    embed_description = embed.description or ""

    rarity = None

    # Check if its a rare spawn based on color and description
    if embed_color not in LOW_RARITY_COLORS and "You caught" in embed_description:
        # Identify the user who caught the Pokémon
        member = await get_pokemeow_reply_member(before_message)
        if not member:
            espeon_log(
                "info",
                "Could not identify member from PokéMeow reply.",
                source="Event Checklist Caught",
            )
            return

        # TODO Member is only valid if they have the hershey role

        if after_message.id in processed_rare_catches:
            return  # Already processed this message

        processed_rare_catches.add(after_message.id)
        catch_type = None
        espeon_log(
            "info",
            f"Processing rare catch for member: {member.display_name}",
            source="Event Checklist Caught",
        )

        # Extract Pokémon name
        pokemon_name = ""
        catch_match = re.search(r"You caught a.*?\*\*([^*]+)\*\*", embed_description)
        if catch_match:
            pokemon_name = catch_match.group(1).strip()
            espeon_log(
                "info",
                f"Extracted Pokémon name: {pokemon_name}",
                source="Event Checklist Caught",
            )
        else:
            espeon_log(
                "info",
                f"Could not extract Pokémon name from description: {embed_description}",
                source="Event Checklist Caught",
            )
            return  # Could not extract Pokémon name

        embed_footer = embed.footer.text

        if embed_color == SHINY_COLOR:
            rarity = "shiny"
            pokemon_name = pokemon_name.replace("Shiny ", "")  # Clean for display
            if pokemon_name in legendary_mons:
                catch_type = "shiny_legendary_full_odds"
            elif embed_footer:
                if "event" in embed_footer.lower():
                    catch_type = "event_shiny"
                elif "full-odds" in embed_footer.lower():
                    catch_type = "full_odds_shiny"
            espeon_log(
                "info",
                f"Identified shiny catch: {pokemon_name}, Catch Type: {catch_type}",
                source="Event Checklist Caught",
            )

        elif embed_color == EVENT_EXCLUSIVE_COLOR:
            catch_type = "event_exclusive"
            rarity = extract_rarity_from_footer(embed_footer)
            if rarity.lower() == "super rare":
                rarity = "superrare"
            espeon_log(
                "info",
                f"Identified event exclusive catch: {pokemon_name}, Rarity: {rarity}",
                source="Event Checklist Caught",
            )

        elif embed_color == LEGENDARY_COLOR:
            rarity = "legendary"
            catch_type = "legendary"
            espeon_log(
                "info",
                f"Identified legendary catch: {pokemon_name}",
                source="Event Checklist Caught",
            )

        elif embed_color not in VALID_COLOR and embed_color != FISHING_COLOR:
            rarity = extract_rarity_from_footer(embed_footer)
            if rarity.lower() == "legendary":
                catch_type = "legendary"
                espeon_log(
                    "info",
                    f"Identified legendary catch from footer: {pokemon_name}",
                    source="Event Checklist Caught",
                )
            else:
                espeon_log(
                    "info",
                    f"Catch is neither shiny, event exclusive, nor legendary: {pokemon_name}",
                    source="Event Checklist Caught",
                )
                return  # Not a rare catch

        elif embed_color == FISHING_COLOR:
            espeon_log(
                "info",
                f"Processing fishing catch for Pokémon: {pokemon_name}",
                source="Event Checklist Caught",
                )
            if pokemon_name in FISHING_EXCLUSIVE_MON:
                catch_type = "fishing_exclusive_checklist"
                rarity = "superrare"
                espeon_log(
                    "info",
                    f"Identified fishing exclusive checklist catch: {pokemon_name}",
                    source="Event Checklist Caught",
                )
            elif pokemon_name in SHINY_FISHIN_EXCLUSIVE_MON:
                catch_type = "fishing_shiny_exclusive_checklist"
                rarity = "shiny"
                pokemon_name = pokemon_name.replace("Shiny ", "")  # Clean for display
                espeon_log(
                    "info",
                    f"Identified fishing shiny exclusive checklist catch: {pokemon_name}",
                    source="Event Checklist Caught",
                )
            elif "Shiny" in embed_description:
                rarity = "shiny"
                pokemon_name = pokemon_name.replace("Shiny ", "")  # Clean for display
                catch_type = "fishing_shiny"
                espeon_log(
                    "info",
                    f"Identified fishing shiny catch: {pokemon_name}",
                    source="Event Checklist Caught",
                )
            elif pokemon_name in legendary_mons:
                catch_type = "fishing_legendary"
                rarity = "legendary"
                espeon_log(
                    "info",
                    f"Identified fishing legendary catch: {pokemon_name}",
                    source="Event Checklist Caught",
                )
            else:
                espeon_log(
                    "info",
                    f"Fishing catch is neither exclusive, shiny, nor legendary: {pokemon_name}",
                    source="Event Checklist Caught",
                )
                return  # Not a rare fishing catch

    points = POINT_MAP.get(catch_type, {}).get("points", 0)
    rarity_emoji = rarity_meta.get(rarity, {}).get("emoji", "")
    pokemon_name = pokemon_name.title()
    context = POINT_MAP.get(catch_type, {}).get("context", "Unknown")
    display_pokemon_name = f"{rarity_emoji} {pokemon_name}"
    source_image_url = embed.image.url if embed.image else None

    # Log the rare catch for debug for now
    #Add points to user balance
    """await add_points_to_user(
        bot=bot,
        user=member,
        points=points,
        display_pokemon_name=display_pokemon_name,
        message=after_message,
        catch_type=context,
    )"""
    bot_log_guild = bot.get_guild(CC_GUILD_ID)
    if bot_log_guild:
        bot_log_channel = bot_log_guild.get_channel(TEST_BOT_LOG_ID)
        if bot_log_channel:
            desc = (
                f"[Jump to Message]({after_message.jump_url})\n"
                f"**Member:** {member.mention}\n"
                f"**Pokémon:** {display_pokemon_name}\n"
                f"**Catch Type:** {context}\n"
                f"**Points:** {points}\n"
            )
            embed = discord.Embed(
                title="🎉 Rare Catch Detected!",
                description=desc,
                color=embed_color,
            )
            embed.set_author(
                name=member.display_name, icon_url=member.display_avatar.url
            )
            if source_image_url:
                embed.set_thumbnail(url=source_image_url)
            await bot_log_channel.send(embed=embed)
