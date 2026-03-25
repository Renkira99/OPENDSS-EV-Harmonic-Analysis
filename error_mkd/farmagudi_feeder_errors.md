# Farmagudi_Feeder.dss — Error Audit Report

**Reference documents used:**
- [Farmagudi_Feeder_pg1.png](file:///Users/overwatch/Documents/OPENDSS-main/docs/resources/Single%20Line%20Digram/Farmagudi_Feeder_pg1.png) — Single Line Diagram Page 1
- [Farmagudi_Feeder_pg2.png](file:///Users/overwatch/Documents/OPENDSS-main/docs/resources/Single%20Line%20Digram/Farmagudi_Feeder_pg2.png) — Single Line Diagram Page 2
- [Farmagudi_Feeder_pg3.png](file:///Users/overwatch/Documents/OPENDSS-main/docs/resources/Single%20Line%20Digram/Farmagudi_Feeder_pg3.png) — Single Line Diagram Page 3
- [Farmagudi_Feeder.png](file:///Users/overwatch/Documents/OPENDSS-main/docs/resources/Data_Table/Farmagudi_Feeder.png) — DTC/HTC Data Table (29 transformers)

---

## 1. Missing Named Section Lines (SO-numbered switching points)

The diagrams show **6 named section/switching points** (SO1–SO6). Only **none** are modelled as named lines in the DSS — all feeder segments are coded as generic `FF##` lines.

| Section | Diagram Location | DSS equivalent | Error |
|---|---|---|---|
| **SO1** | Pg 1 — `ControlRoom_SS → Haveli_Panchayat` (0.755 km) | `FF01` | Named section SO1 missing — `FF01` is unnamed |
| **SO2** | Pg 1 — on `3_Way_Safa_Masjid` junction | No direct line | **No line named SO2 in DSS** |
| **SO3** | Pg 2 — on `4W_PES` junction (0.33 km segment toward PES college) | `FF26` (bus1=PES → 3_Way_Police_Outpost) | Segment direction and SO3 position unclear — not a named object |
| **SO4** | Pg 2 — on the 0.04 km branch toward `GTDC_Tourist` from `4W_PES` | `FF32` | Named section SO4 missing |
| **SO5** | Pg 3 — on the 0.03 km segment from `4_Way_Housingboard` toward `Saad_Phase_II` | `FF34` | Named section SO5 missing |
| **SO6** | Pg 3 — on `3_Way_Katamgal`, 0.24 km branch toward `Katamgal` | `FF41` | Named section SO6 missing |

> [!NOTE]  
> These are protective switching points. Their absence means no recloser/fuse/switch modelling at these critical locations.

---

## 2. Missing Transformers (In Table But Absent From DSS)

The data table has **29 DTCs/HTCs**. The DSS defines only **27 transformers** (T_Haveli_Panchayat through T_Military_Gate). Cross-referencing reveals two complete omissions:

### 2a. Missing: **6TTR HTC** (Table Sr. 24 — 300 kVA)
- The table lists a **300 kVA HTC named "6TTR HTC"** at 40% impedance voltage (4.7%).
- **No transformer or load named `6TTR_HTC` or anything similar exists anywhere in the DSS.**
- On the diagram (Pg 2), the **NIT Goa** node feeds two HTCs downstream (NIT HTC → ITI HTC via FF42). A third HTC branch is implied but not shown — likely this is the missing 6TTR HTC.

### 2b. Missing: **Ambegal II** (Table Sr. 28 — 200 kVA)
- The table lists **"Ambegal II"** as a separate 200 kVA DTC.
- The DSS has `T_Ambegal` (400 kVA) and `T_Ambegal_Branch` (200 kVA at bus `3_Way_Ambegal`), but no transformer explicitly named for "Ambegal II".
- On Pg 2, the diagram shows **two separate tap-off arrows from the Ambegal section** — one for **"Ambegal Suresh"** (above) and one for **"Ambegal"** (inline). The table lists both "Ambegal" (400 kVA, Sr.3) and "Ambegal II" (200 kVA, Sr.28). The DSS `T_Ambegal_Branch` is labelled a placeholder (`! Example placeholder if needed`) at line 126 which confirms its provisional status — it is not a properly modelled transformer for Ambegal II.

---

## 3. Wrong Node Name — `Shapur RTO` vs. `RTO_Office_New` / `Shapur`

On **Page 1**, the diagram shows two distinct nodes on the same branch from `3_Way_Safa_Masjid`:
- **"Shapur RTO"** — a transformer node with a DTC tap-off, at distance 0.18 km from `3_Way_Safa_Masjid`
- This corresponds to the table entry **"RTO Office New"** (Sr. 27 — 200 kVA)

In the DSS, bus names `Shapur` and `RTO_Office_New` are treated as **two separate sequential buses**:
- `FF11`: `3_Way_Safa_Masjid → Shapur` (0.21 km)
- `FF08`: `3_Way_Safa_Masjid → RTO_Office_New` (0.18 km)

**Both lines leave `3_Way_Safa_Masjid` as bus1.** This creates a **topological fork** at the junction — two branches are modelled where the diagram shows a single chain. Per the diagram, the correct sequence is:

```
3_Way_Safa_Masjid → (0.18 km) → Shapur RTO → (0.21 km) → Shapur → ...
```

**Fix required:**
```dss
! CURRENT (wrong — two branches out of 3_Way_Safa_Masjid):
New Line.FF08 bus1=3_Way_Safa_Masjid  bus2=RTO_Office_New  length=0.18
New Line.FF11 bus1=3_Way_Safa_Masjid  bus2=Shapur          length=0.21

! CORRECT (serial chain):
New Line.FF08 bus1=3_Way_Safa_Masjid  bus2=RTO_Office_New  length=0.18
New Line.FF11 bus1=RTO_Office_New     bus2=Shapur          length=0.21
```

---

## 4. Wrong-Direction Bus Connectivity — Line FF46 Creates a Loop

**Line FF46** in the DSS (line 60):
```dss
New Line.FF46 bus1=3_Way_Housingboard bus2=4_Way_Housingboard length=0.77
```

Page 2 shows the topology clearly:
- `4_Way_Housingboard` feeds **downstream** via FF33 (→ GTDC side) and FF43 (→ `Housing_Board_New`)
- `3_Way_Housingboard` is a downstream junction fed from `Housing_Board_I`

**FF46 reverses direction** — it connects `3_Way_Housingboard → 4_Way_Housingboard`, completing a **closed loop**:
```
4_Way_Housingboard → FF43 → Housing_Board_New → FF44 → Housing_Board_I
→ FF45 → 3_Way_Housingboard → FF46 → 4_Way_Housingboard  (LOOP!)
```
This creates an **unintended mesh/loop** in the network. `FF46` should either be removed (if it's a normally-open tie line) or modelled as an open switch. In OpenDSS, a closed loop with no impedance control will cause a topology warning.

---

## 5. Phantom Transformer — `T_Ambegal_Branch` on Junction Bus

**Line 93:**
```dss
New Transformer.T_Ambegal_Branch phases=3 windings=2 buses=[3_Way_Ambegal, 3_Way_AmbegalBus1] ...
```

A transformer is connected to **`3_Way_Ambegal`**, which is a **junction/switching bus**, not a DTC location. The diagram (Pg 2) shows `3_Way_Ambegal` as an orange junction node with no DTC symbol, while the actual **Ambegal Suresh** DTC is shown on the branch 0.505 km above it. Connecting a transformer to a 3-way junction bus is topologically incorrect — the transformer should be on a dedicated tap-off bus.

Additionally, its corresponding load (line 126) has a comment: `! (Example placeholder if needed)` — confirming this is a **placeholder that was never properly modelled**.

---

## 6. Missing Line Segment — `Ambegal Suresh` Branch

Per Page 2 of the diagram, from `4_Way_Ambegal` there are **three** branches:
1. 0.505 km → **Ambegal Suresh** (DTC tap-off upward)
2. 0.510 km — (continuing right toward Ambegal inline DTC)
3. 0.02 km → **Ambegal** DTC (FF14)

The DSS has:
- `FF13`: `3_Way_Ambegal → 4_Way_Ambegal` (0.15 km) ✅
- `FF14`: `4_Way_Ambegal → Ambegal` (0.02 km) ✅
- `FF15`: `Ambegal → Pattantali` (0.02 km) ✅

**Missing:** The **0.505 km branch** from `4_Way_Ambegal` to **Ambegal Suresh** transformer is completely absent from the DSS. There is no bus `Ambegal_Suresh`, no transformer, and no load for this DTC.

> [!CAUTION]
> "Ambegal Suresh" appears to be a separate DTC from "Ambegal". It may correspond to table entry **Sr. 28 — Ambegal II (200 kVA)**, which is also missing (see §2b above).

---

## 7. Transformer kVA Mismatches (vs. Data Table)

| Sr | Table Name | Table kVA | DSS Transformer | DSS kVA | Error |
|---|---|---|---|---|---|
| 1 | Agarwal | **200** | `T_Haveli_Panchayat` | **200** | ✅ — But note: table row 1 is **"Agarwal"**, yet the DSS transformer is named `T_Haveli_Panchayat`. These may be the same physical DTC with inconsistent naming. |
| 7 | GVMS | **100** | `T_GVMS` | **100** | ✅ |
| 12 | GTDC/Tourist Department | **100** | `T_GTDC_Tourist` | **200** | ❌ Wrong — should be **100 kVA** |
| 23 | NIT HTC | **300** | `T_NIT_HTC` | **300** | ✅ |
| 24 | 6TTR HTC | **300** | *(missing)* | — | ❌ Entire transformer absent |
| 21 | Conem II | **63** | `T_Conem_II` | **63** | ✅ |
| 22 | Conem I Highway | **63** | `T_Conem_I_Highway` | **63** | ✅ |

**Key mismatch:**
```dss
! CURRENT (wrong):
New Transformer.T_GTDC_Tourist ... kvas=[200 200] Xhl=4.7
! CORRECT (from table Sr. 12):
New Transformer.T_GTDC_Tourist ... kvas=[100 100] Xhl=4.82
```

---

## 8. Wrong Xhl (Leakage Reactance) for GTDC Tourist

The DSS codes `T_GTDC_Tourist` with `Xhl=4.7` (matching a 200 kVA transformer). The table shows it is a 100 kVA unit with `Impedance %age voltage = 4.82`. Since the kVA is wrong, the Xhl is also wrong and should be `Xhl=4.82`.

---

## 9. Load kW Value Mismatches (vs. Data Table)

Using the same methodology as the Curti audit (kW = kVA × %loading × PF):

| Sr | Table Name | kVA | % Load | DSS Load | DSS kW | Expected kW (×0.9 PF) | Error |
|---|---|---|---|---|---|---|---|
| 1 | Agarwal (Haveli) | 200 | 70% | `Haveli_Panchayat` | 126 | 126 | ✅ |
| 2 | Shapur | 200 | 60% | `Shapur` | 108 | 108 | ✅ |
| 7 | GVMS | 100 | 70% | `GVMS` | 63 | 63 | ✅ |
| 9 | IMA | 200 | 50% | `IMA` | 90 | 90 | ✅ |
| 12 | GTDC Tourist | **100** | 80% | `GTDC_Tourist` | **72** | **72** | ❌ Load kW is correct for 100 kVA×80% — but the **transformer** is wrongly coded as 200 kVA (see §7) |
| 15 | Housing Board New | 400 | 50% | `Housing_Board_New` | **180** | **180** | ✅ |
| 17 | Saad Samrudhi Phase II | 400 | 50% | `Saad_Phase_II` | **180** | **180** | ✅ |
| 18 | Saad I | 400 | 60% | `Saad_I` | **216** | **216** | ✅ |
| 19 | Saad II | 400 | 60% | `Saad_II` | **216** | **216** | ✅ |
| 23 | NIT HTC | 300 | 40% | `NIT_HTC` | **108** | **108** | ✅ |

> [!NOTE]
> Most load kW values are internally consistent at 0.9 PF. The GTDC Tourist load (72 kW) is correct for a 100 kVA DTC at 80%, but the DSS transformer is wrongly rated 200 kVA — so the transformer and load are contradictory.

---

## 10. Missing Load — `Nageshi` (2W Nageshi)

Page 2 shows a **2W Nageshi** bus with a DTC arrow on it at the far right end of the `3_Way_Kashimath` branch:
- `FF19`: `3_Way_Kashimath → 2_Way_Nageshi` (0.07 km) — line exists in DSS ✅
- **But there is no transformer `T_Nageshi` and no `Load.Nageshi` in the DSS at bus `2_Way_Nageshi`.**

The diagram also shows a separate **"To Nageshi"** branch from Pg 2 (0.763 km from `4_Way_PES`), via `FF31`: `Ganesh_Temple → Nageshi` (0.763 km). The DSS has `T_Ganesh_Temple` but no `T_Nageshi` at the final `Nageshi` bus on FF31.

Both `Nageshi` endpoints are energised buses with no load or transformer, which leaves the branches floating.

---

## 11. Missing Transformer — `Military HTC`

Page 1 clearly shows **Military HTC** as an **HTC (oval symbol, indicating a High Tension Consumer)** connected at the `Military_HTC` bus between `Haveli_Panchayat` and `4_Way_Military_Gate`:

```
FF02: Haveli_Panchayat → Military_HTC (0.6 km)
FF03: Military_HTC → 4_Way_Military_Gate (1.18 km)
```

The DSS models `Military_HTC` only as a **pass-through bus** — there is no transformer or load connected to it. An HTC consumer connects directly at 11 kV (no step-down transformer needed), but **no `Load.Military_HTC` element exists in the DSS at this bus.**

> [!IMPORTANT]
> The table does not list Military HTC as a DTC (no step-down transformer), which is consistent with it being a direct HTC. However, there must still be a load or a transformer object representing this consumer. Currently the bus has no attached load at all.

---

## 12. Missing `3_Way_Sports_Complex` Transformer/Load

Page 1 shows **3W Sports Complex** as a blue junction square at the end of `FF04` (0.498 km from `4_Way_Military_Gate`). The DSS models this as a dead-end bus with no transformer and no load. If "Sports Complex" is a DTC location, it needs a transformer and load.

---

## 13. Wrong Transformer Connection Type (All 27 Transformers)

Identical to the Curti feeder issue — all transformers use:
```dss
conns=[wye wye]
```
Standard Indian 11 kV / 0.415 kV distribution practice uses **Delta primary, Star secondary (Dyn11)**. The primary should be `delta`:
```dss
conns=[delta wye]
```

> [!WARNING]
> This affects all 27 transformers in the feeder (lines 67–94). Ground fault modelling, zero-sequence current paths, and harmonic impedance are all incorrect with wye-wye connections at this voltage level.

---

## 14. `3_Way_Maruti_Temple` is a Dead-End Bus

Page 1 shows **3W Maruti Temple** (highlighted in yellow, indicating a junction/switching point) at the end of `FF05` (0.238 km from `4_Way_Military_Gate`). The DSS models this as a dead-end node — there are no further lines, transformers, or loads connected to it. Either:
- A transformer/load should be connected here, or
- A continuing feeder branch is missing

---

## Summary Table

| # | Error Type | Severity | DSS Lines Affected |
|---|---|---|---|
| 1 | Named switching sections SO1–SO6 missing as named objects | Medium | Lines 11–60 |
| 2a | Missing transformer & load: 6TTR HTC (300 kVA) | **High** | — |
| 2b | Missing transformer & load: Ambegal II (200 kVA) | **High** | Lines 93, 126 |
| 3 | `FF11 bus1` wrong — creates fork instead of chain from `3_Way_Safa_Masjid` | **High** | Line 21 |
| 4 | `FF46` creates a closed loop (should be open tie or removed) | **High** | Line 60 |
| 5 | `T_Ambegal_Branch` connected to junction bus — phantom/placeholder transformer | **High** | Lines 93, 126 |
| 6 | Missing 0.505 km line + transformer for Ambegal Suresh DTC | **High** | — |
| 7 | `T_GTDC_Tourist` kVA = 200, should be 100 | **High** | Line 78 |
| 8 | `T_GTDC_Tourist` Xhl = 4.7, should be 4.82 | Medium | Line 78 |
| 9 | Load kW internally consistent but contradicts transformer kVA for GTDC Tourist | Medium | Line 110 |
| 10 | Missing transformer + load at `2_Way_Nageshi` and `Nageshi` (2 locations) | **High** | — |
| 11 | Missing load for `Military_HTC` (HTC direct connection, no load element) | **High** | — |
| 12 | `3_Way_Sports_Complex` is a dead-end bus — possible missing DTC | Medium | — |
| 13 | All 27 transformers use `wye-wye` instead of `delta-wye (Dyn11)` | **High** | Lines 67–94 |
| 14 | `3_Way_Maruti_Temple` is a dead-end bus — possible missing branch | Medium | — |
