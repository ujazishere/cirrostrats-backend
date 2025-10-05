#!/bin/bash
# Production-ready Observability Stack Startup Script
# Starts the complete observability stack with backend

set -e

echo "🚀 Starting Cirrostrats Complete Observability Stack..."
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ Error: .env file not found${NC}"
    echo "Please create a .env file with your configuration"
    echo "See README.md for required environment variables"
    exit 1
fi

# Stop any existing containers on port 8000
echo -e "${YELLOW}🛑 Stopping any existing containers on port 8000...${NC}"
docker ps -q --filter "publish=8000" | xargs -r docker stop || true

# Start the stack
echo -e "${GREEN}🐳 Starting Docker Compose stack...${NC}"
docker-compose -f observability/docker-compose.full.yml up -d --build

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

check_service "Backend API      " "http://localhost:8000/health" "8000"
check_service "Grafana          " "http://localhost:3000/api/health" "3000"
check_service "Prometheus       " "http://localhost:9090/-/healthy" "9090"
check_service "Loki             " "http://localhost:3100/ready" "3100"
check_service "Tempo            " "http://localhost:3200/ready" "3200"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Generate test traffic
echo -e "${GREEN}📈 Generating test traffic...${NC}"
for i in {1..5}; do
    curl -s http://localhost:8000/ > /dev/null
done
echo "  ✓ Sent 5 test requests"
echo ""

# Show access URLs
echo "🌐 Access Points:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "  ${GREEN}Grafana${NC}        → http://localhost:3000  (admin/admin)"
echo -e "  ${GREEN}Prometheus${NC}     → http://localhost:9090"
echo -e "  ${GREEN}Loki${NC}           → http://localhost:3100"
echo -e "  ${GREEN}Tempo${NC}          → http://localhost:3200"
echo -e "  ${GREEN}Backend API${NC}    → http://localhost:8000"
echo -e "  ${GREEN}Metrics${NC}        → http://localhost:8000/metrics"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "✨ Quick Start:"
echo "  1. Open Grafana: http://localhost:3000"
echo "  2. Login with admin/admin"
echo "  3. Go to Explore → Prometheus"
echo "  4. Query: http_requests_total"
echo ""
echo "📝 View Logs:"
echo "  Grafana → Explore → Loki"
echo "  Query: {container_name=\"cirrostrats-backend\"}"
echo ""
echo "📊 View Metrics:"
echo "  Grafana → Explore → Prometheus"
echo "  Query: rate(http_requests_total[1m])"
echo ""
echo "🔍 View Traces:"
echo "  Grafana → Explore → Tempo"
echo "  Search: service.name=\"cirrostrats-backend-api\""
echo ""

echo -e "${GREEN}✅ Observability stack is ready!${NC}"
echo ""
echo "To stop: docker-compose -f observability/docker-compose.full.yml down"
echo "To view logs: docker-compose -f observability/docker-compose.full.yml logs -f [service-name]"
