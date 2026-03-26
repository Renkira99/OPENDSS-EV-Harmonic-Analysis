# Curti_Feeder.dss — Verified Error & Calculation Audit (Updated)

**Last validated against:**
- `dss/feeders/Curti_Feeder.dss`
- `docs/resources/Single Line Digram/Curti_Feeder_pg1.png`
- `docs/resources/Single Line Digram/Curti_Feeder_pg2.png`
- `docs/resources/Data_Table/Curti_Feeder_Table.png`
- `docs/resources/Data_Table/Line Table.png`

---

## 1) Topology and naming status

### 1.1 SO2–SO6 section names
- **Status:** Not modeled as named DSS lines.
- **Decision:** **Accepted / Not an error** per user clarification (decorative labels only).
- **Note:** Physical feeder connectivity is represented through `L*` lines.

### 1.2 Microwave corridor connectivity
- **Status:** **Fixed**
- `L17` now correctly starts from `3_Way_Microwave` toward Verekar branch.
- Duplicate microwave segment `L35` removed.
- No duplicate bus-pair lines remain.

### 1.3 Doctor–Copperwada path length
- **Status:** **Fixed**
- `Doctor_bakale -> 3_Way_Copperwada_1` modeled as `1.32 km` (`L34`), matching SLD length reference.

---

## 2) Transformer and load mapping status

### 2.1 Transformer capacities (DTC capacity)
- **Status:** **Fixed**
- `Kayji_Garden` transformer modeled as `200 kVA` (`T3`).
- `Kayji_Skyline` transformer modeled as `400 kVA` (`T13`).
- `T9` (`Surya_Masala`) = `200 kVA`.
- `T10` (`Doctor_Bhakhale`) = `160 kVA`.

### 2.2 Kayji load swap correction
- **Status:** **Fixed**
- `Load.Kayji_Garden` now uses `108 kW, 52.31 kvar` on `Kayji_GardenBus3` (200 kVA DTC branch).
- `Load.Kayji_Skyline` now uses `288 kW, 139.48 kvar` on `Kayji_SkylineBus13` (400 kVA DTC branch).
- Prior overload on `Transformer.T3` removed after swap.

### 2.3 Transformer connection type
- **Status:** **Fixed**
- All 23 transformers are now `conns=[delta wye]`.

### 2.4 Load spelling consistency
- **Status:** **Fixed**
- `Load.Doctor_Bhakhale` spelling aligned with table naming.

### 2.5 Circuit naming consistency
- **Status:** **Fixed**
- Circuit name updated to `Circuit.Curti_Feeder` (matches file naming convention).

---

## 3) Calculation audit (requested)

## 3.1 Load calculation basis (`kW`, `kvar`)

**Verified formula in current DSS model:**
- `kW = kVA × (%peak_loading/100) × 0.9`
- `kvar = kW × tan(acos(0.9))`

**Result:**
- All 23 loads satisfy the above equations (within rounding precision).
- Therefore, load calculations are internally consistent and table-aligned under **PF = 0.9** assumption.

---

## 3.2 Line `r1` and `x1` from Line Table

From `Line Table.png`:
- SO1..SO6 each satisfy:
  - `Resistance_of_section / Length = 0.13`
  - `Reactance_of_section / Length = 0.0851`

Current Curti feeder model uses:
- `r1=0.13`
- `x1=0.0851`
for all line segments.

**Result:** `r1/x1` values are **correct** w.r.t. the line table derivation.

---

## 3.3 Transformer `%Rs` / `%Xs` (via `Xhl`) audit

Current transformer resistance settings:
- `%Rs=[1.41 1.41]` (total `%R = 2.82`)

Retuning performed to align impedance magnitude to table impedance% values:
- `Xhl` updated per transformer so that:
  - `%Z_target(table) ≈ sqrt((%R_total)^2 + (Xhl)^2)`

Examples:
- For `%Z=4.70`, `Xhl=3.760000`
- For `%Z=4.80`, `Xhl=3.884276`
- For `%Z=4.82`, `Xhl=3.908964`
- For `%Z=4.85`, `Xhl=3.945897`
- For `%Z=4.92`, `Xhl=4.031625`

**Result:** Transformer impedance magnitudes now match table impedance percentages while preserving `%Rs` structure.

---

## 4) Validation after updates

Post-update checks on `Curti_Feeder.dss`:
- **Compile/Solve:** Converged
- **Overloaded elements (`%normal > 100`):** 0
- **Voltage range (summary):**
  - `MaxPuVoltage ≈ 0.9984`
  - `MinPuVoltage ≈ 0.95426`

No new operational issues were detected in the latest run.

---

## Final status summary

| Area | Status |
|---|---|
| SLD topology fixes (critical) | ✅ Fixed |
| Kayji transformer/load mapping | ✅ Fixed |
| Transformer connection type (`delta-wye`) | ✅ Fixed |
| Load formula consistency | ✅ Verified |
| Line `r1/x1` derivation | ✅ Verified |
| Transformer impedance (`%Rs/%Xs` equivalent via `Xhl`) | ✅ Retuned & Verified |
| SO2–SO6 named DSS elements | ℹ️ Not required (accepted as decorative labels) |

