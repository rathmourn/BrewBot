import discord
from discord.ext import commands

import config


class BrewBot(discord.ext.commands.Bot):
    def __init__(self, db_session):
        super().__init__(command_prefix=config.COMMAND_PREFIX)
        self.db_session = db_session

        # Load the bot's modules
        for module in config.BOT_MODULES:
            self.load_extension(module)

    async def on_message(self, message):
        await super().process_commands(message)

    async def on_ready(self):
        print("Bot is Ready")

    def run(self):
        super().run(config.DISCORD_BOT_TOKEN)

