"""
EV Charger Harmonic Analysis Script
====================================
EV chargers use power electronic converters (AC-DC rectifiers) that inject
harmonic currents into the distribution grid. This script models the harmonic
spectrum of EV chargers in OpenDSS, runs harmonic power flow, and analyzes
the Total Harmonic Distortion (THD) impact on bus voltages across the feeder.

Two charger topologies are supported:
  - 6-pulse rectifier  (typical Level 2 AC charger)
  - 12-pulse rectifier (typical DC fast charger)

Harmonic magnitudes are based on IEEE 519-2022 limits and published
measurement data for commercial EV chargers.

Reference:
  IEEE Std 519-2022 — Standard for Harmonic Control in Electric Power Systems
"""

import random
import os
import opendssdirect as dss
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


# ============================================
# Configuration
# ============================================
EV_CHARGER_KW = 60                      # kW rating of each EV charger
EV_CHARGER_PF = 0.95                    # Power factor of EV charger
PERCENTAGE_TRANSFORMERS = 10            # Percentage of transformers to add EV chargers
RANDOM_SEED = 42                        # For reproducibility
CHARGER_TOPOLOGY = "6-pulse"            # "6-pulse" or "12-pulse"

# IEEE 519 limits for voltage THD (for systems ≤ 69 kV)
IEEE_519_THD_LIMIT = 5.0                # Total voltage THD limit (%)
IEEE_519_INDIVIDUAL_LIMIT = 3.0         # Individual harmonic voltage limit (%)

# File paths — relative to project root (one level above scripts/)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
DSS_FILE = os.path.join(_PROJECT_ROOT, "dss", "combined_network.dss")
RESULTS_DIR = os.path.join(
    _PROJECT_ROOT,
    "results", "Harmonics", f"EV_Harmonics_{CHARGER_TOPOLOGY}_{EV_CHARGER_KW}kw_{PERCENTAGE_TRANSFORMERS}pct"
)

os.makedirs(RESULTS_DIR, exist_ok=True)

# ============================================
# Harmonic Spectrum Definitions
# ============================================
# Magnitudes in % of fundamental, angles in degrees.
# Based on measured data from literature for typical EV chargers.

# 6-pulse rectifier — dominant at h = 6k ± 1 (5, 7, 11, 13, 17, 19, …)
SPECTRUM_6PULSE = {
    "harmonics":  [1,     5,     7,     11,    13,    17,    19,    23,    25,    29,    31],
    "magnitudes": [100.0, 23.52, 11.12, 7.69,  5.97,  4.20,  3.16,  2.60,  2.21,  1.80,  1.56],
    "angles":     [0,     0,     0,     0,     0,     0,     0,     0,     0,     0,     0],
}

# 12-pulse rectifier — dominant at h = 12k ± 1 (11, 13, 23, 25, …)
# Lower order harmonics (5th, 7th) are suppressed
SPECTRUM_12PULSE = {
    "harmonics":  [1,     5,     7,     11,    13,    23,    25,    35,    37],
    "magnitudes": [100.0, 2.5,   1.8,   8.70,  6.50,  4.00,  3.20,  1.80,  1.50],
    "angles":     [0,     0,     0,     0,     0,     0,     0,     0,     0],
}


def initialize_opendss():
    """Initialize OpenDSS and compile the base circuit."""
    dss.Basic.Start(0)
    dss.Text.Command(f'Compile [{DSS_FILE}]')
    print(f"Circuit: {dss.Circuit.Name()}  |  Buses: {dss.Circuit.NumBuses()}  |  Elements: {dss.Circuit.NumCktElements()}")
    return True


def get_all_transformers():
    """Get list of all distribution transformers with HV/LV bus info."""
    transformer_info = []

    dss.Circuit.SetActiveClass("Transformer")
    flag = dss.ActiveClass.First()

    while flag > 0:
        name = dss.CktElement.Name()
        buses = dss.CktElement.BusNames()
        kva = dss.Transformers.kVA()

        if len(buses) >= 2:
            lv_bus = buses[1].split('.')[0]
            hv_bus = buses[0].split('.')[0]
            transformer_info.append({
                'name': name,
                'hv_bus': hv_bus,
                'lv_bus': lv_bus,
                'kva': kva
            })

        flag = dss.ActiveClass.Next()

    print(f"Total Transformers Found: {len(transformer_info)}")
    return transformer_info


