# Theoretical Error Analysis — `combined_network.dss`

**Cross-referenced against:**
- `docs/resources/Network_Diagram.pdf` — Kavale (Undir/Karanzal) SLD
- `docs/resources/Curti-Farmagudi_Presentation.pdf` — Curti, Ponda-I, Khadpabandh, Farmagudi SLDs + DTC tables
- `docs/resources/Feeder_Status_Kavale.xlsx` — Undir, Karanzal, Durbhat Express feeder data
- `docs/resources/Transformers_Survery - Transformers_Actual.csv` — Physical field survey of Kavale (Durbhat/Undir) DTCs: nameplate kVA, vector group, measured losses (**primary source for Section 7**)

---

## A. Topology Errors

### 1.✅ Two Different Substations Merged Into One Source Bus (CRITICAL) [Fixed]

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

### 3. ✅ Ambegal_II Connected to Wrong Bus — Farmagudi Feeder [NO ERROR, LLM ERROR]

The SLD (confirmed from physical diagram) shows the trunk as:

```
Shapur ──0.215──► [junction] ──► 3W Ambegal (transformer) ──0.150──► 4W Ambegal ──0.02──► Ambegal
                                                                            │
                                                               0.505 / 0.510 (two circuits)
                                                                            ▼
                                                                     Ambegal Suresh
```

Both upward lines (0.505 and 0.510) to Ambegal Suresh originate from the **4W Ambegal** node. The DSS line `FF47: bus1=4_Way_Ambegal bus2=Ambegal_II length=0.510` is **correct**. 3W Ambegal is a transformer sitting on the trunk, not a junction point for Ambegal Suresh. No fix required.

---

### 4. ✅ Tarangan_I / Rajmudra_I Order Reversed — Ponda-I Feeder [NO ERROR, LLM ERROR]

The Ponda-I SLD shows the sequence along the main trunk as:

```
SLD:  3W Tisk ──0.2──► Mamlatdar ──0.2──► Tarangan ──0.2──► Raj mudra I ──0.118──► PWD ──► Raj mudra II ──► ...
```

The DSS (lines F40–F42) matches this order exactly:

```
DSS:  Mamlatdar → Tarangan_I → Rajmudra_I → PWD → Rajmudra_II
```

No fix required. The original LLM claim that the SLD shows Raj Mudra I before Tarangan was incorrect — the SLD shows Tarangan first.

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

### 6.👍 Duplicate Parallel Lines F16 and F17 — Ponda-I Feeder [FIXED]

Lines F16 and F17 (DSS lines 297–298) are **identical**:

```dss
New Line.F16 bus1=3_Way_Bagaytdar  bus2=Kaziwada  length=0.135
New Line.F17 bus1=3_Way_Bagaytdar  bus2=Kaziwada  length=0.135
```

The Ponda-I SLD shows only one connection between these nodes. This is a copy-paste error that halves the effective impedance of this section.

**Fix:** Delete line F17.

---

## B. Transformer Rating Errors

### 7. ✅ Kavale Feeder Transformers — kVA Mismatches (FIXED)

**Status:** 5 confirmed kVA mismatches have been corrected in the DSS. 5 unverifiable transformers remain at default 200 kVA (physical access not possible).

Field survey (`Transformers_Survery - Transformers_Actual.csv`) found:
- **48 of 53 accessible** transformers correctly rated at 200 kVA ✓
- **5 confirmed mismatches** — corrected per table below
- **5 unverifiable** — location/nameplate access denied; default 200 kVA retained

#### Corrected kVA Ratings (DSS updated)

| DTC | Feeder | Previous (DSS) | Corrected to | %LoadLoss | %NoLoadLoss |
|---|---|---|---|---|---|
| Rajendra Talak | Durbhat | 200 | **630** | 0.728% | 0.113% |
| Perigol | Durbhat | 200 | **400** | 0.742% | 0.121% |
| Ritesh Developers | Durbhat | 200 | **400** | 0.742% | 0.121% |
| Shantadurga | Durbhat | 200 | **400** | 0.742% | 0.121% |
| Kharwada | Undir | 200 | **100** | 1.567% | 0.083% |

#### Unverifiable — Retained at 200 kVA (Default Survey Values)

| DTC | Feeder | DSS kVA | Survey status |
|---|---|---|---|
| Shashikala Pai | Durbhat | 200 | Location Inaccessible |
| Sanatan-I | Durbhat | 200 | Transformer Inaccessible |
| Sanatan-II | Durbhat | 200 | Transformer Inaccessible |
| Dempo HTC | Undir | 200 | Location Inaccessible |
| Old Shantadurga | Undir | 200 | Nameplate Damaged |

