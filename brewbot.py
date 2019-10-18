import yaml
import discord
from discord.ext import commands

bot = commands.Bot(command_prefix='$')

# Notification event for when the bot is up and running
@bot.event
async def on_ready():
    print("Bot is ready.")


# Main message handler
@bot.event
async def on_message(ctx):
    # Process the other commands first
    await bot.process_commands(ctx)


def main():
    # Load configuration file
    with open("config.yml", 'r') as ymlfile:
        cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)

    # Launch the bot
    bot.run(cfg['bot']['discord_api_key'])


if __name__ == '__main__':
    main()

