# OpenDSS Distribution Network Analysis

This repository contains an OpenDSS model of the Ponda distribution network (Goa, India), along with Python utilities for feeder execution, EV charger impact analysis, and harmonic studies.

## Project Structure

```
OPENDSS-main/
|
|-- dss/
|   |-- combined_network.dss
|   `-- feeders/
|       |-- Curti_Feeder.dss
|       |-- Farmagudi_Feeder.dss
|       |-- Khadpabandh_Feeder.dss
|       |-- Ponda1_Feeder.dss
|       `-- Undir_Feeder.dss
|
|-- scripts/
|   |-- run_feeder.py
|   |-- EV_Charger_Impact.py
|   `-- EV_Harmonic_Analysis.py
|
|-- output/
|   |-- Combined/
|   |-- Curti/
|   |-- Farmagudi/
|   |-- Khadpabandh/
|   |-- Ponda1/
|   `-- Undir/
|
|-- results/
|   |-- Chargers/
|   `-- Harmonics/
|
`-- docs/
    `-- resources/
```

## OpenDSS Model

The core OpenDSS model represents the 33/11 kV substation and five 11 kV feeders:

- Curti
- Farmagudi
- Khadpabandh
- Ponda1
- Undir

Main model entry points:

- `dss/combined_network.dss` for full-network simulation
- `dss/feeders/*.dss` for feeder-wise simulation

## Current Export Workflow

Export commands inside DSS files are now commented out by default.

Recommended workflow:

1. Run simulations via `scripts/run_feeder.py`.
2. Let the script solve circuits and collect OpenDSS exports.
3. Review generated CSV files under `output/<FeederName>/`.

Default export set for feeder files:

- Voltages
- Losses
- Meters
- Summary
- Capacity

Additional exports for Combined case:

- Currents
- Powers

## Scripts

### `scripts/run_feeder.py`

Runs one, many, or all feeders and writes clean export files to `output/`.

Configuration in script:

- `FEEDERS_TO_RUN = ["all"]` to execute all registered feeders
- or set explicit names, such as `FEEDERS_TO_RUN = ["Curti", "Undir", "Combined"]`

### `scripts/EV_Charger_Impact.py`

Runs EV load-flow impact analysis. The script now validates that `OpenDSSDirect.py` is installed in the active environment before running.

### `scripts/EV_Harmonic_Analysis.py`

Runs harmonic impact studies and writes outputs under `results/Harmonics/`.

## Setup And Run

Install dependencies:

```bash
pip install OpenDSSDirect.py pandas numpy matplotlib
```

Run feeder exports:

```bash
python scripts/run_feeder.py
```

Run EV studies:

```bash
python scripts/EV_Charger_Impact.py
python scripts/EV_Harmonic_Analysis.py
```

## Outputs

- `output/` stores feeder/combined OpenDSS export CSV files from `run_feeder.py`.
- `results/Chargers/` stores EV charger impact study outputs.
- `results/Harmonics/` stores harmonic analysis outputs.

## Reference Standards

- IEEE Std 519-2022 for harmonic limits.
- IS 12360 for voltage regulation limits.
