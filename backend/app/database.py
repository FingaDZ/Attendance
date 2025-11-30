from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./attendance.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def migrate_database_schema():
    """
    Auto-migration for v1.6.5: Add photo4-6 and embedding4-6 columns if they don't exist.
    This ensures backward compatibility when upgrading from v1.6.0 to v1.6.5.
    """
    inspector = inspect(engine)
    
    # Check if employees table exists
    if 'employees' not in inspector.get_table_names():
        print("Creating new database schema...")
        Base.metadata.create_all(bind=engine)
        return
    
    # Get existing columns
    existing_columns = [col['name'] for col in inspector.get_columns('employees')]
    
    # Define required columns for v1.6.5
    required_columns = ['photo4', 'photo5', 'photo6', 'embedding4', 'embedding5', 'embedding6']
    missing_columns = [col for col in required_columns if col not in existing_columns]
    
    if missing_columns:
        print(f"[Migration] Adding missing columns: {missing_columns}")
        
        # Add missing columns using raw SQL (SQLite doesn't support adding multiple columns at once)
        with engine.connect() as conn:
            for col in missing_columns:
                try:
                    conn.execute(text(f"ALTER TABLE employees ADD COLUMN {col} BLOB"))
                    conn.commit()
                    print(f"  ✓ Added column: {col}")
                except Exception as e:
                    if "duplicate column name" not in str(e).lower():
                        print(f"  ✗ Error adding {col}: {e}")
            
            # Auto-duplicate existing photos for backward compatibility
            if 'photo4' in missing_columns:
                print("[Migration] Auto-duplicating existing employee photos...")
                try:
                    conn.execute(text("""
                        UPDATE employees 
                        SET photo4 = photo1, 
                            photo5 = photo2, 
                            photo6 = photo3,
                            embedding4 = embedding1,
                            embedding5 = embedding2,
                            embedding6 = embedding3
                        WHERE photo1 IS NOT NULL
                    """))
                    conn.commit()
                    print("  ✓ Photos duplicated successfully")
                except Exception as e:
                    print(f"  ✗ Error duplicating photos: {e}")
        
        print("[Migration] Database migration completed!")
    else:
        print("[Migration] Database schema is up to date (v1.6.5)")
