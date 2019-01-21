from flask import current_app

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker, relationship, backref

from storeify.config import Config

Base = declarative_base()
Session = sessionmaker(autocommit=False, autoflush=False)
db_session = None


def init_db_engine():
    engine = create_engine(Config.DATABASE_URI, convert_unicode=True)
    Session.configure(bind=engine)

    global db_session
    db_session = scoped_session(Session)
    Base.query = db_session.query_property()


def get_db_session():
    if not db_session:
        init_db_engine()
        return db_session
    else:
        return db_session


def create_db():
    engine = create_engine(Config.DATABASE_URI, convert_unicode=True)
    Base.metadata.create_all(bind=engine)


def reset_db():
    engine = create_engine(Config.DATABASE_URI, convert_unicode=True)
    Base.metadata.drop_all(bind=engine)
