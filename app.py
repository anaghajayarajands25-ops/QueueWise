import os, sys
APP_DIR = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get('QW_OUT', APP_DIR)
FC_PATH = os.environ.get('QW_FC_PATH', os.path.join(APP_DIR, 'data', 'QueueWise_Forecast_Scenarios.csv'))
sys.path.insert(0, APP_DIR)

import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import queuewise_opt as qo

# ------------------------------------------------------------------ page + palette
st.set_page_config(page_title='QueueWise | Diagnostic Capacity Planning',
                   page_icon='🩺', layout='wide', initial_sidebar_state='expanded')

PANEL, BORDER, TXT, MUTED, GRID = '#131D2B', '#233248', '#E6EDF5', '#8FA3BA', '#223049'
OBS, EXP, HIGH, RED, GREY = '#5B8DEF', '#2EC4B6', '#F4B860', '#F06A5A', '#7F8CA3'
STRAT_COLORS = {'No intervention': GREY, 'Equal': HIGH,
                'Current backlog': OBS, 'QueueWise (forecast-informed)': EXP}

st.markdown(f"""
<style>
.block-container {{padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1400px;}}
#MainMenu, footer {{visibility: hidden;}}
.qw-hero {{background: linear-gradient(120deg, #0B2545 0%, #134074 55%, #13808B 100%);
          padding: 26px 32px; border-radius: 14px; color: #fff; margin-bottom: 18px;
          border: 1px solid {BORDER};}}
.qw-hero h1 {{margin: 0; font-size: 2rem; font-weight: 700; letter-spacing: .3px; color:#fff;}}
.qw-hero p {{margin: 6px 0 0 0; opacity: .9; font-size: .98rem; color:#fff;}}
.qw-badge {{display:inline-block; background: rgba(255,255,255,.14); border: 1px solid rgba(255,255,255,.35);
           padding: 3px 12px; border-radius: 20px; font-size: .78rem; margin: 10px 8px 0 0; color:#fff;}}
.qw-card {{background:{PANEL}; border:1px solid {BORDER}; border-left: 5px solid {EXP};
          border-radius: 10px; padding: 14px 18px; min-height: 140px;
          box-shadow: 0 2px 8px rgba(0,0,0,.25);}}
.qw-card .lbl {{font-size:.74rem; text-transform:uppercase; letter-spacing:.8px; color:{MUTED}; font-weight:600;}}
.qw-card .val {{font-size:1.75rem; font-weight:700; color:#F2F6FA; line-height:1.25;}}
.qw-card .sub {{font-size:.78rem; color:{MUTED};}}
.qw-note {{background:#12263A; border:1px solid #24415E; border-radius:10px; padding:12px 16px;
          font-size:.88rem; color:#CFE0F2; margin: 8px 0 14px 0;}}
.qw-warn {{background:#2B2314; border:1px solid #5A4720; border-radius:10px; padding:12px 16px;
          font-size:.88rem; color:#F1D9A8; margin: 8px 0 14px 0;}}
</style>
""", unsafe_allow_html=True)


def card(col, label, value, sub='', color=EXP):
    col.markdown(f"""<div class="qw-card" style="border-left-color:{color}">
        <div class="lbl">{label}</div><div class="val">{value}</div>
        <div class="sub">{sub}</div></div>""", unsafe_allow_html=True)


def show_plot(fig):
    has_legend = len(fig.data) > 1 and fig.layout.showlegend is not False
    fig.update_layout(
        font=dict(family='Inter, Segoe UI, sans-serif', size=13, color=TXT),
        paper_bgcolor=PANEL, plot_bgcolor=PANEL,
        margin=dict(l=20, r=30, t=70, b=95 if has_legend else 65),
        title_x=0.02, title_xanchor='left', title_font_size=16,
        legend=dict(orientation='h', yanchor='top', y=-0.14, xanchor='left', x=0,
                    bgcolor='rgba(0,0,0,0)', font=dict(color=TXT)))
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=GRID, automargin=True, color=TXT)
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=GRID, automargin=True, color=TXT)
    try:
        st.plotly_chart(fig, width='stretch', theme=None)
    except TypeError:
        st.plotly_chart(fig, use_container_width=True, theme=None)


def show_table(df, **kw):
    try:
        st.dataframe(df, width='stretch', **kw)
    except TypeError:
        st.dataframe(df, use_container_width=True, **kw)


def nice(s):
    return s.replace('_', ' ').title().replace('Mri', 'MRI').replace('Ct', 'CT').replace('Dexa', 'DEXA')


