# NYC Taxi Analytics Dashboard

A full-stack analytics dashboard for **NYC TLC (Taxi & Limousine Commission)** trip data. Built with **Django** (backend API), **React** (frontend), and **Docker** for containerized deployment.

---

## Features

### Data Ingestion
- Upload **CSV** or **Parquet** files (Yellow and Green taxi schemas)
- Automatic schema detection (tpep_* for Yellow, lpep_* for Green)
- Supports datetime in **epoch milliseconds**, epoch seconds, or ISO string

### Filters
- **Cab type tabs**: View **Yellow** or **Green** taxis separately (no combined view)

### Summary Metrics
- Total trips, average fare, average distance, busiest hour

### Visualizations
| Chart | Description |
|-------|-------------|
| **Trips Over Time** | Line chart – daily trip counts |
| **Trips by Hour** | Bar chart – hourly distribution (0–23) |
| **Trips by Day of Week** | Bar chart – Mon–Sun distribution |
| **Trips by Payment Type** | Bar chart – Credit card, Cash, etc. |
| **Pickup Heatmap** | Map – raw pickup density by zone (top 80 per cab type) |
| **Demand Clusters** | Map – geographic clusters of demand zones (DBSCAN) |
| **Demand Prediction** | Line chart – forecast for next 7 days |
| **Fare Prediction** | Bar/scatter – actual vs predicted fare by distance (ordered) |

### ML Models
- **Demand prediction**: Ridge regression + PolynomialFeatures (degree=2) + StandardScaler
- **Fare prediction**: Ridge regression + PolynomialFeatures (degree=2) + StandardScaler
- **Zone clustering**: **DBSCAN** (density-based, finds geographic demand clusters)

---

## ML Models – Technical Documentation

### 1. Demand Prediction (Next 7 Days)

| Parameter | Value |
|-----------|-------|
| **Model** | Pipeline: PolynomialFeatures → StandardScaler → Ridge |
| **Task** | Regression – predict daily trip count |
| **Training data** | Last **31 days** of daily aggregated trips (min 7 days required) |
| **Features** | `weekday` (0–6), `day` (1–31), `month` (1–12) |
| **Target** | Daily trip count |

**Hyperparameters:**
| Hyperparameter | Value |
|----------------|-------|
| `PolynomialFeatures.degree` | 2 |
| `PolynomialFeatures.include_bias` | False |
| `Ridge.alpha` | 1.0 |
| `random_state` | 42 |

**Output:** 7-day forecast appended to last 14 days of actuals.

---

### 2. Fare Prediction (Actual vs Predicted)

| Parameter | Value |
|-----------|-------|
| **Model** | Pipeline: PolynomialFeatures → StandardScaler → Ridge |
| **Task** | Regression – predict fare from trip features |
| **Training data** | Up to **1500 samples** ordered by pickup_datetime; max 2000 trips total |
| **Features** | `trip_distance` (miles), `pickup_hour` (0–23, NYC local time) |
| **Target** | `fare_amount` (USD) |
| **Filters** | `trip_distance > 0`, `0 ≤ fare_amount < 500` |

**Hyperparameters:**
| Hyperparameter | Value |
|----------------|-------|
| `PolynomialFeatures.degree` | 2 |
| `PolynomialFeatures.include_bias` | False |
| `Ridge.alpha` | 0.5 |
| `random_state` | 42 |

**Output:** First 50 trips **ordered by trip_distance** with actual vs predicted fare.

---

### 3. Pickup Heatmap

| Parameter | Value |
|-----------|-------|
| **Type** | Raw aggregation (no ML) |
| **Data** | Pickup counts per zone |
| **Zones** | Top **80** per cab type (yellow, green) when comparative; top **100** when single |
| **Visualization** | Markers on OpenStreetMap; size ∝ count |

**Heatmap vs Demand Clusters:** Heatmap shows raw pickup density. Clusters apply DBSCAN to group zones geographically.

---

### 4. Demand Clusters (DBSCAN)

| Parameter | Value |
|-----------|-------|
| **Model** | DBSCAN (scikit-learn) |
| **Task** | Unsupervised clustering – group zones by geographic proximity |
| **Data** | Top **150** zones by pickup count |
| **Input** | `(lat, lon)` per zone |
| **Metric** | Euclidean |

**DBSCAN hyperparameters:**
| Hyperparameter | Value |
|----------------|-------|
| `eps` | 0.025 (degrees ~2.8 km in NYC) |
| `min_samples` | 4 |
| `metric` | `euclidean` |

**Output:** Zone markers colored by cluster ID; -1 = noise.

---

### Timezone Handling

All temporal aggregations (hour, weekday) use **America/New_York** via `zoneinfo.ZoneInfo('America/New_York')` for correct local-time display.

---

## Dataset

**NYC TLC Trip Record Data** – [nyc.gov TLC](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page)

### Yellow Taxis
Street-hail trips (Manhattan and airports).

| Field | Type | Description |
|-------|------|-------------|
| `VendorID` | int | Vendor code |
| `tpep_pickup_datetime` | datetime/epoch ms | Pickup time |
| `tpep_dropoff_datetime` | datetime/epoch ms | Dropoff time |
| `passenger_count` | float | Passengers |
| `trip_distance` | float | Miles |
| `RatecodeID` | float | Rate code |
| `PULocationID` | int | Pickup zone ID |
| `DOLocationID` | int | Dropoff zone ID |
| `payment_type` | int | 1=CC, 2=Cash, 3=No charge, etc. |
| `fare_amount` | float | Base fare |
| `extra` | float | Surcharges |
| `mta_tax` | float | MTA tax |
| `tip_amount` | float | Tip |
| `tolls_amount` | float | Tolls |
| `improvement_surcharge` | float | Surcharge |
| `total_amount` | float | Total charged |
| `congestion_surcharge` | float | Congestion fee |
| `Airport_fee` | float | Airport fee |
| `cbd_congestion_fee` | float | CBD congestion fee |

