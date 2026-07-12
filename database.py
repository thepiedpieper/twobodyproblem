import sqlite3
import pandas as pd
import os

DB_PATH = 'twobody.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create Universities Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Universities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            city TEXT,
            country TEXT,
            lat REAL,
            lon REAL,
            cat_friendly_rating INTEGER CHECK(cat_friendly_rating BETWEEN 1 AND 5),
            rental_notes TEXT
        )
    ''')
    
    # Create Positions Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            university_id INTEGER,
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
            acceptance_rate TEXT,
            FOREIGN KEY(university_id) REFERENCES Universities(id)
        )
    ''')
    
    conn.commit()
    conn.close()

def get_connection():
    return sqlite3.connect(DB_PATH)

def fetch_data(query, params=()):
    conn = get_connection()
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def execute_query(query, params=()):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    lastrowid = cursor.lastrowid
    conn.close()
    return lastrowid

def seed_data():
    pass

if __name__ == '__main__':
    init_db()
    seed_data()
