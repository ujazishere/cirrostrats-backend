# 📊 Enhanced Grafana Dashboard Guide

## 🎯 Quick Access

**Enhanced Dashboard:** http://localhost:3000/d/cirrostrats-enhanced

## ✨ New Features

### 1. **Interactive Filters (Top of Dashboard)**

#### Endpoint Filter
- **What it does:** Filter all panels by specific endpoints
- **How to use:**
  - Click the "Endpoint" dropdown at the top
  - Select specific endpoints or "All"
  - All charts update automatically

#### Status Code Filter
- **What it does:** Filter by HTTP status codes (200, 404, 500, etc.)
- **How to use:**
  - Click the "Status Code" dropdown
  - Select specific codes or "All"
  - See only requests with those status codes

### 2. **Click-to-Drill-Down (The Magic Feature!)**

#### From Metrics → Logs

**Click anywhere on these panels to view related logs:**

1. **Request Rate Chart** → View logs for that endpoint
2. **Total Requests Bar Chart** → View all logs for clicked endpoint
3. **Error Rate Chart** → View error logs only
4. **Status Code Pie Chart** → View logs with that status code
5. **Slowest Endpoints Table** → View slow request logs
6. **Request Volume Table** → View all logs for endpoint

**How it works:**
- Click on any data point, bar, or row
- Opens Loki (log viewer) filtered to that specific endpoint/status
- Automatically sets the time range

#### From Logs → Traces

**Click on trace_id in logs to see the full trace:**

1. In the "Recent Logs" panel, you'll see JSON logs
2. Each log has a `trace_id` field
3. **Click on the trace_id value** → Opens Tempo with the full distributed trace
4. See the complete request flow with timing breakdown

#### Example Workflow

```
User clicks on "/search" endpoint in bar chart
  ↓
Grafana opens Loki with logs filtered to /search
  ↓
User sees a slow request (300ms)
  ↓
User clicks on the trace_id in that log
  ↓
Tempo opens showing the full trace:
  - MongoDB query: 280ms (the bottleneck!)
  - JSON parsing: 15ms
  - Response: 5ms
  ↓
Root cause identified!
```

## 📈 Panel Descriptions

### Quick Stats (Top Row)
- **Request Rate:** Requests per second across all endpoints
- **Error Rate:** Percentage of 5xx errors
- **p95 Latency:** 95th percentile response time
- **Endpoints:** Total number of active endpoints

### Request Rate by Endpoint
- **Shows:** Real-time request rate per endpoint
- **Click action:** View logs for that endpoint
- **Best for:** Monitoring traffic patterns

### Latency by Endpoint (p50/p95/p99)
- **Shows:** Response time percentiles for each endpoint
- **p50:** Median latency
- **p95:** 95% of requests are faster than this
- **p99:** 99% of requests are faster than this
- **Click action:** View slow request logs
- **Best for:** Finding performance issues

### Total Requests by Endpoint
- **Shows:** Total request count in the last hour
- **Click action:** Opens Loki with all logs for that endpoint
- **Best for:** Understanding endpoint usage

### Error Rate by Endpoint
- **Shows:** Percentage of errors per endpoint
- **Color coding:**
  - Green: < 1% errors
  - Yellow: 1-5% errors
  - Red: > 5% errors
- **Click action:** View error logs only
- **Best for:** Identifying problematic endpoints

### Status Code Distribution
- **Shows:** Breakdown of HTTP status codes
- **Click action:** View logs with that status code
- **Best for:** Understanding response patterns

### Slowest Endpoints
- **Shows:** Top 10 endpoints by p95 latency
- **Gradient bar:** Visual indicator of slowness
- **Click action:** View slow requests (>100ms)
- **Best for:** Performance optimization

### Request Volume Timeline
- **Shows:** Total requests per endpoint
- **Sorted:** Highest to lowest
- **Click action:** View all logs for endpoint
- **Best for:** Capacity planning

### Recent Logs
- **Shows:** Live log stream filtered by your selections
- **Features:**
  - JSON formatted
  - Shows all important fields (method, path, status, latency)
  - Automatically updates every 10s
- **Click action:** Click trace_id to view full trace
- **Best for:** Real-time debugging

### Error Trend
- **Shows:** 4xx and 5xx errors over time
- **Bar chart:** Easy to spot error spikes
- **Best for:** Incident detection

### Top 10 Trace IDs
- **Shows:** Most active traces in the last hour
- **Click action:** Opens Tempo with full trace visualization
- **Best for:** Deep-dive performance analysis

