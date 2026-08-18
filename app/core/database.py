from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.core.config import settings


connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(settings.database_url, connect_args=connect_args, future=True)
# expire_on_commit=False: without this, every POST/PATCH endpoint that
# does `db.commit(); return obj` silently returned an empty `{}` body.
# SQLAlchemy's default expires all attributes on commit, so by the time
# FastAPI serializes the returned ORM object, its fields are gone and
# jsonable_encoder has nothing left to serialize. The request-scoped
# session is discarded after each request anyway, so there is no
# cross-request staleness risk from disabling this.
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
