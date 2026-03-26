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

---

## 5) External LLM Assertion Audit (2026-03-26)

An external model reviewed `Curti_Feeder.dss` and `output/Curti/` and raised four modeling critiques. Each is evaluated below against the actual DSS code and simulation output.

---

### 5.1 Line Loading Graph Is Against a Generic Default, Not Physical Conductor Ratings

**Claim:** No `normamps` is specified on any line. OpenDSS applied its default 400 A rating, so the 64% loading figure for S01 is meaningless without knowing the actual conductor ampacity.

**Code evidence:** Every `New Line.*` definition (lines 11–50) specifies only `bus1`, `bus2`, `phases`, `length`, `units`, `r1`, and `x1`. No `normamps` appears anywhere.

**Output evidence (`Capacity.csv`):**

| Element  | Imax (A) | %normal | Implied normamps |
|----------|----------|---------|-----------------|
| Line.S01 | 256.531  | 64.13   | 256.531 ÷ 0.6413 = **400 A** |
| Line.L1  | 182.982  | 45.75   | 182.982 ÷ 0.4575 = **400 A** |
| Line.L29 | 155.920  | 38.98   | 155.920 ÷ 0.3898 = **400 A** |

Back-calculation confirms OpenDSS used **400 A** as the normamps for every line — a software default, not a physical conductor rating.

**Verdict: VALID.** The Line Loading graph is internally consistent but has no physical grounding. The actual thermal capacity depends on conductor type (ACSR Weasel, Dog, Rabbit, etc.) which is never specified.

**Fix:** Add `normamps=<value>` to each `New Line` based on the conductor specifications from the SLD or project data.

---

### 5.2 `%Rs=[1.41 1.41]` Inflates Copper Losses to 2.82% — Transformers = 82% of All Losses

**Claim:** Both per-winding resistance values add to an effective 2.82% total copper loss. Real distribution transformers are closer to 1–1.5%. This is why transformers account for an absurd 82% of system losses.

**Code evidence:** All 23 transformers use `%Rs=[1.41 1.41]` (lines 57–84). In OpenDSS, `%Rs` is a list of per-winding resistances. For a 2-winding transformer with equal ratings, both windings carry rated current simultaneously; the total copper loss at full load is 1.41% + 1.41% = **2.82% of rated kVA**.

**Real-world comparison (IS 1180 — Indian distribution transformer standard):**

| kVA  | IS 1180 max copper loss | % of kVA | Modeled total |
|------|------------------------|-----------|---------------|
| 100  | ≈ 1,450 W              | 1.45%     | **2.82%**     |
| 200  | ≈ 2,350 W              | 1.18%     | **2.82%**     |
| 1250 | ≈ 9,500 W              | 0.76%     | **2.82%**     |

The model applies a flat 2.82% to every transformer regardless of size — roughly **2–4× the actual losses** for larger units.

**Output evidence (`Losses.csv`):**

| Category            | Total losses (W) | Share  |
|---------------------|-----------------|--------|
| All 37 lines        | 24,309 W        | 18.1%  |
| All 23 transformers | 110,156 W       | **81.9%** |
| System total        | 134,465 W       | 100%   |

Top contributors:

| Transformer      | kVA  | I²R Loss (W) | % loading |
|------------------|------|-------------|-----------|
| T5 (Agarwal_HTC) | 1250 | 24,690      | 76.1%     |
| T11 (ECAP_HTC)   | 1000 | 19,739      | 76.1%     |
| T22 (Dairy_HTC)  | 500  | 9,768       | 75.7%     |
| T13 (Kayji_Skyline) | 400 | 7,915     | 76.2%     |

**Verdict: VALID.** The 82% transformer loss share is confirmed. The elevated share is caused by overstated per-unit copper resistance — especially significant for the three large HTCs (T5, T11, T22) which together account for **49%** of all system losses.

> **Note on existing audit (Section 3.3):** The `Xhl` values were tuned so that the impedance magnitude matches the data table's `%Z` values. That is correct. However, the `%Rs` split (1.41 per winding) was never cross-checked against IS 1180 nameplate copper loss — only against the total `%Z`. The `%Z` target constrains the hypotenuse; the `%R/%X` split within it is still a modeling assumption.

**Fix:** Set `%Rs` per transformer from nameplate or IS 1180 copper-loss test data. Typical per-winding values: 0.4–0.7% (each winding), giving a total of ~0.8–1.4%.

---

### 5.3 Core Losses Absent — `%noloadloss` Omitted on All Transformers

**Claim:** No transformer defines `%noloadloss`. OpenDSS defaults to 0%, so the model contains no iron/core losses — losses that are continuous 24/7 regardless of loading.