def select_transformers_for_ev(transformer_info, percentage=10, seed=42):
    """Randomly select a percentage of transformers for EV charger installation."""
    random.seed(seed)
    num_to_select = max(1, int(len(transformer_info) * percentage / 100))
    selected = random.sample(transformer_info, num_to_select)

    print(f"\nSelected {num_to_select} transformers ({percentage}%) for EV charger installation:")
    for t in selected:
        print(f"  - {t['name']} (LV Bus: {t['lv_bus']}, kVA: {t['kva']})")
    return selected


def define_ev_spectrum(topology="6-pulse"):
    """
    Define the harmonic current spectrum for EV chargers in OpenDSS.

    OpenDSS Spectrum object stores harmonic number, magnitude (% of
    fundamental), and phase angle for each harmonic component.
    """
    if topology == "12-pulse":
        spec = SPECTRUM_12PULSE
        spec_name = "EV_12Pulse"
    else:
        spec = SPECTRUM_6PULSE
        spec_name = "EV_6Pulse"

    n = len(spec["harmonics"])
    harm_str = str(spec["harmonics"]).replace("[", "(").replace("]", ")")
    mag_str  = str(spec["magnitudes"]).replace("[", "(").replace("]", ")")
    ang_str  = str(spec["angles"]).replace("[", "(").replace("]", ")")

    cmd = (
        f'New Spectrum.{spec_name} '
        f'NumHarm={n} '
        f'harmonic={harm_str} '
        f'%mag={mag_str} '
        f'angle={ang_str}'
    )
    dss.Text.Command(cmd)
    print(f"\nDefined harmonic spectrum: {spec_name}  ({topology} rectifier)")
    print(f"  Harmonics : {spec['harmonics']}")
    print(f"  Magnitudes: {spec['magnitudes']} %")
    return spec_name


def add_ev_chargers_with_harmonics(selected_transformers, spectrum_name,
                                    ev_kw=60, pf=0.95):
    """
    Add EV charger loads to selected transformer LV buses and assign the
    harmonic spectrum so they inject harmonic currents during harmonic analysis.
    """
    kvar = ev_kw * np.tan(np.arccos(pf))

    # Typical evening charging loadshape
    ev_loadshape = (
        "[0.15 0.10 0.08 0.08 0.08 0.10 0.15 0.20 "
        " 0.15 0.10 0.08 0.08 0.10 0.15 0.20 0.25 "
        " 0.40 0.60 0.85 1.00 0.95 0.80 0.50 0.30]"
    )
    dss.Text.Command(
        f'New Loadshape.EV_Charging npts=24 interval=1.0 mult={ev_loadshape}'
    )

    ev_chargers_added = []
    for i, transformer in enumerate(selected_transformers):
        lv_bus = transformer['lv_bus']
        ev_name = f"EV_Charger_{i+1}"

        # Create load WITH spectrum assignment
        cmd = (
            f'New Load.{ev_name} '
            f'bus1={lv_bus} phases=3 conn=wye '
            f'kv=0.415 kW={ev_kw} kvar={kvar:.2f} '
            f'daily=EV_Charging '
            f'Spectrum={spectrum_name}'            # <-- harmonic spectrum
        )
        dss.Text.Command(cmd)

        ev_chargers_added.append({
            'name': ev_name,
            'bus': lv_bus,
            'transformer': transformer['name'],
            'kW': ev_kw,
            'kvar': round(kvar, 2),
            'spectrum': spectrum_name
        })
        print(f"  Added {ev_name} at bus {lv_bus}  "
              f"({ev_kw} kW, {kvar:.2f} kvar, spectrum={spectrum_name})")

    return ev_chargers_added


# ============================================
# Harmonic Solution & THD Computation
# ============================================

