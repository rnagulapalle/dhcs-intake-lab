#!/bin/bash
# Setup script for DHCS BHT Multi-Agent System

set -e

echo "================================================"
echo "DHCS BHT Multi-Agent System Setup"
echo "================================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo ""
    echo "📝 Please edit .env and add your OPENAI_API_KEY"
    echo "   Run: nano .env"
    echo ""
    echo "After adding your API key, run this script again."
    exit 1
fi

# Check if OPENAI_API_KEY is set
source .env
if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "your_openai_api_key_here" ]; then
    echo "❌ OPENAI_API_KEY not set in .env file"
    echo "   Please edit .env and add your OpenAI API key"
    exit 1
fi

echo "✅ Environment variables loaded"
echo ""

# Check Docker
echo "Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker Desktop"
    exit 1
fi

if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose not found. Please install Docker Compose"
    exit 1
fi

echo "✅ Docker and Docker Compose found"
echo ""

# Start services
echo "Starting all services..."
docker compose up -d

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 20

# Check service health
echo ""
echo "Checking service health..."
docker compose ps

echo ""
echo "Waiting for Pinot to be ready..."
sleep 10

# Bootstrap Pinot (schema and table)
echo ""
echo "================================================"
echo "Bootstrapping Pinot..."
echo "================================================"

echo "1. Copying schema to Pinot controller..."
docker cp pinot/schema.json pinot-controller:/tmp/schema.json

echo "2. Registering schema..."
docker compose exec -T pinot-controller bash -lc \
  "bin/pinot-admin.sh AddSchema -schemaFile /tmp/schema.json -exec"

echo "3. Creating realtime table..."
curl -s -X POST \
  -H "Content-Type: application/json" \
  --data-binary @pinot/table-realtime.json \
  "http://localhost:9000/tables" | jq .

echo ""
echo "✅ Pinot bootstrap complete"

# Test API
echo ""
echo "Testing Agent API..."
sleep 5

if curl -s -f http://localhost:8000/health > /dev/null; then
    echo "✅ Agent API is healthy"
else
    echo "⚠️  Agent API not responding yet. It may still be initializing..."
fi

echo ""
echo "================================================"
echo "Setup Complete!"
echo "================================================"
echo ""
echo "🎉 All services are running!"
echo ""
echo "Access points:"
echo "  📊 Streamlit Dashboard: http://localhost:8501"
echo "  🤖 Agent API:            http://localhost:8000"
echo "  📈 Pinot Console:        http://localhost:9000"
echo "  🔍 API Docs:             http://localhost:8000/docs"
echo ""
echo "Example queries:"
echo '  curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '"'"'{"message":"How many events in the last hour?"}'"'"''
echo ""
echo "To view logs:"
echo "  docker compose logs -f agent-api"
echo "  docker compose logs -f dashboard"
echo ""
echo "To stop services:"
echo "  docker compose down"
echo ""
