import os
from configparser import ConfigParser

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, scoped_session, sessionmaker


def get_DATABASE_URI(filename="database.ini", section="postgresql"):
    parser = ConfigParser()
    parser.read(filename)

    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception("Section {0} not found in the {1} file".format(section, filename))

    DATABASE_URI = "postgresql://{user}:{password}@{server}/{db}".format(
        user=db["user"],
        password=db["password"],
        server=db["host"],
        db=db["database"],
    )

    return DATABASE_URI


Base = declarative_base()
if os.path.isfile("database.ini"):
    DATABASE_URI = get_DATABASE_URI(filename="database.ini", section="postgresql")
    engine = create_engine(DATABASE_URI, pool_pre_ping=True, pool_size=10, max_overflow=30)

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

    session = Session()
