import brewbot
import config


def main():
    # Instantiate the bot
    bot = brewbot.BrewBot(db_session=None)

    # Run the bot
    bot.run()


if __name__ == '__main__':
    main()