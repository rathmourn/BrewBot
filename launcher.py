import brewbot
import config

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


def main():
    # Establish database connection to pass to the bot
    Base = declarative_base(())
    db_engine = create_engine('sqlite:///' + config.BOT_DB_NAME)
    Base.metadata.bind = db_engine
    db_session_maker = sessionmaker(bind=db_engine)
    db_session = db_session_maker()

    # Instantiate the bot
    bot = brewbot.BrewBot(db_session)

    # Run the bot
    bot.run()

    db_session.close()


if __name__ == '__main__':
    main()
