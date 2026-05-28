#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# YLYI Dashboard launcher.
# Double-click this file in Finder to start the dashboard + Insight Bot.
# (First run sets up the Python environment and takes a few minutes.)
# ─────────────────────────────────────────────────────────────────────────────

cd "$(dirname "$0")" || exit 1

echo "=============================================="
echo "  Your Library, Your Impact — Dashboard"
echo "=============================================="
echo

# 1. Check the local AI model server (Ollama) is running.
if ! curl -s -m 3 http://localhost:11434/api/tags >/dev/null 2>&1; then
  echo "NOTE: Ollama is not responding on localhost:11434."
  echo "      The dashboard will still open, but the Insight Bot needs Ollama"
  echo "      running with the granite4.1:3b model. Open the Ollama app (or run"
  echo "      'ollama serve' and 'ollama pull granite4.1:3b'), then restart this."
  echo
fi

# 2. Create the Python environment on first run.
if [ ! -d ".venv" ]; then
  echo "First-time setup: creating the Python environment (a few minutes)…"
  python3 -m venv .venv || { echo "Could not create venv — is Python 3 installed?"; read -r -n1 -p "Press any key to close."; exit 1; }
  ./.venv/bin/python -m pip install --quiet --upgrade pip
  ./.venv/bin/python -m pip install --quiet -r requirements.txt || { echo "Dependency install failed."; read -r -n1 -p "Press any key to close."; exit 1; }
  echo "Setup complete."
  echo
fi

# 3. Launch. Streamlit opens your browser at http://localhost:8501 automatically.
echo "Starting the dashboard… your browser will open shortly."
echo "Leave this window open while you use it. Close it (or press Ctrl-C) to stop."
echo
exec ./.venv/bin/python -m streamlit run app.py
