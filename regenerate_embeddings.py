
import pandas as pd
from sentence_transformers import SentenceTransformer
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

MODEL_NAME = 'Alibaba-NLP/gte-large-en-v1.5'

def get_db_engine():
    """Establishes a connection engine to the PostgreSQL database using SQLAlchemy."""
    db_uri = (
        f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
    engine = create_engine(db_uri)
    return engine

def main():
    """Main function to regenerate embeddings for all articles."""
    print("Connecting to the database...")
    engine = get_db_engine()
    
    with engine.connect() as connection:
        print("Fetching all article titles...")
        # Fetch only id and title, as content can be large
        df = pd.read_sql_query(text("SELECT id, title FROM articles"), connection)
        print(f"Found {len(df)} articles to process.")

        print(f"Loading sentence transformer model: {MODEL_NAME}...")
        # trust_remote_code is needed for this specific model
        model = SentenceTransformer(MODEL_NAME, trust_remote_code=True)

        print("Generating new 1024-dimension embeddings for each article title...")
        # This may take a while depending on the number of articles
        embeddings = model.encode(df['title'].tolist(), show_progress_bar=True)

        print("Updating database records with new embeddings...")
        for i, row in df.iterrows():
            article_id = row['id']
            embedding = embeddings[i].tolist() # Convert numpy array to list for DB
            
            # Create a SQL-safe string representation of the vector
            vector_str = f"'[{ ", ".join(map(str, embedding)) }]'"

            update_query = text(f"UPDATE articles SET title_vector = {vector_str} WHERE id = {article_id}")
            connection.execute(update_query)
            
            if (i + 1) % 100 == 0:
                print(f"Updated {i + 1}/{len(df)} articles...")
        
        # Commit the transaction to make the changes permanent
        connection.commit()

    print("\nDatabase update complete!")
    print("All articles now have 1024-dimension vectors.")
    print("You can now run the main application with './gini.sh'")

if __name__ == "__main__":
    main()
