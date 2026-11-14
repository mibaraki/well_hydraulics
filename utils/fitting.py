# utils/fitting.py
# Theis curve fitting for T and S (no Streamlit dependency, so it can be tested alone)

import numpy as np
from scipy.optimize import least_squares
from scipy.special import exp1

LOG_T_BOUNDS = (-2.0, 4.0)   # T: 0.01 to 10,000 m²/day
LOG_S_BOUNDS = (-7.0, 0.0)   # S: 1e-7 to 1


def theis_vec(t_min, T, S, r, Q):
    """Vectorised Theis drawdown (m). t in minutes, T in m²/day, Q in m³/day."""
    t_day = np.asarray(t_min, dtype=float) / 1440.0
    u = r ** 2 * S / (4.0 * T * t_day)
    return Q / (4.0 * np.pi * T) * exp1(u)


def fit_theis(t_min, s_obs, r, Q, use_log=True, start=(2.0, -4.0), multi_start=True):
    """
    Least-squares fit of T and S to measured drawdown.

    Parameters
    ----------
    t_min, s_obs : arrays of time (min) and drawdown (m); drawdown must be > 0
    r, Q         : distance (m) and pumping rate (m³/day), held fixed
    use_log      : True  -> misfit is log10(model) - log10(data): every point has
                            equal relative weight (what you judge on a log-log plot)
                   False -> misfit is model - data in metres: large late-time
                            drawdowns dominate the fit
    start        : (log10 T, log10 S) first starting point
    multi_start  : also try a grid of other starting points; keep the best

    Returns
    -------
    dict with T (m²/day), S, sigma_logT, sigma_logS (1-sigma, in log10 units),
    corr (correlation between log T and log S), rms_m, rms_log, n, at_bound
    or None if every start failed.
    """
    t = np.asarray(t_min, dtype=float)
    s = np.asarray(s_obs, dtype=float)
    lo = [LOG_T_BOUNDS[0], LOG_S_BOUNDS[0]]
    hi = [LOG_T_BOUNDS[1], LOG_S_BOUNDS[1]]

    def resid(x):
        m = theis_vec(t, 10.0 ** x[0], 10.0 ** x[1], r, Q)
        if use_log:
            return np.log10(np.maximum(m, 1e-300)) - np.log10(s)
        return m - s

    starts = [tuple(np.clip(start, lo, hi))]
    if multi_start:
        starts += [(a, b) for a in (-1.0, 0.0, 1.0, 2.0, 3.0)
                          for b in (-5.0, -4.0, -3.0, -2.0, -1.0)]

    best = None
    for x0 in starts:
        try:
            res = least_squares(resid, x0, bounds=(lo, hi))
        except Exception:
            continue
        if best is None or res.cost < best.cost:
            best = res
    if best is None:
        return None

    # 1-sigma uncertainty and T-S correlation from the Jacobian
    dof = max(len(t) - 2, 1)
    s2 = 2.0 * best.cost / dof
    try:
        cov = np.linalg.inv(best.jac.T @ best.jac) * s2
        sig = np.sqrt(np.diag(cov))
        corr = float(cov[0, 1] / (sig[0] * sig[1]))
    except (np.linalg.LinAlgError, FloatingPointError, ValueError):
        sig = np.array([np.nan, np.nan])
        corr = float("nan")

    T_fit, S_fit = 10.0 ** best.x[0], 10.0 ** best.x[1]
    m = theis_vec(t, T_fit, S_fit, r, Q)
    return {
        "T": T_fit,
        "S": S_fit,
        "sigma_logT": float(sig[0]),
        "sigma_logS": float(sig[1]),
        "corr": corr,
        "rms_m": float(np.sqrt(np.mean((m - s) ** 2))),
        "rms_log": float(np.sqrt(np.mean((np.log10(np.maximum(m, 1e-300)) - np.log10(s)) ** 2))),
        "n": int(len(t)),
        "at_bound": bool(np.any(np.isclose(best.x, lo, atol=1e-6) | np.isclose(best.x, hi, atol=1e-6))),
    }