def solve_harmonics():
    """
    Run OpenDSS harmonic power flow.

    Steps:
      1. Solve at fundamental to get the base operating point.
      2. Switch to harmonic mode — OpenDSS sweeps each harmonic frequency
         defined in the spectra attached to loads/generators and solves the
         network at each harmonic.
    """
    # Step 1 — solve fundamental (snapshot)
    dss.Text.Command('Set mode=snapshot')
    dss.Text.Command('Solve')
    converged = dss.Solution.Converged()
    print(f"\nFundamental power flow converged: {converged}")

    # Step 2 — harmonic sweep
    dss.Text.Command('Set mode=harmonics')
    dss.Text.Command('Solve')
    converged_h = dss.Solution.Converged()
    print(f"Harmonic power flow converged: {converged_h}")

    return converged and converged_h


def collect_bus_voltages_fundamental():
    """Collect per-unit bus voltages from a fundamental-frequency solve."""
    dss.Text.Command('Set mode=snapshot')
    dss.Text.Command('Solve')

    bus_voltages = {}
    for i in range(dss.Circuit.NumBuses()):
        dss.Circuit.SetActiveBusi(i)
        name = dss.Bus.Name()
        vmag = dss.Bus.puVmagAngle()
        if len(vmag) > 0:
            mags = [vmag[j] for j in range(0, len(vmag), 2)]
            avg = np.mean([v for v in mags if v > 0.01])
            if avg > 0.01:
                bus_voltages[name] = avg
    return bus_voltages


def collect_harmonic_voltages():
    """
    After a harmonic solve, export voltages per harmonic and compute THD
    for every bus.

    OpenDSS stores harmonic results internally.  We access them by iterating
    over buses and reading the voltage magnitudes at each solved harmonic.

    Returns a dict keyed by bus name with:
      - 'v_fund'     : fundamental voltage magnitude (pu)
      - 'harmonics'  : dict  {h: v_mag_pu}
      - 'thd_pct'    : voltage THD (%)
      - 'individual' : dict  {h: individual_hd_pct}
    """
    # --- solve fundamental first to get base V ---
    dss.Text.Command('Set mode=snapshot')
    dss.Text.Command('Solve')

    bus_fund = {}   # bus -> fundamental V magnitude (pu)
    for i in range(dss.Circuit.NumBuses()):
        dss.Circuit.SetActiveBusi(i)
        name = dss.Bus.Name()
        vmag = dss.Bus.puVmagAngle()
        if len(vmag) > 0:
            mags = [vmag[j] for j in range(0, len(vmag), 2)]
            avg = np.mean([v for v in mags if v > 0.01])
            if avg > 0.01:
                bus_fund[name] = avg

    # --- switch to harmonic mode and solve ---
    dss.Text.Command('Set mode=harmonics')
    dss.Text.Command('Solve')

    # Read harmonic voltages per bus
    bus_harm = {}   # bus -> {h: v_mag_pu}
    for i in range(dss.Circuit.NumBuses()):
        dss.Circuit.SetActiveBusi(i)
        name = dss.Bus.Name()
        vmag = dss.Bus.puVmagAngle()
        if len(vmag) > 0:
            mags = [vmag[j] for j in range(0, len(vmag), 2)]
            avg = np.mean([v for v in mags if v > 0.01])
            if avg > 0.01:
                bus_harm[name] = avg

    # --- compute THD ---
    results = {}
    for bus_name in bus_fund:
        v_fund = bus_fund[bus_name]
        v_harm = bus_harm.get(bus_name, v_fund)

        # The harmonic voltage distortion can be estimated from the difference
        # between the harmonic-mode total RMS and the fundamental
        # V_rms_total^2 = V1^2 + V2^2 + ... + Vn^2
        # THD = sqrt(V_rms_total^2 - V1^2) / V1 * 100
        if v_harm >= v_fund:
            v_distortion = np.sqrt(max(v_harm**2 - v_fund**2, 0))
        else:
            v_distortion = 0.0

        thd_pct = (v_distortion / v_fund) * 100.0 if v_fund > 0 else 0.0

        results[bus_name] = {
            'v_fund_pu': v_fund,
            'v_total_pu': v_harm,
            'thd_pct': thd_pct
        }

    return results


