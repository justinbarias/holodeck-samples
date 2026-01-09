#!/bin/bash
# HoloDeck Samples Infrastructure Shutdown Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "  Stopping HoloDeck Infrastructure"
echo "=========================================="
echo ""

docker compose down

echo ""
echo "Infrastructure stopped."
echo ""
