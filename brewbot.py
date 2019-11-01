import discord
from discord.ext import commands

import config


class BrewBot(discord.ext.commands.Bot):
    """BrewBot class base.
    """

    def __init__(self, db_session):
        """
        Instantiate an instance of BrewBot.

        Args:
            db_session (db_session_maker): SQLAlchemy database session for BrewBot to utilize.
        """
        super().__init__(command_prefix=config.BOT_COMMAND_PREFIX)
        self.db_session = db_session

        # Load the bot's modules
        for bot_module in config.BOT_MODULES:
            self.load_extension(bot_module)

    async def on_message(self, message):
        """
        Generic message handler for message received event in discord.

        Args:
            message (discord.Message): the message triggering the event

        """
        await super().process_commands(message)
        #print(str(message.guild) + " : " + str(message.channel) + " : " + str(message.author))

    async def on_ready(self):
        """
        Event handler for when bot has successfully logged in and loaded its modules.
        """
        print("Bot is ready.")

    def run(self):
        """
        Execution function to launch the bot.

        Returns: None.

        """
        super().run(config.DISCORD_BOT_TOKEN)
