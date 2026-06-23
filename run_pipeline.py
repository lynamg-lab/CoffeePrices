"""Daily data pipeline: fetch, process, analyse, and cache all data for Phase 2."""

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.data.fetch_weather import fetch_weather
from src.data.fetch_controls import fetch_all_controls
from src.data.process_weather import process_all
from src.data.merge_data import merge_all
from src.analysis.detect_shocks import detect_all
from src.analysis.event_study import run_event_study
from src.analysis.correlation import run_correlation
from src.analysis.models import run_models

START = "2021-01-01"


def step(label: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"[{time.strftime('%H:%M:%S')}] {label}")
    print(f"{'=' * 60}")


def main() -> None:
    step("1/8 — Fetching weather data from Open-Meteo")
    fetch_weather(start=START, end=None)

    step("2/8 — Fetching control variables (USD/BRL, oil, ENSO)")
    fetch_all_controls(start=START, end=None)

    step("3/8 — Processing weather: climatology, anomalies, rolling stats")
    process_all()

    step("4/8 — Merging coffee + weather + controls into daily panel")
    merge_all(start=START, end=None, refresh_controls=False)

    step("5/8 — Detecting shock events (heatwave, drought, compound)")
    detect_all()

    step("6/8 — Running event study (CAR analysis)")
    run_event_study(pre_window=30, post_window=90)

    step("7/8 — Cross-correlation & Granger causality")
    run_correlation(max_lag=180)

    step("8/8 — Regression models with Newey-West SE")
    run_models()

    print(f"\n{'=' * 60}")
    print("Pipeline complete.")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