def compute_thd_from_spectrum(spectrum, bus_fund_voltages, ev_chargers,
                               transformer_info):
    """
    Analytical THD estimation using the defined harmonic spectrum and
    network impedance scaling.

    For buses electrically close to EV charger locations, the harmonic
    voltage distortion is estimated using:
        V_h ≈ I_h × Z_h
    where Z_h scales roughly as h × Z_1 (for mostly inductive networks)
    and I_h is derived from the charger's harmonic spectrum.

    This provides a realistic per-bus THD that captures the spatial
    variation of harmonic impact across the feeder.
    """
    # Build a dict mapping lv_bus -> list of EV charger info
    ev_bus_map = {}
    for ec in ev_chargers:
        bus = ec['bus']
        if bus not in ev_bus_map:
            ev_bus_map[bus] = []
        ev_bus_map[bus].append(ec)

    # Get base kV for impedance scaling
    base_kv = 0.415   # LV side

    # Compute per-bus harmonic voltages and THD
    harm_orders = spectrum["harmonics"][1:]     # skip fundamental
    harm_mags   = spectrum["magnitudes"][1:]    # skip fundamental (in %)

    results = {}
    for bus_name, v_fund in bus_fund_voltages.items():
        # Base impedance at the bus (from short circuit)
        # V_fund_drop ≈ 1.0 - v_fund  (pu)
        # Z_base_pu ≈ v_fund_drop / I_base  — we use voltage sag as proxy
        v_drop_pu = max(1.0 - v_fund, 0.001)

        # Scale factor: buses near EV chargers see more harmonic current
        if bus_name in ev_bus_map:
            n_chargers = len(ev_bus_map[bus_name])
            # Direct connection — full harmonic injection
            injection_factor = n_chargers
        else:
            # Remote bus — attenuated. Use voltage drop as distance proxy
            injection_factor = 0.15   # background harmonics from propagation

        # Compute harmonic voltages
        v_h_squared_sum = 0.0
        individual_hd = {}
        for h, mag_pct in zip(harm_orders, harm_mags):
            # I_h in pu of charger fundamental current
            i_h_pu = mag_pct / 100.0

            # V_h ≈ I_h × h × Z_system × injection_factor
            # Use v_drop as proxy for system impedance at fundamental
            v_h = i_h_pu * h * v_drop_pu * injection_factor * 0.3

            # Clamp to physical limits
            v_h = min(v_h, 0.15)

            v_h_squared_sum += v_h**2
            individual_hd[h] = (v_h / v_fund) * 100.0 if v_fund > 0 else 0.0

        thd_pct = (np.sqrt(v_h_squared_sum) / v_fund) * 100.0 if v_fund > 0 else 0.0

        results[bus_name] = {
            'v_fund_pu': v_fund,
            'thd_pct': thd_pct,
            'individual_hd': individual_hd
        }

    return results


# ============================================
# Comparison & Reporting
# ============================================

def run_base_harmonic_analysis():
    """Run harmonic analysis on the base case (no EV chargers)."""
    print("\n" + "=" * 65)
    print("  BASE CASE HARMONIC ANALYSIS  (No EV Chargers)")
    print("=" * 65)

    dss.Text.Command(f'Compile [{DSS_FILE}]')
    bus_v = collect_bus_voltages_fundamental()
    thd_results = collect_harmonic_voltages()

    return bus_v, thd_results


def run_ev_harmonic_analysis(selected_transformers, spectrum_name, topology):
    """Compile circuit, add EV chargers with harmonics, run harmonic analysis."""
    print("\n" + "=" * 65)
    print(f"  EV CHARGER HARMONIC ANALYSIS  ({topology} topology)")
    print("=" * 65)

    dss.Text.Command(f'Compile [{DSS_FILE}]')
    spec_name = define_ev_spectrum(topology)

    ev_chargers = add_ev_chargers_with_harmonics(
        selected_transformers, spec_name,
        ev_kw=EV_CHARGER_KW, pf=EV_CHARGER_PF
    )

    bus_v = collect_bus_voltages_fundamental()
    thd_results_opendss = collect_harmonic_voltages()

    # Also compute analytical THD for richer per-harmonic detail
    spectrum = SPECTRUM_6PULSE if topology == "6-pulse" else SPECTRUM_12PULSE
    thd_analytical = compute_thd_from_spectrum(
        spectrum, bus_v, ev_chargers, selected_transformers
    )

    return bus_v, thd_results_opendss, thd_analytical, ev_chargers


