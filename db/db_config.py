from sqlalchemy import Column, ForeignKey, String, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

import config

Base = declarative_base()


class DiscordInfo(Base):
    """DiscordInfo class to define table schema
    """
    __tablename__ = 'discord_info'

    id = Column(Integer, primary_key=True)

    discord_id = Column(String)
    discord_name = Column(String)
    chat_events = Column(Integer)
    characters_typed = Column(Integer)
    vc_minutes = Column(String)

    # Bi-directional link back to the clan_members table
    clan_member = relationship("ClanMember", uselist=False, back_populates='discord_user_info')


class BungieInfo(Base):
    """BungieInfo class to define table schema
    """
    __tablename__ = 'bungie_info'

    id = Column(Integer, primary_key=True)

    bungie_id = Column(String)
    destiny_name = Column(String)
    clan_name = Column(String)
    seconds_played = Column(Integer)
    clan_members_played_with = Column(Integer)
    unique_clan_members_played_with = Column(Integer)

    # Bi-directional link back to the clan_members table
    clan_member = relationship("ClanMember", uselist=False, back_populates='bungie_user_info')


class ClanMember(Base):
    """ClanMember class to define table schema
    """
    __tablename__ = 'clan_members'

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime)

    clan_activity_score = Column(Integer)
    reports_below_threshold = Column(Integer)

    # Foreign key and bi-directional link to discord_info table
    discord_user_info_id = Column(Integer, ForeignKey('discord_info.id'))
    discord_user_info = relationship(DiscordInfo, back_populates='clan_member')

    # Foreign key and bi-directional link to bungie_info table
    bungie_user_info_id = Column(Integer, ForeignKey('bungie_info.id'))
    bungie_user_info = relationship(BungieInfo, back_populates='clan_member')


# Database generation for initial init
engine = create_engine('sqlite:///' + config.BOT_DB_NAME)
Base.metadata.create_all(engine)
