# QueueWise — Member 2: Forecasting and Uncertainty Analysis

**Project:** QueueWise: An Uncertainty-Aware Forecasting and Capacity-Optimization Framework for Reducing Diagnostic Waiting-List Pressure  
**Component:** Forecasting and uncertainty analysis  
**Data source:** NHS England DM01 monthly diagnostic waiting times and activity extracts  
**Data window:** September 2024–August 2026 (24 monthly reporting periods)  
**Forecast origin:** August 2026  
**Forecast horizons:** September, October and November 2026 (1, 2 and 3 months ahead from the forecast origin)

## 1. Objective and outcomes

This component developed and evaluated monthly forecasts of diagnostic waiting-list pressure by healthcare provider and diagnostic test. The **primary target** was the end-of-month total number of patients waiting (`Total WL`), and the **secondary target** was the number waiting at least six weeks (`Waiting_6plus_Weeks`). The forecasts were designed as inputs to the team's capacity-allocation simulation and dashboard, not as direct predictions of how many patients would benefit from additional appointments.

## 2. Dataset preparation and quality checks

Twenty earlier monthly DM01 full-extract ZIP files (September 2024–April 2026) were checked for reporting-period and schema consistency, aggregated to provider × diagnostic test × month using the same approach as Member 1, and combined with Member 1's cleaned May–August 2026 data. The combined provider-level dataset contained **173,600 rows, 24 columns, 24 months and 16 diagnostic categories including `TOTAL`**. The modelling dataset excluded `TOTAL` to avoid double counting, leaving **162,750 provider–service–month records covering 15 individual categories**. There were **48 missing provider-name values**, but no missing numerical values or duplicate provider–service–month keys.

Counts in the 14 waiting-time categories were checked against `Total WL`, and `Waiting_6plus_Weeks` was calculated from the categories beginning at six weeks. A subsequent **internal reconciliation** compared the `TOTAL` record against the sum of the individual services for every provider-month: **10,850 provider-month groups over 24 months, zero mismatches, and maximum absolute difference of zero** for both targets. This confirms internal consistency; an *independent* comparison against published national NHS summary tables remains outstanding.

## 3. Feature engineering and chronological evaluation

Models were trained at the provider × diagnostic service × target month level. Historical features included **calendar-aligned lags of 1, 2 and 3 months** for total waiting list, six-week waits, total activity and waiting-list activity, plus three-month means, month-to-month growth and cyclic month-of-year features. Provider codes and diagnostic service categories were one-hot encoded. Numerical features were scaled for the shared preprocessing pipeline, and the preprocessor was fitted on training data only.

Rows lacking a complete three-month lag history were excluded rather than treating missing observations as zero: **140,280 eligible rows** remained, spanning December 2024–August 2026. Data were split in chronological order:

| Split | Period | Rows |
|---|---|---:|
| Training | Dec 2024–Feb 2026 | 99,855 |
| Validation | Mar–May 2026 | 20,280 |
| Held-out test | Jun–Aug 2026 | 20,145 |

The models compared were (i) **Naive Persistence**, which predicts the target month's count using the preceding month's observed count, (ii) **Linear Regression**, and (iii) **XGBoost regression**. Models were selected according to *validation weighted absolute percentage error (WAPE)*; held-out test data were used only for final evaluation. Accuracy was reported with MAE, RMSE and WAPE. Negative ML predictions were clipped to zero.

## 4. Results

### Validation comparison

| Target | Model | MAE | RMSE | WAPE |
|---|---|---:|---:|---:|
| Total WL | Naive Persistence | **27.639** | 112.989 | **9.792%** |
| Total WL | Linear Regression | 28.975 | **110.431** | 10.265% |
| Total WL | XGBoost | 30.196 | 138.602 | 10.698% |
| Waiting 6+ weeks | Naive Persistence | **14.552** | 78.618 | **22.378%** |
| Waiting 6+ weeks | Linear Regression | 15.226 | **73.085** | 23.415% |
| Waiting 6+ weeks | XGBoost | 14.831 | 82.810 | 22.807% |

**Naive Persistence was selected for both targets** based on its lowest validation WAPE. Linear Regression had a slightly lower validation RMSE, but RMSE was not the predeclared selection criterion.

### Held-out test comparison

| Target | Model | MAE | RMSE | WAPE |
|---|---|---:|---:|---:|
| Total WL | **Naive Persistence (selected)** | 26.549 | 111.597 | 9.466% |
| Total WL | Linear Regression | **25.953** | **101.461** | **9.253%** |
| Total WL | XGBoost | 28.307 | 149.301 | 10.092% |
| Waiting 6+ weeks | **Naive Persistence (selected)** | **12.182** | 62.933 | **18.428%** |
| Waiting 6+ weeks | Linear Regression | 13.247 | **55.931** | 20.039% |
| Waiting 6+ weeks | XGBoost | 13.190 | 86.303 | 19.952% |

