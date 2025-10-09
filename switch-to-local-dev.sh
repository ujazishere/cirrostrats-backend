#!/bin/bash
# Switch from full stack to local development mode

echo "🔄 Switching to local development mode..."
echo ""

# Stop full stack
echo "Stopping full stack..."
docker-compose -f observability/docker-compose.full.yml down

# Start observability only
echo "Starting observability stack only..."
docker-compose -f observability/docker-compose.observability-only.yml up -d

echo ""
echo "⏳ Waiting for services (30s)..."
sleep 30

echo ""
echo "✅ Observability stack ready!"
echo ""
echo "Now run backend locally:"
echo ""
echo "  export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317"
echo "  export OTEL_SERVICE_NAME=cirrostrats-backend-api"
echo "  export ENV=dev"
echo "  uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
echo ""