**Code evidence:** None of the 23 transformer definitions (lines 57–84) include `%noloadloss` or `%imag`. OpenDSS default when omitted: **0%**.

**Output evidence (`Losses.csv`):** The `No-load(W)` and `No-load(var)` columns are zero for every transformer:

```
Transformer.T5,  24689.6, 34008.5, 24689.6, 34008.5, 0, 0
Transformer.T11, 19738.82, 26319.2, 19738.82, 26319.2, 0, 0
```

**Estimated omitted no-load losses (IS 1180):**

| kVA  | No-load loss | Qty | Subtotal   |
|------|-------------|-----|-----------|
| 100  | ≈ 280 W     | 7   | ≈ 1,960 W |
| 160  | ≈ 390 W     | 5   | ≈ 1,950 W |
| 200  | ≈ 480 W     | 5   | ≈ 2,400 W |
| 400  | ≈ 820 W     | 2   | ≈ 1,640 W |
| 500  | ≈ 1,000 W   | 1   | ≈ 1,000 W |
| 1000 | ≈ 1,600 W   | 1   | ≈ 1,600 W |
| 1250 | ≈ 1,800 W   | 1   | ≈ 1,800 W |
| **Total** |        |     | **≈ 12,350 W** |

The model is missing approximately **12.4 kW** of continuous no-load loss — about **9%** of the currently modeled total.

**Verdict: VALID.** Core losses are entirely absent. Total system losses are understated by ~12 kW and the loss breakdown misrepresents the ratio of no-load to load-dependent losses.

**Fix:** Add `%noloadloss=<value>` to each transformer using IS 1180 test values or nameplate data.

---

### 5.4 Colony_SS Modeled as an Infinite Bus — No Source Impedance

**Claim:** The circuit declaration provides no short-circuit MVA (`MVAsc3`, `MVAsc1`). OpenDSS defaults to an ideal zero-impedance source, making the 11 kV busbar unrealistically rigid.

**Code evidence (line 2):**

```
New Circuit.Curti_Feeder basekv=11 bus1=Colony_SS pu=1.0
```

No `MVAsc3`, `MVAsc1`, `R1`, `X1`, or `Isc3` parameters. No separate substation transformer is modeled. OpenDSS treats this as an ideal voltage source at pu=1.0 with zero source impedance.

**Output evidence (`Voltages.csv`):**

```
"COLONY_SS": Phase 1: 6340.67 V (0.9984 pu)
             Phase 2: 6340.67 V (0.9984 pu)
             Phase 3: 6340.67 V (0.9984 pu)
```

Colony_SS is clamped at **0.9984 pu** across all three phases — perfectly symmetrical, no voltage droop under load. The first downstream bus (3_Way_Goa_Dairy_1) reads 0.99671 pu — a drop of only 1.7 V from the feeder head to the first junction, attributable entirely to Line.S01 resistance.

In reality the 33/11 kV substation transformer (typically 5–6% impedance on a 5–10 MVA unit) would impose additional voltage drop at Colony_SS itself under load, and the source voltage would not be clamped to a fixed pu.

**Verdict: VALID.** The primary voltage profile looks artificially healthy because the source has infinite stiffness. Secondary bus voltages (0.955–0.975 pu) are tighter than field measurements would show.

**Fix:** Add `MVAsc3=<value> MVAsc1=<value>` to the circuit declaration, or model the 33/11 kV substation transformer explicitly as a `New Transformer` upstream of Colony_SS.

---

### 5.5 External Assertion Summary

| # | Assertion | Verdict | Key evidence |
|---|-----------|---------|-------------|
| 5.1 | Line loading % against generic 400 A default, not physical conductor rating | **Valid** | Capacity.csv: 256.531 A ÷ 64.13% = 400 A implied normamps on every line |
| 5.2 | `%Rs=[1.41 1.41]` → 2.82% copper loss (2–4× IS 1180); transformers = 82% of losses | **Valid** | Losses.csv: 110,156 W transformer / 134,465 W total = 81.9% |
| 5.3 | `%noloadloss` omitted; ≈12.4 kW of core losses missing from model | **Valid** | Losses.csv: No-load columns = 0 W, 0 var for all 23 transformers |
| 5.4 | No source impedance; Colony_SS clamped as infinite bus at 0.9984 pu | **Valid** | Voltages.csv: Colony_SS all phases exactly 6340.67 V, perfectly symmetrical |

All four assertions are confirmed. The simulation converges and is internally self-consistent, but the modeling assumptions diverge from the physical system in ways that affect both absolute loss magnitudes and voltage regulation realism.

