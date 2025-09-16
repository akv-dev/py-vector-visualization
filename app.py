
import streamlit as st
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer

from database import fetch_articles
from visualization import reduce_dimensionality, create_plot, find_neighbors

st.set_page_config(layout="wide")

st.title("Vector Search Visualization")

st.write("This application visualizes your article vectors in a 2D space. You can search for a query and see the closest articles.")

@st.cache_data
def load_data():
    """Loads data from the database and caches it."""
    df = fetch_articles()
    return df

@st.cache_data
def get_embeddings(df):
    """Gets and caches the 2D embeddings of the article vectors."""
    vectors = np.array(df['title_vector'].tolist())
    vectors_2d, reducer = reduce_dimensionality(vectors)
    df_2d = pd.DataFrame(vectors_2d, columns=['x', 'y'])
    df_2d['title'] = df['title']
    return df_2d, reducer, vectors

df = load_data()

if df.empty:
    st.warning("No data found in the database. Please make sure the 'articles' table is populated.")
else:
    df_2d, reducer, vectors = get_embeddings(df)

    st.header("Article Vector Space")
    plot_placeholder = st.empty()
    plot_placeholder.plotly_chart(create_plot(df_2d), use_container_width=True)

    st.header("Search Query")
    query = st.text_input("Enter your search query:")

    if query:
        # Load the sentence transformer model
        model = SentenceTransformer('all-MiniLM-L6-v2')
        query_vector = model.encode(query)
        
        # Reduce the query vector's dimensionality
        query_vector_2d = reducer.transform([query_vector])[0]
        
        # Find the nearest neighbors
        neighbor_indices = find_neighbors(vectors, query_vector)
        neighbors_2d = df_2d.iloc[neighbor_indices][['x', 'y']].values
        
        # Update the plot with the query and neighbors
        plot_placeholder.plotly_chart(create_plot(df_2d, query_vector_2d, neighbors_2d), use_container_width=True)
