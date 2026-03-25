# Curti_Feeder.dss — Error Audit Report

**Reference documents used:**
- [Curti_Feeder_pg1.png](file:///Users/overwatch/Documents/OPENDSS-main/docs/resources/Single%20Line%20Digram/Curti_Feeder_pg1.png) — Single Line Diagram Page 1
- [Curti_Feeder_pg2.png](file:///Users/overwatch/Documents/OPENDSS-main/docs/resources/Single%20Line%20Digram/Curti_Feeder_pg2.png) — Single Line Diagram Page 2
- [Curti_Feeder_Table.png](file:///Users/overwatch/Documents/OPENDSS-main/docs/resources/Data_Table/Curti_Feeder_Table.png) — DTC/HTC Data Table (23 transformers)

---

## 1. Missing Line Segments (Topology Errors)

These lines appear on the single line diagrams but are **absent** from the DSS file.

| # | Missing Line | From Bus | To Bus | Length (km) | Source |
|---|---|---|---|---|---|
| 1 | **S02** (unlabelled) | `4_Way_saiservice` | `Agarwal_HTC` | **0.14** | Pg 1 — The label **SO2** is shown on the 0.14 km link between 4-Way-Saiservice and Agarwal HTC. In the DSS, `L31` covers this segment but the diagram assigns it a **named section S02**, implying it is a metered/switching section. However the real error is this: the DSS file has **no line named S02**. |
| 2 | **S03** | `3_way_goa_dairy_1` | `3_Way_GoaDairy2` | 0.02 | Pg 1 — Label **SO3** sits on the 0.02 km segment. The DSS names it `L12` with no SO3 reference. |
| 3 | **S04** | `3_Way_Doctor` | `3_Way_Copperwada_1` | **1.32** | Pg 1 — A 1.32 km segment labelled **SO4** connects **3 Way Doctor → 3 Way Copperwada 1** directly. **This line is completely absent from the DSS file.** The DSS routes this path through `Doctor_bakale` and `3_Way_Copperwada_1` via L32 + L33, but the direct 1.32 km SO4 tie-line is not modelled. |
| 4 | **S05** | `3_Way_khadpabandh` | (upstream) | — | Pg 2 — Label **SO5** marks the 3-way Khadpabandh junction bus. No line named S05 exists in the DSS. |
| 5 | **S06** | `4_Way_saiservice` | (main feeder) | — | Pg 2 — Label **SO6** marks the main entry into 4-Way Saiservice from the Colony SS side. No S06 element in DSS. |

> [!NOTE]
> SO1 is correctly represented as `Line.S01` (Colony_SS → 3_way_goa_dairy_1). SO2–SO6 are all missing as named objects, which means protective/switching device modelling is absent for those points.

---

## 2. Wrong Bus Connectivity — Line L15 (Topology Error)

| DSS Line | DSS bus1 | DSS bus2 | Diagram | Error |
|---|---|---|---|---|
| `L15` (line 27) | `Dairy_Old` | `3_Way_Microwave` | Pg 1 shows: `Dairy_Old → 3_Way_Microwave` (0.88 km) | **Correct path** for L15. However `L16` (line 28) reads `bus1=Microwave bus2=3_Way_verekar`. Per the diagram, the 0.495 km link leaves **3_Way_Microwave**, not **Microwave** (which is a transformer tap-off bus). **L16 bus1 should be `3_Way_Microwave`, not `Microwave`.**

**Affected line:**
```
! CURRENT (wrong):
New Line.L16  bus1=Microwave bus2=3_Way_verekar ...
! CORRECT:
New Line.L16  bus1=3_Way_Microwave bus2=3_Way_verekar ...
```

---

## 3. Line L33 — Wrong Length

| DSS Line | DSS Length | Diagram Length | Error |
|---|---|---|---|
| `L33` — `Doctor_bakale → 3_Way_Copperwada_1` | 0.47 km | Pg 1 shows **1.32 km** for the Doctor Bakale → 3-Way Copperwada 1 segment (the SO4 path) | Length is wrong by a factor of ~3× |

> [!CAUTION]
> The 1.32 km value shown with label SO4 on Page 1 appears to represent the **direct Doctor → Copperwada 1** path. The DSS models two hops (L32 = 0.47 km Doctor → Doctor_bakale, L33 = 0.47 km Doctor_bakale → Copperwada_1), but the diagram shows a **single 1.32 km** direct link. The intermediate `Doctor_bakale` bus may need to be removed or L33's length corrected.

---

## 4. Transformer kVA Mismatches (vs. Data Table)

Cross-referencing each DSS transformer `kva=` value against the **DTC/HTC capacity in KVA** column of the table:

| Sr | Table Name | Table kVA | DSS Transformer | DSS kVA | Error |
|---|---|---|---|---|---|
| 4 | Kayji Garden (Agarwal Apt) | **200** | `T13` — `Kayji_Skyline` | **400** | ❌ Wrong — should be 200 kVA |
| 7 | Shivlal | **200** | `T7` — `Shivlal` | **200** | ✅ Correct |
| 10 | K.G Skyline | **400** | `T13` — `Kayji_Skyline` | **400** | — See note below |
| 11 | Navajeevan/Rudra Developers | **160** | `T14` — `Rudra_Developer` | **160** | ✅ Correct |
| 20 | Docter Bhakhale | **160** | `T10` — `Doctor_bakale` | **100** | ❌ Wrong — should be 160 kVA |
| 21 | Surya Masala | **200** | `T9` — `Surya_masala` | **100** | ❌ Wrong — should be 200 kVA |
| 22 | Pisgal | **160** | `T23` — `Pisgal` | **160** | ✅ Correct |

> [!IMPORTANT]
> **T13 (Kayji_Skyline)** serves **two loads**: `Load.Kayji_Garden` (108 kW → 200 kVA transformer in table row 4) and `Load.KG_Skyline` (288 kW → 400 kVA transformer in table row 10). Both loads connect to the **same bus** `Kayji_SkylineBus13` and the **same transformer T13** which is rated 400 kVA. The table shows two separate DTCs (200 kVA for Kayji Garden and 400 kVA for K.G Skyline). These should be **two separate transformers**. Currently, the 200 kVA DTC is missing entirely.

---

## 5. Missing Transformer — Kayji Garden (200 kVA DTC)

Per the table (Sr. 4), **Kayji Garden (Agarwal Apt)** is a separate 200 kVA DTC. In the DSS:
- No separate `Transformer.Kayji_Garden` exists.
- `Load.Kayji_Garden` (line 93) is connected to `Kayji_SkylineBus13` — the **same** LV bus as `Load.KG_Skyline` (line 99).
- These are two distinct field transformers sharing one modelled transformer, which is incorrect.

**Fix required:** Add a new 200 kVA transformer for Kayji Garden with its own LV bus, and reconnect `Load.Kayji_Garden` to that new bus.

---

## 6. Load kW Mismatches (vs. Data Table)

Loads are computed as `kVA × %loading × 0.8 pf` (approximately). Using table's `%age peak loading` and `DTC capacity`:

| Sr | Table Name | kVA | % Load | Expected kW (≈kVA×%×0.8) | DSS Load Name | DSS kW | Error |
|---|---|---|---|---|---|---|---|
| 1 | Dairy Old | 200 | 80% | **128 kW** | `Load.Dairy_Old` | **144 kW** | ❌ Mismatch |
| 2 | Forensic | 200 | 80% | **128 kW** | `Load.Forensic` | **144 kW** | ❌ Mismatch |
| 3 | Dada Vaidhya/Ganganagar | 100 | 90% | **72 kW** | `Load.Dada_Vaidhya` | **81 kW** | ❌ Mismatch |
| 5 | Fiber Glass | 100 | 70% | **56 kW** | `Load.Fiberglass` | **63 kW** | ❌ Mismatch |
| 6 | Yummy | 100 | 80% | **64 kW** | `Load.Yummy` | **72 kW** | ❌ Mismatch |
| 7 | Shivlal | 200 | 30% | **48 kW** | `Load.Shivlal` | **54 kW** | ❌ Mismatch |
| 8 | Prakash Corrugeted | 100 | 80% | **64 kW** | `Load.Prakash` | **72 kW** | ❌ Mismatch |
| 9 | Kapat Factory | 100 | 80% | **64 kW** | `Load.Kapat_Factory` | **72 kW** | ❌ Mismatch |
| 14 | Korde | 100 | 50% | **40 kW** | `Load.Korde` | **45 kW** | ❌ Mismatch |
| 19 | Kelbai | 100 | 60% | **48 kW** | `Load.Kelbai` | **54 kW** | ❌ Mismatch |
| 20 | Docter Bhakhale | 160 | 60% | **76.8 kW** | `Load.Doctor_Bhakale` | **86.4 kW** | ❌ Mismatch |
| 21 | Surya Masala | 200 | 80% | **128 kW** | `Load.Surya_Masala` | **144 kW** | ❌ Mismatch |

> [!NOTE]
> All load kW values in the DSS appear to be calculated using a **0.9 PF** (kW = kVA × % × 0.9), whereas the table column header says "Full load of Primary Current as per name plate" implies using **nameplate kVA × loading%**. If 0.9 PF is the intended system assumption, the loads are internally consistent. However, the table's `%age peak loading` figures do not reproduce the DSS kW values at any single PF assumption — this indicates a data inconsistency that should be reviewed.

---

## 7. Wrong Transformer Connection Type

All 23 transformers in the DSS use:
```
conns=[wye wye]
```
For an 11 kV / 0.415 kV distribution transformer in India, the standard connection is **Delta–Star (Dyn11)** (primary delta, secondary wye with neutral). A wye–wye connection at 11 kV is unusual and typically incorrect for this voltage level.

> [!WARNING]
> This affects zero-sequence current paths, ground fault modelling, and harmonic impedance. The primary winding should be `delta`, not `wye`: `conns=[delta wye]`.

---

## 8. Missing Loads for Some Transformers

The following transformers exist in the DSS but have **no corresponding load** element, leaving them energised but unloaded:

| Transformer | Bus | Note |
|---|---|---|
| `T19` — `4_Way_verekar` / `VerekarBus19` | `VerekarBus19` | **`Load.Verekar` exists (line 112)** ✅ — OK |
| `T22` — `Dairy_HTC` / `Dairy_HTCBus22` | `Dairy_HTCBus22` | **`Load.Dairy_HTC` exists (line 106)** ✅ — OK |
| **`T5` — `Agarwal_htc` / `Agarwal_htcBus5`** | `Agarwal_htcBus5` | Load.Agarwal_HTC exists (line 105) ✅ |
| **`T23` — `Pisgal` / `PisgalBus23`** | `PisgalBus23` | Load.Pisgal exists (line 111) ✅ |

All 23 transformers have corresponding loads — **no missing loads** detected.

---

## 9. Load Name Inconsistency (Minor)

The DSS load name uses an inconsistent spelling compared to the table:

| Table Name | DSS Load Name | Issue |
|---|---|---|
| Docter Bhakhale | `Load.Doctor_Bhakale` (line 109) | Table spells "Bhakhale", DSS uses "Bhakale" (missing 'h') |
| Navajeevan/Rudra Developers | `Load.Rudra_Developer` | Load name omits "Navajeevan" — minor but inconsistent |
| Kendriya Vidhyalay | `Load.KV_School` | Abbreviated differently — acceptable but not traceable |
| Kayji Garden (Agarwal Apt) | `Load.Kayji_Garden` | Table shows this as a separate 200 kVA DTC from K.G Skyline |

---

## 10. Circuit Name Typo (Line 2)

```dss
New Circuit.CurtiFeeder basekv=11 ...
```
The circuit is named `CurtiFeeder` (no underscore/space). While not a functional error, it differs from the file name `Curti_Feeder`. Minor inconsistency.

---

## Summary Table

| # | Error Type | Severity | Lines Affected |
|---|---|---|---|
| 1 | Missing named section lines SO2–SO6 | Medium | — |
| 2 | `L16 bus1=Microwave` should be `3_Way_Microwave` | **High** | Line 28 |
| 3 | `L33` length = 0.47 km, should be 1.32 km | **High** | Line 48 |
| 4 | `T10` kVA = 100, should be 160 (Doctor Bhakhale) | **High** | Line 67 |
| 5 | `T9` kVA = 100, should be 200 (Surya Masala) | **High** | Line 66 |
| 6 | Missing separate 200 kVA transformer for Kayji Garden | **High** | Lines 71, 93, 99 |
| 7 | All load kW values inconsistent with table %loading | Medium | Lines 90–112 |
| 8 | All transformers use `wye-wye` instead of `delta-wye` | **High** | Lines 58–84 |
| 9 | Load name spelling: `Bhakale` vs `Bhakhale` | Low | Line 109 |
| 10 | Circuit name `CurtiFeeder` vs file name `Curti_Feeder` | Low | Line 2 |
