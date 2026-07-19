# 🧪 Campus Wastewater Health Alert Dashboard

**Team: Python and Proteins**

An early-warning wastewater-based epidemiology (WBE) system that monitors synthetic campus wastewater samples across two campuses, flags outbreaks and sanitation failures before they show up in clinical records, and forecasts near-term risk — built as an interactive Streamlit dashboard.

---

## 1. Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| Language | **Python 3** | Core application logic |
| App framework | **Streamlit** | Interactive web dashboard — sidebar filters, tabs, KPIs, live charts, downloads |
| Data handling | **Pandas** | Tabular data generation, filtering, aggregation, grouping |
| Numerical computation | **NumPy** | Vectorized random-number generation, statistical noise models, threshold logic |
| Visualization | **Plotly** (`graph_objects`) | Animated campus map, gauges, donut chart, line/trend charts, forecast chart |

No external database or API is used — the app is fully self-contained. Data is generated on load (and cached with `@st.cache_data`), so the dashboard runs standalone with zero setup beyond `pip install`.

---

## 2. Our Working Methodology

### 2.1 How thresholds were decided

Every marker in the system has a **Yellow (early-warning)** and **Red (critical/outbreak)** threshold. These were not guessed — they were set by cross-referencing two categories of sources:

- **CPCB (Central Pollution Control Board) water quality and effluent standards** — used to ground the physico-chemical markers (pH acceptable range, turbidity limits) in real regulatory limits rather than arbitrary numbers.
- **Published wastewater-based epidemiology (WBE) methods papers** — used to set the pathogen/viral thresholds (E. coli, Salmonella, SARS-CoV-2, Influenza A, Norovirus, antibiotic residues), based on reported baseline ranges and outbreak-associated concentration levels from real-world wastewater surveillance literature (e.g. WHO/CDC-style wastewater surveillance guidance).

Viral markers (SARS-CoV-2, Influenza A, Norovirus) are additionally **flow-normalized** (`marker × 100 / Flow_Rate_kL`) before being compared to a threshold — this corrects for dilution, so a heavily-flushed or rain-diluted sample isn't mistaken for a real drop in viral load, and a low-flow sample isn't mistaken for a spike.

Where a threshold hasn't been established yet (e.g. Campylobacter currently has no Yellow/Red cutoff), this is stated explicitly in the app rather than a number being invented — the dashboard is upfront about what is and isn't scientifically grounded yet.

### 2.2 How the synthetic dataset is generated

Since no real campus sampling data exists yet, the credibility of the system rests on how realistically the synthetic data behaves. The generator (`data_generator.py`) builds one row per (site × day) — **35 sampling sites × 92 days (1 Aug – 31 Oct 2026)** — using a layered model:

1. **Occupancy model.** Each site's baseline output is scaled by how full the building is: Academic blocks drop to **0.2×** on weekends (empty classrooms), residential/mess blocks rise to **1.3×** (students around more), weekdays are baseline **1.0×**.
2. **Seasonal drift.** A slow sinusoidal wave (~±8%, 30-day cycle) is layered on top of occupancy, so the baseline isn't perfectly flat — it drifts gradually the way real environmental/institutional patterns do.
3. **Weather simulation.** Each day is randomly assigned a weather state — Sunny (60%), Cloudy (30%), or Rain (10%). Rain days realistically **increase flow rate (×1.5)** and **turbidity (×1.8)** (stormwater dilution and runoff) while **diluting viral concentration (×0.85)** — modeling the real effect that rain has on sewer systems.
4. **Per-marker random generation.** Every marker (Flow Rate, SARS-CoV-2, Influenza A, Norovirus, E. coli, Salmonella, Campylobacter, pH, Turbidity, Antibiotic Residues) is drawn as `max(floor, baseline × multiplier + Gaussian noise)` using a **seeded NumPy random generator (seed = 42)**, so the dataset is reproducible run after run.
5. **Cross-marker correlation.** Rather than generating every marker fully independently, related markers are partially derived from each other — Salmonella carries a fraction of E. coli's signal, Campylobacter carries a fraction of Salmonella's, antibiotic residues rise with reported clinical cases, and clinical cases rise with Norovirus. This mimics the real co-occurrence you'd expect between related biological signals instead of treating every column as statistically independent noise.
6. **Measurement noise.** A final multiplicative noise layer (±3%, uniform) is applied across all markers to simulate sensor/lab measurement variability on top of the underlying biological signal.
7. **Missing data simulation.** ~1.5% of marker readings are randomly set to missing, simulating real-world sensor dropouts/failed samples — which is also why the dashboard reports a per-row **Confidence Score** (% of markers present for that reading).

### 2.3 How outbreaks were induced in the synthetic data

Rather than a flat baseline with no story, **four synthetic events** are deliberately injected into the dataset so the dashboard has real signals to catch. Two are modeled as genuine epidemic curves, two are modeled as acute contamination incidents:

