import sqlite3
import psycopg2
import os

DATABASE_URL = "postgresql://postgres.odrqqkonfjugovnyhhvi:BoiandMisso@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"
SQLITE_DB = "twobody.db"

def migrate():
    print("Connecting to Supabase...")
    pg_conn = psycopg2.connect(DATABASE_URL)
    pg_cursor = pg_conn.cursor()

    # Drop existing tables just in case we are re-running
    pg_cursor.execute("DROP TABLE IF EXISTS Positions;")
    pg_cursor.execute("DROP TABLE IF EXISTS Universities;")
    
    # Create Universities Table in Postgres
    pg_cursor.execute('''
        CREATE TABLE Universities (
            id SERIAL PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            city TEXT,
            country TEXT,
            lat REAL,
            lon REAL,
            cat_friendly_rating INTEGER CHECK(cat_friendly_rating BETWEEN 1 AND 5),
            rental_notes TEXT
        )
    ''')
    
    # Create Positions Table in Postgres
    pg_cursor.execute('''
        CREATE TABLE Positions (
            id SERIAL PRIMARY KEY,
            university_id INTEGER REFERENCES Universities(id),
            track TEXT,
            department TEXT,
            pi_name TEXT,
            pi_research_abstract TEXT,
            vacancy_status TEXT,
            difficulty_tier TEXT,
            deadline_date TEXT,
            sop_draft_text TEXT,
            document_checklist TEXT,
            core_domain TEXT,
            model_system TEXT,
            link TEXT,
            acceptance_rate TEXT
        )
    ''')
    pg_conn.commit()
    print("Tables created in Supabase.")

    # Read from SQLite
    print("Reading from SQLite...")
    sl_conn = sqlite3.connect(SQLITE_DB)
    sl_cursor = sl_conn.cursor()
    
    # Migrate Universities
    sl_cursor.execute("SELECT id, name, city, country, lat, lon, cat_friendly_rating, rental_notes FROM Universities")
    universities = sl_cursor.fetchall()
    print(f"Found {len(universities)} universities.")
    
    for u in universities:
        # id is index 0
        pg_cursor.execute('''
            INSERT INTO Universities (id, name, city, country, lat, lon, cat_friendly_rating, rental_notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', u)
    
    # Reset sequence for Universities so new inserts work
    pg_cursor.execute("SELECT setval(pg_get_serial_sequence('Universities', 'id'), coalesce(max(id), 1), max(id) IS NOT null) FROM Universities;")
    
    # Migrate Positions
    sl_cursor.execute("SELECT id, university_id, track, department, pi_name, pi_research_abstract, vacancy_status, difficulty_tier, deadline_date, sop_draft_text, document_checklist, core_domain, model_system, link, acceptance_rate FROM Positions")
    positions = sl_cursor.fetchall()
    print(f"Found {len(positions)} positions.")
    
    for p in positions:
        pg_cursor.execute('''
            INSERT INTO Positions (id, university_id, track, department, pi_name, pi_research_abstract, vacancy_status, difficulty_tier, deadline_date, sop_draft_text, document_checklist, core_domain, model_system, link, acceptance_rate)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', p)
        
    # Reset sequence for Positions
    pg_cursor.execute("SELECT setval(pg_get_serial_sequence('Positions', 'id'), coalesce(max(id), 1), max(id) IS NOT null) FROM Positions;")
        
    pg_conn.commit()
    print("Data migrated successfully!")
    
    pg_cursor.close()
    pg_conn.close()
    sl_cursor.close()
    sl_conn.close()

if __name__ == '__main__':
    migrate()
