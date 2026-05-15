# Phase 1b: PostgreSQL Migration

> Add a PostgreSQL database to the Hetzner VPS so the data pipeline writes to SQL instead of parquet files. This replaces the file-based cache with a proper relational database and sets up the infrastructure for Phase 2 weather data.

---

## Why Do This

| Before (Phase 1) | After (Phase 1b) |
|---|---|
| Data lives in `data/raw/coffee_futures.parquet` | Data lives in PostgreSQL `daily_prices` table |
| No schema, no constraints | Typed columns, primary keys, foreign keys |
| No querying — loaded wholesale into pandas | Can query with SQL: "average close price in 2024 by quarter" |
| No migration history | Alembic tracks every schema change (version-controlled) |
| One file, one table | Multiple tables ready for weather, shock events, regions |

---

## Architecture After Migration

```
Cron job (daily 2pm UTC)
    │
    ▼
fetch_coffee(refresh=True)
    │
    ▼  writes via SQLAlchemy ORM
┌────────────────────────────────┐
│  PostgreSQL (coffee_prices DB) │
│  ├─ daily_prices               │
│  ├─ regions                    │
│  └─ weather_readings           │   ← ready for Phase 2
│     shock_events               │
└──────────┬─────────────────────┘
           │
           ▼  reads via SQLAlchemy
    Streamlit dashboard
```

---

## Prerequisite Check

On the server, confirm PostgreSQL is not yet installed:

```bash
psql --version
```

If it says `command not found`, we install it. If it shows a version, it's already there (Hetzner images sometimes include it).

---

## Full Schema

### 1. `regions` — reference table (5 major producing regions)

```sql
CREATE TABLE regions (
    id SERIAL PRIMARY KEY,
    country TEXT NOT NULL,
    region_name TEXT NOT NULL,
    lat_min NUMERIC,
    lat_max NUMERIC,
    lon_min NUMERIC,
    lon_max NUMERIC,
    production_share NUMERIC,
    UNIQUE(country)
);

INSERT INTO regions (country, region_name, lat_min, lat_max, lon_min, lon_max, production_share) VALUES
    ('Brazil', 'Minas Gerais',        -23, -17, -51, -40, 0.35),
    ('Vietnam', 'Central Highlands',   11,  15, 107, 109, 0.15),
    ('Colombia', 'Eje Cafetero',       1,   7, -77, -73, 0.08),
    ('Indonesia', 'Sumatra',           -5,   5,  95, 106, 0.07),
    ('Ethiopia', 'Sidama / Oromia',    5,   9,  36,  42, 0.05);
```

### 2. `daily_prices` — OHLCV coffee futures

```sql
CREATE TABLE daily_prices (
    date DATE NOT NULL,
    ticker TEXT NOT NULL DEFAULT 'KC=F',
    open NUMERIC NOT NULL,
    high NUMERIC NOT NULL,
    low NUMERIC NOT NULL,
    close NUMERIC NOT NULL,
    volume BIGINT,
    source TEXT DEFAULT 'yfinance',
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (date, ticker)
);

CREATE INDEX idx_daily_prices_date ON daily_prices (date DESC);
```

### 3. `weather_readings` — daily weather per region (for Phase 2)

```sql
CREATE TABLE weather_readings (
    region_id INTEGER NOT NULL REFERENCES regions(id),
    date DATE NOT NULL,
    temp_max NUMERIC,
    temp_min NUMERIC,
    temp_mean NUMERIC,
    precipitation_sum NUMERIC,
    soil_moisture NUMERIC,
    evapotranspiration NUMERIC,
    source TEXT DEFAULT 'open-meteo',
    PRIMARY KEY (region_id, date)
);
```

### 4. `shock_events` — detected extreme weather (for Phase 2)

```sql
CREATE TABLE shock_events (
    id SERIAL PRIMARY KEY,
    region_id INTEGER NOT NULL REFERENCES regions(id),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    event_type TEXT NOT NULL CHECK (event_type IN ('heatwave', 'drought', 'compound')),
    severity NUMERIC,
    max_temp_anomaly NUMERIC,
    precip_anomaly NUMERIC,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(region_id, start_date, event_type)
);
```

---

## New Dependencies

Add to `requirements.txt`:

```
sqlalchemy>=2.0
alembic>=1.13
psycopg2-binary>=2.9
python-dotenv>=1.0
```

---

## New Package Structure

```
src/database/
├── __init__.py
├── engine.py           # SQLAlchemy engine + session factory
├── models.py           # ORM classes (Base, DailyPrice, WeatherReading, etc.)
├── credentials.py      # Load DATABASE_URL from .env
├── alembic/
│   ├── alembic.ini
│   ├── env.py
│   └── versions/       # Auto-generated migration files
└── repositories/
    ├── __init__.py
    ├── prices.py       # save_price(), get_prices_in_range()
    ├── weather.py      # save_weather(), get_weather_for_region()
    └── events.py       # record_event(), get_shock_events()
```

