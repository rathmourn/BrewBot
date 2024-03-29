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

        self.clan_roster_update.start()
        self.clan_activity_update.start()
        self.clan_discord_name_update.start()

    def cog_unload(self):
        self.clan_roster_update.cancel()
        self.clan_activity_update.cancel()
        self.clan_discord_name_update.cancel()

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

            with open(config.BOT_BASEDIR + "clans/" + str(clan['clan_id']) + ".json", 'w+') as clan_data_file:
                json.dump(clan_data, clan_data_file)

        print("[*] >>> BACKGROUND: Clan rosters updated!")

    @clan_roster_update.before_loop
    async def before_clan_roster_update(self):
        print("Waiting to start clan roster updater until bot is ready...")
        await self.bot.wait_until_ready()

    # End of Clan Roster Updater
    ####################################################################################################################

    ####################################################################################################################
    # Clan Discord Name Updater

    @tasks.loop(hours=1)
    async def clan_discord_name_update(self):
        print("[*] >>> BACKGROUND: Updating clan's discord names in DB...")

        for user_file in os.listdir(config.BOT_DB):
            if user_file.endswith(".json"):
                with open(config.BOT_DB + user_file) as user_file_data:
                    user_data = json.load(user_file_data)
                           
                for guild in self.bot.guilds:
                    # Only do Ace's Brew Discord
                    if guild.id == 534781834924523520:
                        for member in guild.members:
                            if str(member.id) == str(user_data['discord_id']):
                                if member.nick is not None:
                                    user_data['discord_name'] = str(member.nick)
                                else:
                                    user_data['discord_name'] = str(member.display_name)

                                with open(config.BOT_DB + user_file, 'w') as user_write_file:
                                    json.dump(user_data, user_write_file)

        print("[*] >>> BACKGROUND: Discord names updated!")

    @clan_discord_name_update.before_loop
    async def before_discord_clan_update(self):
        print("Waiting to start clan discord name updater until bot is ready...")
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

                print("[*] >>> BACKGROUND: Updating to {}'s stats...".format(user_data['bungie_name']))

                # Calculate discord stats
                discord_stats = await activity_manager.get_user_discord_activity_stats(user_data['discord_id'])

                # Update the data in the user's record
                user_data['chat_events'] = discord_stats['chat_events']
                user_data['characters_typed'] = discord_stats['characters_typed']
                user_data['vc_minutes'] = discord_stats['vc_minutes']

                # Calculate bungie stats
                daily_bungie_stats = {}

                today_utc = datetime.datetime.utcnow()
                today_report = today_utc.strftime("%Y-%m-%d")
                reporting_period = (today_utc - datetime.timedelta(days=(int(config.STATISTICS_PERIOD))))

                iter_date = reporting_period

                while iter_date < today_utc:
                    print(">>> STATS FOR: {}".format(iter_date))

                    # See if we have stats already for that date (we don't pull current day))
                    if iter_date.strftime("%Y-%m-%d") in user_data['game_activity'].keys() and iter_date.strftime("%Y-%m-%d") != today_report:
                        daily_bungie_stats.update(
                            {
                                iter_date.strftime("%Y-%m-%d"): user_data['game_activity'][iter_date.strftime("%Y-%m-%d")]
                            }
                        )

                    # If we don't, get them
                    else:
                        bungie_stats = await activity_manager.get_user_bungie_activity_stats(user_data['bungie_id'], iter_date)

                        daily_bungie_stats.update(
                            {
                                iter_date.strftime("%Y-%m-%d"): {
                                    "seconds_played": bungie_stats['seconds_played'],
                                    "unique_clan_members_played_with": bungie_stats['unique_clan_members_played_with'],
                                    "clan_members_played_with": bungie_stats['clan_members_played_with']
                                }
                            }
                        )

                    iter_date = iter_date + datetime.timedelta(days=1)

                # Update the data in the user's record.
                user_data['game_activity'] = daily_bungie_stats


                total_seconds_played = 0
                total_unique_members_played_with = 0
                total_clan_members_played_with = 0

                for stat_day, stat_values in user_data['game_activity'].items():
                    total_seconds_played += user_data['game_activity'][stat_day]['seconds_played']
                    total_unique_members_played_with += user_data['game_activity'][stat_day]['unique_clan_members_played_with']
                    total_clan_members_played_with += user_data['game_activity'][stat_day]['clan_members_played_with']

                bonus_multiplier = total_clan_members_played_with + total_unique_members_played_with
                activity_score = total_seconds_played + (user_data['chat_events'] * 60) + \
                                               (user_data['characters_typed'] * 3) * bonus_multiplier

                user_data['clan_activity_score'] = activity_score

                with open(config.BOT_DB + user_file, 'w') as user_file_data:
                    json.dump(user_data, user_file_data)

                print("[*] >>> BACKGROUND: Update to {}'s stats complete.".format(user_data['bungie_name']))

        print("[*] >>> Updating clan activity scores updated in background complete!")


    @clan_activity_update.before_loop
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