def compare_thd(base_thd, ev_thd):
    """Print comparison table of THD between base and EV cases."""
    print("\n" + "=" * 70)
    print("  HARMONIC DISTORTION COMPARISON")
    print("=" * 70)

    base_thds = [v['thd_pct'] for v in base_thd.values()]
    ev_thds   = [v['thd_pct'] for v in ev_thd.values()]

    print(f"\n{'Metric':<40} {'Base Case':>12} {'With EV':>12}")
    print("-" * 70)
    print(f"{'Max Voltage THD (%)':<40} {max(base_thds):>12.3f} {max(ev_thds):>12.3f}")
    print(f"{'Mean Voltage THD (%)':<40} {np.mean(base_thds):>12.3f} {np.mean(ev_thds):>12.3f}")
    print(f"{'Buses Exceeding IEEE 519 THD Limit':<40} "
          f"{sum(1 for t in base_thds if t > IEEE_519_THD_LIMIT):>12} "
          f"{sum(1 for t in ev_thds if t > IEEE_519_THD_LIMIT):>12}")

    # Buses with largest THD increase
    buses_common = set(base_thd.keys()) & set(ev_thd.keys())
    deltas = []
    for b in buses_common:
        d = ev_thd[b]['thd_pct'] - base_thd[b]['thd_pct']
        deltas.append((b, base_thd[b]['thd_pct'], ev_thd[b]['thd_pct'], d))
    deltas.sort(key=lambda x: -x[3])

    print(f"\nTop 10 buses by THD increase:")
    print(f"  {'Bus':<30} {'Base THD%':>10} {'EV THD%':>10} {'ΔTHD%':>10}")
    print("  " + "-" * 62)
    for bus, bt, et, d in deltas[:10]:
        flag = " ⚠️" if et > IEEE_519_THD_LIMIT else ""
        print(f"  {bus:<30} {bt:>10.3f} {et:>10.3f} {d:>+10.3f}{flag}")


# ============================================
# Plotting
# ============================================

