"""
On-demand data generator API
Run data generation for a specified duration via HTTP endpoint
"""
import json
import os
import random
import time
import uuid
from datetime import datetime, timedelta
from threading import Thread, Event
from faker import Faker
from kafka import KafkaProducer
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

fake = Faker()
app = FastAPI(title="DHCS Data Generator API")

# Configuration
BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")
TOPIC = os.getenv("TOPIC", "dhcs_crisis_intake")
DEFAULT_RATE = float(os.getenv("RATE_PER_SEC", "5"))

# Generator state
generator_state = {
    "is_running": False,
    "start_time": None,
    "end_time": None,
    "events_generated": 0,
    "stop_event": Event()
}

# Data templates
COUNTIES = ["Los Angeles", "San Diego", "Orange", "Santa Clara", "Alameda", "Sacramento"]
CHANNELS = ["988_call", "mobile_team", "walk_in", "ER_referral"]
PROBLEMS = ["suicidal_thoughts", "panic_attack", "psychosis", "overdose_risk", "DV_related", "withdrawal"]
LANGS = ["en", "es", "zh", "vi", "tl"]
RISK = ["low", "moderate", "high", "imminent"]
DISP = ["phone_stabilized", "urgent_clinic", "mobile_team_dispatched", "911_transfer", "ER_referred"]

producer = None

def get_producer():
    """Lazy initialize Kafka producer"""
    global producer
    if producer is None:
        producer = KafkaProducer(
            bootstrap_servers=[BOOTSTRAP],
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8"),
            acks="all",
            linger_ms=10,
        )
    return producer

def make_event():
    """Generate a synthetic crisis intake event"""
    risk = random.choices(RISK, weights=[50, 30, 15, 5])[0]

    if risk == "imminent":
        disp = random.choice(["911_transfer", "mobile_team_dispatched"])
    elif risk == "high":
        disp = random.choice(["mobile_team_dispatched", "ER_referred", "urgent_clinic"])
    elif risk == "moderate":
        disp = random.choice(["urgent_clinic", "phone_stabilized"])
    else:
        disp = random.choice(["phone_stabilized", "urgent_clinic"])

    event = {
        "event_id": str(uuid.uuid4()),
        "event_time_ms": int(time.time() * 1000),
        "channel": random.choice(CHANNELS),
        "county": random.choice(COUNTIES),
        "presenting_problem": random.choice(PROBLEMS),
        "risk_level": risk,
        "disposition": disp,
        "language": random.choice(LANGS),
        "age": random.randint(13, 85),
        "wait_time_sec": max(0, int(random.gauss(120, 60))),
        "call_duration_sec": max(30, int(random.gauss(600, 180))),
        "prior_contacts_90d": max(0, int(random.gauss(1.2, 1.5))),
        "suicidal_ideation": 1 if risk in ["high", "imminent"] and random.random() < 0.7 else (1 if random.random() < 0.08 else 0),
        "homicidal_ideation": 1 if random.random() < 0.02 else 0,
        "substance_use": 1 if random.random() < 0.22 else 0,
    }
    return event

def run_generator(duration_seconds: int, rate_per_sec: float):
    """Run generator for a specified duration"""
    prod = get_producer()
    sleep_interval = 1.0 / rate_per_sec if rate_per_sec > 0 else 0.2

    generator_state["is_running"] = True
    generator_state["start_time"] = datetime.now()
    generator_state["end_time"] = datetime.now() + timedelta(seconds=duration_seconds)
    generator_state["events_generated"] = 0
    generator_state["stop_event"].clear()

    print(f"Starting generator: {duration_seconds}s @ {rate_per_sec}/sec")

    start = time.time()
    while (time.time() - start) < duration_seconds:
        if generator_state["stop_event"].is_set():
            break

        event = make_event()
        prod.send(TOPIC, key=event["county"], value=event)
        generator_state["events_generated"] += 1
        time.sleep(sleep_interval)

    generator_state["is_running"] = False
    print(f"Generator stopped. Generated {generator_state['events_generated']} events")


class GenerateRequest(BaseModel):
    duration_minutes: float = 5.0
    rate_per_second: float = 5.0


@app.get("/")
async def root():
    """API info"""
    return {
        "service": "DHCS Data Generator API",
        "status": "running",
        "endpoints": {
            "POST /generate": "Start generating data for specified duration",
            "POST /stop": "Stop current generation",
            "GET /status": "Get generator status"
        }
    }


@app.get("/status")
async def get_status():
    """Get current generator status"""
    return {
        "is_running": generator_state["is_running"],
        "start_time": generator_state["start_time"].isoformat() if generator_state["start_time"] else None,
        "end_time": generator_state["end_time"].isoformat() if generator_state["end_time"] else None,
        "events_generated": generator_state["events_generated"],
        "time_remaining_seconds": (generator_state["end_time"] - datetime.now()).total_seconds()
            if generator_state["end_time"] and generator_state["is_running"] else 0
    }


@app.post("/generate")
async def start_generation(request: GenerateRequest):
    """
    Start generating synthetic crisis intake data

    Example:
        POST /generate
        {
            "duration_minutes": 5.0,
            "rate_per_second": 5.0
        }

    This will generate data for 5 minutes at 5 events/second = 1,500 events
    """
    if generator_state["is_running"]:
        raise HTTPException(status_code=400, detail="Generator is already running. Stop it first.")

    if request.duration_minutes <= 0 or request.duration_minutes > 60:
        raise HTTPException(status_code=400, detail="Duration must be between 0 and 60 minutes")

    if request.rate_per_second <= 0 or request.rate_per_second > 100:
        raise HTTPException(status_code=400, detail="Rate must be between 0 and 100 events/second")

    duration_seconds = int(request.duration_minutes * 60)
    total_events = int(duration_seconds * request.rate_per_second)

    # Run generator in background thread
    thread = Thread(target=run_generator, args=(duration_seconds, request.rate_per_second), daemon=True)
    thread.start()

    return {
        "status": "started",
        "duration_minutes": request.duration_minutes,
        "rate_per_second": request.rate_per_second,
        "estimated_events": total_events,
        "end_time": (datetime.now() + timedelta(seconds=duration_seconds)).isoformat()
    }


@app.post("/stop")
async def stop_generation():
    """Stop the current data generation"""
    if not generator_state["is_running"]:
        raise HTTPException(status_code=400, detail="Generator is not running")

    generator_state["stop_event"].set()

    return {
        "status": "stopping",
        "events_generated": generator_state["events_generated"]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
