# QueueWise — Forecasting Handover for Member 3

## What is ready

Member 2 prepared a 24-month provider × diagnostic-test forecasting pipeline for NHS England DM01 data (September 2024–August 2026). The model chosen on validation WAPE was **Naive Persistence**, for both total waiting-list size and patients waiting at least six weeks. Linear Regression and XGBoost were trained as comparisons. Forecasts and stress scenarios are available for **September–November 2026, from an August 2026 forecast origin**.

## Main input file

**`results/QueueWise_Forecast_Scenarios.csv`** (20,610 rows; 6,870 August provider-service groups × 3 horizons).

Use these columns:

| Field | Meaning |
|---|---|
| `Provider Org Code` | Provider identifier; use this as a grouping/join key |
| `Provider Org Name` | Display label; can be missing for some records |
| `Diagnostic Tests` | Individual DM01 diagnostic test category; `TOTAL` is excluded |
| `forecast_origin` | August 2026 data cutoff |
| `forecast_month` | September, October, November 2026 |
| `horizon_months` | 1, 2 or 3 |
| `Total WL` | Last observed total waiting list at the forecast origin |
| `Waiting_6plus_Weeks` | Last observed count waiting six weeks or longer |
| `forecast_total_wl_expected` | Expected total waiting-list pressure (naive persistence) |
| `forecast_total_wl_high` | High-pressure stress scenario for total WL |
| `forecast_waiting_6plus_expected` | Expected patients waiting ≥6 weeks |
| `forecast_waiting_6plus_high` | High-pressure stress scenario for patients waiting ≥6 weeks |

## Suggested integration steps

1. Load `QueueWise_Forecast_Scenarios.csv` with pandas; parse `forecast_month` as a date and keep `Provider Org Code` as a string.
2. In the dashboard, ask the user to choose a provider and forecast month/horizon, then display the expected and high-pressure counts for the selected diagnostic tests.
3. **Agree a service scope with the team.** The forecasting file contains all 15 individual DM01 diagnostic categories. If the demonstration focuses on MRI, CT, ultrasound, echocardiography and endoscopy, map those to the precise DM01 category labels; endoscopy is split into multiple tests. Never sum `TOTAL` with the 15 individual categories.
4. Define the available additional appointment budget and operational constraints per selected provider/service. Determine fairness rules and realistic maximum extra slots.
5. Compare **no additional intervention**, **equal distribution**, **current-backlog-based allocation**, and **forecast-informed allocation** using an explicitly stated simulation formula and assumptions.
6. Report changes in **simulated** overall backlog, six-week waiting counts, allocations and fairness. Show expected and high-pressure cases separately.
7. Preserve the forecast origin and horizon so historical scenarios are not described as newly generated live forecasts.

## Important constraints and limitations

- **Pressure is not arrivals:** the model predicts a stock of people currently waiting, not the number of new referrals or appointment requests. Avoid calling the forecast `demand` without explaining this distinction.
- **Extra slots do not imply equal reductions in 6+ week waits:** reducing a long-wait count depends on eligibility, who receives the appointment, referrals, case mix and time progression. If a simplified simulation assumes one slot reduces waiting burden by one, label it as an assumption and use sensible caps.
- **High-pressure scenario is not a 90% guaranteed prediction interval:** it uses the empirical 90th percentile of underprediction errors on validation data. Overall held-out coverage was roughly 95–96%, but coverage among actual nonzero waiting lists was lower (roughly 83–90% depending on target/horizon).
- **Model performance gets worse across horizons:** selected persistence WAPE for Total WL rose from 9.466% (one month) to 17.730% (three months); for waiting ≥6 weeks, from 18.428% to 41.141%.
- **Zeros are common:** use caution when comparing percentage-based metrics at small providers and when allocating extra appointments to services with zero forecast backlog.
- **Validation status:** provider-month `TOTAL` values agree exactly with the sum of the 15 service categories across 24 months (10,850 groups); independent agreement with published NHS summary tables is not yet established.

## Recommended outputs for the final dashboard and report

Provide a provider-service table by forecast month, plots of expected versus high-pressure waiting lists, an allocation recommendation and comparison against the three alternatives. Explain the scenario and allocation assumptions visibly on the dashboard. Distinguish simulated improvements from measured patient outcomes.

## Supporting files

- `results/QueueWise_Test_Model_Comparison.csv` — held-out model results
- `results/QueueWise_Multihorizon_Evaluation.csv` — 1–3 month errors and high-scenario coverage
- `results/QueueWise_Uncertainty_Calibration.csv` — validation-data error uplifts
- `results/QueueWise_24Months_ModelReady.csv` — historical provider-service data
- `figures/QueueWise_Forecast_Scenarios.png` — expected/high scenario plot
- `models/model_configuration.json` — selected method and forecast settings
- `Member2_Methodology_Results_Limitations.md` — full research description and limitations
