#!/bin/bash
# HoloDeck Samples Infrastructure Startup Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "  HoloDeck Samples Infrastructure Setup"
echo "=========================================="
echo ""

# Start services
echo "Starting Docker services..."
docker compose up -d

# Wait for ChromaDB to be healthy
echo ""
echo "Waiting for ChromaDB to be ready..."
MAX_RETRIES=30
RETRY_COUNT=0
until curl -s http://localhost:8000/api/v2/heartbeat > /dev/null 2>&1; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "ERROR: ChromaDB failed to start after $MAX_RETRIES attempts"
        exit 1
    fi
    echo "  Waiting... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done
echo "ChromaDB is ready!"

# Wait for Aspire Dashboard
echo ""
echo "Waiting for Aspire Dashboard to be ready..."
RETRY_COUNT=0
until curl -s http://localhost:18888 > /dev/null 2>&1; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "WARNING: Aspire Dashboard may not be fully ready yet"
        break
    fi
    echo "  Waiting... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done
echo "Aspire Dashboard is ready!"

echo ""
echo "=========================================="
echo "  Infrastructure Ready!"
echo "=========================================="
echo ""
echo "Services:"
echo "  - ChromaDB:         http://localhost:8000"
echo "  - Aspire Dashboard: http://localhost:18888"
echo "  - OTLP Endpoint:    http://localhost:4317"
echo ""
echo "Run a sample:"
echo "  cd samples/ticket-routing/openai"
echo "  holodeck serve agent.yaml"
echo ""
echo "Stop infrastructure:"
echo "  ./stop-infra.sh"
echo ""