**Epidemic 1 — Norovirus outbreak at Beas Kund (Boys Hostel, North Campus)**
Modeled as a **Gaussian ("bell-shaped") curve** — a realistic rise, peak (around day 70), and decline — rather than an instant spike, because real fecal shedding during an outbreak ramps up and fades gradually. Reported clinical cases and antibiotic residues follow their own bell curves, staggered a few days *after* the wastewater signal — deliberately reproducing the real-world lag between a wastewater signal and clinical case reporting, which is the core justification for why WBE is useful as an early-warning tool. The outbreak also **spreads to neighboring hostels** (Dashir, Suvalsar, Surajtaal) at ~30% of the peak intensity, simulating realistic cross-contamination / shared social contact between nearby residences rather than treating each hostel as a sealed bubble.

**Epidemic 2 — Influenza outbreak at Chandrataal (Girls Hostel, South Campus)**
Same bell-curve modeling approach, peaking around day 80, with clinical cases lagging behind the wastewater signal, and partial spread to the neighboring hostel Renuka (~30% of peak intensity).

**Acute incident 3 — Contamination spike at Cedar Mess (South Campus)**
A short, sharp **3-day event** (days 20–22) rather than a gradual curve — representing a plumbing/sewage-line failure. E. coli, Salmonella, Campylobacter, and turbidity all spike together and clear within days, testing whether the system correctly flags and then de-escalates a fast-moving contamination event.

**Acute incident 4 — Chemical spill at A1 (Academic block, South Campus)**
A **single-day pH crash** (pH 4.8) with a turbidity spike, simulating a chemical spill or sanitation failure rather than a biological event — testing the physico-chemical alert pathway independently of pathogen markers.

### 2.4 Alert logic

Every reading is classified **Green / Yellow / Red**:
- **Red** is checked first — any marker crossing its critical threshold (or pH outside the 5.5–9.0 band) immediately marks the site Red.
- **Yellow** is only checked if the site isn't already Red — any marker crossing its early-warning threshold marks it Yellow.
- Otherwise the site is **Green**.

On top of the raw alert level, each row also gets:
- **Health Score (0–100):** starts at 100, −40 for Red, −15 for Yellow, with an extra −5 penalty if turbidity is elevated — giving a single continuous risk number instead of just three buckets.
- **Reason:** an auto-generated, human-readable list of exactly which marker(s) triggered the alert (e.g. "Norovirus + E. coli").
- **Recommendation:** an auto-generated suggested action tied to the alert level.
- **Risk Trend:** compares each site's Health Score to its previous day (↑ Rising Health / ↓ Falling Health / → Stable), so a site can be flagged as *worsening* even before it crosses into the next alert color.
- **Confidence Score:** the % of markers actually present (not missing) for that reading, so users can tell a strong signal from a sparse one.

---

## 3. Dashboard Features

### 🤖 Daily AI Analytics & Summary (top of page)
A snapshot of the most recent day at a glance: an **Alert Distribution donut chart**, an **Average Health Score gauge**, a **Critical Sites Load gauge** (% of sites currently Red), and a **Highest-Risk Site card** showing the single worst-scoring site and why.

### 🗺️ Animated Campus Map
A schematic (not geographic) layout of all 35 sites, grouped by campus (North/South) and category (Academic, Mess, Boys Hostel, Girls Hostel), color-coded Green/Yellow/Red. Includes a **Play/Pause animation and date slider**, so you can watch alert levels evolve day-by-day across the full 92-day period — including watching an outbreak visibly spread from one hostel to its neighbors.

### 📈 Trend Explorer & History
Pick any site and any combination of markers to compare on one time-series chart, with the injected outbreak/incident windows shaded directly on the chart for context.

### 🚨 Alert Log
Live-filtered tables of all current Red and Yellow readings, each with its Health Score, auto-generated Reason, Recommendation, and Confidence Score — not just a raw threshold breach list.

### 🔮 7-Day Forecast
Projects each site's Norovirus signal 7 days forward using a simple recent-trend extrapolation (comparing the last reading to 7 days prior and projecting that slope forward), and converts the projected endpoint into an estimated **outbreak probability (%)**. Shown alongside the historical line so the forecast's basis is transparent rather than a black box.

### 📋 Response Plan
A full **Green / Yellow / Red response matrix** — each level has its own Immediate Action checklist and Communication Protocol (e.g. Red triggers mandatory re-sampling, neighboring-building sampling, and escalation to public health authorities). Includes a 3-step **Escalation Workflow**: Signal Detection → Verification → Intervention.

### 🔒 Privacy & Ethics
A dedicated tab covering anonymity model, consent framing for passive population-level surveillance, purpose limitation, data governance, group-harm/stigma mitigation, false-positive handling, equity, proportionate response, oversight/accountability, and alignment with India's Digital Personal Data Protection Act, 2023.

### 📁 Data & Download
Full filtered dataset viewer plus one-click downloads: filtered CSV, full synthetic dataset CSV, and a plain-text daily summary report.

---

## 4. Project Structure

```
├── app.py                 # Streamlit dashboard (UI, tabs, charts, filters)
├── data_generator.py      # Synthetic data generator, thresholds, outbreak events, map layout
└── README.md              # This file
```

## 5. Running the App

```bash
streamlit run app.py
```
