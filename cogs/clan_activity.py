import datetime
from dateutil import tz
import os
import json
from discord.ext import commands
import discord
import pydest
import time
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

    @commands.command()
    async def activity(self, ctx):
        """Give a user their activity stats.

            If given no arguments, pulls the sender's stats.
            Otherwise `$activity [user]` will attempt to pull that user's activity stats.
        """

        with ctx.typing():
            # If we are just looking up the author's stats
            print(ctx.message.mentions)
            if len(ctx.message.mentions) == 0:
                try:
                    with open(config.BOT_DB + str(ctx.author.id) + ".json") as user_data_file:
                        user_data = json.load(user_data_file)

                        report_message = self._print_activity_report(user_data)
                        await ctx.send(embed=report_message)

                except FileNotFoundError:
                    await ctx.send("You do not appear to be registered with me.")
                    return

            # Else, we need to find the user they are looking for
            else:
                for mention in ctx.message.mentions:
                    try:
                        with open(config.BOT_DB + str(mention.id) + ".json") as user_data_file:
                            user_data = json.load(user_data_file)

                            report_message = self._print_activity_report(user_data)
                            await ctx.send(embed=report_message)

                    except FileNotFoundError:
                        await ctx.send(
                            "Unable to find stats for {} among my registered members. Please verify the name and "
                            "search again.".format(
                                mention.mention))
                        return

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
                    if user_data['bungie_id'].lower() != search_name and user_data[
                        'bungie_name'].lower() != search_name and user_data['discord_name'].lower() != search_name:
                        continue

                await ctx.send("Updating {}'s stats...".format(user_data['bungie_name']))

                # Calculate discord stats
                with ctx.typing():
                    discord_stats = await self.get_user_discord_activity_stats(user_data['discord_id'])

                    # Update the data in the user's record
                    user_data['chat_events'] = discord_stats['chat_events']
                    user_data['characters_typed'] = discord_stats['characters_typed']
                    user_data['vc_minutes'] = discord_stats['vc_minutes']

                with ctx.typing():
                    daily_bungie_stats = {}

                    today_utc = datetime.datetime.utcnow()
                    reporting_period = (today_utc - datetime.timedelta(config.STATISTICS_PERIOD))

                    iter_date = reporting_period

                    while iter_date < today_utc:
                        print(iter_date)

                        # See if we have stats already for that date
                        if iter_date.strftime("%Y-%m-%d") in user_data['game_activity'].keys():
                            daily_bungie_stats.update(
                                {
                                    iter_date.strftime("%Y-%m-%d"): user_data['game_activity'][
                                        iter_date.strftime("%Y-%m-%d")]
                                }
                            )

                        # If we don't, get them
                        else:
                            bungie_stats = await self.get_user_bungie_activity_stats(user_data['bungie_id'], iter_date)

                            daily_bungie_stats.update(
                                {
                                    iter_date.strftime("%Y-%m-%d"): {
                                        "seconds_played": bungie_stats['seconds_played'],
                                        "unique_clan_members_played_with": bungie_stats[
                                            'unique_clan_members_played_with'],
                                        "clan_members_played_with": bungie_stats['clan_members_played_with']
                                    }
                                }
                            )

                        iter_date = iter_date + datetime.timedelta(days=1)

                    # Update the data in the user's record.
                    user_data['game_activity'] = daily_bungie_stats

                with ctx.typing():
                    total_seconds_played = 0
                    total_unique_members_played_with = 0
                    total_clan_members_played_with = 0

                    for stat_day, stat_values in user_data['game_activity'].items():
                        total_seconds_played += user_data['game_activity'][stat_day]['seconds_played']
                        total_unique_members_played_with += user_data['game_activity'][stat_day][
                            'unique_clan_members_played_with']
                        total_clan_members_played_with += user_data['game_activity'][stat_day][
                            'clan_members_played_with']

                    bonus_multiplier = total_clan_members_played_with + total_unique_members_played_with
                    activity_score = total_seconds_played + (user_data['chat_events'] * 60) + \
                                     (user_data['characters_typed'] * 3) * bonus_multiplier

                    user_data['clan_activity_score'] = activity_score

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
            if guild.id == 534781834924523520:
                for channel in guild.text_channels:
                    days_before = config.STATISTICS_PERIOD
                    reporting_period = today - datetime.timedelta(days_before)

                    async for message in channel.history(limit=None, after=reporting_period):
                        if str(message.author.id) == str(discord_id):
                            chat_events += 1
                            characters_typed += len(message.content)

        stat_results.update({'characters_typed': int(characters_typed)})
        stat_results.update({'chat_events': int(chat_events)})
        stat_results.update({'vc_minutes': 0})

        return stat_results

    async def get_user_bungie_activity_stats(self, bungie_id, day_to_pull):
        stat_results = {}
        today_utc = datetime.datetime.utcnow()
        days_before = config.STATISTICS_PERIOD
        destiny = pydest.Pydest(config.BUNGIE_API_KEY)
        profile_calls = 0

        profile_types = [3, 2, 1, 5]
        member_type = None

        for profile_type in profile_types:
            profile_data = await destiny.api.get_profile(profile_type, bungie_id, components=['100'])
            print(profile_data)
            await self.debug_api_call(profile_data)

            if str(profile_data['ErrorCode']) == "1":

                member_type = profile_type

                character_ids = profile_data['Response']['profile']['data']['characterIds']

                seconds_played = 0
                clan_members_played_with = 0
                unique_clan_members_played_with = set()
                for character_id in character_ids:
                    pull_more_reports = True
                    report_page = 0

                    while pull_more_reports:
                        # Pull the first 100 activities for the characters

                        history_report = await destiny.api.get_activity_history(member_type, bungie_id, character_id,
                                                                                count=25,
                                                                                mode=None,
                                                                                page=report_page)

                        await self.debug_api_call(history_report)


                        # See if their profile is set to private
                        if str(history_report['ErrorCode']) == "1665":
                            pull_more_reports = False
                            stat_results.update({"seconds_played": 0})
                            stat_results.update({"clan_members_played_with": 0})
                            stat_results.update({"unique_clan_members_played_with": 0})
                            break

                        # If we don't get a response, we're done
                        if len(history_report['Response']) == 0:
                            pull_more_reports = False
                            break

                        # See if it has any activities in it
                        if 'activities' not in history_report['Response'].keys():
                            break

                        # Increment the page count if we loop back
                        report_page += 1
                        character_activities = history_report['Response']['activities']

                        for character_activity in character_activities:
                            activity_time = datetime.datetime.strptime(character_activity['period'],
                                                                       '%Y-%m-%dT%H:%M:%SZ')

                            # If the activity is within the reporting period; process it
                            if activity_time.date() == day_to_pull.date():
                                # Calculate seconds played
                                seconds_played += character_activity['values']['timePlayedSeconds']['basic']['value']
                                activity_info = await destiny.api.get_post_game_carnage_report(
                                    character_activity['activityDetails']['instanceId'])
                                await self.debug_api_call(activity_info)

                                if len(history_report['Response']) == 0:
                                    pull_more_reports = False
                                    break

                                # See who they played with in that activity
                                activity_players = activity_info['Response']['entries']
                                activity_clan_player_count = 0

                                for activity_player in activity_players:

                                    # Make sure it isn't the player getting stats pulled on
                                    if str(activity_player['player']['destinyUserInfo']['membershipId']) != str(
                                            bungie_id):
                                        if str(activity_player['player']['destinyUserInfo']['isPublic']) == "True":
                                            player_name = activity_player['player']['destinyUserInfo']['displayName']
                                        else:
                                            player_name = "<PRIVATE>"

                                        player_id = activity_player['player']['destinyUserInfo']['membershipId']
                                        print("\t\t\tLOOKUP: {} : {}".format(player_name, player_id))
                                        # Find out if the players were in our clans
                                        clan_search_results = await self.check_if_clan_member(bungie_id=player_id)

                                        if clan_search_results['is_member']:
                                            activity_clan_player_count += 1
                                            unique_clan_members_played_with.add(player_id)

                                if activity_clan_player_count > 2:
                                    clan_members_played_with += 2.9
                                else:
                                    clan_members_played_with += activity_clan_player_count
                            elif activity_time.date() < day_to_pull.date():
                                pull_more_reports = False
                                break

                stat_results.update({"seconds_played": seconds_played})
                stat_results.update({"clan_members_played_with": clan_members_played_with})
                stat_results.update({"unique_clan_members_played_with": len(unique_clan_members_played_with)})

                break
        
            # If we get 1665 (private profile)
            elif str(profile_data['ErrorCode']) == "1665":
                stat_results.update({"seconds_played": '0'})
                stat_results.update({"clan_members_played_with": '0'})
                stat_results.update({"unique_clan_members_played_with": '0'})
            
            # If we get some other error code
            else:
                stat_results.update({"seconds_played": '0'})
                stat_results.update({"clan_members_played_with": '0'})
                stat_results.update({"unique_clan_members_played_with": '0'})

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

    def _print_activity_report(self, user_data):
        total_seconds_played = 0
        total_unique_members_played_with = 0

        for stat_day, stat_values in user_data['game_activity'].items():
            total_seconds_played += user_data['game_activity'][stat_day]['seconds_played']
            total_unique_members_played_with += user_data['game_activity'][stat_day][
                'unique_clan_members_played_with']

        embed = discord.Embed(title="Clan Activity Report",
                              description="{}'s activity score over the last {} days".format(
                                  user_data['bungie_name'], config.STATISTICS_PERIOD))

        embed.add_field(name="Discord Messages", value=user_data['chat_events'], inline=True)
        embed.add_field(name="Discord Characters Sent", value=user_data['characters_typed'], inline=True)
        embed.add_field(name="Destiny Time Played",
                        value=str(datetime.timedelta(seconds=total_seconds_played)), inline=False)
        embed.add_field(name="Clan Members Played With ", value=str(total_unique_members_played_with),
                        inline=True)

        clan_activity_score = int(user_data['clan_activity_score'])
        embed.add_field(name="Total Activity Score", value=f"{clan_activity_score:,}",
                        inline=False)

        return embed

    async def debug_api_call(self, api_response):
        # if api_response['ErrorCode'] != 1:
        time_now = datetime.datetime.utcnow()
        print("{}: ErrorCode: {}, ThrottleSeconds: {}, Message: {}, MessageData: {}".format(time_now,
                                                                                            api_response['ErrorCode'],
                                                                                            api_response[
                                                                                                'ThrottleSeconds'],
                                                                                            api_response['Message'],
                                                                                            api_response[
                                                                                                'MessageData']))
        #if 'Response' in api_response.keys():
            #print("\t\tRESPONSE: {}".format(api_response['Response']))


# Cog extension entry point
def setup(bot):
    print("[*] Loading Clan Activity module.")
    bot.add_cog(ClanActivity(bot))


# Cog extension exit point
def teardown(bot):
    print("[*] Unloading Clan Activity module.")
    bot.remove_cog('ClanActivity')
