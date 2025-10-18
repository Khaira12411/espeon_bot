# 🟣────────────────────────────────────────────
#           💜 Market Alert Cache Loader (Indexed) 💜
# ─────────────────────────────────────────────

import sys

from utils.group_func.market_alert.db_func.market_alert_db_func import (
    fetch_active_market_alerts,
)
from utils.loggers.espeon_log import EspeonContext, espeon_log

# Global cache list & index
market_alert_cache: list[dict] = []
_market_alert_index: dict[tuple[str, int], dict] = (
    {}
)  # key = (pokemon.lower(), channel_id)


# -------------------- Load Cache --------------------
async def load_market_alert_cache(bot):
    market_alert_cache.clear()
    _market_alert_index.clear()

    active_alerts = await fetch_active_market_alerts(bot)
    # espeon_log("info", f"[Market Alert Cache] DB returned {len(active_alerts)} alerts")

    for alert in active_alerts:
        alert_entry = {
            "pokemon": alert["pokemon"].lower(),
            "dex_number": alert["dex_number"],
            "max_price": alert["max_price"],
            "channel_id": alert["channel_id"],
            "role_id": alert.get("role_id"),
            "notify": alert.get("notify", True),
            "user_id": alert.get("user_id"),
        }
        market_alert_cache.append(alert_entry)

        key = (
            alert_entry["pokemon"],
            alert_entry["channel_id"],
            alert_entry["user_id"],
        )
        _market_alert_index[key] = alert_entry

    """espeon_log(
        "info",
        f"[Market Alert Cache] After load → {len(market_alert_cache)} in list, {len(_market_alert_index)} in index (sample keys: {list(_market_alert_index.keys())[:3]})",
    )"""

    return market_alert_cache


# -------------------- Cache Size Helper --------------------
def get_cache_size(cache: list) -> int:
    total = sys.getsizeof(cache)
    for entry in cache:
        total += sys.getsizeof(entry)
        for k, v in entry.items():
            total += sys.getsizeof(k) + sys.getsizeof(v)
    return total


# -------------------- Insert / Update / Remove --------------------
def insert_alert(alert: dict):
    """Insert new alert or update existing alert if same (pokemon, channel_id, user_id)."""
    key = (alert["pokemon"].lower(), alert["channel_id"], alert["user_id"])
    existing = _market_alert_index.get(key)

    if existing:
        # Update existing alert (sync both index + list)
        existing.update(alert)
        # Ensure list entry is updated too
        for i, entry in enumerate(market_alert_cache):
            if (
                entry["pokemon"].lower() == alert["pokemon"].lower()
                and entry["channel_id"] == alert["channel_id"]
                and entry["user_id"] == alert["user_id"]
            ):
                market_alert_cache[i] = existing
                break
        _log_cache_size(
            f"Updated existing alert for {alert['pokemon']} in channel {alert['channel_id']} (user {alert['user_id']})"
        )
    else:
        # Insert new alert
        market_alert_cache.append(alert)
        _market_alert_index[key] = alert
        _log_cache_size(
            f"Inserted alert for {alert['pokemon']} in channel {alert['channel_id']} (user {alert['user_id']})"
        )


def remove_alert(pokemon_name: str, channel_id: int, user_id: int):
    """
    Remove a single alert for a specific user, pokemon, and channel.
    -> Update the main market_alert_cache first, then remove any matching keys
       from _market_alert_index (safer if index is stale/broken).
    """
    p_lower = pokemon_name.lower()

    # ---- Remove from main list first ----
    removed_any = False
    # Build a new list skipping the entries we want removed, then replace in-place
    new_list = []
    for entry in market_alert_cache:
        if (
            entry.get("pokemon", "").lower() == p_lower
            and entry.get("channel_id") == channel_id
            and entry.get("user_id") == user_id
        ):
            removed_any = True
            # skip (this is the removed entry)
        else:
            new_list.append(entry)
    market_alert_cache[:] = new_list

    # ---- Then remove from index (clean up any stale keys) ----
    keys_to_remove = [
        k
        for k in list(_market_alert_index.keys())
        if k[0] == p_lower and k[1] == channel_id and k[2] == user_id
    ]
    for k in keys_to_remove:
        _market_alert_index.pop(k, None)

    if removed_any or keys_to_remove:
        _log_cache_size(
            f"Removed alert for {pokemon_name} on channel {channel_id} for user {user_id}"
        )
    else:
        # optional: log that nothing was found (helps debugging)
        _log_cache_size(
            f"No alert found to remove for {pokemon_name} on channel {channel_id} for user {user_id}"
        )


def remove_all_alerts_from_user(user_id: int):
    """Remove all market alerts for a specific user from both cache and index."""
    # Remove from list
    market_alert_cache[:] = [a for a in market_alert_cache if a["user_id"] != user_id]

    # Remove from index
    keys_to_remove = [k for k in _market_alert_index if k[2] == user_id]
    for key in keys_to_remove:
        _market_alert_index.pop(key, None)

    _log_cache_size(f"Removed all alerts for user {user_id}")


def get_alert(pokemon_name: str, channel_id: int, user_id: int) -> dict | None:
    """Retrieve alert by pokemon + channel + user."""
    return _market_alert_index.get((pokemon_name.lower(), channel_id, user_id))


def fetch_user_alerts_from_cache(user_id: int) -> list[dict]:
    user_alerts = [a for a in market_alert_cache if a["user_id"] == user_id]
    return user_alerts


# -------------------- Bulk Update (Channel/Role) --------------------


def update_user_alerts_in_cache(
    user_id: int,
    new_channel_id: int | None = None,
    new_role_id: int | None = None,
    new_notify: bool | None = None,
    target_pokemon: str | None = None,
):
    """
    Update alerts in cache for a given user.
    - If target_pokemon is None → update all of the user’s alerts.
    - If target_pokemon is provided → update only that Pokemon’s alert.
    Works on both the main cache list and the index.
    """
    updated = 0
    target_pokemon = target_pokemon.lower() if target_pokemon else None

    for i, alert in enumerate(market_alert_cache):
        if alert["user_id"] != user_id:
            continue
        if target_pokemon and alert["pokemon"].lower() != target_pokemon:
            continue

        # Update alert dict
        if new_channel_id is not None:
            alert["channel_id"] = new_channel_id
        if new_role_id is not None or new_role_id is None:  # allow explicit removal
            alert["role_id"] = new_role_id
        if new_notify is not None:
            alert["notify"] = new_notify

        market_alert_cache[i] = alert  # keep list updated

        # Rebuild index for this alert
        keys_to_remove = []
        for key, val in _market_alert_index.items():
            if val is alert or (
                val["user_id"] == user_id
                and val["pokemon"].lower() == alert["pokemon"].lower()
            ):
                keys_to_remove.append(key)
        for key in keys_to_remove:
            _market_alert_index.pop(key, None)

        new_key = (alert["pokemon"].lower(), alert["channel_id"], alert["user_id"])
        _market_alert_index[new_key] = alert

        updated += 1

    _log_cache_size(
        f"Updated {updated} alert(s) for user {user_id}{' (filtered)' if target_pokemon else ''}"
    )
    return updated


# -------------------- Internal Logging --------------------
def _log_cache_size(action: str):
    size_bytes = get_cache_size(market_alert_cache)
    size_kb = size_bytes / 1024
    espeon_log(
        tag="",
        label="🦄 MARKET ALERT CACHE",
        message=f"{action} — cache now has {len(market_alert_cache)} alerts (~{size_kb:.2f} KB)",
        context=EspeonContext.STRAYMONS,
    )
