import os
from configparser import ConfigParser
from contextvars import ContextVar

from sqlalchemy import create_engine
from sqlalchemy.orm import (Session, declarative_base, scoped_session,
                            sessionmaker)

session = None


def get_DATABASE_URI(filename="database.ini", section="postgresql"):
    parser = ConfigParser()
    parser.read(filename)

    if not parser.has_section(section):
        raise Exception(f"Section {section} not found in the {filename} file")

    db = {param[0]: param[1] for param in parser.items(section)}

    return f"postgresql://{db['user']}:{db['password']}@{db['host']}/{db['database']}"


Base = declarative_base()
SessionLocal = None

if os.path.isfile("database.ini"):
    DATABASE_URI = get_DATABASE_URI()
    engine = create_engine(DATABASE_URI, pool_pre_ping=True, pool_size=10, max_overflow=30)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    if SessionLocal is None:
        raise RuntimeError("Database is not initialized")

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
