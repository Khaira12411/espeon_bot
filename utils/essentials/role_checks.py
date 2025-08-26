from discord.ext import commands

from config.straymons_constants import STRAYMONS__ROLES

# 🌸──────────────────────────────────────────────────────
# ✨ Custom Exceptions (Sparkles & Cute!) ✨
# ───────────────────────────────────────────────────────
class ClanStaffCheckFailure(commands.CheckFailure):
    pass


class VIPCheckFailure(commands.CheckFailure):
    pass


class ClanMemberCheckFailure(commands.CheckFailure):
    pass


class OwnerCheckFailure(commands.CheckFailure):
    pass


class OwnerCoownerCheckFailure(commands.CheckFailure):
    pass


# 🌸──────────────────────────────────────────────────────
# 🐾💫 Cute Error Messages by Server — Cottagecore Style 💫🌿
# ───────────────────────────────────────────────────────
ERROR_MESSAGES = {
    "straymons": {
        "clan_staff": "❌ You don’t have the 🐾 Clan Staff role! ✨",
        "vip": "✨ You need the VIP role to sparkle here! 💖",
        "clan_member": "🐾 Only Straymon Members can use this command. 🌸",
        "owner": "👑 This command is just for the Clan Owner, sorry! 💜",
        "owner_and_co_owner": "👑 & 🤝 Only Clan Owner and Co-Owner can use this. 🌷",
        "espeon_roles": f"Only those with <@&{STRAYMONS__ROLES.ethereal_eclair}>, and <@&{STRAYMONS__ROLES.sunrise_scone}> can use this command!",
    },
}


# 🌸──────────────────────────────────────────────────────
# 🌿✨ Straymon Server Role Checks — Playful & Sparkly ✨🌿
# ───────────────────────────────────────────────────────
def clan_staff_only():
    async def predicate(ctx):
        if STRAYMONS__ROLES.clan_staff not in [role.id for role in ctx.author.roles]:
            raise ClanStaffCheckFailure(ERROR_MESSAGES["straymons"]["clan_staff"])
        return True

    return commands.check(predicate)


def vip_only():
    async def predicate(ctx):
        if STRAYMONS__ROLES.vip not in [role.id for role in ctx.author.roles]:
            raise VIPCheckFailure(ERROR_MESSAGES["straymons"]["vip"])
        return True

    return commands.check(predicate)


def clan_member_only():
    async def predicate(ctx):
        user_roles = [role.id for role in ctx.author.roles]
        if STRAYMONS__ROLES.straymon not in user_roles:
            raise ClanMemberCheckFailure(ERROR_MESSAGES["straymons"]["clan_member"])
        return True

    return commands.check(predicate)


def owner_only():
    async def predicate(ctx):
        user_roles = [role.id for role in ctx.author.roles]
        if STRAYMONS__ROLES.clan_owner not in user_roles:
            raise OwnerCheckFailure(ERROR_MESSAGES["straymons"]["owner"])
        return True

    return commands.check(predicate)


def owner_and_co_owner_only():
    async def predicate(ctx):
        user_roles = [role.id for role in ctx.author.roles]
        if (
            STRAYMONS__ROLES.clan_owner not in user_roles
            and STRAYMONS__ROLES.clan_co_owner not in user_roles
        ):
            raise OwnerCoownerCheckFailure(
                ERROR_MESSAGES["straymons"]["owner_and_co_owner"]
            )
        return True

    return commands.check(predicate)


def espeon_roles_only():
    async def predicate(ctx):
        user_roles = [role.id for role in ctx.author.roles]

        # ✅ Bypass for Clan Staff
        if STRAYMONS__ROLES.clan_staff in user_roles:
            return True

        # 🔒 Require Espeon roles
        if (
            STRAYMONS__ROLES.sunrise_scone not in user_roles
            and STRAYMONS__ROLES.ethereal_eclair not in user_roles
        ):
            raise OwnerCoownerCheckFailure(
                ERROR_MESSAGES["straymons"]["owner_and_co_owner"]
            )

        return True

    return commands.check(predicate)
