import re

import discord
from discord.ext import commands

from config.current_setup import CC_GUILD_ID
from config.paldea_galar_dict import legendary_mons, rarity_meta, FISHING_COLOR
from utils.essentials.pokemon_reply import get_pokemeow_reply_member
from utils.loggers.espeon_log import espeon_log

# key = embed_color
SHINY_COLOR = 16751052
LEGENDARY_COLOR = 0xF822FF
EVENT_EXCLUSIVE_COLOR = 16751052
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
            return

        # TODO Member is only valid if they have the hershey role

        if after_message.id in processed_rare_catches:
            return  # Already processed this message

        processed_rare_catches.add(after_message.id)
        catch_type = None

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

        elif embed_color == EVENT_EXCLUSIVE_COLOR:
            catch_type = "event_exclusive"
            rarity = extract_rarity_from_footer(embed_footer)
            if rarity.lower() == "super rare":
                rarity = "superrare"

        elif embed_color == LEGENDARY_COLOR:
            rarity = "legendary"
            catch_type = "legendary"

        elif embed_color not in VALID_COLOR and embed_color != FISHING_COLOR:
            rarity = extract_rarity_from_footer(embed_footer)
            if rarity.lower() == "legendary":
                catch_type = "legendary"
            else:
                return  # Not a rare catch

        elif embed_color == FISHING_COLOR:
            if pokemon_name in FISHING_EXCLUSIVE_MON:
                catch_type = "fishing_exclusive_checklist"
                rarity = "superrare"
            elif pokemon_name in SHINY_FISHIN_EXCLUSIVE_MON:
                catch_type = "fishing_shiny_exclusive_checklist"
                rarity = "shiny"
                pokemon_name = pokemon_name.replace("Shiny ", "")  # Clean for display
                catch_type = "fishing_shiny"
            elif "Shiny" in embed_description:
                rarity = "shiny"
                pokemon_name = pokemon_name.replace("Shiny ", "")  # Clean for display
                catch_type = "fishing_shiny"
            elif pokemon_name in legendary_mons:
                catch_type = "fishing_legendary"
                rarity = "legendary"
            else:
                return  # Not a rare fishing catch

    points = POINT_MAP.get(catch_type, 0)
    rarity_emoji = rarity_meta.get(rarity, {}).get("emoji", "")
    pokemon_name = pokemon_name.title()
    context = POINT_MAP.get(catch_type, {}).get("context", "Unknown")
    display_pokemon_name = f"{rarity_emoji} {pokemon_name}"
    source_image_url = embed.image.url if embed.image else None

    # Log the rare catch for debug for now
    # TODO Add points to user balance
    bot_log_guild = bot.get_guild(CC_GUILD_ID)
    if bot_log_guild:
        bot_log_channel = bot_log_guild.get_channel(TEST_BOT_LOG_ID)
        if bot_log_channel:
            desc = (
                f"[Jump to Message]({after_message.jump_url})\n\n"
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
