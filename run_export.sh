#!/bin/bash

# Simple wrapper for Gmail Forensic Export

EXPORT_DIR="export_results"
CONFIG="config.yml"

echo "Starting Gmail Forensic Export..."
echo "Config: $CONFIG"
echo "Output: $EXPORT_DIR"

# Ensure venv is active if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

python3 export_gmail_pierce.py --config "$CONFIG" --export-dir "$EXPORT_DIR"

echo "Export completed. Results are in $EXPORT_DIR"
