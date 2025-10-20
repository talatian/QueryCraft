#!/bin/sh
# entrypoint.sh - start Ollama server and pull models without curl

set -e

# Start Ollama server in background
echo "Starting Ollama server..."
ollama serve &

# Wait for server to be ready using Ollama CLI
echo "Waiting for Ollama server to be ready..."
until ollama list > /dev/null 2>&1; do
  sleep 2
done

echo "Server is ready."

# Pull models
echo "Pulling model: $OLLAMA_MODEL"
ollama pull "$OLLAMA_MODEL"

echo "All models pulled. Ollama server running."

# Wait for the server process to prevent container exit
wait
