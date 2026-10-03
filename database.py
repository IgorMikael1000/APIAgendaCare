import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# A URL do Neon PostgreSQL será pega nas variáveis de ambiente do Render
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://usuario:senha@host/dbname?sslmode=require")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()