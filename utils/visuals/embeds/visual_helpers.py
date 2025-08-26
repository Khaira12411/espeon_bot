import discord


def set_embed_user_context(
    embed: discord.Embed, user: discord.User | discord.Member
) -> discord.Embed:
    """
    Sets the embed's author and thumbnail to match the user's display name and avatar.
    - Author text = user's display name
    - Author icon = user's avatar
    - Thumbnail = user's avatar
    Returns the modified embed.
    """
    avatar_url = user.display_avatar.url
    embed.set_author(name=user.display_name, icon_url=avatar_url)
    embed.set_thumbnail(url=avatar_url)
    embed.set_footer(text=f"💫 User ID: {user.id}", icon_url=user.guild.icon.url)
    return embed
