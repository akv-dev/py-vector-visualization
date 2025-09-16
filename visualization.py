
import numpy as np
import plotly.graph_objects as go
from sklearn.neighbors import NearestNeighbors
from umap import UMAP

def reduce_dimensionality(vectors):
    """Reduces the dimensionality of vectors to 2D using UMAP."""
    reducer = UMAP(n_components=2, random_state=42)
    vectors_2d = reducer.fit_transform(vectors)
    return vectors_2d, reducer

def create_plot(df_2d, query_vector_2d=None, neighbors_2d=None):
    """Creates an interactive scatter plot of the 2D vectors."""
    fig = go.Figure()

    # Add the main scatter plot for all articles
    fig.add_trace(go.Scatter(
        x=df_2d['x'],
        y=df_2d['y'],
        mode='markers',
        marker=dict(
            color='blue',
            size=5,
            opacity=0.6
        ),
        text=df_2d['title'],  # Text to show on hover
        hoverinfo='text',
        name='Articles'
    ))

    if query_vector_2d is not None and neighbors_2d is not None:
        # Add the query vector as a star
        fig.add_trace(go.Scatter(
            x=[query_vector_2d[0]],
            y=[query_vector_2d[1]],
            mode='markers',
            marker=dict(
                color='red',
                size=15,
                symbol='star'
            ),
            name='Query'
        ))

        # Highlight the neighbors
        fig.add_trace(go.Scatter(
            x=neighbors_2d[:, 0],
            y=neighbors_2d[:, 1],
            mode='markers',
            marker=dict(
                color='green',
                size=10,
                symbol='circle'
            ),
            name='Neighbors'
        ))

        # Draw lines from query to neighbors
        for neighbor in neighbors_2d:
            fig.add_shape(
                type="line",
                x0=query_vector_2d[0],
                y0=query_vector_2d[1],
                x1=neighbor[0],
                y1=neighbor[1],
                line=dict(
                    color="rgba(0,0,0,0.3)",
                    width=1,
                )
            )

    fig.update_layout(
        title="2D Visualization of Article Vectors",
        xaxis_title="Dimension 1",
        yaxis_title="Dimension 2",
        showlegend=True
    )

    return fig

def find_neighbors(vectors, query_vector, n_neighbors=5):
    """Finds the nearest neighbors to a query vector."""
    nn = NearestNeighbors(n_neighbors=n_neighbors)
    nn.fit(vectors)
    distances, indices = nn.kneighbors([query_vector])
    return indices[0]
