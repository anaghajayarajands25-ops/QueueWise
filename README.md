# 🩺 QueueWise
### Uncertainty-Aware Forecasting and Capacity Optimisation for NHS England Diagnostic Waiting Lists

<p align="center">
  <strong>Forecasting meets intelligent healthcare resource allocation.</strong>
</p>

**Live Dashboard:** [QueueWise – Streamlit App](https://queuewise-tw82cbi2gjruseps85et9h.streamlit.app/)

---

## 📌 Project Overview

QueueWise is a healthcare analytics and decision-support project designed to address diagnostic waiting-list pressures across NHS England.

The project combines historical diagnostic waiting-list data, predictive forecasting, uncertainty estimation and optimisation techniques to recommend how additional diagnostic appointment capacity can be distributed across healthcare providers and diagnostic services.

Rather than allocating additional appointments equally or relying entirely on existing backlogs, QueueWise introduces a forecast-informed allocation strategy that considers both expected waiting-list requirements and potential high-pressure scenarios.

The final output is an interactive Streamlit dashboard that allows users to explore forecasts, compare allocation strategies, analyse provider-level requirements and evaluate the sensitivity of allocation decisions to different assumptions.

## 🎯 Project Objectives

- Analyse historical NHS England diagnostic waiting-list data.
- Forecast future diagnostic waiting-list volumes across multiple time horizons.
- Quantify uncertainty through high-pressure forecasting scenarios.
- Develop an optimisation-based approach for allocating additional diagnostic capacity.
- Compare forecast-informed allocation against conventional allocation strategies.
- Evaluate allocation efficiency, fairness and potential reduction in long-wait patients.
- Provide an interactive decision-support dashboard for healthcare resource planning.

## 🏗️ Project Architecture

The QueueWise workflow consists of four major stages:

1. **Data Processing:** Cleaning, preparing and reconciling historical NHS DM01 diagnostic waiting-list data.
2. **Forecasting:** Evaluating Naive Persistence, Linear Regression and XGBoost models to estimate future waiting-list volumes.
3. **Uncertainty Estimation:** Incorporating empirical 90th-percentile forecast-error uplifts to construct high-pressure scenarios.
4. **Capacity Optimisation:** Applying a risk-weighted allocation algorithm to distribute additional appointment capacity across provider-service units.

The resulting forecasts and allocation outputs are presented through an interactive Streamlit dashboard.

## 📊 Dataset

**Data source:** NHS England – Diagnostic Waiting Times and Activity (DM01).

The project uses cleaned and processed monthly diagnostic waiting-list data covering:

- September 2024 – August 2026
- Healthcare provider organisations
- Diagnostic service categories
- Total waiting-list volumes
- Patients waiting six weeks or longer
- Diagnostic activity information

The forecasting dataset contains **20,610 provider-service-horizon records**.

Each allocation unit represents a combination of a healthcare provider and a diagnostic service.

## 🤖 Forecasting Methodology

Three forecasting approaches were evaluated:

| Model | Description |
|---|---|
| Naive Persistence | Uses the latest observed value as the future forecast |
| Linear Regression | Captures linear patterns in historical waiting-list data |
| XGBoost | Models nonlinear relationships using gradient-boosted decision trees |

Model performance was evaluated using:

- Mean Absolute Error (MAE)
- Root Mean Squared Error (RMSE)
- Weighted Absolute Percentage Error (WAPE)

### Forecast evaluation

The Naive Persistence model achieved the following test-set results:

| Forecast target | 1-month WAPE | 2-month WAPE | 3-month WAPE |
|---|---:|---:|---:|
| Total waiting list | 9.47% | 14.00% | 17.73% |
| Waiting 6+ weeks | 18.43% | 30.60% | 41.10% |

The forecast horizons represent one, two and three months ahead of the August 2026 forecast origin.

### Uncertainty Estimation

To account for potential underprediction, QueueWise incorporates an empirical 90th-percentile forecast-error uplift.

Two scenarios are generated:

- **Expected scenario:** The baseline forecast using persistence.
- **High-pressure scenario:** The expected forecast adjusted using empirically estimated underprediction allowances.

The high-pressure scenario represents a stress-testing assumption rather than a guaranteed statistical prediction interval.

## ⚖️ Capacity Allocation and Optimisation

QueueWise implements a risk-weighted allocation algorithm using a water-filling approach.

The allocation considers:

- Forecast waiting-list requirements.
- High-pressure waiting-list estimates.
- Available additional appointment capacity.
- A configurable budget.
- Maximum capacity constraints for each provider-service unit.
- A risk-weighting parameter (λ).

The risk-weighted forecast need is:

\[
S_i = E_i + \lambda(H_i-E_i)
\]

Where:

- \(S_i\) = Risk-weighted allocation score.
- \(E_i\) = Expected waiting-list forecast.
- \(H_i\) = High-pressure forecast.
- \(\lambda\) = Risk-weighting parameter between 0 and 1.

The algorithm distributes additional appointment slots proportionally to these scores while respecting capacity constraints.

### Allocation strategies compared

| Strategy | Allocation approach |
|---|---|
| No intervention | No additional appointment capacity |
| Equal allocation | Equal distribution across eligible units |
| Current backlog | Allocation based on observed long-wait backlogs |
| **QueueWise** | Forecast-informed, risk-weighted allocation |

### Evaluation metrics

The allocation strategies are evaluated using:

- Reduction in patients waiting six weeks or longer.
- Percentage reduction in long-wait patients.
- Appointment-slot utilisation.
- Jain's Fairness Index.
- Percentage of units receiving capacity.
- Remaining long-wait patients.
- Unused appointment slots.

All reduction figures are simulated estimates, not observed clinical outcomes.

## 🖥️ Interactive Dashboard

**Explore the live application:** [Launch QueueWise](https://queuewise-tw82cbi2gjruseps85et9h.streamlit.app/)

The dashboard includes six interactive sections:

1. **Forecast:** Visualises observed, expected and high-pressure waiting-list volumes across diagnostic services.
2. **Strategy Comparison:** Compares the four allocation strategies using efficiency, reduction and fairness metrics.
3. **Recommended Allocation:** Displays the recommended distribution of additional appointment slots across provider-service units.
4. **Provider View:** Allows provider-level exploration of waiting-list forecasts and recommended capacity.
5. **Sensitivity Analysis:** Examines how allocation outcomes change with different budgets, clearance efficiencies and risk-weighting assumptions.
6. **Method & Assumptions:** Documents the forecasting pipeline, optimisation methodology and project limitations.

Users can interactively modify forecast horizons, diagnostic services, healthcare providers, scenarios and optimisation parameters.

## 🛠️ Technology Stack

| Category | Technologies |
|---|---|
| Programming Language | Python |
| Data Processing | Pandas, NumPy |
| Machine Learning | Scikit-learn, XGBoost |
| Optimisation | Custom Python optimisation module, Water-filling algorithm |
| Visualisation | Plotly |
| Dashboard Development | Streamlit |
| Data Source | NHS England DM01 |
| Development Environment | Google Colab |
| Version Control | Git, GitHub |
| Deployment | Streamlit Community Cloud |

## 📂 Repository Structure

```text
QueueWise/
│
├── app.py
│   └── Streamlit dashboard application
│
├── queuewise_opt.py
│   └── Capacity allocation and optimisation module
│
├── requirements.txt
│   └── Python dependencies
│
├── README.md
│   └── Project documentation
│
├── .gitignore
│
├── .streamlit/
│   └── config.toml
│       └── Dashboard theme configuration
│
└── data/
    └── QueueWise_Forecast_Scenarios.csv
        └── Forecast scenarios used by the application
```

## 🚀 Running the Project Locally

### 1. Clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/queuewise.git
cd queuewise
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it:

**Windows:**
```bash
venv\Scripts\activate
```

**Mac/Linux:**
```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Launch the dashboard

```bash
streamlit run app.py
```

The application will be accessible at:

```text
http://localhost:8501
```

## ☁️ Deployment

QueueWise is deployed using Streamlit Community Cloud.

The deployment process involves:

1. Hosting the application source code on GitHub.
2. Connecting the GitHub repository to Streamlit Community Cloud.
3. Configuring `app.py` as the application entry point.
4. Installing dependencies through `requirements.txt`.
5. Deploying the interactive dashboard.

**Live Application:** [https://queuewise-tw82cbi2gjruseps85et9h.streamlit.app/](https://queuewise-tw82cbi2gjruseps85et9h.streamlit.app/)

## ⚠️ Limitations and Future Improvements

Although QueueWise provides a structured approach to diagnostic capacity planning, certain limitations should be considered:

- The expected forecast uses a persistence-based approach.
- Forecast uncertainty increases with longer prediction horizons.
- The high-pressure scenario is based on empirical forecast-error uplifts and is not a calibrated prediction interval.
- Appointment clearance efficiency is a configurable simulation assumption.
- Simulated waiting-list reductions do not establish actual improvements in patient outcomes.
- The allocation strategy requires real-world validation before operational implementation.
- The current forecast origin is August 2026; the dashboard does not provide live NHS forecasts.

### Future Enhancements

- Incorporate more advanced time-series and machine-learning forecasting models.
- Develop a historical rolling-origin backtesting framework.
- Introduce calibrated probabilistic forecasting.
- Integrate real-time NHS diagnostic waiting-list data.
- Incorporate provider-specific operational capacity and resource constraints.
- Validate allocation recommendations using real-world outcomes.
- Explore fairness-aware optimisation across healthcare providers.

## 👩‍💻 Project Contributors

**Developed by:**

- **Anagha Jayarajan**
- **Sravana Nambiar**
- **Nakshathra V**

This project was collaboratively developed as an application of data science, forecasting, optimisation and healthcare analytics.

## 📌 Project Disclaimer

QueueWise is an academic and research-oriented decision-support prototype. Its forecasts and allocation recommendations are intended for analytical exploration and simulation.

The estimated reductions in waiting lists are model-based simulations, not verified clinical outcomes or operational recommendations. The application should not be used for actual NHS capacity decisions without further validation.

---

<p align="center">
  <strong>QueueWise — Making Healthcare Capacity Planning More Predictive, Fair and Data-Driven.</strong>
</p>
