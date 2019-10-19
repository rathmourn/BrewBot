import os

from discord.ext import commands
import discord
import csv
import datetime
import config


class DiscordStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def role_report(self, ctx, role_name=None, report_file_name=None):
        """Command generate discord statistics of a server role.

                Args:
                    role_name:
                        - The role you are searching for (case insensitive, but if there are spaces you will need to
                        wrap the role in quotes)
                    report_file_name: (Optional)
                        - The filename of the report to generate. Providing this will generate a full report and when
                        complete the bot will upload the report to the channel for your viewing pleasure. If this is
                        not provided, the bot will only generate some basic macro-level stats of the role.
        """

        if role_name is None:
            await ctx.send("`ERROR: You must provide a role to report against.`")
            return

        # Let's make sure they are looking for a valid role
        matched_role = None
        for role in ctx.guild.roles:
            if str(role).lower() == role_name.lower():
                matched_role = role

        # If not, we let them know we couldn't find it
        if matched_role is None:
            await ctx.send("ERROR: That does not appear to be a valid role.")

        # Else, let's process for the report
        else:
            today = datetime.datetime.now()

            # Build membership dictionary
            report_results = {}
            for member in matched_role.members:
                report_results.update({str(member): [member, 0, 0]})

            async with ctx.typing():
                # Iterate each text channel
                for channel in ctx.guild.text_channels:
                    days_before = config.STATISTICS_PERIOD

                    # For each day in our statistics period
                    while days_before >= 0:
                        async for message in channel.history(after=(today - datetime.timedelta(days_before))):

                            # If its a member we're looking for
                            if str(message.author) in report_results.keys():
                                # Increment the message counter
                                report_results[str(message.author)][1] += 1
                                # Increase sum of characters typed counter
                                report_results[str(message.author)][2] += len(message.content)

                        days_before -= 1

            # If we were provided a file name, run the full report
            if report_file_name is not None:
                async with ctx.typing():
                    await ctx.send("Generating role report for " + str(matched_role) +
                                   " for the last " + str(config.STATISTICS_PERIOD) + " days.")

                    with open(report_file_name, newline='', mode='w', encoding='utf-8') as csv_file:
                        csv_writer = csv.writer(csv_file)
                        csv_writer.writerow(['Name', 'Messages', 'CharactersTyped', 'ActivityScore'])

                        for k, v in report_results.items():
                            # Give preference to server specific nicknames
                            if v[0].nick:
                                user_name = str(v[0].nick)
                            else:
                                user_name = str(v[0].display_name)

                            discord_activity_score = (v[1] * 60) + (v[2] * 3)

                            csv_writer.writerow([user_name, v[1], v[2], discord_activity_score])

                        csv_file.close()

                    # Upload the file to discord
                    await ctx.send(file=discord.File(report_file_name))

                    # Clean up the file when we're done
                    if os.path.exists(report_file_name):
                        os.remove(report_file_name)

            # If we weren't given a filename, print out some macro stats
            else:
                async with ctx.typing():
                    await ctx.send("Generating an overview for " + str(matched_role) + ".")

                    embed = discord.Embed(title="Macro Stats for " + str(matched_role) + " Role" +
                                          "for the last " + str(config.STATISTICS_PERIOD) + " Days")
                    embed.add_field(name="Number of Members", value=str(len(report_results.keys())), inline=True)

                    num_zero_chat_events = 0
                    for k, v in report_results.items():
                        if int(v[1]) == 0:
                            num_zero_chat_events += 1

                    embed.add_field(name="Number of Members With No Activity", value=str(num_zero_chat_events),
                                    inline=True)

                    await ctx.send(embed=embed)


# Cog/Extension entry point
def setup(bot):
    print("[*] Loading Discord Stat extension.")
    bot.add_cog(DiscordStats(bot))


# Cog/Extension exit point
def teardown(bot):
    print("[*] Unloading Discord Stats extension.")
    bot.remove_cog('DiscordStats')
