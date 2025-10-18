# 🟣────────────────────────────────────────────
#           💜 EV Tracker DB Helpers (Current/Goal) 💜
# 🟣────────────────────────────────────────────
from utils.loggers.espeon_log import EspeonContext, espeon_log


# -------------------- Fetch All Tracked EVs --------------------
async def fetch_all_tracked_evs(bot):
    """
    Fetch all tracked EVs from DB.
    Returns list of rows with user_id, user_name, pokemon, dex_number,
    current EVs, and goal EVs.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT user_id, user_name, pokemon, dex_number,
                       hp, atk, spa, def, spd, spe,
                       hp_goal, atk_goal, spa_goal, def_goal, spd_goal, spe_goal
                FROM ev_tracker
                """
            )
        return rows
    except Exception as e:
        espeon_log(
            tag="error",
            message=f"Failed to fetch all tracked EVs: {e}",
            context=EspeonContext.STRAYMONS,
        )
        return []


# -------------------- Add or Update EV --------------------
async def add_or_update_ev(
    bot,
    user_id: int,
    user_name: str,
    pokemon: str,
    evs: dict,  # current EVs: {"hp": 0, "atk": 0, ...}
    goals: dict = None,  # goal EVs: {"hp": 252, "atk": 252, ...}
    dex_number: int = None,
):
    """
    Add or update a tracked Pokemon with current and goal EVs.
    """
    goals = goals or {}
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO ev_tracker(
                    user_id, user_name, pokemon, dex_number,
                    hp, atk, spa, def, spd, spe,
                    hp_goal, atk_goal, spa_goal, def_goal, spd_goal, spe_goal,
                    updated_at
                )
                VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,CURRENT_TIMESTAMP)
                ON CONFLICT (user_id)
                DO UPDATE SET
                    user_name = EXCLUDED.user_name,
                    pokemon = EXCLUDED.pokemon,
                    dex_number = COALESCE(EXCLUDED.dex_number, ev_tracker.dex_number),
                    hp = COALESCE(EXCLUDED.hp, ev_tracker.hp),
                    atk = COALESCE(EXCLUDED.atk, ev_tracker.atk),
                    spa = COALESCE(EXCLUDED.spa, ev_tracker.spa),
                    def = COALESCE(EXCLUDED.def, ev_tracker.def),
                    spd = COALESCE(EXCLUDED.spd, ev_tracker.spd),
                    spe = COALESCE(EXCLUDED.spe, ev_tracker.spe),
                    hp_goal = COALESCE(EXCLUDED.hp_goal, ev_tracker.hp_goal),
                    atk_goal = COALESCE(EXCLUDED.atk_goal, ev_tracker.atk_goal),
                    spa_goal = COALESCE(EXCLUDED.spa_goal, ev_tracker.spa_goal),
                    def_goal = COALESCE(EXCLUDED.def_goal, ev_tracker.def_goal),
                    spd_goal = COALESCE(EXCLUDED.spd_goal, ev_tracker.spd_goal),
                    spe_goal = COALESCE(EXCLUDED.spe_goal, ev_tracker.spe_goal),
                    updated_at = CURRENT_TIMESTAMP
                """,
                user_id,
                user_name,
                pokemon,
                dex_number,
                evs.get("hp"),
                evs.get("atk"),
                evs.get("spa"),
                evs.get("def"),
                evs.get("spd"),
                evs.get("spe"),
                goals.get("hp"),
                goals.get("atk"),
                goals.get("spa"),
                goals.get("def"),
                goals.get("spd"),
                goals.get("spe"),
            )
        espeon_log(
            tag="db",
            message=f"Set EVs for {user_id} ({user_name}) -> {pokemon} | Current: {evs} | Goal: {goals}",
            context=EspeonContext.STRAYMONS,
        )
    except Exception as e:
        espeon_log(
            tag="error",
            message=f"Failed to set EVs for {user_id} ({user_name}): {e}",
            context=EspeonContext.STRAYMONS,
        )


# -------------------- Get Tracked EV --------------------
async def get_tracked_ev(bot, user_id: int):
    """
    Get the tracked Pokemon, dex_number, user_name, current EVs, and goal EVs.
    Returns {"user_name": str, "pokemon": str, "dex_number": int, "evs": {...}, "goals": {...}} or None
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT user_name, pokemon, dex_number,
                       hp, atk, spa, def, spd, spe,
                       hp_goal, atk_goal, spa_goal, def_goal, spd_goal, spe_goal
                FROM ev_tracker
                WHERE user_id = $1
                """,
                user_id,
            )
        if not row:
            return None

        evs = {
            stat: row[stat]
            for stat in ["hp", "atk", "spa", "def", "spd", "spe"]
            if row[stat] is not None
        }
        goals = {
            stat: row[f"{stat}_goal"]
            for stat in ["hp", "atk", "spa", "def", "spd", "spe"]
            if row[f"{stat}_goal"] is not None
        }

        return {
            "user_name": row["user_name"],
            "pokemon": row["pokemon"],
            "dex_number": row["dex_number"],
            "evs": evs,
            "goals": goals,
        }
    except Exception as e:
        espeon_log(
            tag="error",
            message=f"Failed to get EVs for user {user_id}: {e}",
            context=EspeonContext.STRAYMONS,
        )
        return None


# -------------------- Delete Tracked EV --------------------
async def delete_tracked_ev(bot, user_id: int):
    """
    Delete the tracked Pokemon for a user.
    Returns True if deleted, False otherwise.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM ev_tracker WHERE user_id = $1", user_id
            )
        deleted = result.endswith("DELETE 1")
        espeon_log(
            tag="db",
            message=f"Deleted EVs for user {user_id}: {deleted}",
            context=EspeonContext.STRAYMONS,
        )
        return deleted
    except Exception as e:
        espeon_log(
            tag="error",
            message=f"Failed to delete EVs for user {user_id}: {e}",
            context=EspeonContext.STRAYMONS,
        )
        return False
