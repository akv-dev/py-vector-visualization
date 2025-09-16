
import streamlit as st
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from umap import UMAP

from database import fetch_articles
from visualization import create_plot, find_neighbors

st.set_page_config(layout="wide")
st.title("Vector Search Visualization")

# Define the model name as a constant
MODEL_NAME = 'Supabase/gte-large-en-1.5'
DATA_LIMIT = 5000

@st.cache_data
def load_and_process_data():
    """Loads a sample of data from the database and performs dimensionality reduction."""
    df = fetch_articles(limit=DATA_LIMIT)
    if df.empty:
        return None, None, None, None

    st.write(f"Loaded a random sample of {len(df)} articles from the database.")

    vectors = np.array(df['title_vector'].tolist())
    reducer = UMAP(n_components=2, random_state=42, n_jobs=1)
    vectors_2d = reducer.fit_transform(vectors)
    
    df_2d = pd.DataFrame(vectors_2d, columns=['x', 'y'])
    df_2d['title'] = df['title']
    
    return df_2d, reducer, vectors, df

# --- Main App UI ---

query = st.text_area("Enter your search query here:", height=150)

if st.button("Search"):
    if not query.strip():
        st.warning("Please enter a search query.")
    else:
        with st.spinner(f"Loading {DATA_LIMIT} articles, processing vectors, and performing search..."):
            df_2d, reducer, vectors, df_full = load_and_process_data()

            if df_2d is None:
                st.error("Could not load data from the database. Please ensure the database is running and populated.")
            else:
                # 1. Encode the query using the correct model
                model = SentenceTransformer(MODEL_NAME)
                query_vector = model.encode(query)

                # 2. Find nearest neighbors
                neighbor_indices = find_neighbors(vectors, query_vector)
                neighbor_titles = df_full.iloc[neighbor_indices]['title'].tolist()

                # 3. Reduce query vector dimensionality for plotting
                query_vector_2d = reducer.transform([query_vector])[0]
                neighbors_2d = df_2d.iloc[neighbor_indices][['x', 'y']].values

                st.success("Search complete!")

                # --- Display Results ---
                col1, col2 = st.columns([1, 2])

                with col1:
                    st.header("Search Results")
                    st.write(f"The most similar articles in the {DATA_LIMIT}-item sample are:")
                    for i, title in enumerate(neighbor_titles):
                        st.markdown(f"{i+1}. {title}")
                
                with col2:
                    st.header("Vector Visualization")
                    plot = create_plot(df_2d, query_vector_2d, neighbors_2d)
                    st.plotly_chart(plot, use_container_width=True)
