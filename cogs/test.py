from discord.ext import commands
from db.db_config import ClanMember, DiscordInfo, BungieInfo
import datetime


class TestCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def tools(self, ctx):
        await ctx.send("Testing database connection.")
        print(self.bot.db_session)

        new_clan_member = ClanMember(
            created_at=datetime.datetime.now(),
            clan_activity_score=1,
            discord_user_info=DiscordInfo(),
            bungie_user_info=BungieInfo()
        )
        self.bot.db_session.add(new_clan_member)
        self.bot.db_session.commit()

        members = self.bot.db_session.query(ClanMember).all()
        print(members)
        for member in members:
            print(member.id)
            print(member.created_at)


def setup(bot):
    print("Loading test module.")
    bot.add_cog(TestCommand(bot))