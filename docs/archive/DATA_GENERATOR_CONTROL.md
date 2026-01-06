# DHCS Data Generator - On-Demand Control

## Overview

The data generator has been converted from **continuous 24/7 generation** to **on-demand generation via API**.

### Previous Setup (STOPPED)
- ❌ Continuous generator running 24/7
- Generated 5 events/second = 432,000 events/day
- No control, always running

### New Setup (ACTIVE)
- ✅ On-Demand API for controlled data generation
- Generate data only when needed
- Full control over duration and rate

## Architecture

```
┌─────────────────┐
│   Generator API │  (Port 8001)
│   (FastAPI)     │
└────────┬────────┘
         │
         ↓ (produces events)
    ┌─────────┐
    │  Kafka  │  (Port 9092)
    └────┬────┘
         │
         ↓ (streams)
    ┌─────────┐
    │  Pinot  │  (Real-time analytics)
    └────┬────┘
         │
         ↓ (queries)
  ┌──────────────┐
  │  Agent API   │  (Port 8000)
  └──────────────┘
```

## API Endpoints

### Base URL
- **Local**: http://localhost:8001
- **API Docs**: http://localhost:8001/docs

### Endpoints

#### 1. Get Status
```bash
curl http://localhost:8001/status
```

Response:
```json
{
  "is_running": false,
  "start_time": null,
  "end_time": null,
  "events_generated": 0,
  "time_remaining_seconds": 0
}
```

#### 2. Start Generation
```bash
curl -X POST http://localhost:8001/generate \
  -H 'Content-Type: application/json' \
  -d '{
    "duration_minutes": 5,
    "rate_per_second": 5
  }'
```

Parameters:
- `duration_minutes`: How long to generate (0-60 minutes)
- `rate_per_second`: Events per second (0-100)

Response:
```json
{
  "status": "started",
  "duration_minutes": 5.0,
  "rate_per_second": 5.0,
  "estimated_events": 1500,
  "end_time": "2026-01-05T23:15:00.000000"
}
```

#### 3. Stop Generation
```bash
curl -X POST http://localhost:8001/stop
```

Response:
```json
{
  "status": "stopping",
  "events_generated": 342
}
```

## Common Usage Patterns

### Quick Test (1 minute, 10 events/sec)
```bash
curl -X POST http://localhost:8001/generate \
  -H 'Content-Type: application/json' \
  -d '{"duration_minutes": 1, "rate_per_second": 10}'
```
Generates: ~600 events

### Demo Session (5 minutes, 5 events/sec)
```bash
curl -X POST http://localhost:8001/generate \
  -H 'Content-Type: application/json' \
  -d '{"duration_minutes": 5, "rate_per_second": 5}'
```
Generates: ~1,500 events

### Load Test (30 minutes, 20 events/sec)
```bash
curl -X POST http://localhost:8001/generate \
  -H 'Content-Type: application/json' \
  -d '{"duration_minutes": 30, "rate_per_second": 20}'
```
Generates: ~36,000 events

### Production Simulation (60 minutes, 50 events/sec)
```bash
curl -X POST http://localhost:8001/generate \
  -H 'Content-Type: application/json' \
  -d '{"duration_minutes": 60, "rate_per_second": 50}'
```
Generates: ~180,000 events

## Event Data Structure

Each generated event includes:
```json
{
  "event_id": "uuid",
  "event_time_ms": 1735790400000,
  "channel": "988_call | mobile_team | walk_in | ER_referral",
  "county": "Los Angeles | San Diego | Orange | Santa Clara | Alameda | Sacramento",
  "presenting_problem": "suicidal_thoughts | panic_attack | psychosis | overdose_risk | DV_related | withdrawal",
  "risk_level": "low | moderate | high | imminent",
  "disposition": "phone_stabilized | urgent_clinic | mobile_team_dispatched | 911_transfer | ER_referred",
  "language": "en | es | zh | vi | tl",
  "age": 13-85,
  "wait_time_sec": 0-300,
  "call_duration_sec": 30-1200,
  "prior_contacts_90d": 0-5,
  "suicidal_ideation": 0 | 1,
  "homicidal_ideation": 0 | 1,
  "substance_use": 0 | 1
}
```

## Management

### Start the Generator API
```bash
cd /Users/raj/dhcs-intake-lab

docker run -d \
  --name generator-api \
  --network dhcs-intake-lab_default \
  -p 8001:8001 \
  -e KAFKA_BOOTSTRAP="kafka:9092" \
  -e TOPIC="dhcs_crisis_intake" \
  dhcs-generator-api:latest
```

### Stop the Generator API
```bash
docker stop generator-api
docker rm generator-api
```

### View Logs
```bash
docker logs -f generator-api
```

### Rebuild After Code Changes
```bash
cd /Users/raj/dhcs-intake-lab
docker build -f generator/Dockerfile.api -t dhcs-generator-api:latest .
docker stop generator-api && docker rm generator-api
# Then run the start command above
```

## Benefits of On-Demand Generation

1. **Cost Savings**: Only generate data when needed
2. **Resource Efficiency**: No unnecessary CPU/memory usage
3. **Controlled Testing**: Generate exact amounts for specific scenarios
4. **Flexible Demo**: Start/stop as needed during demonstrations
5. **Data Management**: Easier to manage data volumes in Pinot

## Integration with Dashboard

The dashboard will work with whatever data is in Pinot. To refresh data:
1. Generate fresh data using the API
2. Wait a few seconds for Kafka→Pinot ingestion
3. Refresh the dashboard to see new data

## Notes

- Generator API runs in background thread (non-blocking)
- Multiple concurrent generation requests are prevented
- Auto-stops after duration expires
- Can be manually stopped anytime
- Events are immediately streamed to Kafka
- Pinot ingests from Kafka in real-time (~2-5 second lag)
