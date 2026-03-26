# Curti Feeder DSS Update Documentation

This folder documents all updates applied to `dss/feeders/Curti_Feeder.dss`, including the exact input data used, derivation math, implementation choices, and validation outputs.

## 1) Scope and objective

- Replace generic transformer resistance modeling (`%Rs`) with physically-derived `%LoadLoss/%NoLoadLoss` by rating class.
- Use hardcoded IS 7098 cable standards for trunk/medium/small taps with `r1/x1/c1/normamps` in linecodes.
- Set source stiffness to `MVAsc3=400` and remove `MVAsc1` assumption.
- Validate convergence, voltages, losses, overloads, and source fault current consistency.

## 2) Data provenance (how the "correct data" was obtained)

All numeric input data below came from explicit user-provided hardcoded standards in this session (not web-scraped values):

### 2.1 Line/cable standards used (IS 7098 hardcoded)

| Linecode | Type | r1 (ohm/km) | x1 (ohm/km) | c1 (nF/km) | normamps (A) |
|---|---:|---:|---:|---:|---:|
| `IS7098_240SQ_TRUNK` | Trunk (240 sq mm) | 0.125 | 0.088 | 340 | 300 |
| `IS7098_95SQ_MEDIUM` | Medium Tap (95 sq mm) | 0.320 | 0.100 | 250 | 180 |
| `IS7098_35SQ_SMALL` | Small Tap (35 sq mm) | 0.868 | 0.115 | 180 | 100 |

### 2.2 Transformer loss standards used (IS 1180 hardcoded)

| kVA | P50 (W) | P100 (W) |
|---:|---:|---:|
| 100 | 435 | 1350 |
| 160 | 570 | 1700 |
| 200 | 780 | 2300 |
| 400 | 1300 | 3330 |
| 500 | 1510 | 4100 |
| 1000 | 2770 | 7700 |
| 1250 | 3300 | 9200 |

## 3) Derivation method

For each transformer rating, the following equations were solved:

- `Pcore + 0.25*Pcu = P50`
- `Pcore + 1.00*Pcu = P100`
- `Pcu = (P100 - P50)/0.75`
- `Pcore = P100 - Pcu`
- `%LoadLoss = 100*Pcu/(kVA*1000)`
- `%NoLoadLoss = 100*Pcore/(kVA*1000)`

To keep reactance consistent with established rating-class impedance targets in Curti (`%Z`), `Xhl` was computed as:

- `Xhl = sqrt(%Z^2 - (%LoadLoss)^2)`

| kVA | %LoadLoss | %NoLoadLoss | %Z target | Xhl |
|---:|---:|---:|---:|---:|
| 100 | 1.220000 | 0.130000 | 4.820 | 4.663046 |
| 160 | 0.941667 | 0.120833 | 4.850 | 4.757706 |
| 200 | 1.013333 | 0.136667 | 4.700 | 4.589461 |
| 400 | 0.676667 | 0.155833 | 4.920 | 4.873246 |
| 500 | 0.690667 | 0.129333 | 4.800 | 4.750050 |
| 1000 | 0.657333 | 0.112667 | 4.700 | 4.653806 |
| 1250 | 0.629333 | 0.106667 | 4.800 | 4.758565 |

## 4) Implementation details applied to `Curti_Feeder.dss`

- Source declaration now uses: `New Circuit.Curti_Feeder basekv=11 bus1=Colony_SS pu=1.0 MVAsc3=400`
- `MVAsc1` was intentionally omitted to avoid introducing an unverified zero-sequence assumption.
- All 37 line objects were migrated to linecode-based definitions.
- All 23 transformer objects were migrated from `%Rs` to `%LoadLoss/%NoLoadLoss` + computed `Xhl`.

### 4.1 Linecode assignment by line segment

- `IS7098_240SQ_TRUNK` (9 lines): L1, L2, L3, L4, L5, L19, L29, L32, S01
- `IS7098_35SQ_SMALL` (21 lines): L6, L7, L8, L9, L10, L11, L13, L14, L15, L16, L17, L18, L21, L22, L23, L25, L26, L27, L28, L33, L36
- `IS7098_95SQ_MEDIUM` (7 lines): L12, L20, L24, L30, L31, L34, L37

## 5) Validation workflow

For both baseline (HEAD version) and updated feeder:

1. Compile + solve (`Snapshot`).
2. Export `Summary`, `Losses`, `Capacity`, `Voltages` CSVs.
3. Compute KPIs: min/max voltage, LV floor, losses, overload count.
4. Run `FaultStudy` at `COLONY_SS`; compare `Isc` with expected value from `MVAsc3=400`.

## 6) Results (before vs after)

| Metric | Baseline | Updated | Delta |
|---|---:|---:|---:|
| MaxPuVoltage | 0.998400 | 0.992200 | -0.006200 |
| MinPuVoltage | 0.954260 | 0.955950 | 0.001690 |
| lv_min_pu | 0.954260 | 0.955950 | 0.001690 |
| MWLosses | 0.134466 | 0.065979 | -0.068487 |
| pctLosses | 3.090000 | 1.540000 | -1.550000 |
| line_losses_W | 24309.203 | 27356.971 | 3047.768 |
| transformer_losses_W | 110156.461 | 38622.021 | -71534.441 |
| total_losses_W | 134465.664 | 65978.991 | -68486.673 |
| transformer_loss_share_pct | 81.922 | 58.537 | -23.385 |
| line_overload_count | 0 | 0 | 0 |

- Expected source fault current from `MVAsc3=400`: **20994.56 A**
- Updated fault-study source current at `COLONY_SS` (phase A/B/C): **20981.99 / 20981.99 / 20981.99 A**

## 7) Artifact index

- `inputs/linecode_inputs.json`
- `inputs/transformer_loss_inputs.json`
- `inputs/transformer_derived_parameters.csv`
- `inputs/line_assignments.csv`
- `inputs/transformer_assignments.csv`
- `results/baseline/*.csv`
- `results/updated/*.csv`
- `results/comparison_metrics.csv`
- `results/summary.json`
- `thesis_methodology_paragraph.txt` (ready-to-paste thesis wording)

This directory is dedicated to Curti feeder documentation only.
