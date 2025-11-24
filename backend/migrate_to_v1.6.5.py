"""
Database Migration Script for v1.6.5
Adds photo4-6 and embedding4-6 columns and auto-duplicates existing photos
"""
import sqlite3
import sys

def migrate_database(db_path='./attendance.db'):
    print("=== v1.6.5 Database Migration ===")
    print(f"Target database: {db_path}\n")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(employees)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'photo4' in columns:
            print("✓ Migration already applied. Skipping.")
            return
        
        print("[1/3] Adding new columns...")
        # Add new photo columns
        cursor.execute("ALTER TABLE employees ADD COLUMN photo4 BLOB")
        cursor.execute("ALTER TABLE employees ADD COLUMN photo5 BLOB")
        cursor.execute("ALTER TABLE employees ADD COLUMN photo6 BLOB")
        
        # Add new embedding columns
        cursor.execute("ALTER TABLE employees ADD COLUMN embedding4 BLOB")
        cursor.execute("ALTER TABLE employees ADD COLUMN embedding5 BLOB")
        cursor.execute("ALTER TABLE employees ADD COLUMN embedding6 BLOB")
        print("✓ Columns added successfully")
        
        print("\n[2/3] Auto-duplicating existing photos...")
        # Duplicate existing photos for backward compatibility
        cursor.execute("""
            UPDATE employees 
            SET photo4 = photo1, 
                photo5 = photo2, 
                photo6 = photo3,
                embedding4 = embedding1,
                embedding5 = embedding2,
                embedding6 = embedding3
            WHERE photo1 IS NOT NULL
        """)
        
        affected = cursor.rowcount
        print(f"✓ Duplicated photos for {affected} employees")
        
        print("\n[3/3] Committing changes...")
        conn.commit()
        print("✓ Migration completed successfully!")
        
        print("\n=== Summary ===")
        print(f"✓ Added 6 new columns (photo4-6, embedding4-6)")
        print(f"✓ Auto-duplicated photos for {affected} existing employees")
        print(f"✓ New employees will use all 6 photos for better accuracy")
        
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
