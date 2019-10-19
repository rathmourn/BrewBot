import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.db_config import Base, ClanMember, DiscordInfo, BungieInfo


class DBTools:
    def __init__(self, db_name):
        self.engine = create_engine('sqlite:///' + db_name)

        # Bind the engine to the metadata of the Base class so that the
        # declaratives can be accessed through a DBSession instance
        Base.metadata.bind = self.engine

        self.DBSession = sessionmaker(bind=self.engine)
        # A DBSession() instance establishes all conversations with the database
        # and represents a "staging zone" for all the objects loaded into the
        # database session object. Any change made against the objects in the
        # session won't be persisted into the database until you call
        # session.commit(). If you're not happy about the changes, you can
        # revert all of them back to the last commit by calling
        # session.rollback()
        self.session = self.DBSession()

    def close(self):
        self.session.close()

    def add_clan_member(self, discord_member_info, bungie_member_info):
        """Adds and commits a new clan member to the database.
            Args:
                discord_member_info:
                    (db.db_config.DiscordInfo) - DataObject of user's Discord Info
                bungie_member_info:
                    (db.db_config.BungieInfo) - DataObject of user's Bungie Info

        """

        new_clan_member = ClanMember(
            created_at=datetime.datetime.now(),
            clan_activity_score=0,
            reports_below_threshold=0,
            discord_user_info=discord_member_info,
            bungie_user_info=bungie_member_info
        )
        self.session.add(new_clan_member)
        self.session.commit()