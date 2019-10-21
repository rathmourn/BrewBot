from discord.ext import commands
import pydest
import json
import config


class BungieAPI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def api_dump(self, ctx, player_name):
        destiny = pydest.Pydest(config.BUNGIE_API_KEY)

        response = await destiny.api.search_destiny_player(3, player_name)
        await ctx.send("`BungieID: " + str(response['Response'][0]['membershipId']) + "`")

        bungie_id = str(response['Response'][0]['membershipId'])

        bungie_profile = await destiny.api.get_profile(3, bungie_id, components=['100', '204'])
        print(bungie_profile)


        history_report = await destiny.api.get_character_activities(3, bungie_id, 2305843009401705411, 0)
        print(history_report)

        last_activity_time = ""
        total_seconds_played = 0

        for player_activity in history_report['Response']['activities']:
            time_played = player_activity['values']['timePlayedSeconds']['basic']['value']
            print(player_activity['period'] + " : " + str(time_played))
            total_seconds_played += time_played
            last_activity_time = player_activity['period']

        await ctx.send("`You have played " + str(total_seconds_played) + " seconds in destiny since " + str(last_activity_time) + ".`")
        await destiny.close()


def setup(bot):
    print("[*] Loading BungieAPI extension.")
    bot.add_cog(BungieAPI(bot))

# Cog/Extension exit point
def teardown(bot):
    print("[*] Unloading BungieAPI extension.")
    bot.remove_cog('BungieAPI')