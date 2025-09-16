from utils.cache.wb_sub_cache import (
    wb_cache_upsert,
    wb_cache_update_variant_mode,
    wb_cache_remove,
    wb_cache_remove_all,
)
from utils.group_func.wb_sub import wb_sub_db_func as db
from utils.loggers.espeon_log import espeon_log, EspeonContext

# 💜────────────────────────────────────────────
#   🟣 WB Ping Sync Wrappers (DB + Cache)
# 💜────────────────────────────────────────────


async def sync_upsert_wb_ping(
    bot,
    user_id: int,
    user_name: str,
    variant: str,
    boss_name: str,
    mode: str,
    channel_id: int = None,
) -> bool:
    """
    Upsert WB ping in DB, then reflect change in cache.
    """
    row = await db.upsert_user_wb_ping(
        bot=bot,
        user_id=user_id,
        user_name=user_name,
        variant=variant,
        boss_name=boss_name,
        mode=mode,
        channel_id=channel_id,
    )

    if row:  # row contains all fields including created_at
        wb_cache_upsert(
            {
                "user_id": row["user_id"],
                "user_name": row["user_name"],
                "variant": row["variant"],
                "boss_name": row["boss_name"].lower(),
                "mode": row["mode"],
                "channel_id": row["channel_id"],
                "created_at": row["created_at"],
            }
        )

        espeon_log(
            tag="db",
            message=f"💜 Upserted WB Ping for user {user_id}, boss {boss_name}",
            label="🦑 WB SYNC",
            context=EspeonContext.STRAYMONS,
        )
        return True

    return False


async def sync_update_variant_mode(
    bot, user_id: int, boss_name: str, new_variant: str, new_mode: str
) -> bool:
    """
    Update variant/mode in DB, then reflect in cache.
    """
    success = await db.update_user_wb_ping_variant_mode(
        bot, user_id, boss_name, new_variant, new_mode
    )
    if success:
        wb_cache_update_variant_mode(user_id, boss_name, new_variant, new_mode)
        espeon_log(
            tag="db",
            message=f"💜 Updated variant/mode for user {user_id}, boss {boss_name} -> {new_variant}/{new_mode}",
            label="🦑 WB SYNC",
            context=EspeonContext.STRAYMONS,
        )
    return success


async def sync_remove_wb_ping(bot, user_id: int, boss_name: str) -> bool:
    """
    Remove WB ping row in DB, then reflect in cache.
    """
    success = await db.remove_user_wb_ping(bot, user_id, boss_name)
    if success:
        wb_cache_remove(user_id, boss_name)
        espeon_log(
            tag="db",
            message=f"💜 Removed WB Ping for user {user_id}, boss {boss_name}",
            label="🦑 WB SYNC",
            context=EspeonContext.STRAYMONS,
        )
    return success


async def sync_remove_all_wb_pings(bot, user_id: int) -> bool:
    """
    Remove all WB pings for user in DB, then reflect in cache.
    """
    success = await db.remove_all_user_wb_pings(bot, user_id)
    if success:
        wb_cache_remove_all(user_id)
        espeon_log(
            tag="db",
            message=f"💜 Removed all WB Pings for user {user_id}",
            label="🦑 WB SYNC",
            context=EspeonContext.STRAYMONS,
        )
    return success
