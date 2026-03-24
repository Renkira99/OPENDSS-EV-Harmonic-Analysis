# Theoretical Error Analysis — `combined_network.dss`

**Cross-referenced against:**
- `docs/resources/Network_Diagram.pdf` — Kavale (Undir/Karanzal) SLD
- `docs/resources/Curti-Farmagudi_Presentation.pdf` — Curti, Ponda-I, Khadpabandh, Farmagudi SLDs + DTC tables
- `docs/resources/Feeder_Status_Kavale.xlsx` — Undir, Karanzal, Durbhat Express feeder data

---

## A. Topology Errors

### 1. Two Different Substations Merged Into One Source Bus (CRITICAL)

The SLDs show at least two distinct physical substations:

| Feeder(s) | Substation shown in SLD |
|---|---|
| Undir, Karanzal (Durbhat Express) | 33/11kV **Madkai S/S** |
| Curti, Ponda-I, Khadpabandh | 33/11kV **Colony SS** |
| Farmagudi | 33/11kV **Control Room SS** |

The DSS connects **all six feeders** to a single `bus1=Substation` (`combined_network.dss` line 6). The Madkai S/S feeders should have a separate source bus with their own source impedance. Merging them produces incorrect fault levels and cross-feeder flows that do not reflect reality.

---

### 2. Bus Naming Errors — Cross-Feeder Connections Broken (CRITICAL)

The SLDs show that the Khadpabandh and Farmagudi feeders share physical junction points. Different bus names in the DSS make them electrically disconnected:

| Physical Junction | Khadpabandh bus name (DSS) | Farmagudi bus name (DSS) | Status |
|---|---|---|---|
| 4-Way Military Gate | `4W_Military_Gate` (KF12) and `4_Way_Military_Gate` (KF49) | `4W_Military_Gate` (FF03–FF06) | **BROKEN** — KF49 uses wrong name |
| 3-Way Sports Complex | `3W_Sports_C` (KF11–12) | `3W_Sports_Complex` (FF04) | **BROKEN** — different names |

**Fix:**
- Line KF49: change `bus2=4_Way_Military_Gate` → `bus2=4W_Military_Gate`
- Line FF04: change `bus2=3W_Sports_Complex` → `bus2=3W_Sports_C`

---

### 3. Ambegal_II Connected to Wrong Bus — Farmagudi Feeder

The Farmagudi SLD (Page 2) shows Ambegal Suresh (`Ambegal_II`) branching directly from **3W Ambegal**:

```
SLD:    3W Ambegal ──0.505──► Ambegal_II
                   ──0.150──► 4W Ambegal ──0.02──► Ambegal
```

The DSS (line FF47) connects it from the wrong junction:
```dss
! WRONG:
FF47: bus1=4_Way_Ambegal  bus2=Ambegal_II  length=0.510

! CORRECT:
FF47: bus1=3_Way_Ambegal  bus2=Ambegal_II  length=0.510
```

---

### 4. Tarangan_I / Rajmudra_I Order Reversed — Ponda-I Feeder

The Ponda-I SLD (Page 2) shows the sequence along the main trunk as:

```
SLD:  Mamlatdar → Raj Mudra I → Tarangan → PWD → Raj Mudra II
```

The DSS has them swapped (lines F40–F42):

```
DSS:  Mamladtdar → Tarangan_I → Rajmudra_I → PWD → Rajmudra_II
```

**Fix:** Swap `Tarangan_I` and `Rajmudra_I` in lines F40 and F41.

---

### 5. All Ring Mains Modeled as Closed — No Normally-Open Switches

The SLDs confirm the following ring mains are intentional. However, Indian 11kV distribution operates **radially** with one switch normally open (N.O.) per ring. The DSS has all rings fully closed with no switch elements, allowing circular power flows that do not occur in normal operation.

| Ring | Forming lines |
|---|---|
| Feeder 1 (Undir) — Kharwada ring | LU1 → ... → LU30 → LU31 |
| Feeder 1 (Undir) — Galshire ring | LU34 → ... → LU45 |
| Khadpabandh — Sports Complex ring | KF08 → KF09 → KF10 |
| Khadpabandh — Sheetal–Vrindavan ring | KF13 → ... → KF52 |
| Farmagudi — Housing Board ring | FF43 → FF44 → FF45 → FF46 |
| Curti — Copperwada mesh | Three paths to `3_Way_Copperwada_1` (L30, L33, L36) |

**Fix:** Insert `New Line.TIE_xxx switch=y` elements at the N.O. points, or open them with `Open Line.xxx`.

