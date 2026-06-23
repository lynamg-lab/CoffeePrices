# Brazil Coffee-Weather Analysis: Results Summary

*Generated from the Phase 2 mesoregion analysis pipeline (2021–2026)*

---

## 1. Shock Event Detection

**1,122 events** detected across 41 coffee-producing mesoregions:

| Event Type | Count | Avg Duration | Avg Severity |
|------------|-------|-------------|-------------|
| Drought    | 631   | ~22 days     | Moderate     |
| Heatwave   | 399   | ~8 days      | High         |
| Compound   | 92    | ~6 days      | Severe       |

Most event-prone mesoregions: Centro Norte Baiano (41), Sul Baiano (40), Centro Sul Baiano (40).

---

## 2. Event Study: Price Impact

Weather shocks **do** move coffee futures prices. All event types produce statistically significant positive Cumulative Abnormal Returns (CAR) at horizons beyond 10 days (p < 0.001).

| Horizon | Heatwave | Drought | Compound |
|---------|----------|---------|----------|
| 10d     | +0.23%   | +1.61%  | +2.29%   |
| 30d     | +2.60%   | +3.18%  | +3.01%   |
| 60d     | +5.31%   | +7.24%  | +11.10%  |
| 90d     | +9.99%   | +10.64% | **+17.31%** |

**Key insight**: Compound events (heatwave + drought co-occurring) drive ~70% more price impact at 90 days than heatwaves or droughts alone. Droughts have faster onset impact (positive at 10d) while heatwaves take longer to price in.

**Production weighting matters**: Events in larger-producing mesoregions show higher CAR at 90d, confirming that production-weighted aggregation captures a stronger price signal.

---

## 3. Cross-Correlation & Granger Causality

**Cross-correlation**: Temperature anomalies in top mesoregions show weak contemporaneous correlation with coffee returns (peak |r| < 0.06), but signals strengthen at lags of 10–30 days — consistent with market digestion delays.

**Granger causality** (lag=5): No mesoregion's temperature anomaly significantly Granger-causes daily coffee returns at conventional thresholds. This is expected for daily-frequency data where weather shocks accumulate over weeks, not days.

---

## 4. Regression Models

Five OLS specifications with Newey-West standard errors were tested on daily returns (N ≈ 1,374):

| Model | Variables | R² | Adj R² |
|-------|-----------|-----|--------|
| 1: Sul de Minas only | Temp + precip anomalies | 0.0013 | −0.0002 |
| 2: Top 3 MG mesos | 3 mesos × 2 vars | 0.0067 | 0.0024 |
| 3: All 6 top mesos | 6 mesos × 2 vars | 0.0098 | 0.0010 |
| **4: Weather + controls** | MG temp + USD/BRL + Oil + ENSO | **0.0132** | **0.0089** |
| 5: Lags + controls | Sul de Minas (t0/t30/t60) + controls | 0.0092 | 0.0054 |

**Model 4 (best fit)** findings:
- **Sul de Minas temperature anomaly**: Now statistically significant (**+0.0009**, p = 0.03) — a notable improvement after removing COVID-era noise.
- **Oil prices**: Highly significant positive coefficient (**+0.081**, p = 0.004) — higher oil → higher coffee (cost pass-through).
- **USD/BRL exchange rate**: No longer significant (p = 0.13) — the COVID-era FX volatility that drove this relationship has been excluded.
- **Weather anomalies**: Sul de Minas temp anomaly now shows a significant daily-frequency signal, though the effect size remains small — event-study methodology over 30–90 days captures much larger cumulative impacts.

---

## 5. Key Takeaways

1. **Weather shocks matter for coffee prices**, but the effect accumulates over 30–90 days, not overnight. Event study methodology captures this better than daily return regressions.

2. **Compound events are the most impactful** — a heatwave and drought hitting the same mesoregion simultaneously produces +17.3% CAR at 90 days, vs. ~+10% for either event alone.

3. **Oil prices are the dominant short-term driver** (p = 0.004), and **Sul de Minas temperature anomaly becomes significant** (p = 0.03) once COVID-era noise is removed. Weather effects also operate through supply expectations over weeks to months.

4. **Sul de Minas (31_10) is the single most important region** — its 857k tonnes (32% of national production) makes it the weather bellwether for global arabica markets.

5. **Production weighting amplifies the signal** — mesoregions with higher production tonnage show stronger price responses to comparable weather shocks.

---

## 6. Limitations & Caveats

- Daily return regressions have inherently low R² (typical for financial data).
- Weather anomalies are measured at the daily level but likely have non-linear threshold effects not captured by linear OLS.
- Futures prices reflect global supply expectations (Vietnam, Colombia, Ethiopia) — Brazil-only weather cannot explain all price variation.