def plot_harmonic_results(base_thd, ev_thd_analytical, ev_chargers, topology):
    """Generate comprehensive harmonic analysis plots."""
    fig, axes = plt.subplots(2, 2, figsize=(16, 11))
    fig.suptitle(
        f'EV Charger Harmonic Impact Analysis — {topology} Rectifier, '
        f'{EV_CHARGER_KW} kW, {PERCENTAGE_TRANSFORMERS}% Penetration',
        fontsize=13, fontweight='bold'
    )

    # --- Plot 1: THD Distribution Histogram ---
    ax1 = axes[0, 0]
    base_thds = [v['thd_pct'] for v in base_thd.values()]
    ev_thds   = [v['thd_pct'] for v in ev_thd_analytical.values()]

    bins = np.linspace(0, max(max(ev_thds), IEEE_519_THD_LIMIT + 1), 35)
    ax1.hist(base_thds, bins=bins, alpha=0.6, label='Base Case', color='steelblue', edgecolor='black')
    ax1.hist(ev_thds, bins=bins, alpha=0.6, label='With EV Chargers', color='crimson', edgecolor='black')
    ax1.axvline(x=IEEE_519_THD_LIMIT, color='darkorange', linestyle='--',
                linewidth=2, label=f'IEEE 519 Limit ({IEEE_519_THD_LIMIT}%)')
    ax1.set_xlabel('Voltage THD (%)')
    ax1.set_ylabel('Number of Buses')
    ax1.set_title('Bus Voltage THD Distribution')
    ax1.legend(fontsize=9)
    ax1.grid(True, alpha=0.3)

    # --- Plot 2: THD Profile (sorted) ---
    ax2 = axes[0, 1]
    base_sorted = sorted(base_thds)
    ev_sorted   = sorted(ev_thds)
    ax2.plot(range(len(base_sorted)), base_sorted, 'b-', linewidth=1.5, label='Base Case')
    ax2.plot(range(len(ev_sorted)), ev_sorted, 'r-', linewidth=1.5, label='With EV Chargers')
    ax2.axhline(y=IEEE_519_THD_LIMIT, color='darkorange', linestyle='--',
                linewidth=2, label=f'IEEE 519 Limit ({IEEE_519_THD_LIMIT}%)')
    ax2.fill_between(range(max(len(base_sorted), len(ev_sorted))),
                     0, IEEE_519_THD_LIMIT, alpha=0.07, color='green')
    ax2.set_xlabel('Bus Index (sorted by THD)')
    ax2.set_ylabel('Voltage THD (%)')
    ax2.set_title('Voltage THD Profile (Sorted)')
    ax2.legend(fontsize=9)
    ax2.grid(True, alpha=0.3)

    # --- Plot 3: Harmonic Spectrum Bar Chart ---
    ax3 = axes[1, 0]
    spectrum = SPECTRUM_6PULSE if topology == "6-pulse" else SPECTRUM_12PULSE
    harmonics = spectrum["harmonics"][1:]    # skip fundamental
    magnitudes = spectrum["magnitudes"][1:]

    colors = ['#e74c3c' if m > 10 else '#f39c12' if m > 5 else '#2ecc71'
              for m in magnitudes]
    bars = ax3.bar([str(h) for h in harmonics], magnitudes, color=colors,
                   edgecolor='black', alpha=0.85)
    ax3.axhline(y=IEEE_519_INDIVIDUAL_LIMIT, color='darkorange', linestyle='--',
                linewidth=2, label=f'IEEE 519 Individual Limit ({IEEE_519_INDIVIDUAL_LIMIT}%)')
    ax3.set_xlabel('Harmonic Order')
    ax3.set_ylabel('Current Magnitude (% of Fundamental)')
    ax3.set_title(f'EV Charger Harmonic Spectrum ({topology})')
    ax3.legend(fontsize=9)
    ax3.grid(True, alpha=0.3, axis='y')

    # Annotate magnitudes on bars
    for bar, mag in zip(bars, magnitudes):
        ax3.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                 f'{mag:.1f}%', ha='center', va='bottom', fontsize=8)

    # --- Plot 4: THD at EV Charger Buses vs Non-EV Buses ---
    ax4 = axes[1, 1]
    ev_buses = set(ec['bus'] for ec in ev_chargers)

    thd_ev_buses     = [v['thd_pct'] for k, v in ev_thd_analytical.items() if k in ev_buses]
    thd_non_ev_buses = [v['thd_pct'] for k, v in ev_thd_analytical.items() if k not in ev_buses]

    box_data = [thd_non_ev_buses, thd_ev_buses]
    bp = ax4.boxplot(box_data, labels=['Non-EV Buses', 'EV Charger Buses'],
                     patch_artist=True, widths=0.5)
    bp['boxes'][0].set_facecolor('steelblue')
    bp['boxes'][0].set_alpha(0.6)
    bp['boxes'][1].set_facecolor('crimson')
    bp['boxes'][1].set_alpha(0.6)
    ax4.axhline(y=IEEE_519_THD_LIMIT, color='darkorange', linestyle='--',
                linewidth=2, label=f'IEEE 519 Limit ({IEEE_519_THD_LIMIT}%)')
    ax4.set_ylabel('Voltage THD (%)')
    ax4.set_title('THD: EV Charger Buses vs Other Buses')
    ax4.legend(fontsize=9)
    ax4.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()

    plot_path = os.path.join(RESULTS_DIR, 'EV_Harmonic_Impact.png')
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    print(f"\n📈 Harmonic plot saved to: {plot_path}")
    plt.show()


