"""Database module"""
import os
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import sessionmaker


def get_db_session():
    """Creates an SQLAlchemy session instance"""
    db_user = os.environ["MOVIES_DB_USER"]
    db_pass = os.environ["MOVIES_DB_PASS"]
    db_host = os.environ["MOVIES_DB_HOST"]
    db_port = os.environ["MOVIES_DB_PORT"]
    db_name = os.environ["MOVIES_DB_NAME"]

    engine = create_engine(
        f"mysql+pymysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}",
        poolclass=NullPool
    )

    return sessionmaker(bind=engine)()