The slightly better Total WL test WAPE of Linear Regression was **not used to change the already selected model**, which would introduce test-set selection bias. The test results suggest simple persistence is a strong benchmark, although more complex approaches may improve certain error measures and should be assessed further in subsequent work.

### Multi-horizon persistence accuracy

| Horizon | Total WL WAPE | Waiting 6+ weeks WAPE |
|---|---:|---:|
| 1 month | 9.466% | 18.428% |
| 2 months | 14.003% | 30.601% |
| 3 months | 17.730% | 41.141% |

Errors increased with the forecast horizon, especially for six-week waiting-list pressure.

## 5. Uncertainty approach and forecasts

Two outputs were produced per provider, diagnostic test and forecast month:

- **Expected pressure:** Naive Persistence — August 2026's observed count carried forward to each future horizon.
- **High-pressure stress scenario:** The expected count plus a nonnegative uplift based on the **90th percentile of historical underprediction errors**, estimated on March–May 2026 validation observations. Uplifts were stratified by diagnostic category, target, horizon and historical size band when there were at least 30 examples; a service-level fallback was used otherwise. Uplifts were constrained not to decrease with the horizon, and six-week high counts were capped at the total-waiting-list high estimate.

The final scenario dataset contains **20,610 records**: 6,870 provider–service combinations at the August 2026 origin, each forecast for 1–3 months.

| Forecast month | Expected Total WL | High Total WL | Expected Waiting 6+ weeks | High Waiting 6+ weeks |
|---|---:|---:|---:|---:|
| Sep 2026 | 1,833,070 | 2,117,666 | 452,306 | 616,656 |
| Oct 2026 | 1,833,070 | 2,305,778 | 452,306 | 725,639 |
| Nov 2026 | 1,833,070 | 2,490,398 | 452,306 | 776,849 |

These are **forecasts relative to the August 2026 data cutoff**. September and October are not future calendar months as of November 2026.

### High-scenario coverage on held-out test observations

| Horizon | Total WL: all / positive actuals | Waiting 6+ weeks: all / positive actuals |
|---|---|---|
| 1 month | 95.90% / 89.07% | 95.27% / 83.73% |
| 2 months | 96.03% / 89.42% | 95.52% / 84.60% |
| 3 months | 96.38% / 90.35% | 95.10% / 83.15% |

The high-pressure values are **empirical stress scenarios, not guaranteed 90% prediction intervals**. Overall coverage is inflated by numerous zero-waiting-list records; coverage among actual nonzero counts is more informative for operational planning.

## 6. Limitations and interpretation

1. **Limited time span:** Although 24 months is much better than the original four months, there are only 21 eligible target months after lag generation and just three months per validation/test period. Seasonal and multi-horizon estimates need further evaluation on longer history.
2. **Simple selected forecaster:** Persistence assumes the most recent observed count continues. It does not explicitly model new referrals, capacity changes, policy shifts, or sudden pressure increases; expected values consequently remain constant at horizons 1–3.
3. **Zero-heavy dataset and new waiting lists:** Many provider-service records have zero counts. In the one-month held-out evaluation there were 155 zero-to-positive cases for Total WL and 494 for the six-week target. A zero-valued naive forecast may not anticipate emerging waiting lists.
4. **Uncertainty is heuristic:** The error-percentile uplift was fitted on validation data and checked on the held-out test period, but was not derived as a formally calibrated distribution-free interval; group sizes and constraints affect coverage.
5. **Aggregation and comparability:** Internal reconciliation passed for all 24 months, but independent comparison with official NHS published summary totals has not yet been documented. Provider-level changes over time and reporting conventions may affect comparability.
6. **Scope of optimization:** Forecasts cover all 15 individual DM01 diagnostic categories. The team must decide which categories and provider groups are operationally eligible for allocating extra capacity. The `TOTAL` category must not be added to individual service counts.
7. **Decision-support, not clinical outcomes:** The project has not demonstrated that additional appointment slots result in an equal reduction in prolonged waits or actual patient waiting times; Member 3 must state the simulation assumptions and constraints.

## 7. Conclusion

A reproducible provider–diagnostic-test forecasting workflow was developed using 24 months of DM01 data. Naive Persistence achieved the lowest validation WAPE for both total waiting-list size and six-week waiting counts. Held-out evaluation showed increasing errors at longer horizons and lower high-scenario coverage when evaluated only on active waiting lists. Expected and high-pressure forecasts were exported for the capacity-allocation simulation, with limitations documented to prevent overstating the results.