# ------------------------------------------------------------------ data
@st.cache_data(show_spinner='Loading forecasts...')
def get_data(path):
    df = qo.load_forecasts(path)
    df['Provider Org Name'] = df['Provider Org Name'].fillna('(name unavailable)')
    df['Provider'] = df['Provider Org Name'] + ' [' + df['Provider Org Code'] + ']'
    df['Test'] = df['Diagnostic Tests'].map(nice)
    return df


if not os.path.exists(FC_PATH):
    st.error(f'Forecast file not found at `{FC_PATH}`. Make sure `data/QueueWise_Forecast_Scenarios.csv` '
             'sits next to app.py.')
    st.stop()
fc = get_data(FC_PATH)
origin_dt = pd.to_datetime(fc['forecast_origin']).max()
origin = origin_dt.strftime('%B %Y')

# ------------------------------------------------------------------ hero
st.markdown(f"""
<div class="qw-hero">
  <h1>🩺 QueueWise</h1>
  <p>Uncertainty-aware forecasting and capacity optimisation for NHS England diagnostic waiting lists</p>
  <span class="qw-badge">Data: NHS England DM01</span>
  <span class="qw-badge">Forecast origin: {origin}</span>
  <span class="qw-badge">Results are simulated, not measured patient outcomes</span>
</div>""", unsafe_allow_html=True)

# ------------------------------------------------------------------ sidebar
with st.sidebar:
    st.markdown('### Scope')
    h = st.selectbox('Forecast horizon', [1, 2, 3], format_func=lambda x: f'{x} month{"s" if x > 1 else ""} ahead')
    all_tests = sorted(fc['Diagnostic Tests'].unique())
    sel_raw = st.multiselect('Diagnostic tests (empty = all)', all_tests, format_func=nice)
    sel_tests = sel_raw or all_tests
    all_provs = sorted(fc['Provider'].unique())
    sel_provs = st.multiselect('Providers (empty = all)', all_provs)
    scen = st.radio('Scenario to evaluate', ['expected', 'high'], horizontal=True,
                    format_func=lambda s: 'Expected' if s == 'expected' else 'High pressure')

    st.markdown('### Allocation assumptions')
    budget_pct = st.slider('Extra appointments (% of forecast 6+ wk waits)', 1, 50, 10)
    cap_pct = st.slider('Max extra slots per unit (% of waiting list)', 5, 100, 20)
    eff = st.slider('Long waits cleared per extra slot', 0.1, 1.0, 1.0, 0.1,
                    help='Assumption: how many 6+ week waits one extra appointment removes.')
    lam = st.slider('Risk weight on high-pressure scenario (λ)', 0.0, 1.0, 0.5, 0.1,
                    help='0 = plan on expected only; 1 = plan on the high-pressure forecast.')
    st.caption('A unit is one provider and diagnostic test combination.')

d = fc[(fc.horizon_months == h) & (fc['Diagnostic Tests'].isin(sel_tests))]
if sel_provs:
    d = d[d['Provider'].isin(sel_provs)]
d = d.reset_index(drop=True)
if d.empty:
    st.warning('No records for this selection.'); st.stop()

PARAMS = dict(budget_pct=budget_pct, cap_pct=cap_pct, eff=eff, risk_lambda=lam)
tbl, allocs, budget = qo.compare(d, scenario=scen, **PARAMS)
fmonth = d['forecast_month'].iloc[0].strftime('%B %Y')

# ------------------------------------------------------------------ KPI row
k1, k2, k3, k4 = st.columns(4)
obs, exp, hi = (d['Waiting_6plus_Weeks'].sum(), d['forecast_waiting_6plus_expected'].sum(),
                d['forecast_waiting_6plus_high'].sum())
card(k1, f'Observed 6+ wk ({origin})', f'{obs:,.0f}', f'{len(d):,} provider-test units', OBS)
card(k2, f'Expected 6+ wk ({fmonth})', f'{exp:,.0f}', 'Persistence forecast', EXP)
card(k3, 'High-pressure 6+ wk', f'{hi:,.0f}', f'+{(hi - exp) / max(exp, 1) * 100:.1f}% stress allowance', HIGH)
qw = tbl.loc['QueueWise (forecast-informed)']
card(k4, 'QueueWise reduction', f"{qw['Reduction %']:.1f}%",
     f"{qw['Reduction in 6+ wk waits']:,.0f} simulated waits cleared · {budget:,.0f} slots", RED)
st.write('')

tabs = st.tabs(['📈 Forecast', '⚖️ Strategy comparison', '🎯 Recommended allocation',
                '🏥 Provider view', '🔬 Sensitivity', '📘 Method & assumptions'])

