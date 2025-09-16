import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def get_db_engine():
    """Establishes a connection engine to the PostgreSQL database using SQLAlchemy."""
    db_uri = (
        f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
    engine = create_engine(db_uri)
    return engine

def fetch_articles(limit=5000):
    """Fetches a random sample of articles and their title vectors from the database."""
    engine = get_db_engine()
    # Use ORDER BY RANDOM() to get a different sample each time, which is good for visualization.
    # For a production app with stable plots, you might use a seeded random or another sampling method.
    query = text(f"SELECT title, title_vector FROM articles ORDER BY RANDOM() LIMIT {limit}")
    
    with engine.connect() as connection:
        df = pd.read_sql_query(query, connection)

    # Convert the vector strings back to numpy arrays
    df['title_vector'] = df['title_vector'].apply(lambda x: tuple(float(val) for val in x.strip('[]').split(',')))
    return df