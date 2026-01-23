from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from sqlalchemy.pool import StaticPool 
from pathlib import Path

from database.models import Base

db_dir = Path(__file__).parent.parent / "data"
db_dir.mkdir(exist_ok=True)

db_path = db_dir / "contamination_gauge.db"

database_url = f"sqlite:///{db_path}"

engine = create_engine(
    database_url,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

@contextmanager
def get_db() -> Session:
    db=SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
        
