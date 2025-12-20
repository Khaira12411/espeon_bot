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
            pokemon_name.lower(),
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
            pokemon_name = pokemon.lower()
            result = await conn.execute(
                "DELETE FROM market_alerts WHERE user_id=$1 AND pokemon=$2",
                user_id,
                pokemon_name,
            )
    return int(result.split()[-1])


# 💙────────────────────────────────────────────
#       🗑️ Remove all market alerts for a user
#       and reset alerts_used in counter
# 💙────────────────────────────────────────────
async def remove_all_market_alerts(bot, user_id: int):
    """Remove all market alerts for a user and reset alerts_used to 0."""
    async with bot.pg_pool.acquire() as conn:
        # 💙 Delete all alerts for the user
        result = await conn.execute(
            "DELETE FROM market_alerts WHERE user_id=$1", user_id
        )

        # 💙 Reset alerts_used in market_alert_counter
        await conn.execute(
            "UPDATE market_alert_counter SET alerts_used = 0 WHERE user_id=$1", user_id
        )

    # 💙 Return number of deleted rows
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


# 🔮────────────────────────────────────────────
#           📝 Update Functions
# 🔮────────────────────────────────────────────
async def update_market_alert(
    bot,
    user_id: int,
    pokemon: str = None,
    dex_number: int = None,
    **updates,
):
    """
    Update one or more columns in market_alerts.

    Example:
        await update_market_alert(
            bot,
            user_id=123,
            pokemon="Pikachu",
            max_price=5000,
            notify=False
        )
    """
    if not updates:
        raise ValueError("No update values provided.")

    # Build SET clause dynamically
    set_clause = ", ".join([f"{col} = ${i+3}" for i, col in enumerate(updates.keys())])
    values = list(updates.values())

    async with bot.pg_pool.acquire() as conn:
        if dex_number is not None:
            query = f"""
                UPDATE market_alerts
                SET {set_clause}
                WHERE user_id=$1 AND dex_number=$2
            """
            result = await conn.execute(query, user_id, dex_number, *values)

        elif pokemon is not None:
            query = f"""
                UPDATE market_alerts
                SET {set_clause}
                WHERE user_id=$1 AND pokemon=$2
            """
            result = await conn.execute(query, user_id, pokemon, *values)

        else:
            raise ValueError(
                "Must provide either pokemon or dex_number for targeting row."
            )

    return int(result.split()[-1])  # returns number of rows updated


# 🔮────────────────────────────────────────────
#           📝 Bulk Update Role/Channel
# 🔮────────────────────────────────────────────
async def update_user_alerts_channel_or_role(
    bot,
    user_id: int,
    channel_id: int = None,
    role_id: int | str = None,
):
    """
    Bulk update all alerts for a user to a new channel or role.

    Only one or both of channel_id / role_id can be provided.

    Returns the number of alerts updated.
    """
    if channel_id is None and role_id is None:
        raise ValueError("Must provide at least channel_id or role_id to update.")

    if isinstance(role_id, str) and role_id.lower() == "none":
        role_id = None

    set_clauses = []
    values = []

    if channel_id is not None:
        set_clauses.append("channel_id = $1")
        values.append(channel_id)
    if role_id is not None:
        set_clauses.append("role_id = $" + str(len(values) + 1))
        values.append(role_id)

    set_sql = ", ".join(set_clauses)
    query = f"UPDATE market_alerts SET {set_sql} WHERE user_id=$" + str(len(values) + 1)
    values.append(user_id)

    async with bot.pg_pool.acquire() as conn:
        result = await conn.execute(query, *values)

    return int(result.split()[-1])  # number of rows updated
