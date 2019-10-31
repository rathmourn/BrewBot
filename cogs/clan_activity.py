import datetime
import os
import json
from discord.ext import commands
import discord
import pydest

import config


def is_authorized():
    """
    Command decorator to validate if a user is authorized for a bot's command or not.
    Returns: None

    """

    async def check_authorization(ctx):
        return str(ctx.author.display_name) == "Rathmourn"

    return commands.check(check_authorization)


class ClanActivity(commands.Cog):
    """
    Base cog class to support all clan activity reporting for BrewBot.
    """

    def __init__(self, bot):
        self.bot = bot


    @commands.command(hidden=True)
    @is_authorized()
    async def ctest(self, ctx, profile_name):
        print(self.bot.guilds)


    @commands.command(hidden=True)
    @is_authorized()
    async def api_dump(self, ctx, bungie_id):
        destiny = pydest.Pydest(config.BUNGIE_API_KEY)

        response = await destiny.api.get_profile(3, bungie_id, components=[100])
        await ctx.send(response)
        print(response)

        await destiny.close()

    @commands.command(hidden=True)
    @is_authorized()
    async def api_search(self, ctx, profile_name):
        destiny = pydest.Pydest(config.BUNGIE_API_KEY)

        response = await destiny.api.search_destiny_player(3, profile_name)
        await ctx.send(response)
        print(response)

        await destiny.close()

    @commands.command()
    async def activity(self, ctx, *args):
        """Give a user their activity stats.

            If given no arguments, pulls the sender's stats.
            Otherwise `$activity [user]` will attempt to pull that user's activity stats.
        """

        if len(args) > 0:
            search_entity = str(args[0]).lower()
        else:
            search_entity = None

        with ctx.typing():
            try:
                if search_entity is None:
                    with open(config.BOT_DB + str(ctx.author.id) + ".json") as user_data_file:
                        user_data = json.load(user_data_file)
                else:
                    for user_file in os.listdir("users/"):
                        with open(config.BOT_DB + str(user_file)) as user_data_file:
                            user_data = json.load(user_data_file)

                        if str(user_data['discord_name']).lower() == search_entity or str(user_data['bungie_name']).lower() == search_entity:
                            break


                embed = discord.Embed(title="Clan Activity Report",
                                      description="{}'s activity score over the last {} days".format(user_data['bungie_name'], config.STATISTICS_PERIOD))

                embed.add_field(name="Discord Messages", value=user_data['chat_events'], inline=True)
                embed.add_field(name="Discord Characters Sent", value=user_data['characters_typed'], inline=True)
                embed.add_field(name="Destiny Time Played",
                                value=str(datetime.timedelta(seconds=user_data['seconds_played'])), inline=False)
                embed.add_field(name="Different Clan Members Played With ", value=user_data['unique_clan_members_played_with'],
                                inline=True)
                embed.add_field(name="Total Activity Score", value=int(user_data['clan_activity_score']), inline=False)

                await ctx.send(embed=embed)
            except FileNotFoundError:
                await ctx.send(
                    "You do not appear to be registered. If you believe to be in error, please contact an admin.")

    @commands.command()
    @is_authorized()
    async def activity_update(self, ctx, *args):
        """Update activity stats and scores. [ADMIN ONLY]

            No arguments will update everyone.
            `$activity_update [user]` will attempt to update just that user.
        """
        if len(args) > 0:
            search_name = args[0]
            search_name = search_name.lower()
        else:
            if ctx.author.nick:
                search_name = str(ctx.author.nick).lower()
            else:
                search_name = str(ctx.author.display_name).lower()

        for user_file in os.listdir(config.BOT_DB):
            if user_file.endswith(".json"):
                with open(config.BOT_DB + user_file) as user_file_data:
                    user_data = json.load(user_file_data)

                if search_name is not None:
                    if user_data['bungie_id'].lower() != search_name and user_data['bungie_name'].lower() != search_name and user_data['discord_name'].lower() != search_name:
                        continue

                await ctx.send("Updating {}'s stats...".format(user_data['bungie_name']))

                # Calculate discord stats
                print("[*] Getting stats for {}".format(user_data['discord_name']))

                with ctx.typing():
                    discord_stats = await self.get_user_discord_activity_stats(user_data['discord_id'])

                    # Update the data in the user's record
                    user_data['chat_events'] = discord_stats['chat_events']
                    user_data['characters_typed'] = discord_stats['characters_typed']
                    user_data['vc_minutes'] = discord_stats['vc_minutes']

                print("[*] >>> Getting stats for {}".format(user_data['bungie_id']))

                with ctx.typing():
                    bungie_stats = await self.get_user_bungie_activity_stats(user_data['bungie_id'])

                    # Update the data in the user's record.
                    user_data['seconds_played'] = bungie_stats['seconds_played']
                    user_data['clan_members_played_with'] = bungie_stats['clan_members_played_with']
                    user_data['unique_clan_members_played_with'] = bungie_stats['unique_clan_members_played_with']

                with ctx.typing():
                    bonus_multiplier = user_data['unique_clan_members_played_with'] + user_data[
                        'clan_members_played_with']
                    user_data['clan_activity_score'] = user_data['seconds_played'] + (user_data['chat_events'] * 60) + \
                                                       (user_data['characters_typed'] * 3) * bonus_multiplier

                    with open(config.BOT_DB + user_file, 'w') as user_file_data:
                        json.dump(user_data, user_file_data)

            print("[*] >>> Update complete.")
            await ctx.send("Update complete.")

    async def get_user_discord_activity_stats(self, discord_id):
        stat_results = {}
        chat_events = 0
        characters_typed = 0
        today = datetime.datetime.utcnow()

        for guild in self.bot.guilds:
            # Only do Ace's Brew Discord
            if str(guild.id) == "534781834924523520":
                for channel in guild.text_channels:
                    days_before = config.STATISTICS_PERIOD
                    reporting_period = today - datetime.timedelta(days_before)

                    async for message in channel.history(after=reporting_period):
                        if int(message.author.id) == int(discord_id):
                            chat_events += 1
                            characters_typed += len(message.content)

        stat_results.update({'characters_typed': int(characters_typed)})
        stat_results.update({'chat_events': int(chat_events)})
        stat_results.update({'vc_minutes': 0})

        return stat_results

    async def get_user_bungie_activity_stats(self, bungie_id):
        stat_results = {}
        today_utc = datetime.datetime.utcnow()
        days_before = config.STATISTICS_PERIOD
        reporting_period = (today_utc - datetime.timedelta(days_before))
        destiny = pydest.Pydest(config.BUNGIE_API_KEY)

        profile_data = await destiny.api.get_profile(3, bungie_id, components=['100'])
        character_ids = profile_data['Response']['profile']['data']['characterIds']

        seconds_played = 0
        clan_members_played_with = 0
        unique_clan_members_played_with = set()

        for character_id in character_ids:

            pull_more_reports = True
            report_page = 0
            while pull_more_reports:
                # Pull the first 25 activities for the characters
                history_report = await destiny.api.get_activity_history(3, bungie_id, character_id, count=25, mode=None,
                                                                        page=report_page)

                # Increment the page count if we loop back
                report_page += 1
                character_activities = history_report['Response']['activities']

                for character_activity in character_activities:
                    activity_time = datetime.datetime.strptime(character_activity['period'], '%Y-%m-%dT%H:%M:%SZ')

                    # If the activity is within the reporting period; process it
                    if activity_time > reporting_period:
                        # Calculate seconds played
                        seconds_played += character_activity['values']['timePlayedSeconds']['basic']['value']
                        activity_info = await destiny.api.get_post_game_carnage_report(
                            character_activity['activityDetails']['instanceId'])

                        # See who they played with in that activity
                        activity_players = activity_info['Response']['entries']
                        activity_clan_player_count = 0

                        for activity_player in activity_players:
                            player_id = activity_player['player']['destinyUserInfo']['membershipId']
                            player_name = activity_player['player']['destinyUserInfo']['displayName']

                            # Find out if the players were in our clans
                            clan_search_results = await self.check_if_clan_member(bungie_id=player_id)

                            if clan_search_results['is_member']:
                                activity_clan_player_count += 1
                                unique_clan_members_played_with.add(player_id)

                        if activity_clan_player_count > 2:
                            clan_members_played_with += 2.9
                        else:
                            clan_members_played_with += activity_clan_player_count
                    # Else if its not, don't, and set the iteration flag to be complete
                    else:
                        pull_more_reports = False
                        break

        stat_results.update({"seconds_played": seconds_played})
        stat_results.update({"clan_members_played_with": clan_members_played_with})
        stat_results.update({"unique_clan_members_played_with": len(unique_clan_members_played_with)})

        await destiny.close()
        return stat_results

    async def check_if_clan_member(self, bungie_id=None, profile_name=None):
        """Checks the cached roster if member is in the clans.

            Returns (dict):
                            return_results['bungie_id'] = member['id']
                            return_results['bungie_name'] = member['name']
                            return_results['is_member'] = True
        """
        return_results = {}
        return_results['is_member'] = False

        for clan_roster in os.listdir("clans/"):
            with open("clans/" + clan_roster) as clan_data_file:
                clan_data = json.load(clan_data_file)

            for member in clan_data['members']:
                if bungie_id is not None:
                    if str(member['id']) == str(bungie_id):
                        return_results['bungie_id'] = member['id']
                        return_results['bungie_name'] = member['name']
                        return_results['is_member'] = True
                        break

                if profile_name is not None:
                    if str(member['name']).lower() == str(profile_name).lower():
                        return_results['bungie_id'] = member['id']
                        return_results['bungie_name'] = member['name']
                        return_results['is_member'] = True
                        break

            if return_results['is_member']:
                break

        return return_results

# Cog extension entry point
def setup(bot):
    print("[*] Loading Clan Activity module.")
    bot.add_cog(ClanActivity(bot))


# Cog extension exit point
def teardown(bot):
    print("[*] Unloading Clan Activity module.")
    bot.remove_cog('ClanActivity')
