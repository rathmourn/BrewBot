from discord.ext import commands


class TestCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def tools(self, ctx):
        await ctx.send("Tools functional.")
        print("tools invoked.")


def setup(bot):
    print("Loading TestCommand extension")
    bot.add_cog(TestCommand(bot))
