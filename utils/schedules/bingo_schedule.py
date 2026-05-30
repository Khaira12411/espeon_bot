import discord
from datetime import datetime
from config.aesthetic import Espeon_Emoji
from config.current_setup import STRAYMONS_GUILD_ID
from config.petal_lace_settings import COLOR
from config.straymons_constants import STRAYMONS__ROLES, STRAYMONS__TEXT_CHANNELS
from utils.loggers.espeon_log import espeon_log


async def scheduled_bingo_opening(bot: discord.Client):
    guild = bot.get_guild(STRAYMONS_GUILD_ID)
    if not guild:
        espeon_log(
            "error",
            "Straymons guild not found when trying to post Bingo news.",
            source="Bingo Event Post",
        )
        return

    news_channel = guild.get_channel(STRAYMONS__TEXT_CHANNELS.clueberry)
    if news_channel is None:
        espeon_log(
            "error",
            "Bingo news channel not found when trying to post event news.",
            source="Bingo Event Post",
        )
        return

    straymons_role = guild.get_role(STRAYMONS__ROLES.straymon)
    if straymons_role is None:
        espeon_log(
            "error",
            "Straymons role not found when trying to post Bingo news.",
            source="Bingo Event Post",
        )
        return

    content = f"{straymons_role.mention} {Espeon_Emoji.pink_flower_two}"
    NEWS_POST_DESC = f"""## __Carnivalesque__ <a:sakura_branch:1473977291276161251>
-# Each member will choose a partner to form a team of two with and be received with a [bingo](https://cdn.discordapp.com/attachments/1330619831627812904/1510268245972615298/straymons_1.png?ex=6a1c3269&is=6a1ae0e9&hm=dadbf9c4d7664bd867319e74264125c458949557a8e32a6a68745140abeb7549&) card.

Each team will have to work together and complete a full line in the card from successful tasks or missions associated with a specific box in the card. The first six teams to finish a line, wins. There are a total of 24 tasks which are divided into team mission or individual tasks. Each team will have their own channel during the duration of the event.

-# __Team missions__ can be completed if **any one member of the team** successfully completed a mission.
-# __Individual tasks__ can be completed if **both members of the team** successfully completed a task.

There will be four special quests from Skaia every week from the start of the event. These quests will **only appear in your DMs** and it's considered an __individual task__. The prerequisites for getting these special quests are unknown, so keep playing in the event and good luck figuring it out!

__**Prize Pool**__
-# There are various prizes to be won and staffs can also participate in the event to win them if they wished to. The [prize pot](https://cdn.discordapp.com/attachments/1330619831627812904/1510268232156582088/image2.png?ex=6a1c3265&is=6a1ae0e5&hm=ee04fedaa66d6ffa2064597892246f96fd32d02aaba66fa7e9ad1636ec6ba4cf&) will be divided amongst the winners evenly along with different prizes based on standings. Consolation prizes will be 1,000,000 <:PokeCoin:1166253401546436648> each."""

    embed = discord.Embed(
        description=NEWS_POST_DESC,
        color=COLOR,
        timestamp=datetime.now(),
    )
    await news_channel.send(content=content, embed=embed)
