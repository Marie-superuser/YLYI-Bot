#!/usr/bin/env bash
# Pull the Ollama model defined in .env (or the default) into the running container.
# Run once after: docker compose up -d

set -euo pipefail

MODEL="${OLLAMA_MODEL:-granite4.1:3b}"

echo "Pulling model '$MODEL' into the Ollama container..."
# Must use 'docker compose exec' (not local ollama) — the container has its own model store.
docker compose exec ollama ollama pull "$MODEL"
echo "Done. Verifying..."
docker compose exec ollama ollama list | grep "$MODEL" && echo "Model '$MODEL' is ready." || echo "WARNING: model not found after pull."
