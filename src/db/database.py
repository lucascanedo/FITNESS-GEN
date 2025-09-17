# src/db/database.py
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from src.core.settings import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    future=True,
)
SessionLocal = sessionmaker(
    bind=engine, 
    autoflush=False, 
    autocommit=False, future=True
    )

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def ping_db() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False

# 👇 Só para teste direto via: python -m src.db.database
if __name__ == "__main__":
    print("DB OK?", ping_db())
