import brewbot
import config
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


def main():
    dirpath = os.getcwd()
    print("current directory is : " + dirpath)
    foldername = os.path.basename(dirpath)
    print("Directory name is : " + foldername)

    Base = declarative_base(())
    db_engine = create_engine('sqlite:///' + config.BOT_DB_NAME)
    Base.metadata.bind = db_engine
    db_session_maker = sessionmaker(bind=db_engine)
    db_session = db_session_maker()

    bot = brewbot.BrewBot(db_session)
    bot.run()

    db_session.close()


if __name__ == '__main__':
    main()