# ------------------------------------------------------------------ tab 1: forecast
with tabs[0]:
    c1, c2 = st.columns([3, 2])
    by = (d.groupby('Test')[['Waiting_6plus_Weeks', 'forecast_waiting_6plus_expected',
                             'forecast_waiting_6plus_high']].sum().sort_values('forecast_waiting_6plus_high'))
    fig = go.Figure()
    fig.add_bar(y=by.index, x=by['Waiting_6plus_Weeks'], name=f'Observed ({origin})', orientation='h', marker_color=OBS)
    fig.add_bar(y=by.index, x=by['forecast_waiting_6plus_expected'], name='Expected', orientation='h', marker_color=EXP)
    fig.add_bar(y=by.index, x=by['forecast_waiting_6plus_high'], name='High pressure', orientation='h', marker_color=HIGH)
    fig.update_layout(title=f'Patients waiting 6+ weeks by test, {fmonth}', barmode='group', height=600)
    fig.update_xaxes(tickformat='~s')
    with c1:
        show_plot(fig)

    t = fc[fc['Diagnostic Tests'].isin(sel_tests)]
    if sel_provs:
        t = t[t['Provider'].isin(sel_provs)]
    tr = t.groupby('forecast_month')[['forecast_total_wl_expected', 'forecast_total_wl_high']].sum().reset_index()
    base_total = t[t.horizon_months == 1]['Total WL'].sum()
    xs = [origin_dt] + tr['forecast_month'].tolist()
    fig2 = go.Figure()
    fig2.add_scatter(x=xs, y=[base_total] + tr['forecast_total_wl_expected'].tolist(),
                     name='Expected', mode='lines+markers', line=dict(color=EXP, width=3))
    fig2.add_scatter(x=xs, y=[base_total] + tr['forecast_total_wl_high'].tolist(),
                     name='High pressure', mode='lines+markers', line=dict(color=HIGH, width=3, dash='dash'),
                     fill='tonexty', fillcolor='rgba(244,184,96,.16)')
    fig2.update_layout(title='Total waiting list outlook (patients)', height=600)
    fig2.update_yaxes(tickformat='~s', rangemode='tozero')
    fig2.update_xaxes(tickformat='%b %Y', dtick='M1')
    with c2:
        show_plot(fig2)
    st.markdown('<div class="qw-note"><b>Reading this:</b> the forecast is a <i>stock of patients already '
                'waiting</i>, not new referrals or demand. High pressure = expected plus an empirical '
                '90th-percentile underprediction allowance from validation data. It is a stress scenario, '
                'not a guaranteed 90% interval.</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------ tab 2: comparison
with tabs[1]:
    st.markdown(f'#### Four strategies, {fmonth}, **{"expected" if scen == "expected" else "high-pressure"}** scenario')
    plot_df = tbl.reset_index()
    c1, c2, c3 = st.columns(3)
    for col, metric, title in [(c1, 'Reduction in 6+ wk waits', 'Simulated reduction in 6+ wk waits'),
                               (c2, 'Fairness (Jain index, 0-1)', 'Fairness (Jain index)'),
                               (c3, 'Utilization % (useful slots)', 'Slot utilisation (%)')]:
        f = px.bar(plot_df, x='Strategy', y=metric, color='Strategy', color_discrete_map=STRAT_COLORS,
                   title=title, text_auto=',.3g')
        f.update_layout(showlegend=False, height=400, xaxis_title=None, yaxis_title=None)
        f.update_xaxes(tickangle=-30)
        f.update_traces(textfont_color=TXT, textposition='outside', cliponaxis=False)
        with col:
            show_plot(f)
    show_table(tbl.style.format('{:,.2f}', subset=['Reduction %', 'Utilization % (useful slots)',
                                                   'Units with need served %'])
                        .format('{:,.0f}', subset=['Slots allocated', 'Remaining 6+ wk waits',
                                                   'Reduction in 6+ wk waits', 'Wasted slots'])
                        .format('{:.3f}', subset=['Fairness (Jain index, 0-1)']))
    st.download_button('⬇ Download comparison (CSV)', tbl.to_csv().encode(), 'queuewise_comparison.csv', 'text/csv')
    st.markdown('<div class="qw-warn"><b>Interpretation:</b> under the expected scenario the forecast equals '
                'the current backlog (persistence), so QueueWise and backlog-based allocation behave alike. '
                'QueueWise separates mainly under high pressure, through the uncertainty weight λ. '
                'Both the allocator and the evaluation use the same forecast, so results favour QueueWise '
                'by construction; a backtest on actual June–August 2026 waits is the stronger test.</div>',
                unsafe_allow_html=True)

# ------------------------------------------------------------------ tab 3: allocation
with tabs[2]:
    out = d[['Provider Org Code', 'Provider Org Name', 'Test', 'Waiting_6plus_Weeks',
             'forecast_waiting_6plus_expected', 'forecast_waiting_6plus_high']].copy()
    out.columns = ['Code', 'Provider', 'Diagnostic test', 'Observed 6+ wk', 'Expected 6+ wk', 'High 6+ wk']
    for name, short in [('QueueWise (forecast-informed)', 'QueueWise slots'),
                        ('Current backlog', 'Backlog slots'), ('Equal', 'Equal slots')]:
        out[short] = allocs[name].round(1)
    out['Share of QueueWise budget %'] = (100 * out['QueueWise slots'] / out['QueueWise slots'].sum()).round(2)
    out = out[out['QueueWise slots'] > 0].sort_values('QueueWise slots', ascending=False)

    c1, c2 = st.columns([2, 3])
    with c1:
        bt = out.groupby('Diagnostic test')['QueueWise slots'].sum().sort_values()
        f = px.bar(x=bt.values, y=bt.index, orientation='h', title='QueueWise slots by test',
                   color_discrete_sequence=[EXP])
        f.update_layout(height=500, xaxis_title='Extra slots', yaxis_title=None)
        show_plot(f)
    with c2:
        top = out.head(15).iloc[::-1]
        labels = (top['Provider'].str.slice(0, 32) + ' · ' + top['Diagnostic test'])
        f = px.bar(top, x='QueueWise slots', y=labels, orientation='h', title='Top 15 recommended units',
                   color_discrete_sequence=[OBS])
        f.update_layout(height=500, xaxis_title='Extra slots', yaxis_title=None)
        show_plot(f)
    st.markdown(f'**{len(out):,} units** receive slots (of {len(d):,}). Top 10 units take '
                f'**{out["Share of QueueWise budget %"].head(10).sum():.1f}%** of the budget.')
    show_table(out.head(1000), hide_index=True)
    st.download_button('⬇ Download full allocation (CSV)', out.to_csv(index=False).encode(),
                       'queuewise_allocation.csv', 'text/csv')

# ------------------------------------------------------------------ tab 4: provider view
with tabs[3]:
    prov_pool = sorted(d['Provider'].unique())
    p = st.selectbox('Select provider', prov_pool)
    dp = d[d['Provider'] == p].copy()
    dp['QueueWise slots'] = allocs['QueueWise (forecast-informed)'][dp.index].round(1)
    dp = dp[(dp['Total WL'] > 0) | (dp['forecast_total_wl_expected'] > 0)]
    if dp.empty:
        st.info('This provider has no waiting list in the selected tests.')
    else:
        a, b, c = st.columns(3)
        card(a, 'Total waiting list (Aug)', f"{dp['Total WL'].sum():,.0f}", p, OBS)
        card(b, 'Expected 6+ wk', f"{dp['forecast_waiting_6plus_expected'].sum():,.0f}", fmonth, EXP)
        card(c, 'QueueWise extra slots', f"{dp['QueueWise slots'].sum():,.0f}", 'recommended', RED)
        st.write('')
        m = dp.melt(id_vars='Test', value_vars=['Waiting_6plus_Weeks', 'forecast_waiting_6plus_expected',
                                                  'forecast_waiting_6plus_high'],
                    var_name='Measure', value_name='Patients')
        m['Measure'] = m['Measure'].map({'Waiting_6plus_Weeks': 'Observed', 'forecast_waiting_6plus_expected': 'Expected',
                                         'forecast_waiting_6plus_high': 'High pressure'})
        f = px.bar(m, x='Test', y='Patients', color='Measure', barmode='group',
                   color_discrete_map={'Observed': OBS, 'Expected': EXP, 'High pressure': HIGH},
                   title='Patients waiting 6+ weeks by test')
        f.update_layout(height=440, xaxis_title=None)
        show_plot(f)
        show_table(dp[['Test', 'Total WL', 'Waiting_6plus_Weeks', 'forecast_waiting_6plus_expected',
                       'forecast_waiting_6plus_high', 'QueueWise slots']]
                   .rename(columns={'Waiting_6plus_Weeks': 'Observed 6+ wk',
                                    'forecast_waiting_6plus_expected': 'Expected 6+ wk',
                                    'forecast_waiting_6plus_high': 'High 6+ wk'}), hide_index=True)

# ------------------------------------------------------------------ tab 5: sensitivity
with tabs[4]:
    st.markdown('#### How robust is the QueueWise result to the assumptions?')
    st.caption('Recomputed live for the current scope, horizon and scenario.')

    @st.cache_data(show_spinner='Running sensitivity grid...')
    def sens_grid(df, scenario, cap, lam_):
        rows = []
        for e in [0.3, 0.5, 0.7, 1.0]:
            for b in [5, 10, 15, 20, 30]:
                t_, _, _ = qo.compare(df, scenario, budget_pct=b, cap_pct=cap, eff=e, risk_lambda=lam_)
                q = t_.loc['QueueWise (forecast-informed)']; bl = t_.loc['Current backlog']
                rows.append(dict(eff=e, budget=b, red=q['Reduction %'], fair=q['Fairness (Jain index, 0-1)'],
                                 fair_gap=q['Fairness (Jain index, 0-1)'] - bl['Fairness (Jain index, 0-1)']))
        return pd.DataFrame(rows)

    sg = sens_grid(d, scen, cap_pct, lam)
    c1, c2, c3 = st.columns(3)
    for col, key, title, scale in [(c1, 'red', 'QueueWise reduction (%)', 'Teal'),
                                   (c2, 'fair', 'QueueWise fairness (Jain)', 'Blues'),
                                   (c3, 'fair_gap', 'Fairness edge over backlog', 'RdYlGn')]:
        pv = sg.pivot(index='eff', columns='budget', values=key)
        f = px.imshow(pv, text_auto='.2f', aspect='auto', color_continuous_scale=scale,
                      labels=dict(x='Budget (% of 6+ wk waits)', y='Clearance per slot'), title=title)
        f.update_layout(height=400, coloraxis_showscale=False)
        with col:
            show_plot(f)

    st.markdown('##### Effect of the risk weight λ')
    lrows = []
    for l_ in np.round(np.arange(0, 1.01, 0.25), 2):
        t_, _, _ = qo.compare(d, scen, **dict(PARAMS, risk_lambda=l_))
        q = t_.loc['QueueWise (forecast-informed)']
        lrows.append(dict(lam=l_, Reduction=q['Reduction %'], Fairness=q['Fairness (Jain index, 0-1)']))
    ld = pd.DataFrame(lrows)
    f = go.Figure()
    f.add_scatter(x=ld['lam'], y=ld['Fairness'], name='Fairness (Jain)', line=dict(color=EXP, width=3), mode='lines+markers')
    f.add_scatter(x=ld['lam'], y=ld['Reduction'] / 100, name='Reduction (fraction)', line=dict(color=RED, width=3), mode='lines+markers')
    f.update_layout(height=380, xaxis_title='λ (risk weight)', yaxis_title='Value')
    show_plot(f)

# ------------------------------------------------------------------ tab 6: method
with tabs[5]:
    st.markdown("""
#### Pipeline
**Data** (cleaned NHS DM01 extracts, Sep 2024 – Aug 2026) → **Forecasting** (naive persistence selected on
validation WAPE; Linear Regression and XGBoost as comparisons; 90th-percentile error uplift for the high scenario)
→ **Optimisation and dashboard** (this app).

#### Allocation strategies
| Strategy | Rule |
|---|---|
| No intervention | Baseline, zero extra slots |
| Equal | Budget split evenly across units, capped by unit capacity |
| Current backlog | Proportional to observed 6+ week waits, capped |
| **QueueWise** | Proportional to expected + λ × (high − expected), capped by capacity and plausible need |

#### Simulation formula
Reduction per unit = min(slots × clearance factor, forecast 6+ week waits).
Utilisation = useful slots ÷ allocated slots. Fairness = Jain index of coverage (share of each unit's forecast
need that is met); 1.0 means perfectly equal coverage.

#### Limitations
- The forecast is a **stock of waiting patients**, not referrals or demand.
- The clearance factor is an **assumption**; real reductions depend on eligibility, case mix and referrals.
- Expected values are persistence (the August value carried forward); the high scenario is heuristic,
  not a calibrated 90% interval.
- Forecast error grows with horizon (Total WL WAPE 9.5% at 1 month, 17.7% at 3 months; 6+ weeks 18.4% to 41.1%).
- Evaluation uses the same forecast the allocator uses, so simulated gains are optimistic by construction.
- Months shown are forecasts relative to an **August 2026 cutoff**, not live forecasts.
- Internal reconciliation passed; agreement with published NHS national summaries is not yet established.
""")
