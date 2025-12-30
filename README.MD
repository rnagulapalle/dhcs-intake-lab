# DHCS Crisis Intake Lab

**Status:** Working (local dev)  
**Scope:** Local lab to simulate DHCS crisis intake events and validate real-time ingestion + querying using Kafka + Apache Pinot.  
**Data:** Synthetic only (no PHI).

---

## 1. Objective

Provide a reproducible, dockerized lab that:
- generates synthetic crisis-intake JSON events,
- streams them to Kafka,
- ingests them into Pinot as a REALTIME table,
- validates ingestion via Pinot controller endpoints and SQL queries.

---

## 2. Non-Goals

- No production hardening (security, HA, multi-broker, TLS, auth).
- No dashboards/UI.
- No PHI ingestion.

---

## 3. Requirements

- Docker Desktop (Mac/Linux)
- Docker Compose v2
- `curl`
- `jq` (recommended)

Sanity check:
```bash
docker --version
docker compose version
curl --version
jq --version
```

---

## 4. Repo Layout (expected)

```
dhcs-intake-lab/
  docker-compose.yml
  pinot/
    schema.json
    table-realtime.json
  generator/
    Dockerfile
    producer.py
```

---

## 5. Ports

- Pinot Controller: `http://localhost:9000`
- Pinot Broker (SQL): `http://localhost:8099`
- Kafka: `localhost:29092` (host access), `kafka:9092` (container network)
- Zookeeper: `localhost:2181`

---

## 6. Setup & Run

### 6.1 Start containers
```bash
docker compose up -d
docker compose ps
```

Expected:
- `zookeeper` healthy
- `kafka` healthy
- `pinot-controller`, `pinot-broker`, `pinot-server` running
- `generator` running

---

## 7. Bootstrap Pinot (Schema + Realtime Table)

### 7.1 Register schema
```bash
docker cp pinot/schema.json pinot-controller:/tmp/schema.json
docker compose exec -T pinot-controller bash -lc   "bin/pinot-admin.sh AddSchema -schemaFile /tmp/schema.json -exec"
```

Verify:
```bash
curl -s http://localhost:9000/schemas | jq .
curl -s http://localhost:9000/schemas/dhcs_crisis_intake | jq .
```

---

### 7.2 Register realtime table
```bash
curl -s -X POST   -H "Content-Type: application/json"   --data-binary @pinot/table-realtime.json   "http://localhost:9000/tables" | jq .
```

Verify:
```bash
curl -s http://localhost:9000/tables | jq .
curl -s http://localhost:9000/tables/dhcs_crisis_intake_REALTIME | jq .
```

---

## 8. Verification (Kafka + Pinot)

### 8.1 Verify Kafka topic exists
```bash
docker compose exec -T kafka bash -lc   "kafka-topics --bootstrap-server localhost:9092 --list | grep dhcs"
```

Expected output includes:
- `dhcs_crisis_intake`

---

### 8.2 Verify Kafka messages (sample)
```bash
docker compose exec -T kafka bash -lc   "kafka-console-consumer --bootstrap-server localhost:9092    --topic dhcs_crisis_intake --from-beginning --max-messages 5"
```

Expected: JSON objects with fields like `event_id`, `event_time_ms`, `county`, `channel`, `risk_level`, etc.

---

### 8.3 Verify Pinot is consuming
```bash
curl -s "http://localhost:9000/tables/dhcs_crisis_intake_REALTIME/consumingSegmentsInfo" | jq .
```

Expected:
- `consumerState` is `CONSUMING`
- `recordsLagMap` is `0` (or near 0)

---

### 8.4 Query Pinot (SQL)

#### Count events
```bash
curl -s -X POST "http://localhost:8099/query/sql"   -H "Content-Type: application/json"   -d '{"sql":"select count(*) as c from dhcs_crisis_intake"}' | jq .
```

#### Latest events
```bash
curl -s -X POST "http://localhost:8099/query/sql"   -H "Content-Type: application/json"   -d '{"sql":"select event_id, county, channel, risk_level, event_time_ms from dhcs_crisis_intake order by event_time_ms desc limit 10"}' | jq .
```

#### Channel distribution
```bash
curl -s -X POST "http://localhost:8099/query/sql"   -H "Content-Type: application/json"   -d '{"sql":"select channel, count(*) c from dhcs_crisis_intake group by channel order by c desc"}' | jq .
```

#### Realtime window (last 5 seconds)
```bash
curl -s -X POST "http://localhost:8099/query/sql"   -H "Content-Type: application/json"   -d '{"sql":"select channel, count(*) c from dhcs_crisis_intake where event_time_ms > (now() - 5000) group by channel"}' | jq .
```

---

## 9. Stop / Cleanup

Stop:
```bash
docker compose down
```

Full cleanup (including volumes):
```bash
docker compose down -v
```

---

## 10. Troubleshooting

### 10.1 Pinot shows schema but no table
- Confirm table creation:
```bash
curl -s http://localhost:9000/tables | jq .
```
- Re-add table using `pinot/table-realtime.json`.

### 10.2 Table add fails with indexingConfig streamConfigs error
If you use `ingestionConfig.streamIngestionConfig`, do **not** also set `tableIndexConfig.streamConfigs`.

### 10.3 Kafka topic exists but Pinot count is 0
- Confirm `consumingSegmentsInfo`
- Confirm table points to correct topic (`dhcs_crisis_intake`) and broker list (`kafka:9092`)
- Confirm generator is running:
```bash
docker compose logs --tail=50 generator
```

---

## 11. Change Rate / Load

Edit `docker-compose.yml` for generator:
- `RATE_PER_SEC`
- `TOPIC`

Restart generator:
```bash
docker compose restart generator
```

---

## 12. Notes

- This lab is meant for demos, experimentation, and reproducible validation.
- Keep all datasets synthetic.
