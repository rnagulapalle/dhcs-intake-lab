import json
import os
import random
import time
import uuid
from faker import Faker
from kafka import KafkaProducer

fake = Faker()

BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")
TOPIC = os.getenv("TOPIC", "dhcs_crisis_intake")
RATE = float(os.getenv("RATE_PER_SEC", "5"))

COUNTIES = ["Los Angeles", "San Diego", "Orange", "Santa Clara", "Alameda", "Sacramento"]
CHANNELS = ["988_call", "mobile_team", "walk_in", "ER_referral"]
PROBLEMS = ["suicidal_thoughts", "panic_attack", "psychosis", "overdose_risk", "DV_related", "withdrawal"]
LANGS = ["en", "es", "zh", "vi", "tl"]
RISK = ["low", "moderate", "high", "imminent"]
DISP = ["phone_stabilized", "urgent_clinic", "mobile_team_dispatched", "911_transfer", "ER_referred"]

producer = KafkaProducer(
    bootstrap_servers=[BOOTSTRAP],
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    key_serializer=lambda k: k.encode("utf-8"),
    acks="all",
    linger_ms=10,
)

def make_event():
    risk = random.choices(RISK, weights=[50, 30, 15, 5])[0]
    # disposition correlated with risk (simple rules for demo)
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

        # flags (0/1)
        "suicidal_ideation": 1 if risk in ["high", "imminent"] and random.random() < 0.7 else (1 if random.random() < 0.08 else 0),
        "homicidal_ideation": 1 if random.random() < 0.02 else 0,
        "substance_use": 1 if random.random() < 0.22 else 0,
    }
    return event

def main():
    sleep_s = 1.0 / RATE if RATE > 0 else 0.2
    print(f"Producing to {TOPIC} @ {RATE}/sec -> {BOOTSTRAP}")
    while True:
        e = make_event()
        producer.send(TOPIC, key=e["county"], value=e)
        time.sleep(sleep_s)

if __name__ == "__main__":
    main()
