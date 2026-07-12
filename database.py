import psycopg2
import psycopg2.extras
import pandas as pd
import os
import streamlit as st

def get_connection():
    # Use streamlit secrets if available, else environment variable
    try:
        db_url = st.secrets["DATABASE_URL"]
    except:
        db_url = os.environ.get("DATABASE_URL", "postgresql://postgres.odrqqkonfjugovnyhhvi:BoiandMisso@aws-1-ap-south-1.pooler.supabase.com:6543/postgres")
    
    return psycopg2.connect(db_url)

def init_db():
    pass # Managed by seed.sql now

def fetch_data(query, params=()):
    conn = get_connection()
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def execute_query(query, params=()):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    
    lastrowid = None
    if "RETURNING" in query:
        lastrowid = cursor.fetchone()[0]
        
    conn.commit()
    conn.close()
    return lastrowid

def seed_data():
    pass

if __name__ == '__main__':
    pass
