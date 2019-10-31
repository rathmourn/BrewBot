import os
import discord
from discord.ext import commands
import json
import pydest
import datetime

import config
import bungie_api

def is_authorized():
    """
    Command decorator to validate if a user is authorized for a bot's command or not.
    Returns: None

    """

    async def check_authorization(ctx):
        return str(ctx.author.display_name) == "Rathmourn"

    return commands.check(check_authorization)


class ClanManagement(commands.Cog):
    """Base cog class to support all clan management activities.
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def roster_count(self, ctx):
        """View clan roster counts.
        """

        with ctx.typing():
            embed = discord.Embed(title="Clan Roster Counts",
                                  description="Roster counts across all clans.")

            for clan in config.BREW_CLANS:
                with open("clans/" + str(clan['clan_id']) + ".json") as clan_data_file:
                    print("Loading {} : {}".format(clan['clan_name'], clan['clan_id']))
                    clan_data = json.load(clan_data_file)
                    embed.add_field(name=clan['clan_name'], value=str(len(clan_data['members'])), inline=False)

            await ctx.send(embed=embed)

    @commands.command()
    @is_authorized()
    async def roster_update(self, ctx):
        """Updates the clan rosters. [ADMIN ONLY]
        """
        await ctx.send("Updating clan rosters...")

        with ctx.typing():
            for clan in config.BREW_CLANS:
                clan_members = bungie_api.generate_clan_list(clan['clan_id'])
                print(clan_members)

                clan_data = {}
                clan_data.update({'last_updated': str(datetime.datetime.utcnow())})
                clan_data.update({'members': clan_members})

                with open("clans/" + str(clan['clan_id']) + ".json", 'w+') as clan_data_file:
                    json.dump(clan_data, clan_data_file)

            await ctx.send("Rosters updated.")

    @commands.command(hidden=False)
    async def register(self, ctx, *args):
        """Registers the user with the bot.

            Simply running the register command will cause the bot to search for a destiny profile that matches your
            discord name.

            Running `register profile [name]` will cause the bot to search for your destiny profile by the name given
            if your names don't match.
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

                await ctx.author.send("If you wish to finalize your registration please type:")
                await ctx.author.send('Please type `{}register verify {}` to complete registration.'.format(
                             config.BOT_COMMAND_PREFIX, clan_member['bungie_id']))

            else:
                await ctx.send("You are not in our clan rosters. If your in-game name does not match your discord "
                               "name try searching for it with `$register profile [name]`")

        # Register if discord name doesn't match
        elif args[0] == 'profile' and len(args) == 2:

            # See if they are clan member
            clan_member = await self.check_if_clan_member(profile_name=str(args[1]))

            if clan_member['is_member']:
                await ctx.send("Found you in the clan rosters. DM'ing you with further instructions.")

                await ctx.author.send("If you wish to finalize your registration please type:")
                await ctx.author.send('Please reply to this DM with `{}register verify {}` to complete registration.'.format(
                    config.BOT_COMMAND_PREFIX, clan_member['bungie_id']))

            else:
                await ctx.send("You are not in our clan rosters. Please validate your membership before registering.")

        # Verify and complete registration
        elif args[0] == 'verify' and len(args) == 2:
            user_data = {}

            verify_id = args[1]

            profile_data = await destiny.api.get_profile(3, verify_id, components=['100'])
            player_groups_query = await destiny.api.get_groups_for_member(3, args[1])

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
            user_data.update({'seconds_played': 0})
            user_data.update({'unique_clan_members_played_with': 0})
            user_data.update({'clan_members_played_with': 0})

            if os.path.isfile(config.BOT_DB + str(ctx.author.id) + ".json"):
                await ctx.author.send("Profile already registered. Contact an admin.")
            else:
                with open(config.BOT_DB + str(ctx.author.id) + ".json", 'w+') as user_file:
                    json.dump(user_data, user_file)

                await ctx.author.send("You are registered!")

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
