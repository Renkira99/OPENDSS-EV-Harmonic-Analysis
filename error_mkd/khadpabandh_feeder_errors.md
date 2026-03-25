# Khadpabandh_Feeder.dss — Error Audit Report

**Reference documents used:**
- [Khadpabandh_Feeder_pg1.png](file:///Users/overwatch/Documents/OPENDSS-main/docs/resources/Single%20Line%20Digram/Khadpabandh_Feeder_pg1.png) — Single Line Diagram Page 1
- [Khadpabandh_Feeder_pg2.png](file:///Users/overwatch/Documents/OPENDSS-main/docs/resources/Single%20Line%20Digram/Khadpabandh_Feeder_pg2.png) — Single Line Diagram Page 2
- [Khadpabandh_Feeder_pg3.png](file:///Users/overwatch/Documents/OPENDSS-main/docs/resources/Single%20Line%20Digram/Khadpabandh_Feeder_pg3.png) — Single Line Diagram Page 3
- [Khadpabandh_Feeder.png](file:///Users/overwatch/Documents/OPENDSS-main/docs/resources/Data_Table/Khadpabandh_Feeder.png) — DTC/HTC Data Table (29 transformers)

---

## 1. Duplicate Line — L16 and L17 Are Identical

**Lines 24–25:**
```dss
New Line.L16 bus1=4w_ganganath bus2=Ganganath phases=3 length=0.05 units=km ...
New Line.L17 bus1=4w_ganganath bus2=Ganganath phases=3 length=0.05 units=km ...
```

`L16` and `L17` are **exact duplicates** — same bus1, bus2, and length. OpenDSS will create two parallel branches between `4w_ganganath` and `Ganganath`, halving the effective impedance and doubling the power flow on that segment. Per the diagram (Pg 2), only a **single 0.05 km tap** connects `4W_Ganganath → Ganganath`.

**Fix:** Delete `Line.L17` entirely.

---

## 2. Closed Loop — Lines L8 and L9 Create a Ring

**Lines 16–17:**
```dss
New Line.L8  bus1=Sports_Complex      bus2=Sports_Complex_HTC  length=0.298
New Line.L9  bus1=Sports_Complex      bus2=4w_sports_c         length=0.398
```

Page 1 shows:
- `4W_Sports_C → Sports_Complex` (0.195 km, via `L7`) — feeds the complex
- `Sports_Complex → Sports_Complex_HTC` (0.298 km, via `L8`) — HTC tap-off ✅

However **L9** goes `Sports_Complex → 4w_sports_c` (0.398 km). The diagram shows the 0.398 km segment runs **from** `4W_Sports_C` **back toward** `3W_Sports_C` (i.e., `L9` is the return path of the box, not a separate downstream line from `Sports_Complex`). This creates a **closed mesh**:

```
4w_sports_c → L7 (0.195) → Sports_Complex → L9 (0.398) → 4w_sports_c  [LOOP]
```

`L9` should use `bus1=4w_sports_c` and `bus2=3w_sports_c` (matching the 0.398 km path shown from `4W Sports C → 3W Sports C` on the diagram), not `Sports_Complex` as bus1.

**Fix:**
```dss
! CURRENT (wrong — creates loop):
New Line.L9  bus1=Sports_Complex  bus2=4w_sports_c  length=0.398
! CORRECT:
New Line.L9  bus1=4w_sports_c     bus2=3w_sports_c  length=0.398
```

> [!CAUTION]
> With this loop active, OpenDSS will model an unintended meshed network. Voltage and current results for the entire sports complex branch will be incorrect.

---

## 3. Wrong Bus Connectivity — Line L26 Creates a Second Loop

**Line 34:**
```dss
New Line.L26 bus1=Vrudhavan_Garden bus2=4w_sheetal_bar length=0.378
```

Page 2 shows the chain starting from `4W_Sheetal_Bar`:
```
4W_Sheetal_bar → L13 (0.02) → Varkhande → L14 (0.44) → 4W_Ganganath
4W_Sheetal_bar → L27 (0.238) → 2W_Panditwada
4W_Sheetal_bar (upstream from) ← L12 (0.469) ← 4W_Sports_C
```

`Vrudhavan_Garden` is fed downstream from `L25` (from `Sungrace_HTC`). `L26` then routes back **into `4w_sheetal_bar`**, which is upstream. This creates another **closed loop**:
```
4w_sports_c → L12 (0.469) → 4w_sheetal_bar → L13 (0.02) → Varkhande
→ L14 → 4w_ganganath → L18 → Heritage_II ... → Vrudhavan_Garden
→ L26 (0.378) → 4w_sheetal_bar  [LOOP]
```

Per the diagram, `Vrudhavan_Garden` is a **dead-end DTC** served via `3W_Maruti_Temple`. The 0.378 km line from `Vrudhavan_Garden` should not connect back to `4w_sheetal_bar`.

---

## 4. Wrong Bus Connectivity — Line L15 (`2w_Varkhandem` Spelling Mismatch)

**Line 23:**
```dss
New Line.L15 bus1=4w_ganganath bus2=2w_Varkhandem length=0.05
```

The diagram (Pg 2) labels this bus **"2W Varkhandem"**. Elsewhere in the file, the transformer is named `Varkhande` (no 'm') and connected to bus `Varkhande`. The `2w_Varkhandem` bus (with 'm') is different from `Varkhande` — it becomes a **floating dead-end bus** with no transformer or load. 

The diagram shows `2W Varkhandem` as a plain blue junction square (not a DTC), so a load/transformer may not be needed — but the bus name inconsistency (`Varkhande` vs `2w_Varkhandem`) must be intentional for the separate 2-way junction node. This is acceptable but should be confirmed.

---

## 5. Missing Transformer — `Nagamasjid_new` Bus Has No Line Connection

**Transformer (line 71):**
```dss
New Transformer.Nagamasjid_new buses=[Nagamasjid_new, Nagamasjid_newBus] kvas=[200 200]
```

**Load (line 104):**
```dss
New Load.Nagamasjid_new bus1=Nagamasjid_newBus kW=72
```

The bus `Nagamasjid_new` is referenced only in the transformer definition. There is **no line anywhere in the DSS that has `bus2=Nagamasjid_new`** — this transformer is an **island** with no connection to the feeder network.

Per Page 1 of the diagram, **"Naga Masjid new"** is a DTC tap-off on the main backbone line between `Colony` and `Lotlikar_Naga_masjid`, on the 0.495 km segment. A line connecting `Colony → Nagamasjid_new` (or creating the tap) is completely missing.

**Fix required:** Add a line tapping from the main backbone into `Nagamasjid_new`, e.g.:
```dss
New Line.Ltap_NagaMasjid bus1=Colony bus2=Nagamasjid_new phases=3 length=0.01 units=km r1=0.13 x1=0.0851
```

---

## 6. Missing Transformer and Load — `Hussain` Bus

**Lines 13–14:**
```dss
New Line.L5  bus1=USMANIA  bus2=Hussain  length=0.2
New Line.L6  bus1=Hussain  bus2=4w_sports_c  length=0.28
```

`Hussain` is modelled as a **pass-through bus** only. Page 1 shows it has a downward-pointing DTC arrow (transformer symbol). Yet there is no `Transformer.Hussain` and no `Load.Hussain` anywhere in the DSS. The data table also does not include a "Hussain" entry, which suggests this DTC may have been renamed — but no kVA is captured for this bus at all.

---

## 7. Dead-End Buses With No Transformer or Load

| DSS Bus | Created By | Diagram | Issue |
|---|---|---|---|
| `2W_Curti` | `L1` (line 9) | Pg 1 — blue square, no DTC | No transformer/load — acceptable if it is a normally-open tie point to Curti feeder |
| `4w_military_gate` | `L11`, `L28` (lines 19, 36) | Pg 1 & 2 — blue square junction | No transformer/load — may be a tie junction only |
| `2w_panditwada` | `L27` (line 35) | Pg 2 — blue square | No transformer/load — dead end |
| `3w_sports_c` | `L10`, `L11` (lines 18–19) | Pg 1 — junction node | No transformer/load — junction only, acceptable |
| `2w_Ravinagar` | `L35` (line 43) | Pg 2 — blue square at far right | No transformer/load — dead end |
| `3w_ponda_1` | `L49` (line 57) | Pg 3 — plain junction | No transformer/load — junction only |
| `2w_satyanarayan_temple` | `L53` (line 61) | Pg 3 — blue square at end | No transformer/load — dead end |
| `2W_Perigol` | `L41` (line 49) | Pg 2 — blue square at end | No transformer/load — dead end |

> [!NOTE]
> Dead-end buses with no connected element are not simulation errors in themselves, but they indicate either missing loads or normally-open tie points that should be documented and possibly modelled as open switches.

---

## 8. Transformer kVA Mismatches (vs. Data Table)

| Sr | Table Name | Table kVA | DSS Transformer | DSS kVA | Error |
|---|---|---|---|---|---|
| 3 | USMANIA | **100** | `USMANIA` | **100** | ✅ |
| 4 | Varkhande | **160** | `Varkhande` | **160** | ✅ |
| 9 | Heritage I | **400** | `Heritage_I` | **400** | ✅ |
| 10 | Heritage II | **400** | `Heritage_II` | **400** | ✅ |
| 14 | BHARDWAJ | **100** | `BHARDWAJ` | **100** | ✅ |
| 15 | Mahalaxmi Dev | **400** | `Mahalaxmi_Dev` | **400** | ✅ |
| 17 | Dessai (Santoba) | **200** | `Dessai_Santoba` | **200** | ✅ |
| 18 | Rani Construction | **100** | `Rani_Construction` | **100** | ✅ |
| 19 | Maharudra | **400** | `Maharudra` | **400** | ✅ |
| 22 | Khadpabandh Garden II | **315** | `Khadpabandh_Garden_II` | **315** | ✅ |
| 23 | Khadpabandh Garden I | **630** | `Khadpabandh_Garden_I` | **630** | ✅ |
| 27 | Sewerage HTC | **750** | `Sewerage_HTC` | **750** | ✅ |
| 28 | Sports Complex HTC | **260** | `Sports_Complex_HTC` | **260** | ✅ |
| 29 | Sungrace HTC | **200** | `Sungrace_HTC` | **200** | ✅ |

> [!NOTE]
> All transformer kVA values that exist in the DSS match the data table correctly. The kVA errors seen in Curti and Farmagudi do not appear here.

---

## 9. Wrong Xhl (Impedance) — All Transformers Use Xhl=4.48

All 29 transformers in the DSS use a uniform `Xhl=4.48`. The data table shows varying impedance %age values: **4.7%, 4.82%, 4.85%, 4.92%, 4.8%, 4.38%** depending on kVA rating. This means the leakage reactance modelled for each transformer is wrong for all units that deviate from 4.48%.

Correct Xhl values by kVA (from table):

| kVA Rating | Table Xhl% | DSS Xhl | Error |
|---|---|---|---|
| 100 kVA | 4.82 | 4.48 | ❌ |
| 160 kVA | 4.85 | 4.48 | ❌ |
| 200 kVA | 4.7 | 4.48 | ❌ |
| 315 kVA | 4.8 | 4.48 | ❌ |
| 400 kVA | 4.92 | 4.48 | ❌ |
| 630 kVA | 4.38 | 4.48 | ❌ |
| 750 kVA | 4.8 | 4.48 | ❌ |
| 260 kVA | 4.8 | 4.48 | ❌ |

Only transformers with `Xhl=4.48` in the table (if any) would be correct — and 4.48 does not appear in the table at all. **Every transformer has the wrong impedance.**

> [!IMPORTANT]
> Compare with Curti (Xhl=4.48) and Farmagudi (Xhl=4.7/4.82/4.85/4.92) — Farmagudi correctly varied Xhl by kVA. Khadpabandh used a flat 4.48 for all, which is incorrect.

---

## 10. Load kW Mismatches (vs. Data Table)

Using kW = kVA × %loading × 0.9 PF:

| Sr | Table Name | kVA | % Load | Expected kW | DSS kW | Error |
|---|---|---|---|---|---|---|
| 1 | Colony | 200 | 60% | **108** | **108** | ✅ |
| 2 | Lotlikar/Naga masjid | 200 | 80% | **144** | **144** | ✅ |
| 3 | USMANIA | 100 | 80% | **72** | **72** | ✅ |
| 4 | Varkhande | 160 | 70% | **100.8** | **100.8** | ✅ |
| 5 | Vrudhavan Garden | 200 | 60% | **108** | **108** | ✅ |
| 6 | Nagamasjid new | 200 | 40% | **72** | **72** | ✅ (but transformer is disconnected — see §5) |
| 7 | Angarki | 200 | 80% | **144** | **144** | ✅ |
| 8 | Ganganath | 200 | 80% | **144** | **144** | ✅ |
| 9 | Heritage I | 400 | 60% | **216** | **216** | ✅ |
| 10 | Heritage II | 400 | 60% | **216** | **216** | ✅ |
| 11 | Almeda | 160 | 80% | **115.2** | **115.2** | ✅ |
| 12 | Patil | 200 | 70% | **126** | **126** | ✅ |
| 13 | Purohit | 200 | 80% | **144** | **144** | ✅ |
| 14 | BHARDWAJ | 100 | 70% | **63** | **63** | ✅ |
| 15 | Mahalaxmi Dev | 400 | 60% | **216** | **216** | ✅ |
| 16 | Kedar | 200 | 80% | **144** | **144** | ✅ |
| 17 | Dessai (Santoba) | 200 | 50% | **90** | **90** | ✅ |
| 18 | Rani Construction | 100 | 70% | **63** | **63** | ✅ |
| 19 | Maharudra | 400 | 60% | **216** | **216** | ✅ |
| 20 | Ravinagar | 160 | 80% | **115.2** | **115.2** | ✅ |
| 21 | Friends Colony | 100 | 80% | **72** | **72** | ✅ |
| 22 | Khadpabandh Garden II | 315 | 40% | **113.4** | **113.4** | ✅ |
| 23 | Khadpabandh Garden I | 630 | 50% | **283.5** | **283.5** | ✅ |
| 24 | Sports Complex | 200 | 80% | **144** | **144** | ✅ |
| 25 | Bhagwati I | 200 | 80% | **144** | **144** | ✅ |
| 26 | Bhagwati II | 200 | 80% | **144** | **144** | ✅ |
| 27 | Sewerage HTC | 750 | 60% | **405** | **405** | ✅ |
| 28 | Sports Complex HTC | 260 | 70% | **163.8** | **163.8** | ✅ |
| 29 | Sungrace HTC | 200 | 60% | **108** | **108** | ✅ |

All load kW values match the data table exactly.

---

## 11. Load Bus Name Mismatch — Heritage I and II

**Lines 107–108:**
```dss
New Load.Heritage_I   bus1=HeritageIBus   ...
New Load.Heritage_II  bus1=HeritageIIBus  ...
```

The transformer secondary buses are named `Heritage_IBus` and `Heritage_IIBus` (lines 74–75), but the loads reference `HeritageIBus` and `HeritageIIBus` (no underscore after "Heritage"). OpenDSS bus name matching is case-insensitive and ignores some punctuation, but these bus names differ by the underscore character:

- Transformer creates: `Heritage_IBus` 
- Load references: `HeritageIBus`  ← **different bus name**

This means the loads are connected to a **new floating bus** (`HeritageIBus`) rather than the transformer LV terminal (`Heritage_IBus`). The transformers are energised but deliver no power to the loads.

**Fix:**
```dss
! CURRENT (wrong):
New Load.Heritage_I   bus1=HeritageIBus   ...
New Load.Heritage_II  bus1=HeritageIIBus  ...
! CORRECT:
New Load.Heritage_I   bus1=Heritage_IBus  ...
New Load.Heritage_II  bus1=Heritage_IIBus ...
```

---

## 12. Wrong Transformer Connection Type (All 29 Transformers)

All 29 transformers use:
```dss
conns=[wye wye]
```
Standard Indian 11 kV / 0.415 kV distribution uses **Delta–Star (Dyn11)**. The primary should be `delta`:
```dss
conns=[delta wye]
```

> [!WARNING]
> This affects all transformers (lines 66–94). Ground fault and zero-sequence modelling are incorrect with wye-wye at 11 kV.

---

## Summary Table

| # | Error Type | Severity | DSS Lines Affected |
|---|---|---|---|
| 1 | L16 and L17 are duplicate lines (identical bus1/bus2/length) | **High** | Lines 24–25 |
| 2 | L8/L9/L7 create a closed loop around `Sports_Complex` | **High** | Lines 15–17 |
| 3 | L26 routes `Vrudhavan_Garden → 4w_sheetal_bar`, creating a second loop | **High** | Line 34 |
| 4 | `2w_Varkhandem` bus spelling inconsistency vs `Varkhande` | Low | Line 23 |
| 5 | `Nagamasjid_new` transformer/load is an island — no line connects it to the network | **High** | Line 71, 104 |
| 6 | `Hussain` bus has no transformer or load (DTC shown on diagram) | Medium | Lines 13–14 |
| 7 | Multiple dead-end buses with no transformer/load or tie switch | Medium | Various |
| 8 | All kVA values correct ✅ | — | — |
| 9 | All 29 transformers use flat `Xhl=4.48` — wrong for every kVA rating | **High** | Lines 66–94 |
| 10 | All load kW values correct ✅ | — | — |
| 11 | `Load.Heritage_I/II` reference wrong bus names (`HeritageIBus` vs `Heritage_IBus`) | **High** | Lines 107–108 |
| 12 | All 29 transformers use `wye-wye` instead of `delta-wye (Dyn11)` | **High** | Lines 66–94 |
