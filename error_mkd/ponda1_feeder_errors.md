# Ponda1_Feeder.dss — Error Audit Report

**Reference documents used:**
- [Ponda_1_Feeder_pg1.png](file:///Users/overwatch/Documents/OPENDSS-main/docs/resources/Single%20Line%20Digram/Ponda_1_Feeder_pg1.png) — Single Line Diagram Page 1
- [Ponda_1_Feeder_pg2.png](file:///Users/overwatch/Documents/OPENDSS-main/docs/resources/Single%20Line%20Digram/Ponda_1_Feeder_pg2.png) — Single Line Diagram Page 2
- [Ponda_1_Feeder_Table1.png](file:///Users/overwatch/Documents/OPENDSS-main/docs/resources/Data_Table/Ponda_1_Feeder_Table1.png) — Data Table Sr. 1–17
- [Ponda_1_Feeder_Table2.png](file:///Users/overwatch/Documents/OPENDSS-main/docs/resources/Data_Table/Ponda_1_Feeder_Table2.png) — Data Table Sr. 18–38

---

## 1. Duplicate Line — F16 and F17 Are Identical

**Lines 27–28:**
```dss
New Line.F16 bus1=3_Way_Bagaytdar bus2=Kaziwada length=0.135
New Line.F17 bus1=3_Way_Bagaytdar bus2=Kaziwada length=0.135
```

`F16` and `F17` are **exact duplicates** — same bus1, bus2, and length. This creates two parallel branches halving effective impedance. Per the diagram (Pg 1), only a **single 0.135 km** line exists from `3_Way_Bagaytdar → Kaziwada`.

**Fix:** Delete `Line.F17` entirely.

---

## 2. Missing Transformer — `Josheph HTC` (Table Sr. 37 — 222 kVA)

The data table lists **Sr. 37: "Josheph HTC" at 222 kVA, Xhl=4.8**, with a Power Tech Trf manufacturer. This is a distinct HTC consumer not modelled anywhere in the DSS — no `Transformer.Josheph_HTC` and no related load exist.

On Pg 2 of the diagram, the `Kanir_Construction_HTC` bus has an oval HTC symbol (line F29: `3_Way_Bhosle_2 → Kanir_Construction_HTC`, 0.12 km). The DSS does model `T59` at `Kanir_Construction_HTC` (400 kVA) — but table Sr. 36 confirms Kanir Construction HTC = 400 kVA. The separate 222 kVA "Josheph HTC" is a completely absent consumer.

---

## 3. Missing Transformer — `Tarangan II` (Table Sr. 30 — 400 kVA)

Table Sr. 30 lists **"Tarangan II" at 400 kVA**. Page 2 shows two DTC tap-offs from the spine: `Tarangan I` and — visually — a second downstream transformer implied near the Mamlatdar section. The DSS models only `T52` (`Tarangan_I`, 400 kVA) with no corresponding `Tarangan_II` transformer or load. This is an entirely missing 400 kVA DTC.

---

## 4. Missing Road from `3W_Canara` → `3W_Bazar`

Page 2 shows `3W_Bazar` at the top of Pg 2 linked as:
```
A (Bhosle) → F48 (0.19) → 4_Way_Menino → ...
A → (from Pg 1 side) → [3W_Bhosle_2] → F26 → Super_Market → F27 → 3_Way_Bazar
```

In the DSS, `F27` ends at `3_Way_Bazar` (line 39). But the diagram (Pg 2 left side) shows `3W_Bazar` also connects **downward to `Supermarket`** via 0.23 km, and `3W_Bazar` is distinct from the junction on the Bhosle side. This is the segment labeled `SO3` at 0.23 km on Pg 2. The DSS has no line with both `bus1=3_Way_Bazar` and the downstream junction — `3_Way_Bazar` is a dead-end.

---

## 5. Wrong Bus Connectivity — `F58` Wrong bus2 (Creates a Loop)

**Line 76:**
```dss
New Line.F58 bus1=Aiesha bus2=3_Way_Tisk length=0.21
```

On Pg 2, the chain is:
```
3_Way_Apollo → F57 (0.13) → Aiesha → F58 (0.21) → (back toward Tisk)
3_Way_Tisk ← F37 (0.351) ← 3_Way_Muncipality ← F36 (0.351) ← Goa_State_Bank
```

`3_Way_Tisk` is already connected from `3_Way_Muncipality` via `F37`. `F58` creating a second path from `Aiesha → 3_Way_Tisk` makes a **closed loop** through:
```
Goa_State_Bank → F36 → 3_Way_Muncipality → F37 → 3_Way_Tisk → F38 → 3_Way_Mamlatdar
→ ... → 3_Way_Apollo → F57 → Aiesha → F58 → 3_Way_Tisk [LOOP]
```

Per the diagram, `F58` (`Aiesha → 0.21 km`) should end at **`3_Way_Tisk`** — but the diagram shows this as a **normally-open tie** (dashed connection). It should be modelled as an open switch, not a closed line.

> [!CAUTION]
> This closed loop will cause OpenDSS to model a meshed network between the Municipality branch and the Apollo branch, producing incorrect voltages throughout.

---

## 6. `Ratnadeep_Apt` Has No Line Connection to the Feeder

**Transformer (line 118):**
```dss
New Transformer.T61 buses=[Ratnadeep_Apt, Ratnadeep_AptBus] kvas=[200 200]
```

**Load (line 163):**
```dss
New Load.Ratnadeep_Apt bus1=Ratnadeep_AptBus kW=144
```

Line `F02` (line 12) correctly defines `bus1=Golden_Nest bus2=Ratnadeep_Apt`. **However, there is no issue with the line itself.** The transformer is connected to `Ratnadeep_Apt` — the bus is served by F02. ✅ (This is not an error.)

---

## 7. Transformer kVA Mismatches (vs. Data Table)

| Sr | Table Name | Table kVA | DSS Transformer | DSS kVA | Error |
|---|---|---|---|---|---|
| 7 | Panditwada | **160** | `T30` | **160** | ✅ |
| 10 | Kaziwada | **150** | `T33` | **150** | ✅ |
| 13 | Kurtarkar Arcade (KCA) | **160** | `T36` | **160** | ✅ |
| 15 | Super Market | **100** | `T38` | **100** | ✅ |
| 18 | AVR (Kamat AVR Realtors) | **630** | `T41` | **630** | ✅ |
| 20 | Kanir Construction | **400** | `T43` | **400** | ✅ |
| 25 | Rajdeep Galaria I | **400** | `T48` | **400** | ✅ |
| 26 | Rajdeep Galaria II | **400** | `T49` | **400** | ✅ |
| 28 | Mamladtdar | **160** | `T51` | **160** | ✅ |
| 29 | Tarangan I | **400** | `T52` | **400** | ✅ |
| 31 | Rajmudra I | **200** | `T54` | **200** | ✅ |
| 32 | Rajmudra II | **400** | `T55` | **400** | ✅ |
| 33 | Rajdurga | **630** | `T56` | **630** | ✅ |
| 34 | Sumit Plumeria | **400** | `T57` | **400** | ✅ |
| 36 | Kanir Construction HTC | **400** | `T59` | **400** | ✅ |

All transformer kVA values present in the DSS correctly match the data table. No kVA mismatches.

---

## 8. Wrong Xhl — All 36 Transformers Use `Xhl=4.48`

The data table lists varying impedance %age by kVA:

| kVA | Table Xhl% | DSS Xhl | Error |
|---|---|---|---|
| 100 kVA | 4.82 | 4.48 | ❌ |
| 160 kVA | 4.85 | 4.48 | ❌ |
| 200 kVA | 4.7 | 4.48 | ❌ |
| 400 kVA | 4.92 | 4.48 | ❌ |
| 630 kVA | 4.38 | 4.48 | ❌ |
| 222 kVA | 4.8 | N/A | Missing transformer |

Every transformer in the DSS has `Xhl=4.48`, while the table shows 4.48 does not correspond to any kVA rating. **All 36 transformers have the wrong impedance**. (Same issue as Khadpabandh.)

---

## 9. Load kW Mismatches (vs. Data Table)

Using kW = kVA × %loading × 0.9 PF:

| Sr | Table Name | kVA | % Load | Expected kW | DSS Load Name | DSS kW | Error |
|---|---|---|---|---|---|---|---|
| 1 | Golden Nest | 200 | 60% | 108 | `Golden_Nest` | 108 | ✅ |
| 2 | Surekha Parkar | 200 | 80% | 144 | `Surekha_Parkar` | 144 | ✅ |
| 3 | Nagzar | 200 | 80% | 144 | `Nagzar` | 144 | ✅ |
| 4 | Sarthak Nest | 200 | 60% | 108 | `Sarthak_Nest` | 108 | ✅ |
| 5 | Progress | 200 | 80% | 144 | `Progress` | 144 | ✅ |
| 6 | Commercial Tax | 200 | 80% | 144 | `Commertial_Tax` | 144 | ✅ |
| 7 | Panditwada | 160 | 60% | 86.4 | `Panditwada` | 86.4 | ✅ |
| 8 | Verekar | 200 | 70% | 126 | `Verekar_2` | 126 | ✅ |
| 9 | Bandodkar | 200 | 70% | 126 | `Bandodkar` | 126 | ✅ |
| 10 | Kaziwada | 150 | 80% | 108 | `Kaziwada` | 108 | ✅ |
| 11 | Twin Tower | 200 | 60% | 108 | `Twin_Tower` | 108 | ✅ |
| 12 | Canara Bank | 200 | 80% | 144 | `Canara_Bank` | 144 | ✅ |
| 13 | KCA | 160 | 60% | 86.4 | `Kurtarkar_Arcade` | 86.4 | ✅ |
| 14 | Bhosle | 200 | 80% | 144 | `Bhosle` | 144 | ✅ |
| 15 | Super Market | 100 | 60% | 54 | `Super_Market` | 54 | ✅ |
| 16 | DK Arcade | 200 | 80% | 144 | `DK_Arcade` | 144 | ✅ |
| 17 | Coelo | 200 | 80% | 144 | `Coelo` | 144 | ✅ |
| 18 | AVR (Kamat) | 630 | 50% | 283.5 | `Kamat_AVR` | 283.5 | ✅ |
| 19 | BSNL Internal | 200 | 50% | 90 | `BSNL_Internal` | 90 | ✅ |
| 20 | Kanir Construction | 400 | 50% | 180 | `Kanir_Const` | 180 | ✅ |
| 21 | Sumit (Sumit Shivam) | 200 | 70% | 126 | `Sumit_Shivam` | 126 | ✅ |
| 22 | Kalpana | 200 | 80% | 144 | `Kalpana` | 144 | ✅ |
| 23 | Police Station | 200 | 80% | 144 | `Police_Station` | 144 | ✅ |
| 24 | Goa State Bank | 200 | 80% | 144 | `Goa_State_Bank` | 144 | ✅ |
| 25 | Rajdeep Galaria I | 400 | 70% | 252 | `Rajdeep_Mall_1` | 252 | ✅ |
| 26 | Rajdeep Galaria II | 400 | 70% | 252 | `Rajdeep_Mall_2` | 252 | ✅ |
| 27 | Aiesha | 200 | 80% | 144 | `Aiesha` | 144 | ✅ |
| 28 | Mamladtdar | 160 | 80% | 115.2 | `Mamlatdar` | 115.2 | ✅ |
| 29 | Tarangan I | 400 | 60% | 216 | `Tarangan_I` | 216 | ✅ |
| 31 | Rajmudra I | 200 | 80% | 144 | `Rajmudra_I` | 144 | ✅ |
| 32 | Rajmudra II | 400 | 60% | 216 | `Rajmudra_II` | 216 | ✅ |
| 33 | Rajdurga | 630 | 60% | 340.2 | `Raj_Durga` | 340.2 | ✅ |
| 34 | Sumit Plumeria | 400 | 50% | 180 | `Sumit_Plumeria` | 180 | ✅ |
| 35 | Daag | 200 | 80% | 144 | `Daag` | 144 | ✅ |
| 38 | Ratnadeep Apt | 200 | 0%! | **0** | `Ratnadeep_Apt` | **144** | ❌ |

**Key mismatch:**
- **Sr. 38 — Ratnadeep Apt**: The table shows `%age peak loading = 0%`. This is the only entry with 0% loading, suggesting the transformer is currently unloaded / not yet commissioned. The DSS models it at `kW=144` (80% loading). The DSS load should either be `kW=0` or the transformer should be absent.

> [!NOTE]
> PWD Office load (`kW=216`) maps to table Sr. 31 which corresponds to `PWD` transformer (T53, 400 kVA, 60% × 0.9). But the DSS load is `Load.PWD_Office bus1=PWDBus kW=216`. T53 = 400 kVA × 60% × 0.9 = 216 kW ✅

---

## 10. Dead-End Buses

| Bus | Line | Diagram Indication | Issue |
|---|---|---|---|
| `3_Way_Bazar` | F27 end | Pg 2 — junction square | No continuing line or transformer. Diagram shows tie going to `3W Bazar feeder` with SO3 — should be open switch |
| `2W_Ganganath` | F24 end | Pg 1 — blue square | No transformer or load — diagram confirms it is a dead-end/tie point to another feeder |
| `2_Way_Bazar` | F56 end | Pg 2 — blue square top | No transformer or load — tie end |
| `2_Way_Shantinagar` | F51 end | Pg 2 — blue square | No transformer or load — tie end |
| `3_Way_Daag` | F46, F47 | Pg 2 — junction | F47 continues to `Daag` ✅, but `3_Way_Daag` junction has no tap-off transformer |

---

## 11. Wrong Transformer Connection Type (All 36 Transformers)

All transformers use:
```dss
conns=[wye wye]
```
Standard Indian 11 kV / 0.415 kV practice: `conns=[delta wye]` (Dyn11).

> [!WARNING]
> This affects every transformer (lines 82–119). Zero-sequence currents, ground faults, and harmonic impedance are all incorrectly modelled.

---

## Summary Table

| # | Error Type | Severity | DSS Lines Affected |
|---|---|---|---|
| 1 | F16 and F17 are duplicate lines (3_Way_Bagaytdar → Kaziwada) | **High** | Lines 27–28 |
| 2 | Missing Josheph HTC transformer & load (222 kVA, table Sr. 37) | **High** | — |
| 3 | Missing Tarangan II transformer & load (400 kVA, table Sr. 30) | **High** | — |
| 4 | `3_Way_Bazar` is a dead-end — SO3 tie line not modelled as open switch | Medium | Line 39 |
| 5 | F58 (`Aiesha → 3_Way_Tisk`) creates a closed loop — should be open tie | **High** | Line 76 |
| 6 | All 36 transformers use flat `Xhl=4.48` — wrong for all kVA ratings | **High** | Lines 82–119 |
| 7 | `Ratnadeep_Apt` load = 144 kW but table shows 0% loading | Medium | Line 163 |
| 8 | All 36 transformers use `wye-wye` instead of `delta-wye (Dyn11)` | **High** | Lines 82–119 |