### Green Taxis
Borough taxis (outer boroughs).

| Field | Type | Description |
|-------|------|-------------|
| `VendorID` | int | Vendor code |
| `lpep_pickup_datetime` | datetime/epoch ms | Pickup time |
| `lpep_dropoff_datetime` | datetime/epoch ms | Dropoff time |
| `store_and_fwd_flag` | str | Stored/forwarded |
| `RatecodeID` | float | Rate code |
| `PULocationID` | int | Pickup zone ID |
| `DOLocationID` | int | Dropoff zone ID |
| `passenger_count` | float | Passengers |
| `trip_distance` | float | Miles |
| `fare_amount` | float | Base fare |
| `extra` | float | Surcharges |
| `mta_tax` | float | MTA tax |
| `tip_amount` | float | Tip |
| `tolls_amount` | float | Tolls |
| `improvement_surcharge` | float | Surcharge |
| `total_amount` | float | Total charged |
| `payment_type` | float | 1=CC, 2=Cash, etc. |
| `trip_type` | float | Street-hail vs dispatch |
| `congestion_surcharge` | float | Congestion fee |
| `cbd_congestion_fee` | float | CBD congestion fee |
| `ehail_fee` | float | e-hail fee (nullable) |

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Django 4, SQLite, Gunicorn |
| Frontend | React 18, Vite, Plotly.js |
| Charts | Plotly (react-plotly.js), OpenStreetMap |
| ML | scikit-learn (Ridge, PolynomialFeatures, DBSCAN) |
| Deployment | Docker, Docker Compose |

---

## Quick Start (Docker)

1. **Place parquet files** in `data/`:
   - `green_tripdata_YYYY-MM.parquet`
   - `yellow_tripdata_YYYY-MM.parquet`

2. **Build and run:**

```bash
docker-compose up --build
```

3. **Open** [http://localhost:8000](http://localhost:8000)

4. **Load sample data** on the Upload page ("Load Sample"), then view the dashboard.

---

## Development Setup

### Backend in Docker, frontend locally

```bash
# Terminal 1: backend
docker-compose -f docker-compose.dev.yml up --build

# Terminal 2: frontend (Node 18 or 20 LTS)
cd frontend
nvm use 20
rm -rf node_modules package-lock.json
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) – Vite proxies `/api` to the backend.

> **Note:** Use Node 18 or 20 LTS. Node 24 can cause Vite `SyntaxError`. Run `nvm install 20` if needed.

### Local (no Docker)

```bash
# Backend
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py load_zones
python manage.py runserver

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

---

## Data Loading

1. **Upload**: Upload CSV or Parquet on the Upload page. Choose cab type (Yellow/Green) and max rows.
2. **Load sample**: "Load Sample" ingests the 6 preloaded files from `data/` (green & yellow, Jan–Mar 2025).

---

## API Endpoints

All analytics endpoints accept `?cab_type=all|yellow|green`.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/metrics/` | GET | Summary metrics |
| `/api/trips-over-time/` | GET | Trips per day |
| `/api/payment-type/` | GET | Trips by payment type |
| `/api/trips-by-hour/` | GET | Trips by hour (0–23) |
| `/api/trips-by-weekday/` | GET | Trips by day of week |
| `/api/heatmap/` | GET | Pickup heatmap data |
| `/api/demand-predictions/` | GET | Demand forecast |
| `/api/cluster-zones/` | GET | DBSCAN cluster zones |
| `/api/dashboard/` | GET | All dashboard data (single request) |
| `/api/duration-predictions/` | GET | Fare prediction sample |
| `/api/upload/` | POST | Upload CSV/Parquet |
| `/api/load-sample/` | POST | Load from `data/` |

---

## Project Structure

```
├── dashboard/              # Django app
│   ├── models.py          # TaxiTrip, TaxiZone
│   ├── parsers.py         # CSV/Parquet parsing (epoch ms support)
│   ├── analytics.py       # Queries + ML (Ridge, PolynomialFeatures, DBSCAN)
│   ├── views.py           # API views
│   └── management/commands/
│       └── load_zones.py
├── frontend/               # React app
│   ├── src/
│   │   ├── pages/         # Dashboard, Upload
│   │   ├── api.js         # API client (cab_type filter)
│   │   └── App.jsx
│   └── index.html
├── data/                   # Parquet files
├── Dockerfile
├── Dockerfile.dev          # Backend-only for dev
├── docker-compose.yml
└── requirements.txt
```

---

## Suggested Additional Charts (Future Work)

Based on the available data:

| Chart | Value |
|-------|-------|
| **Tip vs Fare scatter** | Shows tipping behavior by cab type |
| **Distance distribution** | Histogram of trip distances |
| **Ratecode breakdown** | Bar chart by rate code |
| **Congestion surcharge over time** | Impact of congestion pricing |
| **Peak hour classifier** | Logistic Regression – is this hour high-demand? |
| **Top pickup/dropoff zone pairs** | Sankey or table of popular routes |

---

## License

MIT
