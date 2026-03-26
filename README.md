# OpenDSS Distribution Network Analysis

OpenDSS model of the Ponda 33/11 kV distribution network (Goa, India), with Python utilities for feeder execution, EV charger impact analysis, and harmonic studies.

---

## Project Structure

```
OPENDSS-main/
├── dss/
│   ├── combined_network.dss          # Full 5-feeder combined model
│   └── feeders/
│       ├── Curti_Feeder.dss
│       ├── Farmagudi_Feeder.dss
│       ├── Khadpabandh_Feeder.dss
│       ├── Ponda1_Feeder.dss
│       └── Undir_Feeder.dss
│
├── scripts/
│   ├── run_feeder.py                 # Main feeder runner + plot generator
│   ├── EV_Charger_Impact.py          # EV charger load-flow impact study
│   └── EV_Harmonic_Analysis.py       # EV harmonic injection study
│
├── output/
│   └── <FeederName>/                 # One folder per feeder + Combined
│       ├── csv/
│       │   ├── Voltages.csv
│       │   ├── Losses.csv
│       │   ├── Meters.csv
│       │   ├── Summary.csv
│       │   └── Capacity.csv
│       └── plots/
│           ├── Voltage_Profile.png
│           ├── Voltage_Profile_Interactive.html
│           ├── Line_Loading.png
│           ├── Losses_Breakdown.png
│           └── Voltage_Histogram.png
│
├── docs/
│   ├── curti_feeder_dss/             # Full update documentation for Curti
│   │   ├── README.md                 # Methodology, derivations, validation
│   │   ├── inputs/
│   │   │   ├── linecode_inputs.json
│   │   │   ├── transformer_loss_inputs.json
│   │   │   ├── transformer_derived_parameters.csv
│   │   │   ├── line_assignments.csv
│   │   │   └── transformer_assignments.csv
│   │   └── results/
│   │       ├── baseline/             # Pre-update simulation outputs
│   │       ├── updated/              # Post-update simulation outputs
│   │       ├── comparison_metrics.csv
│   │       └── summary.json
│   └── resources/
│       ├── Data_Table/               # Feeder data tables and line tables
│       ├── Single Line Diagram/
│       ├── Opendss_Sample_Profile.png
│       ├── Network_Diagram.pdf
│       └── OpenDSS_Formula_Calculator.xlsx
│
├── results/
│   ├── Chargers/                     # EV charger impact study outputs
│   └── Harmonics/                    # Harmonic analysis outputs
│
└── error_mkd/
    ├── curti_feeder_errors.md
    └── farmagudi_feeder_errors.md
```

---

## OpenDSS Model

The model represents the **Ponda 33/11 kV substation** and five 11 kV feeders:

| Feeder | DSS File |
|---|---|
| Curti | `dss/feeders/Curti_Feeder.dss` |
| Farmagudi | `dss/feeders/Farmagudi_Feeder.dss` |
| Khadpabandh | `dss/feeders/Khadpabandh_Feeder.dss` |
| Ponda1 | `dss/feeders/Ponda1_Feeder.dss` |
| Undir | `dss/feeders/Undir_Feeder.dss` |
| All five combined | `dss/combined_network.dss` |

Each feeder models 11 kV trunk lines, 11/0.415 kV distribution transformers, and LV buses. Export commands inside DSS files are commented out — all exports are managed by `scripts/run_feeder.py`.

---

## Curti Feeder Update

The Curti feeder DSS file was substantially revised to use physically-derived, standards-compliant parameters. Full documentation is in `docs/curti_feeder_dss/README.md`.

### What changed

**Line/cable parameters** — Replaced generic R/X values with IS 7098 hardcoded cable standards:

| Linecode | Application | r1 (Ω/km) | x1 (Ω/km) | normamps (A) |
|---|---|---:|---:|---:|
| `IS7098_240SQ_TRUNK` | Trunk lines (9 segments) | 0.125 | 0.088 | 300 |
| `IS7098_95SQ_MEDIUM` | Medium taps (7 segments) | 0.320 | 0.100 | 180 |
| `IS7098_35SQ_SMALL` | Small taps (21 segments) | 0.868 | 0.115 | 100 |

**Transformer loss parameters** — Replaced `%Rs` with physically-derived `%LoadLoss`/`%NoLoadLoss` per IS 1180 standards:

| kVA | %LoadLoss | %NoLoadLoss | Xhl |
|---:|---:|---:|---:|
| 100 | 1.220 | 0.130 | 4.663 |
| 160 | 0.942 | 0.121 | 4.758 |
| 200 | 1.013 | 0.137 | 4.589 |
| 400 | 0.677 | 0.156 | 4.873 |
| 500 | 0.691 | 0.129 | 4.750 |
| 1000 | 0.657 | 0.113 | 4.654 |
| 1250 | 0.629 | 0.107 | 4.759 |

