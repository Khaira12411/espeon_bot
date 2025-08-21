# 🟣────────────────────────────────────────────
#           💜 Market Alert DB Functions 💜
# ─────────────────────────────────────────────
# Functions to manage market alerts via bot.pg_pool
# 🟣────────────────────────────────────────────


# 🔮────────────────────────────────────────────
#           📥 Fetch Functions
# 🔮────────────────────────────────────────────


async def fetch_all_market_alerts(bot):
    """Fetch all market alerts."""
    async with bot.pg_pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT user_id, pokemon, dex_number, max_price, channel_id, role_id, notify FROM market_alerts"
        )
    return [dict(row) for row in rows]


async def fetch_active_market_alerts(bot):
    """Fetch only active alerts (notify = TRUE)."""
    async with bot.pg_pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT user_id, pokemon, dex_number, max_price, channel_id, role_id, notify "
            "FROM market_alerts WHERE notify = TRUE"
        )
    return [dict(row) for row in rows]


async def fetch_user_alerts(bot, user_id: int):
    """Fetch all market alerts for a specific user."""
    async with bot.pg_pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT user_id, pokemon, dex_number, max_price, channel_id, role_id, notify "
            "FROM market_alerts WHERE user_id=$1 ORDER BY dex_number ASC",
            user_id,
        )
    return [dict(row) for row in rows]


# 🔮────────────────────────────────────────────
#           ✨ Insert Functions
# 🔮────────────────────────────────────────────


async def insert_name_alert(
    bot,
    user_id: int,
    pokemon_name: str,
    dex_number: int,
    max_price: int,
    channel_id: int,
    role_id: int = None,
    notify: bool = True,
):
    """Insert a name-based market alert."""
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO market_alerts (user_id, pokemon, dex_number, max_price, channel_id, role_id, notify)
            VALUES ($1,$2,$3,$4,$5,$6,$7)
            ON CONFLICT (user_id, pokemon, channel_id) DO NOTHING;
            """,
            user_id,
            pokemon_name,
            dex_number,
            max_price,
            channel_id,
            role_id,
            notify,
        )


async def insert_dex_alert(
    bot,
    user_id: int,
    pokemon_name: str,
    dex_number: int,
    max_price: int,
    channel_id: int,
    role_id: int = None,
    notify: bool = True,
):
    """Insert a Dex-based market alert."""
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO market_alerts (user_id, pokemon, dex_number, max_price, channel_id, role_id, notify)
            VALUES ($1,$2,$3,$4,$5,$6,$7)
            ON CONFLICT (user_id, dex_number, channel_id) DO NOTHING;
            """,
            user_id,
            pokemon_name,
            dex_number,
            max_price,
            channel_id,
            role_id,
            notify,
        )


# 🔮────────────────────────────────────────────
#           ❌ Remove Functions
# 🔮────────────────────────────────────────────


async def remove_market_alert(bot, user_id: int, pokemon: str):
    """Remove a single market alert for a user by name or Dex."""
    is_dex = str(pokemon).isdigit()
    async with bot.pg_pool.acquire() as conn:
        if is_dex:
            dex_number = int(pokemon)
            result = await conn.execute(
                "DELETE FROM market_alerts WHERE user_id=$1 AND dex_number=$2",
                user_id,
                dex_number,
            )
        else:
            # pokemon_name = pokemon.lower()
            result = await conn.execute(
                "DELETE FROM market_alerts WHERE user_id=$1 AND pokemon=$2",
                user_id,
                pokemon,
            )
    return int(result.split()[-1])


async def remove_all_market_alerts(bot, user_id: int):
    """Remove all market alerts for a user."""
    async with bot.pg_pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM market_alerts WHERE user_id=$1", user_id
        )
    return int(result.split()[-1])


# 🔮────────────────────────────────────────────
#           🔔 Toggle Functions
# 🔮────────────────────────────────────────────


async def toggle_market_alert_notify(
    bot, user_id: int, notify: bool, pokemon: str = None
):
    """Toggle the notify column for one or all alerts."""
    async with bot.pg_pool.acquire() as conn:
        if pokemon and pokemon.lower() != "all":
            is_dex = str(pokemon).isdigit()
            if is_dex:
                dex_number = int(pokemon)
                result = await conn.execute(
                    "UPDATE market_alerts SET notify=$1 WHERE user_id=$2 AND dex_number=$3",
                    notify,
                    user_id,
                    dex_number,
                )
            else:
                pokemon_name = pokemon.lower()
                result = await conn.execute(
                    "UPDATE market_alerts SET notify=$1 WHERE user_id=$2 AND pokemon=$3",
                    notify,
                    user_id,
                    pokemon,
                )
        else:
            # toggle all alerts for the user
            result = await conn.execute(
                "UPDATE market_alerts SET notify=$1 WHERE user_id=$2",
                notify,
                user_id,
            )
    return int(result.split()[-1])
