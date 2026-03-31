# utils/theis.py
# Core Theis groundwater mathematics shared by all pages

import numpy as np
from scipy.special import exp1
from scipy.integrate import quad


def well_function(u):
    """Theis well function W(u) = E1(u)."""
    return exp1(u)


def calc_drawdown(times, T, S, r, Q):
    """
    Standard Theis drawdown at a single observation point.

    Parameters
    ----------
    times : array-like  times in minutes
    T     : float       transmissivity (m²/day)
    S     : float       storativity
    r     : float       distance from pumping well to observation point (m)
    Q     : float       pumping rate (m³/day)

    Returns
    -------
    np.ndarray : drawdown at each time (m)
    """
    times = np.asarray(times, dtype=float)
    drawdown = np.zeros_like(times)
    for i, time in enumerate(times):
        t = time / 1440.0  # minutes to days
        u = r ** 2 * S / (4.0 * T * t)
        drawdown[i] = Q / (4.0 * np.pi * T) * well_function(u)
    return drawdown


def hantush_W(u, beta):
    """
    Hantush well function W(u, beta).

    W(u, β) = ∫_u^∞ (1/t) exp(-t - β²/4t) dt

    Parameters
    ----------
    u    : float  Theis parameter u = r²S/4Tt
    beta : float  β = nπr/b

    Returns
    -------
    float : value of Hantush well function

    Notes
    -----
    - When β → 0 reduces to Theis W(u) = E1(u)
    - When u → 0 reduces to 2K0(β)
    """
    if u <= 0 or beta < 0:
        return 0.0
    result, _ = quad(
        lambda t: np.exp(-t - beta ** 2 / (4.0 * t)) / t,
        u, np.inf,
        limit=100
    )
    return result


def calc_drawdown_partial(times, T, S, r, Q, b, l, d, z, n_terms=20):
    """
    Hantush (1961) partial penetration — full transient solution using W(u, nπr/b).

    Parameters
    ----------
    times  : array-like  times in minutes
    T      : float       transmissivity (m²/day)
    S      : float       storativity
    r      : float       distance from well to observation point (m)
    Q      : float       pumping rate (m³/day)
    b      : float       total aquifer thickness (m)
    l      : float       depth to top of well screen (m)
    d      : float       depth to bottom of well screen (m)
    z      : float       depth of observation point (m)
    n_terms: int         number of Fourier series terms

    Returns
    -------
    np.ndarray : drawdown at each time (m)
    """
    times = np.asarray(times, dtype=float)
    drawdown = np.zeros_like(times)

    for i, time in enumerate(times):
        t = time / 1440.0
        u = r ** 2 * S / (4.0 * T * t)

        # Standard Theis term
        s_theis = Q / (4.0 * np.pi * T) * exp1(u)

        # Partial penetration correction — Fourier series
        correction = 0.0
        for n in range(1, n_terms + 1):
            beta = n * np.pi * r / b
            fn = np.sin(n * np.pi * d / b) - np.sin(n * np.pi * l / b)
            gn = np.cos(n * np.pi * z / b)
            wu_beta = hantush_W(u, beta)
            term = (1.0 / n) * fn * gn * wu_beta
            correction += term
            # Early termination if series converges
            if abs(term) < 1e-8 * abs(correction + 1e-30):
                break

        correction *= (Q / (2.0 * np.pi ** 2 * T)) * (b / (d - l))
        drawdown[i] = s_theis + correction

    return drawdown


def compute_image_distance(r, theta_deg, a):
    """
    Compute radial distance from image well to observation point.

    Setup
    -----
    - Pumping well at origin (0, 0)
    - Boundary at x = a (river or barrier)
    - Image well at x = 2a, y = 0
    - Observation point at (r·cosθ, r·sinθ)

    Parameters
    ----------
    r         : float  radial distance from pump to obs point (m)
    theta_deg : float  angle (degrees) — angle between pump-to-obs line and x-axis
    a         : float  distance from pumping well to boundary (m)

    Returns
    -------
    r_image : float  radial distance from image well to obs point (m)
    x_obs   : float  x-coordinate of observation point (for validity check)
    """
    theta = np.radians(theta_deg)
    x_obs = r * np.cos(theta)
    y_obs = r * np.sin(theta)
    x_image = 2.0 * a
    y_image = 0.0
    r_image = np.sqrt((x_obs - x_image) ** 2 + (y_obs - y_image) ** 2)
    return r_image, x_obs, y_obs


def calc_drawdown_river(times, T, S, r, theta_deg, a, Q):
    """
    Theis with constant-head river boundary (method of images).
    Image well is an injection well (-Q).

    Drawdown is less than standard Theis at late time.
    """
    r_image, x_obs, y_obs = compute_image_distance(r, theta_deg, a)
    s_pump = calc_drawdown(times, T, S, r, Q)
    s_image = calc_drawdown(times, T, S, r_image, -Q)
    return s_pump + s_image, r_image, x_obs, y_obs


def calc_drawdown_barrier(times, T, S, r, theta_deg, a, Q):
    """
    Theis with no-flow barrier (method of images).
    Image well is a pumping well (+Q).

    Drawdown is greater than standard Theis at late time.
    """
    r_image, x_obs, y_obs = compute_image_distance(r, theta_deg, a)
    s_pump = calc_drawdown(times, T, S, r, Q)
    s_image = calc_drawdown(times, T, S, r_image, Q)
    return s_pump + s_image, r_image, x_obs, y_obs
