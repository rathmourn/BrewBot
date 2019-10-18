import discord
from discord.ext import commands

bot = commands.Bot(command_prefix='$')


@bot.event
async def on_ready():
    print("Bot is ready.")


def main():
    bot.run('NjIyMDQ2Mjg1NzIxMTA4NTQw.XaSX6A.zvHd1PQNJWak8TaPPywSh-fPkok')


if __name__ == '__main__':
    main()