#### Karanzal Branch — All Verified Correct ✓

All 9 Karanzal branch DTCs (Pearl, Mogru, MG School, Shigumomand, Kunal, Vagdor, KashimathGround, Sneh Mandir, Konar Gaunem) survey at 200 kVA. No errors found.

> **Note:** The Curti, Ponda-I, Khadpabandh, and Farmagudi transformer ratings are **correct** — they match their respective DTC tables in the PDF.

---

### 8. Wye-Wye Transformer Connections — Curti / Ponda-I / Khadpabandh / Farmagudi

All transformers from DSS line 242 onward use `conns=[wye wye]`.

Indian 11kV/0.415kV distribution transformers are **Dyn11 (Delta primary, Star secondary)** per IS 2026 and CEA regulations. The Kavale batch (lines 111–170) correctly uses `conns=[delta wye]`.

The field survey independently confirms this: every physically accessible Kavale DTC (53 transformers across Durbhat and Undir feeders) has a nameplate vector group of Dyn-11 or Dy-11, with no exceptions.

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
| Venkatesh_Leela | 141 | Survey | ~120 kW (200 kVA × 60%) |
| Golden_Properties | 149 | Excel | ~110 kW (200 kVA × 55%) |
| Ritesh | 150 | Survey | ~110 kW (200 kVA × 55%) |
| T_Mogru | 166 | Survey | ~100 kW (200 kVA × 50%) |
| T_Vagdor | 161 | Survey | ~130 kW (200 kVA × 65%) |
| T_KashimathGround | 156 | Survey | ~100 kW (200 kVA × 50%) |
| Agarwal_gardens (T3) | 244 | Curti SLD | ~144 kW (200 kVA × 72%) |

**Total missing load: ~1,430 kW** — underestimates Kavale feeder loading significantly. (Revised upward from ~1,170 kW after correcting kVA assumptions for Venkatesh_Leela, Ritesh, Mogru, Vagdor, and KashimathGround using survey data.)

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

The field survey measured loss data for Kavale DTCs and confirms the Kavale batch parameters are physically grounded. Measured values by rating class:

| Rating | Survey %R (%LoadLoss) | Survey %NLL (%NoLoadLoss) | Cu Loss (W) | Iron Loss (W) |
|---|---|---|---|---|
| 100 kVA | **1.567%** | **0.083%** | 1,567 | 83 |
| 200 kVA | **1.013%** | **0.137%** | 2,027 | 273 |
| 400 kVA | **0.742%** | **0.121%** | 2,967 | 483 |
| 630 kVA | **0.728%** | **0.113%** | 4,587 | 713 |

The 200 kVA values (1.013%, 0.137%) match the existing Kavale batch parameters exactly. The 5 mis-rated DTCs in Section 7 have been updated to use the appropriate loss values per their corrected kVA rating:
- **630 kVA** (Rajendra Talak): 0.728% / 0.113%
- **400 kVA** (Perigol, Ritesh Developers, Shantadurga): 0.742% / 0.121%
- **100 kVA** (Kharwada): 1.567% / 0.083%

For non-Kavale feeders (Curti, Ponda-I, Khadpabandh, Farmagudi), the issue remains unresolved: `%LoadLoss ~2.82%` and `%NoLoadLoss=0%` differ from physical survey values.

**Fix (non-Kavale):** Update Curti/Ponda/Khadpabandh/Farmagudi transformer loss parameters to match their respective DTC survey tables.

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
| 1 | Two substations merged into one | **Critical** | Wrong source impedance; Madkai S/S and Colony SS modeled as identical |
| 2 | Bus naming disconnects Military Gate / Sports Complex | **Critical** | Khadpabandh–Farmagudi interconnection physically broken |
| 5 | All ring mains closed (no N.O. switches) | **High** | Non-physical circular power flows in all feeders |
| 9 | ~12 transformers with no load | **High** | ~1,170 kW of real load absent from model |
| 3 | ~~Ambegal_II on wrong bus (Farmagudi)~~ | ~~High~~ | **FALSE POSITIVE** — DSS is correct per SLD |
| 4 | Tarangan/Rajmudra order reversed (Ponda-I) | **High** | Node voltage profile incorrect along trunk |
| 8 | Wye-wye transformer connections | **Medium** | Incorrect harmonic and unbalanced load behaviour |
| 10 | Inconsistent loss parameters (2.82% vs 1.01%) | **Medium** | 3× difference in copper losses between feeder groups |
| 6 | Duplicate line F16/F17 (Ponda-I) | **Low** | Section impedance halved between Bagaytdar and Kaziwada |
| 11 | Linecode named "ACSR_Conductor" | **Low** | Cosmetic only — impedance values are correct |
