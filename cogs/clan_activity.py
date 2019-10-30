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

    @commands.command()
    @is_authorized()
    async def dtest(self, ctx, discord_id):
        results = await self.get_user_discord_activity_stats(ctx, discord_id)
        await ctx.send(results)

    @commands.command()
    @is_authorized()
    async def api_dump(self, ctx, bungie_id):
        destiny = pydest.Pydest(config.BUNGIE_API_KEY)

        response = await destiny.api.get_profile(3, bungie_id, components=[100])
        await ctx.send(response)
        print(response)

        await destiny.close()

    @commands.command()
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
        """

        if len(args) > 0:
            search_entity = str(args[0]).lower()
            print(search_entity)
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
                embed.add_field(name="Clan Members Played With", value=user_data['clan_members_played_with'],
                                inline=True)
                embed.add_field(name="Unique Clan Members ", value=user_data['unique_clan_members_played_with'],
                                inline=True)
                embed.add_field(name="Total Activity Score", value=int(user_data['clan_activity_score']), inline=False)

                await ctx.send(embed=embed)
            except FileNotFoundError:
                await ctx.send(
                    "You do not appear to be registered. If you believe to be in error, please contact an admid.")

    @commands.command()
    @is_authorized()
    async def activity_update(self, ctx, *args):
        """Update all registered users.
        """
        if len(args) > 0:
            search_name = args[0]
            search_name = search_name.lower()
            print(search_name)
        else:
            search_name = None

        for user_file in os.listdir(config.BOT_DB):
            if user_file.endswith(".json"):
                with open(config.BOT_DB + user_file) as user_file_data:
                    user_data = json.load(user_file_data)

                if search_name is not None:
                    if user_data['bungie_id'].lower() != search_name and user_data['bungie_name'].lower() != search_name and user_data['discord_name'].lower() != search_name:
                        continue

                # Calculate discord stats
                await ctx.send("Updating {} discord stats...".format(user_data['bungie_name']))
                print("[*] Getting stats for {}".format(user_data['discord_name']))

                with ctx.typing():
                    discord_stats = await self.get_user_discord_activity_stats(ctx, user_data['discord_id'])

                    # Update the data in the user's record
                    user_data['chat_events'] = discord_stats['chat_events']
                    user_data['characters_typed'] = discord_stats['characters_typed']
                    user_data['vc_minutes'] = discord_stats['vc_minutes']

                await ctx.send("Discord stats updated.")
                await ctx.send("Updating {} bungie stats...".format(user_data['bungie_name']))
                print("[*] >>> Getting stats for {}".format(user_data['bungie_id']))

                with ctx.typing():
                    bungie_stats = await self.get_user_bungie_activity_stats(user_data['bungie_id'])

                    # Update the data in the user's record.
                    user_data['seconds_played'] = bungie_stats['seconds_played']
                    user_data['clan_members_played_with'] = bungie_stats['clan_members_played_with']
                    user_data['unique_clan_members_played_with'] = bungie_stats['unique_clan_members_played_with']

                await ctx.send("Bungie stats updated.")
                await ctx.send("Updating your record.")

                with ctx.typing():
                    bonus_multiplier = user_data['unique_clan_members_played_with'] + user_data[
                        'clan_members_played_with']
                    user_data['clan_activity_score'] = user_data['seconds_played'] + (user_data['chat_events'] * 60) + \
                                                       (user_data['characters_typed'] * 3) * bonus_multiplier

                    with open(config.BOT_DB + user_file, 'w') as user_file_data:
                        json.dump(user_data, user_file_data)

                await ctx.send("Record updated.")

    @commands.command()
    async def tools(self, ctx, bungie_id):
        await self.get_user_bungie_activity_stats(bungie_id)

    async def get_user_discord_activity_stats(self, ctx, discord_id):
        stat_results = {}
        chat_events = 0
        characters_typed = 0
        today = datetime.datetime.utcnow()

        print("[*] >>> Getting discord stats for ID:" + discord_id)

        for channel in ctx.guild.text_channels:
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

                        for activity_player in activity_players:
                            player_id = activity_player['player']['destinyUserInfo']['membershipId']
                            player_name = activity_player['player']['destinyUserInfo']['displayName']

                            # Find out if the players were in our clans
                            player_groups_query = await destiny.api.get_groups_for_member(3, player_id)

                            if len(player_groups_query['Response']['results']) > 0:
                                player_clan_id = player_groups_query['Response']['results'][0]['group']['groupId']
                                player_clan_name = player_groups_query['Response']['results'][0]['group']['name']
                            else:
                                player_clan_id = None
                                player_clan_name = None

                            if player_clan_name:
                                if str(player_clan_name).find("Ace's Brew") != -1:
                                    # Make sure we don't count ourselves
                                    if player_id != bungie_id:
                                        clan_members_played_with += 1
                                        unique_clan_members_played_with.add(player_id)

                    # Else if its not, don't, and set the iteration flag to be complete
                    else:
                        pull_more_reports = False
                        break

        stat_results.update({"seconds_played": seconds_played})
        stat_results.update({"clan_members_played_with": clan_members_played_with})
        stat_results.update({"unique_clan_members_played_with": len(unique_clan_members_played_with)})

        await destiny.close()
        return stat_results


# Cog extension entry point
def setup(bot):
    print("[*] Loading Clan Activity module.")
    bot.add_cog(ClanActivity(bot))


# Cog extension exit point
def teardown(bot):
    print("[*] Unloading Clan Activity module.")
    bot.remove_cog('ClanActivity')
