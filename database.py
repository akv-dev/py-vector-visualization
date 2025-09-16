
import os
import pandas as pd
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )
    return conn

def fetch_articles():
    """Fetches articles and their title vectors from the database."""
    conn = get_db_connection()
    query = "SELECT title, title_vector FROM articles;"
    # Use pandas to directly read the SQL query into a DataFrame
    df = pd.read_sql_query(query, conn)
    conn.close()
    # Convert the vector strings back to numpy arrays
    # The vector from pgvector looks like '[1,2,3,...]', so we slice and split
    df['title_vector'] = df['title_vector'].apply(lambda x: [float(val) for val in x.strip('[]').split(',')])
    return df
