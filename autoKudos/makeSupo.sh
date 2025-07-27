#!/bin/bash

# Get the directory this script is in
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Use that as the project directory
PROJECT_DIR="$SCRIPT_DIR"

# Virtual environment location
VENV_DIR="$HOME/.venvs/autoKudos"

# Paths to key files
TEMPLATE_PATH="$PROJECT_DIR/template.tex"
INCLUDES_PATH="$PROJECT_DIR/includes.tex"
ENV_FILE="$PROJECT_DIR/.env"


# --- Step 2: Update template.tex to point to includes.tex ---
if [ -f "$TEMPLATE_PATH" ]; then
  # Only replace the first \input line if it exists
  if grep -q '\\input{.*includes\.tex}' "$TEMPLATE_PATH"; then
    sed -i "0,/\\input{.*includes\.tex}/s|\\input{.*includes\.tex}|\\input{$INCLUDES_PATH}|" "$TEMPLATE_PATH"
    echo "Updated \\input path in template.tex to: $INCLUDES_PATH"
  else
    echo "Warning: template.tex does not contain an \\input{...includes.tex} line"
  fi
else
  echo "Warning: template.tex not found at $TEMPLATE_PATH"
fi

# --- Step 3: Create venv if needed ---
if [ ! -d "$VENV_DIR" ]; then
  echo "Creating virtual environment at $VENV_DIR"
  python3 -m venv --copies "$VENV_DIR" || {
    echo "Failed to create virtual environment" >&2
    exit 1
  }

  echo "Installing requirements..."
  "$VENV_DIR/bin/pip" install -r "$PROJECT_DIR/requirements.txt" || {
    echo "Failed to install requirements" >&2
    exit 1
  }

  # Run playwright install to download browsers
  echo "Running 'playwright install' to download browsers..."
  "$VENV_DIR/bin/playwright" install || {
    echo "Failed to install playwright browsers" >&2
    exit 1
  }
fi

# --- Step 4: Run the Python script ---
echo "Running updateTex.py..."
"$VENV_DIR/bin/python" "$PROJECT_DIR/updateTex.py" --env-file "$ENV_FILE" --template-path "$TEMPLATE_PATH" "$@"