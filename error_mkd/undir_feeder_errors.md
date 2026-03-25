# Undir_Feeder.dss — Error Audit Report

**Reference documents used:**
- [UndirFeeder_pg1.png](file:///Users/overwatch/Documents/OPENDSS-main/docs/resources/Single%20Line%20Digram/UndirFeeder_pg1.png) — Single Line Diagram Page 1
- [UndirFeeder_pg2.png](file:///Users/overwatch/Documents/OPENDSS-main/docs/resources/Single%20Line%20Digram/UndirFeeder_pg2.png) — Single Line Diagram Page 2
- [Undir_Feeder_Table.csv](file:///Users/overwatch/Documents/OPENDSS-main/docs/resources/Data_Table/Undir_Feeder_Table.csv) — DTC data table (58 entries across Durbhat + Undir feeders)

> [!NOTE]
> The DSS file is significantly more complex than the other feeders — it uses two distinct loadshapes (`Res_Goa_2025`, `Comm_Goa_2025`), two feeder trunks (M01/M02), actual per-transformer Xhl values computed from the CSV, and `delta-wye` connections on all transformers. Several structural issues remain, however.

---

## 1. Closed Loop — Lines L30 and L31 Create a Ring Back to Source

**Lines 57–58:**
```dss
New Line.L30 bus1=Tolulem bus2=Kharwada length=1.28
New Line.L31 bus1=Kharwada bus2=3_Way_Kharwada length=0.182
```

Page 1 clearly shows:
- `3_Way_RMU_Kharwada` is the major junction fed by `M01` (1.77 km from `Madkai_SS`) — it is the **source junction** of Feeder 1.
- `Tolulem` is a downstream DTC after `RPRS_School`, fed from `3_Way_Ramnathi`.
- `L30: Tolulem → Kharwada (1.28 km)` and `L31: Kharwada → 3_Way_Kharwada (0.182 km)` create a path **back to the source**, completing a large closed ring:

```
3_Way_Kharwada → L1 → Ram_Mandir → ... → Ramnathi → 3_Way_Ramnathi
→ L29 → RPRS_School → L30 → Tolulem? Wait ...
→ L28 → RPRS_School → L29 → Tolulem → L30 → Kharwada → L31 → 3_Way_Kharwada [LOOP!]
```

Actually per the diagram, the chain ending with "Kharwada DTC → 3W RMU Kharwada" with 0.182 km is correct — **but `Kharwada DTC` IS a transformer, not the source junction.** The bus name `Kharwada` (DTC) in L30/L31 is different from `3_Way_Kharwada` (source junction). These buses share the same root name and may cause confusion, but structurally the chain `Tolulem → Kharwada_DTC → 3_Way_Kharwada` is exactly what the diagram shows (Kharwada DTC feeds back to the main junction which is the source — this IS the intended ring topology).

> [!NOTE]
> On closer inspection, L30/L31 correctly model the "Kharwada DTC → 3W RMU Kharwada" return path shown on the diagram. This **is a closed ring** by design per the SLD. The issue is that this meshed segment is not modelled with a normally-open switch, meaning OpenDSS will solve it as a closed loop. The diagram shows "C.B" (Circuit Breaker) symbols at key points on this ring — those CB open points are absent from the DSS.

---

## 2. Missing Link — `Shantinagar_Interlink` Bus Has No Incoming Line

**Line 80:**
```dss
New Line.L49 bus1=Matruchaya bus2=Shantinagar_Interlink length=0.109
```

Page 1 shows `3_Way_Shantinagar` is a junction fed from `Kapileshwari → L47 → 3_Way_Rathamal → L48 → Matruchaya → (some segment) → 3_Way_Shantinagar`. In the DSS:

- `L49: Matruchaya → Shantinagar_Interlink` (0.109 km) — links to the interlink bus ✅
- But then **Lines L50 and L51 both use `bus1=3_Way_Shantinagar`** (lines 81–82), which is a **different bus** from `Shantinagar_Interlink`.

`3_Way_Shantinagar` has no incoming line with `bus2=3_Way_Shantinagar`. It is an **island bus** — no line feeds it. The correct connectivity should be:
```
Matruchaya → L49 → 3_Way_Shantinagar (not Shantinagar_Interlink)
```
Or alternatively, a short link `Shantinagar_Interlink → 3_Way_Shantinagar` is missing, making `Vamneshwar` and `Golden_Properties` (and `Ritesh`) unreachable from the source.

---

## 3. Missing Transformer — `Saila Bhat` DTC

Page 2 of the SLD shows the `Konar_Gaunem → (Mogru branch)` chain as:
```
Konar_Gaunem_DTC → L57 (1.0 km) → Mogru_DTC → (Saila Bhat DTC) → L58 → Shamrao_Builders_DTC
```

Between `Mogru_DTC` and `Shamrao_Builders_DTC` there is a **"Saila bhat DTC"** shown with a yellow triangle (transformer symbol) on Pg 2. The DSS skips from `Mogru` directly to `Shamrao`:
```dss
New Line.L58 bus1=Mogru_DTC bus2=Shamrao_Builders_DTC length=0.803
```
No bus, transformer, or load for `Saila_Bhat_DTC` exists anywhere. The CSV table column headers list 58 DTCs but **"Saila bhat"** is one of them (visible in the diagram between Mogru and Shamrao). The total CSV DTC count (58) matches — but `Saila bhat` appears in the table as "Saila bhat DTC" and must be cross-checked. Checking the CSV row 2: the column sequence after Mogru shows **"Shamrao Builder"** directly — suggesting "Saila bhat" may be a DTC listed but not in the CSV's current Undir feeder section. However the diagram clearly shows it as a separate intermediate node.

> [!IMPORTANT]
> The 0.803 km distance from `Mogru → Shamrao_Builders` is too long for a direct connection given the intermediate "Saila bhat" node visible on the diagram. The line length should be split, with Saila bhat tapped off.

---

## 4. Uniform kVA = 100 kVA for All Batch-1 Transformers

The first batch of transformers (lines 109–159) all use `kvas=[100 100]`. The CSV table shows varying actual kVA values across the covered DTCs:

| DTC Name | CSV kVA | DSS kVA | Error |
|---|---|---|---|
| 3_Way_Kharwada | not in table — junction bus | 100 | Junction transformer — see §5 |
| Ram_Mandir | 200 | 100 | ❌ |
| Dempo_HTC | table: "Location Inaccessible" | 100 | Cannot verify — suspicious |
| RB_Engg | 200 | 100 | ❌ |
| Undir_Bakale | 200 | 100 | ❌ |
| MuleBhat | 200 | 100 | ❌ |
| Maruti_Temple | 200 | 100 | ❌ |
| Chikali | 200 | 100 | ❌ |
| Adpai | 200 | 100 | ❌ |
| Durbhat | 200 | 100 | ❌ |
| Sewerage | 200 | 100 | ❌ |
| Kaswada | 200 | 100 | ❌ |
| Londiyar_Wadem | 200 | 100 | ❌ |
| 3_Way_Talaulim | junction | 100 | Junction transformer — see §5 |
| New_Talaulim | 200 | 100 | ❌ |
| Wadi | 200 | 100 | ❌ |
| Talaulim | 200 | 100 | ❌ |
| Mahalakshmi_Nagar | 200 | 100 | ❌ |
| Paunwada | 200 | 100 | ❌ |
| 3_Way_Don_Khamb | junction | 100 | Junction transformer — see §5 |
| Kavle_Math | 200 | 100 | ❌ |
| Shantadurga_Old | 200 | 100 | ❌ |
| 3_Way_Shantadurga | junction | 100 | Junction transformer — see §5 |
| Sanatan_1 | 200 | 100 | ❌ |
| Sanatan_2 | table: "Transformer Inaccessible" | 100 | Cannot verify |
| Ramnathi_Devasthan | 200 | 100 | ❌ |
| Ramnathi | 200 | 100 | ❌ |
| 3_Way_Ramnathi | junction | 100 | Junction transformer — see §5 |
| RPRS_School | 200 | 100 | ❌ |
| Tolulem | 200 | 100 | ❌ |
| Kharwada | 100 | 100 | ✅ |
| Shantadurga_New | 200 | 100 | ❌ |
| Galshire | 200 | 100 | ❌ |
| 3_Way_Galshire | junction | 100 | Junction — see §5 |
| 3_Way_Harish_Bar | junction | 100 | Junction — see §5 |
| Rajendra_Talak | 630 | 100 | ❌ **Major mismatch** |
| Ritesh_Developers | 400 | 100 | ❌ |
| Venkatesh_Leela | 200 | 100 | ❌ |
| Perigol | 400 | 100 | ❌ |
| Manmohan_Singh | 200 | 100 | ❌ |
| Dhumre | 200 | 100 | ❌ |
| 3_Way_Royal_Enfield | junction | 100 | Junction — see §5 |
| Shashikala_Pai | 200 | 100 | ❌ |
| Kapileshwari | 200 | 100 | ❌ |
| 3_Way_Rathamal | junction | 100 | Junction — see §5 |
| Matruchaya | 200 | 100 | ❌ |
| Shantinagar_Interlink | 200 | 100 | ❌ |
| 3_Way_Shantinagar | junction | 100 | Junction — see §5 |
| Vamneshwar | 200 | 100 | ❌ |
| Golden_Properties | 200 | 100 | ❌ |
| Ritesh | 200 | 100 | ❌ |

**Most critical:** `Rajendra_Talak` is 630 kVA in the table but only 100 kVA in the DSS — a 6× underrating that will severely misrepresent fault currents and losses at that node.

---

## 5. Transformers on Junction/RMU Buses

The following buses are clearly **RMU/switching junction nodes** per the diagram (blue squares with "C.B" or "3-way RMU" labels), not DTC locations, yet the DSS attaches transformers to them:

- `3_Way_Kharwada` (T defined at line 109)
- `3_Way_Talaulim` (line 122)
- `3_Way_Don_Khamb` (line 128)
- `3_Way_Shantadurga` (line 131)
- `3_Way_Ramnathi` (line 136)
- `3_Way_Galshire` (line 142)
- `3_Way_Harish_Bar` (line 143)
- `3_Way_Royal_Enfield` (line 150)
- `3_Way_Rathamal` (line 153)
- `3_Way_Shantinagar` (line 156)

These junction buses should have **no transformer**. The diagram shows them as switching/measurement points, not consumer DTCs.

---

## 6. Missing Batch-2 Transformers for `Konar_Gaunem` Side (Feeder 2)

The batch-2 transformers (lines 162–179) correctly model the Konar-Gaunem side DTCs as 200 kVA `delta-wye` with proper Xhl values from the CSV. **However, `Tilve_RMU` is modelled only as a pass-through bus** — it is visible on Pg 2 as a "3-way RMU Tilve" (circuit-breaker junction) yet no transformer or switching object models it. This is consistent with it being a junction, but the RMU point should be represented as a switch/CB for proper protection modelling.

---

## 7. `L73` Creates a Second Path — Potential Loop

**Line 103:**
```dss
New Line.L73 bus1=3_Way_Harish_Bar bus2=3_Way_Sneh_Mandir length=0.295
```

Page 1 shows `3_Way_Harish_Bar` already feeds `Sneh_Mandir` via `L36` (0.162 km). `L73` creates a **second connection** with `bus2=3_Way_Sneh_Mandir`. If `3_Way_Sneh_Mandir` is the same bus as `Sneh_Mandir`, this creates a parallel branch. If it is a different junction node, the intermediate segment between `3_Way_Harish_Bar → 3_Way_Sneh_Mandir (0.295 km)` as a connector to the Rainguinim-side branch is correct per the diagram — but the bus name should be confirmed.

---

## 8. Load kW Values Not Cross-Referenced to Table % Loading

The Batch-1 (100 kVA) loads use kW values derived from the actual metered currents in the CSV rather than `kVA × %loading × PF`. For example:
- `Ram_Mandir`: Table real power at measurement time = 0.902 kW (instantaneous) — but the DSS uses `kW=38.5` which is peak load. This approach is acceptable if the loadshape compensates, but no explicit calculation basis is documented.

The Batch-2 (200 kVA) loads similarly use flat kW values without a per-transformer table cross-check column in the CSV.

---

## Summary Table

| # | Error Type | Severity | DSS Lines Affected |
|---|---|---|---|
| 1 | Ring topology (L30/L31) has no open-switch model — CB points missing | **High** | Lines 57–58 |
| 2 | `3_Way_Shantinagar` is an island bus — no incoming line, Vamneshwar/Golden_Properties/Ritesh unreachable | **High** | Lines 80–83 |
| 3 | Missing `Saila_Bhat_DTC` — bus, transformer, load absent; L58 skips over it | **High** | Line 90 |
| 4 | All Batch-1 transformers use 100 kVA — most should be 200 kVA (several should be 400/630 kVA) | **High** | Lines 109–159 |
| 4a | `Rajendra_Talak` is 630 kVA in table, 100 kVA in DSS (6× underrating) | **Critical** | Line 144 |
| 5 | Transformers attached to 10 junction/RMU buses that should have no DTC | Medium | Lines 109–159 |
| 6 | `Tilve_RMU` has no switching/CB object — protection point absent | Low | Lines 95–96 |
| 7 | `L73` (3_Way_Harish_Bar → 3_Way_Sneh_Mandir) may create parallel path with L36 | Medium | Line 103 |
| 8 | kW values for Batch-1 loads not verified against table %loading basis | Low | Lines 186–232 |
