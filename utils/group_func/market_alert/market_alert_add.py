# 🟣────────────────────────────────────────────
#           💜 Market Alert Brain 💜
# ─────────────────────────────────────────────

import discord

from config.emojis import PokeCoin
from utils.group_func.market_alert.db_func.market_alert_db_func import (
    insert_name_alert,
)
from utils.group_func.market_alert.parsers import (
    parse_special_mega_input,
    resolve_pokemon_input,
)
from utils.loggers.espeon_log import espeon_log


async def add_market_alert_func(
    bot,
    user_id: int,
    pokemon: str,
    max_price: int,
    channel_id: int,
    role_id: int = None,
    notify: bool = True,
) -> discord.Embed:
    """
    Adds a new market alert and returns a confirmation embed.
    Handles:
    - Numeric Dex input (normal, shiny, golden, special forms)
    - Name input (with hyphens, spaces, mega forms)
    - Rejects invalid 4-digit codes (e.g., 8046)
    """

    from utils.cache.market_alert_cache import load_market_alert_cache

    # 💜 Step 1: Start process
    espeon_log(
        "ready",
        f"Starting market alert creation for user {user_id}",
        source="MarketAlert",
    )

    # 💜 Step 2: Resolve Pokémon name & Dex
    pokemon_title = pokemon.title()

    # 🔎 Handle numeric Dex input
    if pokemon.isdigit():
        # 🚫 Reject 4-digit dex that don’t start with 1, 7, or 9
        if len(pokemon) == 4 and not pokemon.startswith(("1", "7", "9")):
            espeon_log(
                "critical",
                f"Rejected invalid numeric input {pokemon} from user {user_id}",
                source="MarketAlert",
            )
            raise ValueError("Invalid Dex number provided.")

        # If valid digits, just resolve directly
        try:
            target_name, dex_number = resolve_pokemon_input(pokemon)
            espeon_log(
                "ready",
                f"Resolved numeric input → {target_name} (Dex {dex_number})",
                source="MarketAlert",
            )
        except Exception as e:
            espeon_log(
                "critical",
                f"Failed resolving numeric Dex: {e}",
                source="MarketAlert",
                exc=e,
                include_trace=True,
            )
            raise

    # 🔎 Handle Mega forms (including shiny/golden mega)
    elif any(
        pokemon_title.startswith(f"{prefix}Mega ")
        for prefix in ["", "Shiny ", "Golden "]
    ):
        espeon_log(
            "ready", f"Detected Mega input → {pokemon_title}", source="MarketAlert"
        )
        try:
            dex_number = parse_special_mega_input(pokemon)
            target_name = pokemon_title
            espeon_log(
                "ready",
                f"Resolved Mega to {target_name} (Dex {dex_number})",
                source="MarketAlert",
            )
        except Exception as e:
            espeon_log(
                "critical",
                f"Failed resolving Mega form: {e}",
                source="MarketAlert",
                exc=e,
                include_trace=True,
            )
            raise

    # 🔎 Handle normal names
    else:
        try:
            target_name, dex_number = resolve_pokemon_input(pokemon)
            espeon_log(
                "ready",
                f"Resolved normal input → {target_name} (Dex {dex_number})",
                source="MarketAlert",
            )
        except ValueError as e:
            espeon_log(
                "critical",
                f"Pokémon resolve failed: {e}",
                source="MarketAlert",
                exc=e,
                include_trace=True,
            )
            raise

    # 💜 Step 3: Validate max price
    try:
        max_price = int(max_price)
    except ValueError:
        espeon_log("critical", f"Invalid max_price={max_price}", source="MarketAlert")
        raise ValueError("Max price must be an integer.")

    # 💜 Step 4: Insert into database
    espeon_log(
        "db",
        f"Inserting market alert for {target_name} (Dex {dex_number})",
        source="MarketAlert",
    )
    await insert_name_alert(
        bot, user_id, target_name, dex_number, max_price, channel_id, role_id, notify
    )
    espeon_log("db", "Database insert successful", source="MarketAlert")

    # 💜 Step 5: Refresh cache
    espeon_log("ready", "Refreshing market alert cache…", source="MarketAlert")
    await load_market_alert_cache(bot)
    espeon_log("ready", "Cache refresh complete", source="MarketAlert")

    # 💜 Step 6: Build confirmation embed
    role_mention = f" <@&{role_id}>" if role_id else ""
    embed = discord.Embed(
        title="💜 Market Alert Added!",
        description=f"Your market alert has been successfully created!{role_mention}",
        color=0xFF99FF,
    )
    embed.add_field(
        name="Pokémon",
        value=f"{target_name.title()} (Dex #{dex_number})",
        inline=False,
    )
    embed.add_field(name="Max Price", value=f"{PokeCoin} {max_price:,}", inline=False)
    embed.add_field(
        name="Channel", value=f"<#{channel_id}>{role_mention}", inline=False
    )
    embed.set_footer(text="You'll be notified when a Pokémon matches your alert 💜")

    # 💜 Step 7: Finish
    espeon_log(
        "sent",
        f"Market alert created for {target_name} @ {max_price}",
        source="MarketAlert",
    )
    return embed
