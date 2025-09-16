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
export $(grep -v '^#' .env | xargs)
DB_CONTAINER_NAME="postgres"
if ! $CONTAINER_CMD ps --filter "name=^/${DB_CONTAINER_NAME}$" --format '{{.Names}}' | grep -q "${DB_CONTAINER_NAME}"; then
    if $CONTAINER_CMD ps -a --filter "name=^/${DB_CONTAINER_NAME}$" --format '{{.Names}}' | grep -q "${DB_CONTAINER_NAME}"; then
        echo "Container '${DB_CONTAINER_NAME}' is stopped. Starting it..."
        $CONTAINER_CMD start ${DB_CONTAINER_NAME}
    else
        echo "Container '${DB_CONTAINER_NAME}' not found. Creating and starting a new one..."
        $CONTAINER_CMD run -d --name ${DB_CONTAINER_NAME} -p "${DB_PORT:-5432}:5432" -e "POSTGRES_DB=${DB_NAME}" -e "POSTGRES_USER=${DB_USER}" -e "POSTGRES_PASSWORD=${DB_PASSWORD}" pgvector/pgvector:pg17-trixie
    fi
    echo "Waiting for the database to initialize (10 seconds)..."
    sleep 10
else
    echo "Database container '${DB_CONTAINER_NAME}' is already running."
fi

# --- 3. Check and Install uv ---
echo "Checking for 'uv'..."
if ! command -v uv &> /dev/null; then
    echo "'uv' not found. Installing it with pip..."
    pip install uv
else
    echo "'uv' is already installed."
fi

# --- 4. Setup Environment and Install Dependencies ---
CORRECT_PYTHON_VERSION="3.11"
VENV_PYTHON=".venv/bin/python"
if [ -d ".venv" ] && $VENV_PYTHON --version 2>&1 | grep -q "Python $CORRECT_PYTHON_VERSION"; then
    echo "Correct virtual environment (.venv with Python $CORRECT_PYTHON_VERSION) already exists."
else
    echo "Virtual environment is missing or has the wrong Python version."
    echo "Removing old environment (if it exists) and creating a new one with Python $CORRECT_PYTHON_VERSION..."
    rm -rf .venv
    uv venv --python $CORRECT_PYTHON_VERSION
fi
echo "Installing Python dependencies with uv..."
uv pip install -r requirements.txt

# --- 5. Main Menu ---
echo ""
echo "--------------------------------------------------"
echo "Setup complete. What would you like to do next?"
echo "--------------------------------------------------"

PS3='Please enter your choice: '
options=("Regenerate Database Embeddings" "Run Visualization App" "Quit")
select opt in "${options[@]}"
do
    case $opt in
        "Regenerate Database Embeddings")
            echo ""
            echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!! WARNING !!!!!!!!!!!!!!!!!!!!!!!!!!!!"
            echo "This will replace the vectors for ALL articles in your database with 1024-dimension vectors."
            echo "This is a destructive operation."
            echo ""
            echo "Before proceeding, you MUST run this SQL command on your database:"
            echo "=> ALTER TABLE articles ALTER COLUMN title_vector TYPE vector(1024);"
            echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
            echo ""
            read -p "Have you run the ALTER TABLE command and wish to proceed? (y/n) " -n 1 -r
            echo ""
            if [[ $REPLY =~ ^[Yy]$ ]]
            then
                echo "Starting embedding regeneration..."
                uv run python regenerate_embeddings.py
                echo "Regeneration complete."
            else
                echo "Regeneration cancelled."
            fi
            # After running, exit the script. User can re-run to see the menu again.
            exit 0
            ;;
        "Run Visualization App")
            echo "Starting visualization app..."
            uv run streamlit run app.py
            exit 0
            ;;
        "Quit")
            break
            ;;
        *) echo "invalid option $REPLY";;
    esac
done