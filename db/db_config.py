from sqlalchemy import Column, ForeignKey, String, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

import config

Base = declarative_base()


class ActivityStats(Base):
    """
    Base class to define ActivityStats table schema.
    """
    __tablename__ = "activity_stats"

    id = Column(Integer, primary_key=True)

    # Stat Fields
    discord_chat_events = Column(Integer)
    discord_characters_typed = Column(Integer)
    discord_vc_time = Column(String)

    bungie_seconds_played = Column(Integer)
    bungie_sum_clan_members_played_with = Column(Integer)
    bungie_unique_clan_members_played_with = Column(Integer)

    activity_score = Column(Integer)
    activity_rank = Column(Integer)
    activity_status = Column(Integer)

    reports_below_threshold = Column(Integer)

    # Bidirectional link back to the clan member table
    clan_member_info = relationship("ClanMember", userlist=False, back_populates='activity_stats_info')


class ClanMember(Base):
    """
    Base class to define ClanMember table schema.
    """
    __tablename__ = 'clan_members'

    id = Column(Integer, primary_key=True)

    bungie_id = Column(String)
    steam_display_name = Column(String)
    discord_display_name = Column(String)
    clan_name = Column(String)
    clan_id = Column(Integer)
    steam_join_id = Column(Integer)

    # Foreign key and bidirectional link to ActivityStats
    activity_stats_info_id = Column(Integer, ForeignKey('activity_stats.id'))
    activity_stats_info = relationship("ActivityStats", back_populates='clan_member_info')


# Database generation for database init
engine = create_engine('sqlite:///' + config.BOT_DB_NAME)
Base.metadata.create_all(engine)
