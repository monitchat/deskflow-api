from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from deskflow.config import SQLALCHEMY_DATABASE_URI

# engine used for all
engine = create_engine(
    SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,
    pool_recycle=60,
    pool_size=20,
    max_overflow=20,
)

Session = sessionmaker(engine, expire_on_commit=False)

Base = declarative_base()
