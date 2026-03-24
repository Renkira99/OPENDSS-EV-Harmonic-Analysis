# OpenDSS Distribution Network Analysis

A power systems simulation project modelling the Ponda distribution network (Goa, India) using [OpenDSS](https://www.epri.com/pages/sa/opendss). The project includes a combined multi-feeder network model and two Python analysis scripts for studying the impact of EV charger deployment on the grid.

---

## Project Structure

```
OPENDSS-main/
│
├── dss/                          # OpenDSS circuit model files
│   ├── combined_network.dss      # Full combined network (all feeders merged — use this for analysis)
│   └── feeders/                  # Individual feeder models
│       ├── Curti_Feeder.dss
│       ├── Farmagudi_Feeder.dss
│       ├── Khadpabandh_Feeder.dss
│       └── Ponda1_Feeder.dss
│
├── scripts/                      # Python analysis scripts
│   ├── EV_Charger_Impact.py      # Load flow analysis with EV charger penetration
│   └── EV_Harmonic_Analysis.py   # Harmonic distortion analysis for EV chargers
│
├── docs/
│   └── resources/                # Reference documents
│       ├── Curti-Farmagudi_Presentation.pdf
│       ├── Feeder_Status_Kavale.xlsx
│       ├── Network_Diagram.pdf
│       └── OpenDSS_Formula_Calculator.xlsx
│
└── results/                      # Auto-generated output (created at runtime, not in repo)
    ├── Chargers/                 # Output from EV_Charger_Impact.py
    └── Harmonics/                # Output from EV_Harmonic_Analysis.py
```

---

## Network Model

The distribution network models the **Ponda 33/11 kV substation** area in Goa, India. It contains four 11 kV feeders combined into a single OpenDSS circuit file:

| Feeder | File | Description |
|--------|------|-------------|
| Curti | `feeders/Curti_Feeder.dss` | Curti area residential/commercial loads |
| Farmagudi | `feeders/Farmagudi_Feeder.dss` | Farmagudi area loads |
| Khadpabandh | `feeders/Khadpabandh_Feeder.dss` | Khadpabandh area loads |
| Ponda 1 | `feeders/Ponda1_Feeder.dss` | Ponda town centre loads |
| **Combined** | `combined_network.dss` | **All feeders merged — use this for simulation** |

The combined network includes the substation voltage source, all 11 kV overhead lines, distribution transformers (11 kV / 0.415 kV), and consumer loads.

---

## Analysis Scripts

### 1. `EV_Charger_Impact.py` — Load Flow Analysis

Analyses the impact of adding EV chargers to a configurable percentage of distribution transformers.

**What it does:**
- Runs a 24-hour daily load flow (base case — no EV chargers)
- Randomly selects a percentage of transformers and attaches EV charger loads
- Re-runs the daily simulation with EV chargers active
- Compares voltage profiles, system losses, and transformer loading
- Saves plots and CSV reports to `results/Chargers/`

**Key configuration (top of script):**
```python
EV_CHARGER_KW = 60          # Rating of each EV charger in kW
EV_CHARGER_PF = 0.95        # Power factor
PERCENTAGE_TRANSFORMERS = 10 # % of transformers to install chargers on
RANDOM_SEED = 42             # For reproducibility
```

**Run:**
```bash
python scripts/EV_Charger_Impact.py
```

**Outputs** (saved to `results/Chargers/EV_Impact__<kw>kw_<pct>%/`):
- `EV_Charger_Impact_Analysis.png` — voltage histograms and system metric comparison
- `Transformer_Loading_Comparison.png` — per-transformer loading bar chart
- `EV_Charger_Locations.csv` — which transformers received chargers
- `Voltage_Comparison.csv` — per-bus voltage before and after
- `EV_Impact_Summary.csv` — high-level summary metrics

---

### 2. `EV_Harmonic_Analysis.py` — Harmonic Distortion Analysis

Models the harmonic current injection from EV charger power electronics and analyses Total Harmonic Distortion (THD) across the network against IEEE 519-2022 limits.

**What it does:**
- Defines a harmonic current spectrum for EV chargers (6-pulse or 12-pulse rectifier topology)
- Runs a fundamental + harmonic power flow in OpenDSS
- Estimates per-bus voltage THD using analytical impedance scaling
- Flags buses exceeding IEEE 519-2022 limits
- Saves plots and CSV reports to `results/Harmonics/`

**Key configuration (top of script):**
```python
EV_CHARGER_KW = 60
CHARGER_TOPOLOGY = "6-pulse"   # "6-pulse" or "12-pulse"
PERCENTAGE_TRANSFORMERS = 10
IEEE_519_THD_LIMIT = 5.0       # % — voltage THD compliance limit
IEEE_519_INDIVIDUAL_LIMIT = 3.0 # % — per-harmonic limit
```

**Run:**
```bash
python scripts/EV_Harmonic_Analysis.py
```

**Outputs** (saved to `results/Harmonics/EV_Harmonics_<topology>_<kw>kw_<pct>pct/`):
- `EV_Harmonic_Impact.png` — THD distribution, spectrum bar chart, and boxplot
- `Individual_Harmonic_Distortion.png` — per-harmonic distortion at worst bus
- `Bus_THD_Comparison.csv` — per-bus THD before and after
- `EV_Harmonic_Spectrum.csv` — harmonic spectrum reference data
- `Harmonic_Impact_Summary.csv` — summary metrics

---

## Requirements

### Python Dependencies

```bash
pip install opendssdirect[extras] pandas numpy matplotlib
```

| Package | Purpose |
|---------|---------|
| `opendssdirect` | Python interface to OpenDSS engine |
| `pandas` | CSV data export |
| `numpy` | Numerical computations |
| `matplotlib` | Plot generation |

### OpenDSS

The scripts use `opendssdirect` which bundles OpenDSS — no separate OpenDSS installation is required.

---

## Usage

1. **Clone the repo** and install dependencies (see above).
2. **Run a script** from the project root:
   ```bash
   cd OPENDSS-main
   python scripts/EV_Charger_Impact.py
   ```
3. **Adjust parameters** at the top of the script file — no command-line arguments needed.
4. **Find results** in the auto-created `results/` folder.

> **Note:** The `results/` directory is created automatically at runtime. It should not be committed to version control.

---

## Reference Standards

- **IEEE Std 519-2022** — *Standard for Harmonic Control in Electric Power Systems* (THD limits used in `EV_Harmonic_Analysis.py`)
- **IS 12360** — Indian voltage regulation limits (0.95–1.05 p.u. band used in `EV_Charger_Impact.py`)