---

### 6. Duplicate Parallel Lines F16 and F17 — Ponda-I Feeder

Lines F16 and F17 (DSS lines 297–298) are **identical**:

```dss
New Line.F16 bus1=3_Way_Bagaytdar  bus2=Kaziwada  length=0.135
New Line.F17 bus1=3_Way_Bagaytdar  bus2=Kaziwada  length=0.135
```

The Ponda-I SLD shows only one connection between these nodes. This is a copy-paste error that halves the effective impedance of this section.

**Fix:** Delete line F17.

---

## B. Transformer Rating Errors

### 7. Kavale Feeder Transformers — Blanket 200 kVA (CRITICAL)

Every transformer in **Batch 1** (DSS lines 111–150) and **Batch 2** (DSS lines 153–170) is set to `kVA=200` regardless of actual DTC capacity from the Feeder_Status_Kavale.xlsx. Actual ratings range from 63 kVA to 630 kVA.

#### Durbhat Express / Undir Feeder Mismatches

| DTC | DSS kVA | Actual kVA (Excel) | Error |
|---|---|---|---|
| Rajendra Talak | 200 | **630** | 3.15× under-rated |
| Ritesh Developers | 200 | **400** | 2× under-rated |
| Dempo HTC | 200 | **275** | 1.4× under-rated |
| Venkatesh Leela | 200 | **63** | 3.2× over-rated |
| RB Engineers | 200 | **63** | 3.2× over-rated |
| Vamneshwar | 200 | **63** | 3.2× over-rated |
| Dhumre | 200 | **160** | 1.25× over-rated |
| Galshire | 200 | **160** | 1.25× over-rated |
| Perigol | 200 | **160** | 1.25× over-rated |
| Sewerage HTC | 200 | **145** | 1.4× over-rated |
| Ram Mandir | 200 | **100** | 2× over-rated |
| Kharwada | 200 | **100** | 2× over-rated |
| MuleBhat | 200 | **100** | 2× over-rated |
| Maruti Temple | 200 | **100** | 2× over-rated |
| Undir Bakale | 200 | **100** | 2× over-rated |
| Manmohan Singh | 200 | **100** | 2× over-rated |
| Matruchaya | 200 | **100** | 2× over-rated |
| Paunwada | 200 | **100** | 2× over-rated |
| Kaswada | 200 | **100** | 2× over-rated |
| Ritesh | 200 | **100** | 2× over-rated |

#### Karanzal Feeder Mismatches

| DTC | DSS kVA | Actual kVA (Excel) | Error |
|---|---|---|---|
| Pearl | 200 | **63** | 3.2× over-rated |
| Mogru | 200 | **160** | 1.25× over-rated |
| Konar Gaunem | 200 | **100** | 2× over-rated |
| MG School | 200 | **100** | 2× over-rated |
| Shigumomand | 200 | **100** | 2× over-rated |
| Kunal | 200 | **100** | 2× over-rated |
| Vagdor | 200 | **100** | 2× over-rated |
| KashimathGround | 200 | **100** | 2× over-rated |
| Sneh Mandir | 200 | **100** | 2× over-rated |

> **Note:** Transformer impedance in per-unit scales with kVA rating. Using a wrong rating distorts voltage drop, loss calculation, and overload detection. A 63 kVA transformer modeled as 200 kVA shows ~1/3 the actual voltage drop and will never flag overloading.

> **Note:** The Curti, Ponda-I, Khadpabandh, and Farmagudi transformer ratings are **correct** — they match their respective DTC tables in the PDF.

---

### 8. Wye-Wye Transformer Connections — Curti / Ponda-I / Khadpabandh / Farmagudi

All transformers from DSS line 242 onward use `conns=[wye wye]`.

Indian 11kV/0.415kV distribution transformers are **Dyn11 (Delta primary, Star secondary)** per IS 2026 and CEA regulations. The Kavale batch (lines 111–170) correctly uses `conns=[delta wye]`.

A wye-wye connection:
- Lacks the delta winding needed to suppress triplen harmonics
- Causes neutral voltage shift under unbalanced loading
- Provides no zero-sequence current path

**Fix:** Change `conns=[wye wye]` → `conns=[delta wye]` for all Curti/Ponda/Khadpabandh/Farmagudi transformers (DSS lines 242–643).

---

## C. Missing Elements

### 9. Missing Loads on Multiple Transformers

The following transformers exist in the model but have **no load** connected to their LV bus. All are confirmed present in the SLDs and/or Excel data:

