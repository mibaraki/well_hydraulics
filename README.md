# Theis Groundwater Calculator

A multi-page Streamlit app for confined aquifer drawdown analysis based on the
**Theis (1935)** equation and its extensions.

## Pages

| Page | Type | Description |
|---|---|---|
| Home | Landing | App overview and assumptions |
| 1 Theory | Theory | Theis equation, W(u), method of images |
| 2 Single Well | Calculator | Standard Theis drawdown |
| 3 Multiple Wells | Calculator | Superposition of multiple wells |
| 4 River Boundary | Calculator | Constant-head boundary (injection image well) |
| 5 No-Flow Barrier | Calculator | No-flow boundary (pumping image well) |
| 6 Partial Penetration Theory | Theory | Hantush (1961), W(u,β), K₀ |
| 7 Partial Penetration | Calculator | Hantush (1961) full transient solution |
| 8 Parameter Estimation | Calculator | Least-squares T and S fitting |

## Installation

```bash
pip install -r requirements.txt
```

## Running

```bash
streamlit run Home.py
```

## Data Upload Format

All calculator pages accept two-column CSV/TXT files:

```
# time (min), drawdown (m)
10,  0.12
30,  0.45
60,  0.78
```

## Project Structure

```
theis_app/
├── Home.py
├── requirements.txt
├── README.md
├── pages/
│   ├── 1_Theory.py
│   ├── 2_Single_Well.py
│   ├── 3_Multiple_Wells.py
│   ├── 4_River_Boundary.py
│   ├── 5_NoFlow_Barrier.py
│   ├── 6_Partial_Penetration_Theory.py
│   ├── 7_Partial_Penetration.py
│   └── 8_Parameter_Estimation.py
└── utils/
    ├── __init__.py
    ├── theis.py        ← core math (shared by all pages)
    └── plotting.py     ← shared Plotly chart builders and Streamlit widgets
```

## References

- Theis, C.V. (1935). The relation between the lowering of the piezometric surface
  and the rate and duration of discharge of a well using ground-water storage.
  *Transactions AGU*, 16, 519–524.
- Hantush, M.S. (1961). Aquifer tests on partially penetrating wells.
  *Journal of the Hydraulics Division*, ASCE, 87(5), 171–195.
- Kruseman, G.P. and de Ridder, N.A. (1994).
  *Analysis and Evaluation of Pumping Test Data* (2nd ed.). ILRI Publication 47.
