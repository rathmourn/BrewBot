from discord.ext import commands
import discord


def is_authorized():
    async def check_authorization(ctx):
        return str(ctx.author.display_name) == "Rathmourn"
    return commands.check(check_authorization)


class ClanActivity(commands.Cog):
    """
    Base cog class to support all clan activity reporting for BrewBot.
    """

    def __init__(self, bot):
        self.bot = bot

    # ---- HELPER FUNCTIONS
    # ---- END HELPER FUNCTIONS

    @commands.command(hidden=True)
    @is_authorized()
    async def tools(self, ctx):
        await ctx.send("Developer tools invoked.")

    @tools.error
    async def tools_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("Unauthorized.")


# Cog extension entry point
def setup(bot):
    print("[*] Loading Clan Activity module.")
    bot.add_cog(ClanActivity(bot))


# Cog extension exit point
def teardown(bot):
    print("[*] Unloading Clan Activity module.")
    bot.remove_cog('ClanActivity')

