import datetime
import discord
import json
import os
import bungie_api
from discord.ext import commands, tasks
import cogs.clan_activity

import config

class BackgroundTasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        #self.clan_roster_update.start()
        #self.clan_activity_update.start()

    def cog_unload(self):
        self.clan_roster_update.cancel()
        self.clan_activity_update.cancel()

    ####################################################################################################################
    # Clan Roster Updater

    @tasks.loop(hours=1)
    async def clan_roster_update(self):
        print("[*] >>> BACKGROUND: Updating clan rosters per background task...")
        for clan in config.BREW_CLANS:
            clan_members = bungie_api.generate_clan_list(clan['clan_id'])

            clan_data = {}
            clan_data.update({'last_updated': str(datetime.datetime.utcnow())})
            clan_data.update({'members': clan_members})

            with open("clans/" + str(clan['clan_id']) + ".json", 'w+') as clan_data_file:
                json.dump(clan_data, clan_data_file)

        print("[*] >>> BACKGROUND: Clan rosters updated!")

    @clan_roster_update.before_loop
    async def before_clan_roster_update(self):
        print("Waiting to start clan roster updater until bot is ready...")
        await self.bot.wait_until_ready()

    # End of Clan Roster Updater
    ####################################################################################################################

    ####################################################################################################################
    # Clan Activity Updater

    @tasks.loop(hours=24)
    async def clan_activity_update(self):
        print("[*] >>> Updating clan activity scores per background task...")
        activity_manager = cogs.clan_activity.ClanActivity(self.bot)

        for user_file in os.listdir(config.BOT_DB):
            if user_file.endswith(".json"):
                with open(config.BOT_DB + user_file) as user_file_data:
                    user_data = json.load(user_file_data)

                print("[*] >>> BACKGROUND: Updating {}'s stats...".format(user_data['bungie_name']))
                # Discord Stats Update
                discord_stats = await activity_manager.get_user_discord_activity_stats(user_data['discord_id'])

                # Update the data in the user's record
                user_data['chat_events'] = discord_stats['chat_events']
                user_data['characters_typed'] = discord_stats['characters_typed']
                user_data['vc_minutes'] = discord_stats['vc_minutes']


                # Bungie Stats
                bungie_stats = await activity_manager.get_user_bungie_activity_stats(user_data['bungie_id'])

                # Update the data in the user's record.
                user_data['seconds_played'] = bungie_stats['seconds_played']
                user_data['clan_members_played_with'] = bungie_stats['clan_members_played_with']
                user_data['unique_clan_members_played_with'] = bungie_stats['unique_clan_members_played_with']

                # Calculate Scores and update
                bonus_multiplier = user_data['unique_clan_members_played_with'] + user_data[
                    'clan_members_played_with']
                user_data['clan_activity_score'] = user_data['seconds_played'] + (user_data['chat_events'] * 60) + \
                                                   (user_data['characters_typed'] * 3) * bonus_multiplier

                with open(config.BOT_DB + user_file, 'w') as user_file_data:
                    json.dump(user_data, user_file_data)

                print("[*] >>> BACKGROUND: Update to {}'s stats complete.".format(user_data['bungie_name']))

        print("[*] >>> Updating clan activity scores updated in background complete!")


    @clan_roster_update.before_loop
    async def before_clan_activity_update(self):
        print("Waiting to start clan activity updater until bot is ready...")
        await self.bot.wait_until_ready()

    # End of Clan Roster Updater
    ####################################################################################################################

# Cog extension entry point
def setup(bot):
    print("[*] Loading Background Tasks module.")
    bot.add_cog(BackgroundTasks(bot))

# Cog extension exit point
def teardown(bot):
    print("[*] Unloading Background Tasks module.")
    bot.remove_cog('BackgroundTasks')

