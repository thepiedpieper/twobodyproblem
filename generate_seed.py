import sqlite3

SQLITE_DB = "twobody.db"
SEED_FILE = "seed.sql"

def escape_sql(value):
    if value is None:
        return 'NULL'
    if isinstance(value, (int, float)):
        return str(value)
    # Escape single quotes
    clean_val = str(value).replace("'", "''")
    return f"'{clean_val}'"

def generate():
    sl_conn = sqlite3.connect(SQLITE_DB)
    sl_cursor = sl_conn.cursor()
    
    with open(SEED_FILE, 'w') as f:
        # Schema definition
        f.write("-- Create Tables\n")
        f.write("DROP TABLE IF EXISTS Positions;\n")
        f.write("DROP TABLE IF EXISTS Universities;\n\n")
        
        f.write('''CREATE TABLE Universities (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    city TEXT,
    country TEXT,
    lat REAL,
    lon REAL,
    cat_friendly_rating INTEGER CHECK(cat_friendly_rating BETWEEN 1 AND 5),
    rental_notes TEXT
);\n\n''')
        
        f.write('''CREATE TABLE Positions (
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
);\n\n''')
        
        # Universities Data
        f.write("-- Insert Universities\n")
        sl_cursor.execute("SELECT id, name, city, country, lat, lon, cat_friendly_rating, rental_notes FROM Universities")
        universities = sl_cursor.fetchall()
        for u in universities:
            values = ", ".join([escape_sql(v) for v in u])
            f.write(f"INSERT INTO Universities (id, name, city, country, lat, lon, cat_friendly_rating, rental_notes) VALUES ({values});\n")
            
        f.write("\nSELECT setval(pg_get_serial_sequence('Universities', 'id'), coalesce(max(id), 1), max(id) IS NOT null) FROM Universities;\n\n")

        # Positions Data
        f.write("-- Insert Positions\n")
        sl_cursor.execute("SELECT id, university_id, track, department, pi_name, pi_research_abstract, vacancy_status, difficulty_tier, deadline_date, sop_draft_text, document_checklist, core_domain, model_system, link, acceptance_rate FROM Positions WHERE university_id IN (SELECT id FROM Universities)")
        positions = sl_cursor.fetchall()
        for p in positions:
            values = ", ".join([escape_sql(v) for v in p])
            f.write(f"INSERT INTO Positions (id, university_id, track, department, pi_name, pi_research_abstract, vacancy_status, difficulty_tier, deadline_date, sop_draft_text, document_checklist, core_domain, model_system, link, acceptance_rate) VALUES ({values});\n")
            
        f.write("\nSELECT setval(pg_get_serial_sequence('Positions', 'id'), coalesce(max(id), 1), max(id) IS NOT null) FROM Positions;\n")
        
    print(f"Generated {SEED_FILE} successfully!")
    sl_conn.close()

if __name__ == '__main__':
    generate()
