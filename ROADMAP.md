# DHCS Intake Lab – Roadmap & Next Steps

This document captures the next phases of work for the **DHCS Crisis Intake Realtime Analytics Lab**.
The goal is to evolve this from a working local lab into a **credible, reusable IP asset** that
demonstrates how streaming analytics + AI can improve behavioral health operations.

---

## 1. Project & Platform Improvements

These items focus on making the lab easier to run, more robust, and demo-ready.

---

### 1.1 Documentation & Developer Experience
**Goal:** Make onboarding frictionless.

- Add a comprehensive `README.md`
  - Problem statement & goals
  - High-level architecture (Kafka → Pinot)
  - Local setup instructions
  - Common troubleshooting steps
- Add a `queries/` folder with example Pinot SQL
- Document data model (schema + table config)

**Outcome:** A new engineer can run the lab and see results in <10 minutes.

---

### 1.2 Schema & Table Bootstrap Automation
**Goal:** Eliminate manual steps.

- Automatically register:
  - Pinot schema
  - Pinot realtime table
- Options:
  - Init container
  - Startup script
  - `make bootstrap`

**Outcome:** `docker compose up -d` fully initializes the system.

---

### 1.3 Data Persistence
**Goal:** Avoid losing data on restart.

- Add Docker volumes for:
  - Kafka logs
  - Pinot segments
- Ensure restarts do not wipe state

**Outcome:** Enables longer-running demos and iterative analysis.

---

### 1.4 Synthetic Data Generator Enhancements
**Goal:** Simulate realistic operational scenarios.

- Configurable ingestion rate
- Adjustable distributions:
  - Risk levels
  - Counties
  - Languages
- Spike simulation:
  - Crisis surges
  - Localized incidents

**Outcome:** Enables stress testing and “what-if” demos.

---

### 1.5 Observability & Health
**Goal:** Show operational maturity.

- Kafka consumer lag checks
- Pinot consuming segment health
- Basic metrics & health endpoints

**Outcome:** Demonstrates production awareness, not just functionality.

---

### 1.6 Demo & Release Hygiene
**Goal:** Make this sharable IP.

- Versioned releases (e.g. `v0.1-demo`)
- Clear release notes
- Stable demo queries

**Outcome:** Can be shared with stakeholders confidently.

---

## 2. DHCS IP Use-Cases & End-Goal Vision

This section defines **why this project exists** and how it maps to DHCS needs.

---

### 2.1 Core Problem Statement
DHCS and county behavioral health systems face:
- High call volumes with unpredictable surges
- Limited real-time visibility into risk escalation
- Fragmented data across channels (988, walk-ins, ER, mobile teams)
- Delayed insights that affect staffing and outcomes

This lab demonstrates how **real-time streaming analytics** can close those gaps.

---

### 2.2 Primary DHCS Use-Cases (Initial IP)

#### 2.2.1 Realtime Crisis Intake Monitoring
- Live volume by channel
- Recent intake events timeline
- County-level load visibility

**Impact:** Faster situational awareness during spikes.

---

#### 2.2.2 Risk Level Escalation Detection
- Monitor high-risk events in near-real time
- Compare risk distribution across counties
- Identify abnormal patterns

**Impact:** Earlier intervention and escalation.

---

#### 2.2.3 Staffing & Capacity Signals
- Intake volume vs wait times
- Channel mix changes (ER vs phone vs mobile)
- Sudden load imbalance detection

**Impact:** Data-driven staffing decisions.

---

#### 2.2.4 Equity & Language Access Insights
- Intake distribution by language
- County-specific language demand
- Correlate language with wait times

**Impact:** Supports equitable access to care.

---

### 2.3 Near-Term Advanced Analytics
**Goal:** Move beyond dashboards.

- Sliding-window surge detection
- Anomaly detection on intake velocity
- Leading indicators for system stress

**Impact:** Proactive vs reactive operations.

---

### 2.4 Long-Term AI / RAG Vision
**Goal:** Turn analytics into decision intelligence.

- Curated datasets for RAG pipelines
- LLM-assisted:
  - Incident summaries
  - Daily situation briefs
  - “What happened and why?” analysis
- Natural language queries over operational data

**Impact:**  
Shift from *“What is happening?”* to *“What should we do next?”*

---

### 2.5 End-State IP Positioning
This project should ultimately represent:

- A **reference architecture** for DHCS analytics
- A **safe, synthetic dataset** for demos and AI experimentation
- A **low-risk, high-visibility proof** that AI + streaming improves outcomes
- A foundation for agentic workflows in behavioral health

---

## Summary

This lab is intentionally scoped to:
- Start simple
- Be explainable
- Build trust

From there, it becomes a platform for:
- Advanced analytics
- AI-assisted operations
- Scalable DHCS modernization initiatives
