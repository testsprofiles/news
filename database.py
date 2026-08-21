import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
from contextlib import contextmanager


load_dotenv()

def get_db_connection():
   
   
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            database=os.getenv("DB_NAME", "news_db"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD"),
            port=os.getenv("DB_PORT", "5432"),
            cursor_factory=RealDictCursor
        )
        return conn
    except Exception as e:
        print(f"Bazada xatolik: {e}")
        return None
@contextmanager
def db_cursor(commit=False):
    conn = get_db_connection()
    if not conn:
        raise ConnectionError("DB_CONNECTION_FAILED")
    try:
        cur = conn.cursor()
        yield cur
        if commit:
            conn.commit()
    finally:
        cur.close()
        conn.close()