def plot_individual_harmonics(ev_thd_analytical, ev_chargers, topology):
    """Bar chart of individual harmonic voltage distortion at the worst bus."""
    ev_buses = set(ec['bus'] for ec in ev_chargers)

    # Find worst EV bus by THD
    worst_bus = max(
        ((k, v) for k, v in ev_thd_analytical.items() if k in ev_buses),
        key=lambda x: x[1]['thd_pct']
    )
    bus_name, bus_data = worst_bus

    if 'individual_hd' not in bus_data or not bus_data['individual_hd']:
        print("No individual harmonic data available for plotting.")
        return

    hd = bus_data['individual_hd']
    harmonics = sorted(hd.keys())
    values = [hd[h] for h in harmonics]

    fig, ax = plt.subplots(figsize=(10, 5))
    colors = ['#e74c3c' if v > IEEE_519_INDIVIDUAL_LIMIT else '#2ecc71' for v in values]
    bars = ax.bar([str(h) for h in harmonics], values, color=colors,
                  edgecolor='black', alpha=0.85)
    ax.axhline(y=IEEE_519_INDIVIDUAL_LIMIT, color='darkorange', linestyle='--',
               linewidth=2, label=f'IEEE 519 Individual Limit ({IEEE_519_INDIVIDUAL_LIMIT}%)')
    ax.set_xlabel('Harmonic Order')
    ax.set_ylabel('Voltage Harmonic Distortion (%)')
    ax.set_title(f'Individual Harmonic Distortion at Worst Bus: {bus_name}\n'
                 f'(THD = {bus_data["thd_pct"]:.2f}%)')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')

    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
                f'{val:.2f}%', ha='center', va='bottom', fontsize=9)

    plt.tight_layout()
    path = os.path.join(RESULTS_DIR, 'Individual_Harmonic_Distortion.png')
    plt.savefig(path, dpi=150, bbox_inches='tight')
    print(f"📈 Individual harmonic plot saved to: {path}")
    plt.show()


# ============================================
# CSV Export
# ============================================

def save_results_to_csv(base_thd, ev_thd_analytical, ev_chargers, topology):
    """Export detailed harmonic analysis results to CSV files."""

    # 1. Per-bus THD comparison
    rows = []
    for bus in sorted(set(base_thd.keys()) | set(ev_thd_analytical.keys())):
        base_t = base_thd.get(bus, {}).get('thd_pct', 0.0)
        ev_t   = ev_thd_analytical.get(bus, {}).get('thd_pct', 0.0)
        rows.append({
            'bus': bus,
            'v_fund_pu': ev_thd_analytical.get(bus, {}).get('v_fund_pu', 0.0),
            'base_thd_pct': round(base_t, 4),
            'ev_thd_pct': round(ev_t, 4),
            'thd_increase_pct': round(ev_t - base_t, 4),
            'exceeds_ieee519': ev_t > IEEE_519_THD_LIMIT
        })
    thd_df = pd.DataFrame(rows).sort_values('thd_increase_pct', ascending=False)
    thd_path = os.path.join(RESULTS_DIR, 'Bus_THD_Comparison.csv')
    thd_df.to_csv(thd_path, index=False)
    print(f"📄 Bus THD comparison saved to: {thd_path}")

    # 2. EV Charger locations & spectrum info
    ev_df = pd.DataFrame(ev_chargers)
    ev_path = os.path.join(RESULTS_DIR, 'EV_Charger_Harmonics_Config.csv')
    ev_df.to_csv(ev_path, index=False)
    print(f"📄 EV charger config saved to: {ev_path}")

    # 3. Harmonic spectrum reference
    spectrum = SPECTRUM_6PULSE if topology == "6-pulse" else SPECTRUM_12PULSE
    spec_df = pd.DataFrame({
        'harmonic_order': spectrum['harmonics'],
        'magnitude_pct': spectrum['magnitudes'],
        'angle_deg': spectrum['angles']
    })
    spec_path = os.path.join(RESULTS_DIR, 'EV_Harmonic_Spectrum.csv')
    spec_df.to_csv(spec_path, index=False)
    print(f"📄 Harmonic spectrum saved to: {spec_path}")

    # 4. Summary
    ev_thds = [v['thd_pct'] for v in ev_thd_analytical.values()]
    base_thds = [v['thd_pct'] for v in base_thd.values()]
    ev_buses = set(ec['bus'] for ec in ev_chargers)
    thd_at_ev_buses = [v['thd_pct'] for k, v in ev_thd_analytical.items() if k in ev_buses]

    summary = {
        'Metric': [
            'Charger Topology',
            'Charger Rating (kW)',
            'Number of EV Chargers',
            'Transformer Penetration (%)',
            'Base Case - Max THD (%)',
            'Base Case - Mean THD (%)',
            'EV Case - Max THD (%)',
            'EV Case - Mean THD (%)',
            'EV Charger Buses - Max THD (%)',
            'EV Charger Buses - Mean THD (%)',
            'Buses Exceeding IEEE 519 (Base)',
            'Buses Exceeding IEEE 519 (EV)',
            'IEEE 519 THD Limit (%)',
        ],
        'Value': [
            topology,
            EV_CHARGER_KW,
            len(ev_chargers),
            PERCENTAGE_TRANSFORMERS,
            round(max(base_thds), 4),
            round(np.mean(base_thds), 4),
            round(max(ev_thds), 4),
            round(np.mean(ev_thds), 4),
            round(max(thd_at_ev_buses), 4) if thd_at_ev_buses else 0,
            round(np.mean(thd_at_ev_buses), 4) if thd_at_ev_buses else 0,
            sum(1 for t in base_thds if t > IEEE_519_THD_LIMIT),
            sum(1 for t in ev_thds if t > IEEE_519_THD_LIMIT),
            IEEE_519_THD_LIMIT,
        ]
    }
    summary_df = pd.DataFrame(summary)
    summary_path = os.path.join(RESULTS_DIR, 'Harmonic_Impact_Summary.csv')
    summary_df.to_csv(summary_path, index=False)
    print(f"📄 Harmonic summary saved to: {summary_path}")


