#!/bin/bash
set -e

echo "Starting setup for Mahabharata Hybrid RAG Knowledge Base..."

echo "1. Downloading and preparing data..."
python scripts/download_and_prep_data.py

echo "2. Building Vector Index..."
python scripts/build_index.py

echo "3. Building Knowledge Graph..."
python scripts/build_graph.py

echo "4. Building RAPTOR Index..."
python scripts/build_raptor.py

echo "Setup complete! You can now run agentic_query.py or hybrid_query.py."
