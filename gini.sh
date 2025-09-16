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
    echo ".env file not found. Creating one with default credentials."
    cat > .env << EOL
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
EOL
    echo "Default .env file created. You can edit this file to change the database configuration."
else
    echo "Using existing .env file."
fi

# Export variables from .env file for the container
export $(grep -v '^#' .env | xargs)

DB_CONTAINER_NAME="postgres"

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
            pgvector/pgvector:pg17-trixie
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

# --- 4. Setup Environment and Install Dependencies ---
CORRECT_PYTHON_VERSION="3.11"
VENV_PYTHON=".venv/bin/python"

# Check if venv exists and if it has the correct python version
if [ -d ".venv" ] && $VENV_PYTHON --version 2>&1 | grep -q "Python $CORRECT_PYTHON_VERSION"; then
    echo "Correct virtual environment (.venv with Python $CORRECT_PYTHON_VERSION) already exists."
else
    echo "Virtual environment is missing or has the wrong Python version."
    echo "Removing old environment (if it exists) and creating a new one with Python $CORRECT_PYTHON_VERSION..."
    rm -rf .venv
    # Requesting Python 3.11 to ensure compatibility with scientific computing packages.
    # uv will download it if not available.
    uv venv --python $CORRECT_PYTHON_VERSION
fi

echo "Installing Python dependencies with uv..."
uv pip install -r requirements.txt

# --- 5. Run the Project ---
echo "Starting the Streamlit application with 'uv run'..."
uv run streamlit run app.py