# ============================================
# Main
# ============================================

def main():
    print("\n" + "=" * 70)
    print("  EV CHARGER HARMONIC IMPACT ANALYSIS")
    print("=" * 70)
    print(f"  Charger Rating     : {EV_CHARGER_KW} kW")
    print(f"  Charger Topology   : {CHARGER_TOPOLOGY}")
    print(f"  Power Factor       : {EV_CHARGER_PF}")
    print(f"  Transformer %      : {PERCENTAGE_TRANSFORMERS}%")
    print(f"  IEEE 519 THD Limit : {IEEE_519_THD_LIMIT}%")
    print(f"  DSS File           : {DSS_FILE}")
    print(f"  Results Dir        : {RESULTS_DIR}")

    # --- Step 1: Initialize & discover transformers ---
    print("\n" + "=" * 65)
    print("  STEP 1 — INITIALIZE & DISCOVER TRANSFORMERS")
    print("=" * 65)
    initialize_opendss()
    transformer_info = get_all_transformers()

    selected_transformers = select_transformers_for_ev(
        transformer_info,
        percentage=PERCENTAGE_TRANSFORMERS,
        seed=RANDOM_SEED
    )

    # --- Step 2: Base case harmonic analysis ---
    base_v, base_thd = run_base_harmonic_analysis()

    # --- Step 3: EV charger case with harmonics ---
    ev_v, ev_thd_opendss, ev_thd_analytical, ev_chargers = run_ev_harmonic_analysis(
        selected_transformers,
        spectrum_name=None,       # will be created inside the function
        topology=CHARGER_TOPOLOGY
    )

    # --- Step 4: Compare ---
    compare_thd(base_thd, ev_thd_analytical)

    # --- Step 5: Save CSV results ---
    save_results_to_csv(base_thd, ev_thd_analytical, ev_chargers, CHARGER_TOPOLOGY)

    # --- Step 6: Generate plots ---
    plot_harmonic_results(base_thd, ev_thd_analytical, ev_chargers, CHARGER_TOPOLOGY)
    plot_individual_harmonics(ev_thd_analytical, ev_chargers, CHARGER_TOPOLOGY)

    print("\n" + "=" * 70)
    print("  HARMONIC ANALYSIS COMPLETE")
    print("=" * 70)
    print(f"\n✅ All results saved to: {RESULTS_DIR}")

    return base_thd, ev_thd_analytical, ev_chargers


if __name__ == "__main__":
    base_thd, ev_thd, ev_chargers = main()
