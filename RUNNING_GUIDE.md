# 🚀 Running the Backend & Observability Stack

Three ways to run your application with observability.

---

## Option 1: Everything Together (Recommended for Testing)

**Use Case:** Quick testing, CI/CD, demo

**Command:**
```bash
# Start everything (backend + observability)
docker-compose -f observability/docker-compose.full.yml up -d

# Check status
docker ps

# Stop everything
docker-compose -f observability/docker-compose.full.yml down
```

**Pros:**
- ✅ One command to start everything
- ✅ Backend runs in production-like environment
- ✅ All services networked together

**Cons:**
- ❌ Must rebuild Docker image for code changes
- ❌ Slower iteration during development

---

## Option 2: Observability Stack + Local Backend (Recommended for Development)

**Use Case:** Active development, fast iteration

### Step 1: Start Observability Stack

```bash
# Start observability services (Grafana, Prometheus, Loki, Tempo, OTel Collector)
docker-compose -f observability/docker-compose.observability-only.yml up -d

# Verify services are healthy
docker ps
```

**Services started:**
- ✅ Grafana (port 3000)
- ✅ Prometheus (port 9090)
- ✅ Loki (port 3100)
- ✅ Tempo (port 3200)
- ✅ OTel Collector (port 4317)

### Step 2: Run Backend Locally

**Option 2A: Using Uvicorn (Hot Reload)**

```bash
# Install dependencies (if not already)
pip install -r requirements.txt

# Set environment variables
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
export OTEL_SERVICE_NAME=cirrostrats-backend-api
export ENV=dev

# Run with auto-reload (detects code changes)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Pros:**
- ✅ Auto-reload on code changes (instant feedback!)
- ✅ Debug with breakpoints
- ✅ Fast iteration

**Option 2B: Using Python Directly**

```bash
# Set environment variables
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
export OTEL_SERVICE_NAME=cirrostrats-backend-api
export ENV=dev

# Run with multiple workers (production-like)
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
```

### Step 3: Verify Everything Works

```bash
# Test backend
curl http://localhost:8000/health

# Check metrics
curl http://localhost:8000/metrics | grep http_requests

# Open Grafana
open http://localhost:3000
```

### Step 4: Stop Services

```bash
# Stop backend: Ctrl+C in the terminal

# Stop observability stack
docker-compose -f observability/docker-compose.observability-only.yml down
```

---

## Option 3: Using Helper Script (Quick Start)

**Use Case:** Don't remember commands, want convenience

```bash
# Start everything with health checks and test traffic
./start-observability.sh
```

This script:
1. Starts backend + observability in Docker
2. Waits for services to be healthy
3. Generates test traffic
4. Shows access URLs

---

## Comparison Table

| Feature | Everything Together | Observability + Local Backend | Helper Script |
|---------|-------------------|------------------------------|---------------|
| **Speed** | Slow (Docker rebuild) | Fast (instant reload) | Slow (Docker rebuild) |
| **Setup** | One command | Two commands | One command |
| **Debugging** | Hard (inside container) | Easy (breakpoints) | Hard (inside container) |
| **Production-like** | Yes | No (local env) | Yes |
| **Best for** | Testing, CI/CD | Development | Quick demos |

---

## Detailed: Running Backend Locally with Observability

### Prerequisites

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Verify `.env` file exists with correct format:**
   ```bash
   cat .env
   ```

   Should look like (no spaces around `=`, no quotes):
   ```
   env=dev
   connection_string=mongodb+srv://...
   connection_string_uj=mongodb+srv://...
   ```

### Start Observability Stack

```bash
cd /path/to/cirrostrats-backend

# Start observability services only
docker-compose -f observability/docker-compose.observability-only.yml up -d

# Wait for services to be healthy (about 30 seconds)
sleep 30

# Check status
docker ps
```

**Expected output:**
```
✓ grafana (healthy)
✓ prometheus (healthy)
✓ loki (healthy)
✓ tempo (healthy)
✓ otel-collector (healthy)
✓ promtail (running)
```

### Configure Backend for Local Development

**Option A: Export environment variables**

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
export OTEL_SERVICE_NAME=cirrostrats-backend-api
export OTEL_RESOURCE_ATTRIBUTES=deployment.environment=dev,service.version=1.0.0
export ENV=dev
```

**Option B: Create a `.env.local` file**

```bash
# Create .env.local
cat > .env.local << 'EOF'
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
OTEL_SERVICE_NAME=cirrostrats-backend-api
OTEL_RESOURCE_ATTRIBUTES=deployment.environment=dev,service.version=1.0.0
ENV=dev
EOF

# Load it
source .env.local
```

### Run Backend

