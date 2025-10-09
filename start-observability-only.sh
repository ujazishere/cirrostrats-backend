#!/bin/bash
# Start Observability Stack Only (for local backend development)

set -e

echo "🔍 Starting Observability Stack (without backend)..."
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Start the stack
echo -e "${GREEN}🐳 Starting Docker Compose observability services...${NC}"
docker-compose -f observability/docker-compose.observability-only.yml up -d

echo ""
echo -e "${YELLOW}⏳ Waiting for services to become healthy (30s)...${NC}"
sleep 30

# Check service health
echo ""
echo "📊 Service Health Check:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

check_service() {
    local name=$1
    local url=$2
    local port=$3

    if curl -sf "$url" > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} $name (http://localhost:$port)"
    else
        echo -e "  ${RED}✗${NC} $name (http://localhost:$port) - NOT READY"
    fi
}

check_service "Grafana          " "http://localhost:3000/api/health" "3000"
check_service "Prometheus       " "http://localhost:9090/-/healthy" "9090"
check_service "Loki             " "http://localhost:3100/ready" "3100"
check_service "Tempo            " "http://localhost:3200/ready" "3200"
check_service "OTel Collector   " "http://localhost:13133/" "13133"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Show access URLs
echo "🌐 Access Points:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "  ${GREEN}Grafana${NC}        → http://localhost:3000  (admin/admin)"
echo -e "  ${GREEN}Prometheus${NC}     → http://localhost:9090"
echo -e "  ${GREEN}Loki${NC}           → http://localhost:3100"
echo -e "  ${GREEN}Tempo${NC}          → http://localhost:3200"
echo -e "  ${GREEN}OTel Collector${NC} → http://localhost:4317 (gRPC)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "🚀 Now run your backend locally:"
echo ""
echo "  # Set environment variables"
echo "  export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317"
echo "  export OTEL_SERVICE_NAME=cirrostrats-backend-api"
echo "  export ENV=dev"
echo ""
echo "  # Run with auto-reload (development)"
echo "  uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
echo ""
echo "  # Or with multiple workers (production-like)"
echo "  uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2"
echo ""

echo -e "${GREEN}✅ Observability stack is ready!${NC}"
echo ""
echo "To stop: docker-compose -f observability/docker-compose.observability-only.yml down"
echo ""