### Key files explained

**`src/database/engine.py`**
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.credentials import DATABASE_URL

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
```

**`src/database/models.py`**
```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import ForeignKey, Numeric, Text, Date, BigInteger, DateTime
from datetime import date, datetime

class Base(DeclarativeBase):
    pass

class DailyPrice(Base):
    __tablename__ = "daily_prices"
    date: Mapped[date] = mapped_column(Date, primary_key=True)
    ticker: Mapped[str] = mapped_column(Text, primary_key=True, default="KC=F")
    open: Mapped[float] = mapped_column(Numeric)
    high: Mapped[float] = mapped_column(Numeric)
    low: Mapped[float] = mapped_column(Numeric)
    close: Mapped[float] = mapped_column(Numeric)
    volume: Mapped[int | None] = mapped_column(BigInteger)
    # ... Region, WeatherReading, ShockEvent classes follow the same pattern
```

**`.env`** (gitignored)
```
DATABASE_URL=postgresql://coffee:password@localhost:5432/coffee_prices
STREAMLIT_SERVER_PORT=8501
```

---

## Step-by-Step Migration

### Step 1 — Install PostgreSQL on the server
```bash
sudo apt install -y postgresql postgresql-client
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### Step 2 — Create database and user
```bash
sudo -u postgres psql
```

Inside `psql`:
```sql
CREATE USER coffee WITH PASSWORD 'your-password-here';
CREATE DATABASE coffee_prices OWNER coffee;
GRANT ALL PRIVILEGES ON DATABASE coffee_prices TO coffee;
\c coffee_prices
GRANT ALL ON SCHEMA public TO coffee;
\q
```

### Step 3 — Create `.env` file
```bash
nano /home/coffee/CoffeePrices/.env
```

Contents:
```
DATABASE_URL=postgresql://coffee:your-password-here@localhost:5432/coffee_prices
```

### Step 4 — Add the `src/database/` package
Create all the files listed in the package structure above:
- `engine.py`
- `models.py`
- `credentials.py`
- `repositories/prices.py`
- `repositories/weather.py`
- `repositories/events.py`

### Step 5 — Initialize Alembic
```bash
cd ~/CoffeePrices
.venv/bin/alembic init src/database/alembic
```

Edit `src/database/alembic/env.py` to point at the models:
```python
from src.database.models import Base
target_metadata = Base.metadata
```

### Step 6 — Generate and run the migration
```bash
.venv/bin/alembic revision --autogenerate -m "create all tables"
.venv/bin/alembic upgrade head
```

Verify:
```bash
sudo -u postgres psql -d coffee_prices -c "\dt"
```

### Step 7 — Rewrite `fetch_coffee.py` to write to DB

New flow:
1. `fetch_coffee(refresh=True)` downloads from yfinance
2. Writes each row to `daily_prices` table via `repositories.prices.save_prices(df)`
3. Uses `ON CONFLICT (date, ticker) DO UPDATE` so repeated cron runs don't error out

### Step 8 — Update Streamlit dashboard to read from DB

Replace `fetch_coffee()` call with:
```python
from src.database.repositories.prices import get_prices_in_range
df = get_prices_in_range(start_date, end_date)
```

Returns the same pandas DataFrame the dashboard already expects — no chart code changes needed.

### Step 9 — Disable the old parquet path
- Remove `data/raw/` gitignore exception for parquet (parquet is obsolete)
- `fetch_coffee()` still works as fallback but the primary path is DB

### Step 10 — Restart and verify
```bash
sudo systemctl restart coffee-dashboard
```

Check the logs:
```bash
journalctl -u coffee-dashboard -n 20
```

---

## Rollback Plan (if something breaks)

```bash
# Reset the database (keep schema, clear data)
.venv/bin/alembic downgrade base
.venv/bin/alembic upgrade head

# Or restore the old parquet-based fetch_coffee.py
git checkout main -- src/data/fetch_coffee.py
sudo systemctl restart coffee-dashboard
```

---

## CV Talking Points

After this migration, you can describe:

> "Designed and deployed a PostgreSQL database on a Hetzner VPS to replace file-based data storage for a coffee futures pipeline. Used SQLAlchemy ORM for type-safe inserts and Alembic for version-controlled schema migrations — enabling scalable ingestion of weather data in Phase 2."

**Demonstrates**: PostgreSQL, SQLAlchemy, Alembic, ETL pipeline design, database migrations, production deployment.

---

*Estimated time: ~50 minutes to implement*