**Development mode (with auto-reload):**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Production-like (with multiple workers):**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
```

**Watch logs in terminal:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     OpenTelemetry tracing initialized for cirrostrats-backend-api
INFO:     Application startup complete.
```

### Test the Setup

**1. Test backend is running:**
```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy","service":"cirrostrats-backend-api"}
```

**2. Test metrics endpoint:**
```bash
curl http://localhost:8000/metrics | grep http_requests_total
# Expected: http_requests_total{handler="/health"...} 1.0
```

**3. Generate some traffic:**
```bash
for i in {1..20}; do curl -s http://localhost:8000/ > /dev/null; done
echo "Generated 20 requests"
```

**4. Open Grafana:**
```bash
open http://localhost:3000
# Login: admin / admin
```

**5. Check metrics in Grafana:**
- Explore → Prometheus
- Query: `rate(http_requests_total[1m])`
- Should see your requests!

**6. Check logs:**
- Explore → Loki
- Query: `{service="cirrostrats-backend-api"}`
- Note: If backend is local, logs might not appear in Loki (they're in your terminal)

**7. Check traces (wait 20 seconds for tail sampling):**
- Explore → Tempo
- Query: `{service.name="cirrostrats-backend-api"}`
- Should see traces with timing!

### Stop Everything

**Stop backend:**
- Press `Ctrl+C` in terminal where uvicorn is running

**Stop observability stack:**
```bash
docker-compose -f observability/docker-compose.observability-only.yml down
```

**Keep data (don't remove volumes):**
```bash
docker-compose -f observability/docker-compose.observability-only.yml down
```

**Clean slate (remove all data):**
```bash
docker-compose -f observability/docker-compose.observability-only.yml down -v
```

---

## Troubleshooting

### Backend Can't Connect to OTel Collector

**Error:** `Connection refused to localhost:4317`

**Fix:**
```bash
# Check OTel Collector is running
docker ps | grep otel-collector

# Check port is exposed
docker ps | grep 4317

# Verify environment variable
echo $OTEL_EXPORTER_OTLP_ENDPOINT
```

### Prometheus Not Scraping Local Backend

**Error:** `Get "http://host.docker.internal:8000/metrics": dial tcp: lookup host.docker.internal`

**Fix for Linux:**
```bash
# Add to docker-compose.observability-only.yml
extra_hosts:
  - "host.docker.internal:host-gateway"
```

**Fix for Docker Desktop (Mac/Windows):**
- Should work automatically
- If not, use `http://172.17.0.1:8000` (Docker bridge IP)

### Logs Not Appearing in Loki

**Why:** Promtail collects logs from Docker containers, not from local processes

**Solution:**
- View logs in your terminal (where uvicorn is running)
- Or use Docker backend: `docker-compose -f observability/docker-compose.full.yml up -d`

### Hot Reload Not Working

**Fix:**
```bash
# Make sure you're using --reload flag
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Check uvicorn is watching files
# You should see: "INFO: Will watch for changes in these directories: ['/path/to/project']"
```

---

## Quick Reference Commands

```bash
# === Observability Stack Only ===

# Start
docker-compose -f observability/docker-compose.observability-only.yml up -d

# Stop
docker-compose -f observability/docker-compose.observability-only.yml down

# View logs
docker-compose -f observability/docker-compose.observability-only.yml logs -f

# Restart specific service
docker-compose -f observability/docker-compose.observability-only.yml restart prometheus


# === Backend + Observability (All-in-One) ===

# Start
docker-compose -f observability/docker-compose.full.yml up -d

# Stop
docker-compose -f observability/docker-compose.full.yml down

# Rebuild backend
docker-compose -f observability/docker-compose.full.yml up -d --build backend


# === Local Backend ===

# Development mode (auto-reload)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Production mode (multi-worker)
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2

# With specific env vars
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317 \
ENV=dev \
uvicorn main:app --host 0.0.0.0 --port 8000 --reload


# === Helper Script ===

# Start everything with checks
./start-observability.sh
```

---

## Recommended Workflow

**For Development:**
```bash
# Terminal 1: Start observability
docker-compose -f observability/docker-compose.observability-only.yml up -d

# Terminal 2: Run backend with auto-reload
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
export ENV=dev
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Make changes to code → backend auto-reloads → test → repeat!
```

**For Testing/Demo:**
```bash
# One command
./start-observability.sh

# Or
docker-compose -f observability/docker-compose.full.yml up -d
```

---

## Next Steps

Once everything is running:

1. ✅ Open Grafana: http://localhost:3000 (admin/admin)
2. ✅ View Dashboard: Dashboards → Cirrostrats → Service Overview
3. ✅ Try queries from `OBSERVABILITY.md`
4. ✅ Make code changes and see metrics update in real-time!

For complete observability documentation, see `OBSERVABILITY.md`.
