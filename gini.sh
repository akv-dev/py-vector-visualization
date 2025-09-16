#!/bin/bash
# Exit immediately if a command exits with a non-zero status.
set -e

# --- 1. Detect Container Engine ---
echo "Checking for Docker or Podman..."
if command -v docker &> /dev/null; then
    CONTAINER_CMD="docker"
elif command -v podman &> /dev/null; then
    CONTAINER_CMD="podman"
else
    echo "Error: Neither Docker nor Podman found. Please install one to proceed."
    exit 1
fi
echo "Using '$CONTAINER_CMD' as the container engine."

# --- 2. Load Environment and Start Database ---
echo "Loading database configuration..."
if [ ! -f .env ]; then
    echo "Error: .env file not found. Please copy .env.example to .env and fill in your database details."
    exit 1
fi

# Export variables from .env file for the container
export $(grep -v '^#' .env | xargs)

DB_CONTAINER_NAME="vector-db"

# Check if the container is already running
if ! $CONTAINER_CMD ps --filter "name=^/${DB_CONTAINER_NAME}$" --format '{{.Names}}' | grep -q "${DB_CONTAINER_NAME}"; then
    # Check if the container exists but is stopped
    if $CONTAINER_CMD ps -a --filter "name=^/${DB_CONTAINER_NAME}$" --format '{{.Names}}' | grep -q "${DB_CONTAINER_NAME}"; then
        echo "Container '${DB_CONTAINER_NAME}' is stopped. Starting it..."
        $CONTAINER_CMD start ${DB_CONTAINER_NAME}
    else
        echo "Container '${DB_CONTAINER_NAME}' not found. Creating and starting a new one..."
        $CONTAINER_CMD run -d \
            --name ${DB_CONTAINER_NAME} \
            -p "${DB_PORT:-5432}:5432" \
            -e "POSTGRES_DB=${DB_NAME}" \
            -e "POSTGRES_USER=${DB_USER}" \
            -e "POSTGRES_PASSWORD=${DB_PASSWORD}" \
            ankane/pgvector:latest
    fi
    echo "Waiting for the database to initialize (10 seconds)..."
    sleep 10
else
    echo "Database container '${DB_CONTAINER_NAME}' is already running."
fi

# --- 3. Check and Install uv ---
echo "Checking for 'uv'வுகளை..."
if ! command -v uv &> /dev/null; then
    echo "'uv' not found. Installing it with pip..."
    pip install uv
else
    echo "'uv' is already installed."
fi

# --- 4. Install Dependencies ---
echo "Installing Python dependencies with uv..."
uv pip install -r requirements.txt

# --- 5. Run the Project ---
echo "Starting the Streamlit application with uv..."
uv streamlit run app.py
