import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://neondb_owner:npg_7ywqSe2Vrunz@ep-divine-boat-azfdlaer.c-3.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def run_sql_script(filename: str):
    """
    Executes raw SQL scripts by splitting multi-statement files.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    possible_paths = [
        os.path.normpath(os.path.join(base_dir, "..", "sql", filename)),
        os.path.normpath(os.path.join(base_dir, "sql", filename)),
        os.path.normpath(os.path.join(base_dir, filename))
    ]

    target_path = None
    for p in possible_paths:
        if os.path.exists(p):
            target_path = p
            break

    if target_path:
        try:
            with engine.connect() as connection:
                with open(target_path, "r", encoding="utf-8") as file:
                    sql_content = file.read()
                
                statements = [stmt.strip() for stmt in sql_content.split(";") if stmt.strip()]
                for stmt in statements:
                    connection.execute(text(stmt))
                connection.commit()
            print(f"[NEON DB] Successfully executed script: {target_path}")
        except Exception as e:
            print(f"[NEON DB ERROR] Failed executing {target_path}: {e}")
    else:
        print(f"[NEON DB NOTICE] Script '{filename}' not found. Skipping raw SQL execution.")

def init_db():
    """Executes raw SQL scripts first to build PostGIS tables, then falls back to ORM metadata."""
    print("[NEON DB] Initializing Cloud Database...")
    
    # Run PostGIS schema and seed files first
    run_sql_script("01_schema.sql")
    run_sql_script("02_seed_data.sql")

    # Metadata check to sync any remaining SQLAlchemy models
    try:
        import models
        models.Base.metadata.create_all(bind=engine)
        print("[NEON DB] Models schema verified.")
    except Exception as e:
        print(f"[NEON DB WARNING] Standard metadata creation skipped: {e}")