import discord

from utils.cache.cache_list import user_balance_cache
from utils.database.server_currency import fetch_all_user_balances
from utils.loggers.espeon_log import EspeonContext, espeon_log


# 💜────────────────────────────────────────────
#   🟣 User Balance Cache Manager 🟣
# 💜────────────────────────────────────────────
async def load_user_balance_cache(bot: discord.Client):
    """
    Load all user balances from the database into the cache.
    """
    rows = await fetch_all_user_balances(bot)
    for row in rows:
        user_balance_cache[row["user_id"]] = {
            "user_name": row.get("user_name"),
            "cherry_pin_balance": row.get("cherry_pin_balance", 0),
            "bought_daisyia_box": row.get("bought_daisyia_box", "no"),
            "bought_gardelette_box": row.get("bought_gardelette_box", "no"),
            "bought_melaryne_box": row.get("bought_melaryne_box", "no"),
        }

    espeon_log(
        tag="cache",
        message=f"Loaded {len(rows)} user balances into cache",
        label="💰 USER BALANCE CACHE",
        context=EspeonContext.ESPEON,
    )
    return user_balance_cache


def fetch_user_balance_from_cache(user_id: int) -> int | None:
    """
    Fetch a user's balance from the cache.
    """
    user_data = user_balance_cache.get(user_id)
    if user_data:
        return user_data.get("cherry_pin_balance", 0)
    return None


def upsert_user_balance_in_cache(
    user_id: int,
    user_name: str,
    amount: int = 0,
    bought_daisyia_box: str = "no",
    bought_gardelette_box: str = "no",
    bought_melaryne_box: str = "no",
):
    """
    Upsert a user's balance in the cache.
    """
    user_balance_cache[user_id] = {
        "user_name": user_name,
        "cherry_pin_balance": amount,
        "bought_daisyia_box": bought_daisyia_box,
        "bought_gardelette_box": bought_gardelette_box,
        "bought_melaryne_box": bought_melaryne_box,
    }
    espeon_log(
        tag="cache",
        message=f"Upserted user '{user_name}' (user_id: {user_id}) with balance {amount} in cache",
        label="💰 USER BALANCE CACHE",
        context=EspeonContext.ESPEON,
    )


def update_user_balance_in_cache(user_id: int, user_name: str, new_balance: int):
    """
    Update a user's balance in the cache.
    """
    if user_id in user_balance_cache:
        user_balance_cache[user_id]["cherry_pin_balance"] = new_balance
        espeon_log(
            tag="cache",
            message=f"Updated balance for '{user_name}' to {new_balance} in cache",
            label="💰 USER BALANCE CACHE",
            context=EspeonContext.ESPEON,
        )

def  bought_box_in_cache(user_id: int, box_type: str):
    """
    Mark that a user has bought a specific box in the cache.
    """
    if user_id in user_balance_cache:
        if box_type == "daisyia":
            user_balance_cache[user_id]["bought_daisyia_box"] = "yes"
        elif box_type == "gardelette":
            user_balance_cache[user_id]["bought_gardelette_box"] = "yes"
        elif box_type == "melaryne":
            user_balance_cache[user_id]["bought_melaryne_box"] = "yes"
        espeon_log(
            tag="cache",
            message=f"Marked '{user_balance_cache[user_id]['user_name']}' as having bought the {box_type} box in cache",
            label="💰 USER BALANCE CACHE",
            context=EspeonContext.ESPEON,
        )
        
def delete_user_balance_from_cache(user_id: int, user_name: str):
    """
    Remove a user's balance from the cache.
    """
    if user_id in user_balance_cache:
        del user_balance_cache[user_id]
        espeon_log(
            tag="cache",
            message=f"Removed '{user_name}' from user balance cache",
            label="💰 USER BALANCE CACHE",
            context=EspeonContext.ESPEON,
        )


def reset_all_user_balances_in_cache():
    """
    Clear the entire user balance cache.
    """
    user_balance_cache.clear()
    espeon_log(
        tag="cache",
        message="Cleared all user balances from cache",
        label="💰 USER BALANCE CACHE",
        context=EspeonContext.ESPEON,
    )
