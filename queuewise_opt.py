import numpy as np, pandas as pd

def load_forecasts(path):
    return pd.read_csv(path, dtype={'Provider Org Code': str}, parse_dates=['forecast_month'])

def waterfill(weights, caps, budget):
    """Distribute budget proportionally to weights, never exceeding caps; leftover is redistributed."""
    w = np.asarray(weights, float); caps = np.asarray(caps, float)
    x = np.zeros_like(w); remaining = float(budget)
    active = (w > 0) & (caps > 0)
    for _ in range(200):
        if remaining < 1e-6 or not active.any():
            break
        share = remaining * w * active / w[active].sum()
        give = np.minimum(share, caps - x) * active
        x += give; remaining -= give.sum()
        active &= (caps - x) > 1e-9
    return x

def allocate(d, budget_pct=10, cap_pct=20, eff=1.0, risk_lambda=0.5):
    """Return dict of allocations (extra slots per provider-service unit) for each strategy."""
    exp6  = d['forecast_waiting_6plus_expected'].values
    high6 = d['forecast_waiting_6plus_high'].values
    cur6  = d['Waiting_6plus_Weeks'].values
    capacity = np.ceil(cap_pct / 100 * np.maximum(d['forecast_total_wl_expected'].values,
                                                  d['Total WL'].values))
    budget = budget_pct / 100 * exp6.sum()
    score = exp6 + risk_lambda * (high6 - exp6)            # risk-weighted forecast need

    equal   = waterfill(np.ones(len(d)), capacity, budget)
    backlog = waterfill(cur6, np.minimum(capacity, np.ceil(cur6 / eff)), budget)
    queuew  = waterfill(score, np.minimum(capacity, np.ceil(high6 / eff)), budget)
    return {'Equal': equal, 'Current backlog': backlog, 'QueueWise (forecast-informed)': queuew,
            'No intervention': np.zeros(len(d))}, budget

def evaluate(d, x, scenario='expected', eff=1.0):
    need = d[f'forecast_waiting_6plus_{scenario}'].values
    reduced = np.minimum(eff * x, need)
    pos = need > 0
    cov = reduced[pos] / need[pos]
    jain = (cov.sum() ** 2) / (len(cov) * (cov ** 2).sum()) if (cov ** 2).sum() > 0 else 0.0
    slots = x.sum()
    return {
        'Slots allocated': round(slots),
        'Remaining 6+ wk waits': round(need.sum() - reduced.sum()),
        'Reduction in 6+ wk waits': round(reduced.sum()),
        'Reduction %': round(100 * reduced.sum() / need.sum(), 2) if need.sum() else 0,
        'Utilization % (useful slots)': round(100 * (reduced.sum() / eff) / slots, 2) if slots > 0 else 0,
        'Units with need served %': round(100 * (cov > 0).mean(), 2) if len(cov) else 0,
        'Fairness (Jain index, 0-1)': round(jain, 3),
        'Wasted slots': round(max(slots - reduced.sum() / eff, 0)),
    }

def compare(d, scenario='expected', **kw):
    eff = kw.get('eff', 1.0)
    allocs, budget = allocate(d, **kw)
    rows = []
    for name, x in allocs.items():
        r = evaluate(d, x, scenario, eff); r['Strategy'] = name; rows.append(r)
    return pd.DataFrame(rows).set_index('Strategy'), allocs, budget