## 🎓 How to Use It

### Scenario 1: "Why is /search slow?"

1. Click on the "Endpoint" filter → Select "/search"
2. Look at "Latency by Endpoint" panel → See p95 is 300ms
3. Click on the "/search" line in the chart
4. Loki opens with filtered logs showing slow requests
5. Click on a trace_id from a 300ms request
6. Tempo shows: MongoDB query took 280ms
7. **Action:** Add database index!

### Scenario 2: "Are we getting errors?"

1. Look at "Quick Stats" → Error Rate shows 2.5%
2. Check "Error Rate by Endpoint" → /api/flights has 5% errors
3. Click on "/api/flights" bar
4. Loki shows error logs with stack traces
5. See error: "MongoDB connection timeout"
6. **Action:** Increase connection pool size

### Scenario 3: "Which endpoints are most used?"

1. Look at "Total Requests by Endpoint"
2. See visual ranking of all endpoints
3. Click on top endpoint to see its logs
4. Check "Request Volume Timeline" table for exact numbers
5. **Action:** Optimize hot paths

### Scenario 4: "Trace a specific request"

1. User reports issue at 14:30
2. Go to "Recent Logs" panel
3. Adjust time range to 14:25 - 14:35
4. Find the user's request by IP or endpoint
5. Click on trace_id
6. See complete request flow in Tempo
7. **Action:** Fix the identified bottleneck

## 💡 Pro Tips

### 1. Use Time Range Picker
- Top right corner: "Last 1 hour", "Last 6 hours", etc.
- Click to change the time window for all panels

### 2. Combine Filters
- Select specific endpoint: `/search`
- Select status code: `500`
- See only errors for that endpoint!

### 3. Refresh Rate
- Dashboard auto-refreshes every 10s
- Change in top right corner if needed

### 4. Save Views
- After filtering, click "Share" → Copy shortened URL
- Share with your team for specific issues

### 5. Create Alerts
- Right-click any panel → "More" → "Create alert rule"
- Get notified when metrics cross thresholds

## 🔗 Data Links Reference

All panels have clickable data links:

| Panel | Click Target | Opens |
|-------|-------------|-------|
| Request Rate | Any line | Logs for that endpoint |
| Latency | Any line | Slow request logs |
| Total Requests | Any bar | All logs for endpoint |
| Error Rate | Any bar | Error logs only |
| Status Codes | Any slice | Logs with that status |
| Slowest Endpoints | Any row | Slow requests (>100ms) |
| Request Volume | Any row | All logs |
| Recent Logs | trace_id | Full trace in Tempo |
| Top Trace IDs | Trace ID | Trace visualization |

## 🎨 Color Coding

### Latency (Response Time)
- **Green:** < 200ms (Good)
- **Yellow:** 200-500ms (Monitor)
- **Red:** > 500ms (Action needed)

### Error Rate
- **Green:** < 1% (Healthy)
- **Yellow:** 1-5% (Warning)
- **Orange:** 5-10% (Critical)
- **Red:** > 10% (Emergency)

## 🚀 Quick Start Checklist

- [ ] Open dashboard: http://localhost:3000/d/cirrostrats-enhanced
- [ ] Try filtering by endpoint
- [ ] Click on a bar chart → See logs open
- [ ] Find a log with trace_id
- [ ] Click trace_id → See full trace in Tempo
- [ ] Try changing time range
- [ ] Combine endpoint + status code filters

## 📚 Related Docs

- **Query Guide:** See `/Users/harshv/Projects/base/OBSERVABILITY-GUIDE.md`
- **Running Guide:** See `/Users/harshv/Projects/base/OBSERVABILITY-GUIDE.md`
- **Troubleshooting:** See observability guide

## 🎯 Comparison: Old vs New Dashboard

### Old Dashboard
- Shows only 3 panels
- No filtering
- No drill-down
- Only rate metrics (shows 0 for low traffic)

### New Enhanced Dashboard
- **14 interactive panels**
- **Endpoint + Status Code filters**
- **Click-to-drill-down everywhere**
- **Metrics → Logs → Traces correlation**
- **Total counts + rates**
- **Tables with detailed breakdown**
- **Color-coded thresholds**
- **Auto-refresh every 10s**

## 🎉 You're All Set!

Open the dashboard and start exploring:
**http://localhost:3000/d/cirrostrats-enhanced**

Happy debugging! 🐛🔍