| Transformer | DSS Line | Source | Expected peak load |
|---|---|---|---|
| Sanatan_2 | 131 | Excel | ~160 kW (200 kVA × 80%) |
| Ramnathi | 133 | Excel | ~160 kW (200 kVA × 80%) |
| Tolulem | 135 | Excel | ~140 kW (200 kVA × 70%) |
| Kharwada | 136 | Excel | ~50 kW (100 kVA × 50%) |
| Shashikala_Pai | 145 | Excel | ~120 kW (200 kVA × 60%) |
| Venkatesh_Leela | 141 | Excel | ~38 kW (63 kVA × 60%) |
| Golden_Properties | 149 | Excel | ~110 kW (200 kVA × 55%) |
| Ritesh | 150 | Excel | ~55 kW (100 kVA × 55%) |
| T_Mogru | 166 | Excel | ~80 kW (160 kVA × 50%) |
| T_Vagdor | 161 | Excel | ~65 kW (100 kVA × 65%) |
| T_KashimathGround | 156 | Excel | ~50 kW (100 kVA × 50%) |
| Agarwal_gardens (T3) | 244 | Curti SLD | ~144 kW (200 kVA × 72%) |

**Total missing load: ~1,170 kW** — underestimates Kavale feeder loading significantly.

---

## D. Parameter Errors

### 10. Inconsistent Transformer Loss Parameters

Two completely different parameter styles are used across the same file with no justification:

| Feeder group | DSS lines | %LoadLoss | %NoLoadLoss |
|---|---|---|---|
| Kavale (Undir/Karanzal) | 111–170 | **1.0133%** (per winding total) | **0.13667%** (iron losses modeled) |
| Curti, Ponda-I, Khadpabandh, Farmagudi | 242–643 | **~2.82%** (`%Rs=[1.41 1.41]` × 2) | **0%** (omitted, defaults to zero) |

Issues:
- Copper losses are ~**2.8× higher** in the second group vs the first, without physical justification.
- Iron/core losses are **completely absent** for ~80 transformers in the second group.

**Fix:** Standardize to `%LoadLoss` + `%NoLoadLoss` for all transformers, using values from the respective DTC tables.

---

### 11. Linecode Named "ACSR_Conductor" — Misnomer

The linecode at DSS line 17:
```dss
New Linecode.ACSR_Conductor nphases=3 r1=0.13 x1=0.0851 units=km
```

The impedance values are **numerically correct** — they are consistent with what the PDF section tables derive (e.g., Curti SO1: R=0.31265 Ω / 2.405 km = **0.13 Ω/km**; x = 0.0851 Ω/km is characteristic of underground cable, not overhead ACSR).

The Feeder_Status_Kavale.xlsx and PDF section tables explicitly state **"XLPE 3C Cable, 300 Sq.mm, 355A in Ground"** for all feeder sections. ACSR is an overhead bare conductor — a different technology.

**Fix:** Rename to `XLPE_300sqmm` (or similar) for accuracy. Values do not need changing.

---

## Priority Summary

| # | Error | Severity | Impact on results |
|---|---|---|---|
| 7 | Kavale transformer kVA all set to 200 | **Critical** | Wrong voltage drops, losses, overload detection for 29+ DTCs |
| 1 | Two substations merged into one | **Critical** | Wrong source impedance; Madkai S/S and Colony SS modeled as identical |
| 2 | Bus naming disconnects Military Gate / Sports Complex | **Critical** | Khadpabandh–Farmagudi interconnection physically broken |
| 5 | All ring mains closed (no N.O. switches) | **High** | Non-physical circular power flows in all feeders |
| 9 | ~12 transformers with no load | **High** | ~1,170 kW of real load absent from model |
| 3 | Ambegal_II on wrong bus (Farmagudi) | **High** | Branch topology incorrect; node has wrong impedance path |
| 4 | Tarangan/Rajmudra order reversed (Ponda-I) | **High** | Node voltage profile incorrect along trunk |
| 8 | Wye-wye transformer connections | **Medium** | Incorrect harmonic and unbalanced load behaviour |
| 10 | Inconsistent loss parameters (2.82% vs 1.01%) | **Medium** | 3× difference in copper losses between feeder groups |
| 6 | Duplicate line F16/F17 (Ponda-I) | **Low** | Section impedance halved between Bagaytdar and Kaziwada |
| 11 | Linecode named "ACSR_Conductor" | **Low** | Cosmetic only — impedance values are correct |