**Source stiffness** — Set to `MVAsc3=400` with `MVAsc1` omitted to avoid unverified zero-sequence assumptions.

### Validation results (baseline vs updated)

| Metric | Baseline | Updated | Delta |
|---|---:|---:|---:|
| Max pu Voltage | 0.9984 | 0.9922 | −0.0062 |
| Min pu Voltage | 0.9543 | 0.9560 | +0.0017 |
| Total Losses (kW) | 134.47 | 65.98 | −68.49 |
| Loss % | 3.09% | 1.54% | −1.55% |
| Transformer loss share | 81.9% | 58.5% | −23.4% |
| Line overloads | 0 | 0 | 0 |

Fault current at `COLONY_SS` (expected from MVAsc3=400: **20 994.56 A**) → simulated: **20 981.99 A** ✓

---

## Scripts

### `scripts/run_feeder.py`

Compiles, solves, and exports results for one or all feeders. Configure at the top of the file:

```python
FEEDERS_TO_RUN = ["all"]
# or specific feeders:
FEEDERS_TO_RUN = ["Curti", "Undir", "Combined"]
```

**Exports produced per feeder:**

| File | Contents |
|---|---|
| `csv/Voltages.csv` | Per-bus voltage magnitude, angle, and pu |
| `csv/Losses.csv` | Per-element active and reactive losses |
| `csv/Meters.csv` | Energy meter readings |
| `csv/Summary.csv` | Circuit-level summary (kW, kvar, losses) |
| `csv/Capacity.csv` | Line/transformer loading as % of normal rating |
| `csv/Currents.csv` | Per-element currents *(Combined only)* |
| `csv/Powers.csv` | Per-element active and reactive power *(Combined only)* |

**Plots produced per feeder:**

| Plot | Description |
|---|---|
| `Voltage_Profile.png` | Per-unit voltage vs. electrical distance from substation. Blue dots = 11 kV buses, orange triangles = 0.415 kV buses. Red dashed lines at ANSI ±5% limits. |
| `Voltage_Profile_Interactive.html` | Interactive version — click buses to inspect name, voltage, distance, and connected nodes; click line segments for voltage drop and loading; toggle to show ANSI violations only. |
| `Line_Loading.png` | Horizontal bar chart of each line's % normal ampacity. Bars coloured blue (< 80%), orange (80–100%), red (> 100%). |
| `Losses_Breakdown.png` | Pie chart (lines vs transformers) + top-10 elements by total losses (kW). |
| `Voltage_Histogram.png` | Distribution of all bus per-unit voltages with ANSI limit markers. |
| `Power_Flow.png` | Top-15 elements by active power at Terminal 1 *(Combined only)*. |

Run:

```bash
python scripts/run_feeder.py
```

---

### `scripts/EV_Charger_Impact.py`

Analyses the load-flow impact of adding EV chargers to a configurable percentage of distribution transformers in the combined feeder.

Key configuration at the top of the script:

```python
EV_CHARGER_KW = 60            # kW rating per charger
EV_CHARGER_PF = 0.95          # Power factor
PERCENTAGE_TRANSFORMERS = 10  # % of transformers to receive a charger
```

The script runs a base case, adds EV loads at randomly selected transformers, re-solves, and compares voltage profiles and line loading before/after. Outputs are saved to `results/Chargers/`.

Run:

```bash
python scripts/EV_Charger_Impact.py
```

---

### `scripts/EV_Harmonic_Analysis.py`

Models harmonic current injection from EV chargers using two rectifier topologies:

- **6-pulse** (typical Level 2 AC charger)
- **12-pulse** (typical DC fast charger)

Harmonic spectra are based on IEEE 519-2022 limits and published EV charger measurements. The script runs harmonic power flow, computes THD at each bus, and flags buses exceeding IEEE 519 voltage distortion limits. Outputs are saved to `results/Harmonics/`.

Run:

```bash
python scripts/EV_Harmonic_Analysis.py
```

---

## Setup

```bash
pip install OpenDSSDirect.py pandas numpy matplotlib plotly
```

A `.venv` virtual environment is included in the repository root. Activate it with:

```bash
source .venv/bin/activate   # macOS/Linux
.venv\Scripts\activate      # Windows
```

---

## Reference Standards

| Standard | Application |
|---|---|
| **IS 7098** | XLPE cable r1/x1/c1 parameters (11 kV) |
| **IS 1180** | Distribution transformer no-load and load loss limits |
| **IEEE 519-2022** | Harmonic voltage and current distortion limits |
| **IS 12360** | Voltage regulation limits for distribution networks |
| **ANSI C84.1** | Service voltage range (0.95–1.05 pu used in plots) |
