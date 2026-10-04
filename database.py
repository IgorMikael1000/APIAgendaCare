import os
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import CreateColumn

# A URL do Neon PostgreSQL será pega nas variáveis de ambiente do Render
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://usuario:senha@host/dbname?sslmode=require")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def create_or_update_schema():
    Base.metadata.create_all(bind=engine)

    with engine.begin() as connection:
        inspector = inspect(connection)
        preparer = connection.dialect.identifier_preparer

        for table in Base.metadata.sorted_tables:
            if not inspector.has_table(table.name):
                continue

            existing_columns = {
                column["name"] for column in inspector.get_columns(table.name)
            }
            quoted_table = preparer.quote(table.name)
            for column in table.columns:
                if column.name in existing_columns:
                    continue

                column_ddl = CreateColumn(column).compile(dialect=connection.dialect)
                connection.execute(
                    text(f"ALTER TABLE {quoted_table} ADD COLUMN {column_ddl}")
                )
                existing_columns.add(column.name)

        for table in Base.metadata.sorted_tables:
            if inspector.has_table(table.name):
                for index in table.indexes:
                    index.create(bind=connection, checkfirst=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()