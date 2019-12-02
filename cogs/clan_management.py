import os
import discord
from discord.ext import commands
import json
import csv
import pydest
import datetime
import random
import config
import bungie_api


def is_authorized():
    """
    Command decorator to validate if a user is authorized for a bot's command or not.
    Returns: None

    """

    async def check_authorization(ctx):
        is_allowed = False
        for role in ctx.author.roles:
            if str(role.name) == "Mod" or str(role.name) == "Admin":
                is_allowed = True
                break

        return is_allowed

    return commands.check(check_authorization)


class ClanManagement(commands.Cog):
    """Base cog class to support all clan management activities.
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True)
    async def jman(self,ctx):
        with open(config.BOT_BASEDIR + "gman.json") as gman_memes_file:
            gman_memes = json.load(gman_memes_file)

        random_choice = random.choice(list(gman_memes.values()))
        print(random_choice)
        activity = discord.Game(name=str(random_choice))
        await self.bot.change_presence(activity=activity)

    @commands.command(hidden=True)
    @is_authorized()
    async def clan_report(self, ctx):
        """Generate a clan report. [ADMIN ONLY]
        """

        with ctx.typing():

            for clan in config.BREW_CLANS:
                await ctx.send("Generating report for {}...".format(clan['clan_name']))

                # Open the initial report file and write the header
                report_file_name = str(clan['clan_name']).replace(" ", "_").replace("'", "") + ".csv"

                with open(config.BOT_BASEDIR + "reports/" + report_file_name, 'w+') as csv_report:
                    csv_writer = csv.writer(csv_report)
                    csv_writer.writerow(
                        ['steam_name', 'discord_name', 'registered?', 'in_clan?', 'in_discord?', 'activity_score'])

                    registered_users = []

                    # Iterate the registered users
                    for registered_user in os.listdir(config.BOT_DB):
                        if registered_user.endswith('.json'):
                            with open(config.BOT_DB + registered_user) as user_data_file:
                                user_data = json.load(user_data_file)

                            # If they are in the current clan we care about
                            if user_data['clan_id'] == clan['clan_id']:
                                steam_name = user_data['bungie_name']
                                discord_name = user_data['discord_name']
                                is_registered = True

                                clan_search_results = await self.check_if_clan_member(bungie_id=user_data['bungie_id'])
                                is_in_clan = clan_search_results['is_member']

                                activity_score = user_data['clan_activity_score']

                                is_in_discord = False
                                for guild in self.bot.guilds:
                                    # Only do Ace's Brew Discord
                                    if str(guild.id) == "534781834924523520":
                                        for member in guild.members:
                                            if str(member.id) == str(user_data['discord_id']):
                                                is_in_discord = True

                                csv_writer.writerow(
                                    [steam_name, discord_name, is_registered, is_in_clan, is_in_discord, int(activity_score)])

                                registered_users.append(user_data)

                    # Iterate the roster for all the unregistered folks
                    with open(config.BOT_BASEDIR + "clans/" + str(clan['clan_id']) + ".json") as clan_data_file:
                        clan_data = json.load(clan_data_file)

                    for clan_member in clan_data['members']:

                        # See if he was on our registered list
                        member_registered = False
                        for registered_user in registered_users:
                            if clan_member['id'] == registered_user['bungie_id']:
                                member_registered = True

                        # If he was, we can ignore this one
                        if member_registered is False:
                            csv_writer.writerow([clan_member['name'], 'N/A', 'False', 'True', 'N/A', '0'])

                # Upload the file to discord
                await ctx.send(file=discord.File(config.BOT_BASEDIR + "reports/" + report_file_name))

    @commands.command()
    async def roster_count(self, ctx):
        """View clan roster counts.
        """

        with ctx.typing():
            embed = discord.Embed(title="Clan Roster Counts",
                                  description="Roster counts across all clans.")

            for clan in config.BREW_CLANS:
                with open(config.BOT_BASEDIR + "clans/" + str(clan['clan_id']) + ".json") as clan_data_file:
                    clan_data = json.load(clan_data_file)
                    embed.add_field(name=clan['clan_name'], value=str(len(clan_data['members'])), inline=False)

            await ctx.send(embed=embed)

    @commands.command(hidden=False)
    async def register(self, ctx, *args):
        """Registers the user with the bot.
            $register [profile SteamName]

            Simply running the register command will cause the bot to search for a destiny profile that matches your
            discord name.

            [!] If BrewBot doesn't recognize your user name, type $register profile SteamName. 

            [!] If your Steam name is more than 1 word, you need to put quotation marks around it. E.g. $register profile "Steam Name".

            [!] If you're on cross-save and console is your main account, use your console username to register instead.
        """

        destiny = pydest.Pydest(config.BUNGIE_API_KEY)

        # Register if discord name matches
        if len(args) == 0:

            # See if they are clan member
            if ctx.author.nick is not None:
                clan_member = await self.check_if_clan_member(profile_name=ctx.author.nick)
            else:
                clan_member = await self.check_if_clan_member(profile_name=ctx.author.display_name)

            if clan_member['is_member']:
                await ctx.send("Found you in the clan rosters. DM'ing you with further instructions.")

                await ctx.author.send("Please verify your ID to complete the registration process.")
                await ctx.author.send('Reply to this message with `{}register verify {}` to complete registration.'.format(
                    config.BOT_COMMAND_PREFIX, clan_member['bungie_id']))

            else:
                await ctx.send("We could not find you in any of our clans. Please make sure that your in-game name matches your Discord name. "
                    "For more information, type `$help register` or contact a Mod. ")

        # Register if discord name doesn't match
        elif args[0] == 'profile' and len(args) == 2:

            # See if they are clan member
            clan_member = await self.check_if_clan_member(profile_name=str(args[1]))

            if clan_member['is_member']:
                await ctx.send("Found you in the clan rosters. DM'ing you with further instructions.")

                await ctx.author.send("Please verify your ID to complete the registration process.")
                await ctx.author.send(
                    'Reply to this message with `{}register verify {}` to complete registration.'.format(
                        config.BOT_COMMAND_PREFIX, clan_member['bungie_id']))

            else:
                await ctx.send("We could not find you in any of our clans. Please make sure that your in-game name matches your Discord name. "
                    "For more information, type `$help register` or contact a Mod. ")

        # Verify and complete registration
        elif args[0] == 'verify' and len(args) == 2:
            user_data = {}

            verify_id = args[1]

            profile_types = [3, 2, 1, 5]

            for profile_type in profile_types:
                profile_data = await destiny.api.get_profile(profile_type, verify_id, components=['100'])

                if profile_data['ErrorCode'] == 1:
                    player_groups_query = await destiny.api.get_groups_for_member(profile_type, args[1])

                    if len(player_groups_query['Response']['results']) > 0:
                        player_clan_id = player_groups_query['Response']['results'][0]['group']['groupId']
                        player_clan_name = player_groups_query['Response']['results'][0]['group']['name']
                    else:
                        player_clan_id = None
                        player_clan_name = None

                    # Add their discord ID and name to the records
                    user_data.update({'discord_id': str(ctx.author.id)})

                    if hasattr(ctx.author, 'nick'):
                        user_data.update({'discord_name': str(ctx.author.nick)})
                    else:
                        user_data.update({'discord_name': str(ctx.author.display_name)})

                    # Add their bungie id and name to the records
                    user_data.update({'bungie_id': str(verify_id)})

                    # Let's see if they've tried to register before
                    for user_file in os.listdir(config.BOT_DB):
                        try:
                            if user_file.endswith(".json"):
                                with open(config.BOT_DB + user_file) as current_profile_file:
                                    current_profile = json.load(current_profile_file)

                                if str(current_profile['discord_id']) == str(user_data['discord_id']) or \
                                        str(current_profile['bungie_id']) == str(user_data['bungie_id']):
                                    await ctx.author.send("Profile already registered. Contact an admin.")
                                    return

                        except FileNotFoundError:
                            pass

                    user_data.update(
                        {'bungie_name': str(profile_data['Response']['profile']['data']['userInfo']['displayName'])})

                    # Add their clan info
                    if player_clan_name:
                        user_data.update({'clan_name': player_clan_name})
                        user_data.update({'clan_id': player_clan_id})

                    # Set time created
                    user_data.update({'created_at': str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))})

                    # Complete the record with null values for now
                    user_data.update({'steam_join_id': '0'})
                    user_data.update({'clan_activity_score': 0})
                    user_data.update({'reports_below_threshold': 0})
                    user_data.update({'chat_events': 0})
                    user_data.update({'characters_typed': 0})
                    user_data.update({'vc_minutes': 0})
                    user_data.update({'game_activity': {}})
                    user_data.update({'seconds_played': 0})
                    user_data.update({'unique_clan_members_played_with': 0})
                    user_data.update({'clan_members_played_with': 0})

                    with open(config.BOT_DB + str(ctx.author.id) + ".json", 'w+') as user_file:
                        json.dump(user_data, user_file)

                    await ctx.author.send("You’re now registered! Please allow 24 – 48 hours for your data to be tabulated." 
                        "During this time, your activity scorecard may not display the correct stats.")

                    break

        await destiny.close()

    async def check_if_clan_member(self, bungie_id=None, profile_name=None):
        """Checks the cached roster if member is in the clans.

            Returns (dict):
                            return_results['bungie_id'] = member['id']
                            return_results['bungie_name'] = member['name']
                            return_results['is_member'] = True
        """
        return_results = {}
        return_results['is_member'] = False

        for clan_roster in os.listdir(config.BOT_BASEDIR + "clans/"):
            with open(config.BOT_BASEDIR + "clans/" + clan_roster) as clan_data_file:
                clan_data = json.load(clan_data_file)

            for member in clan_data['members']:
                if bungie_id is not None:
                    if str(member['id']) == str(bungie_id):
                        return_results['bungie_id'] = member['id']
                        return_results['bungie_name'] = member['name']
                        return_results['is_member'] = True
                        break
                elif profile_name is not None:
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
    print("[*] Loading Clan Management module.")
    bot.add_cog(ClanManagement(bot))


# Cog extension exit point
def teardown(bot):
    print("[*] Unloading Clan Management module.")
    bot.remove_cog('ClanManagement')
