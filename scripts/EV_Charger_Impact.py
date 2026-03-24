"""
EV Charger Impact Analysis Script
================================
This script uses OpenDSS-Direct to analyze the impact of adding EV chargers
to a percent of the distribution transformers in the combined feeder system. The 
wattage of EV chargers and percentage of transforrmers can be configured at the 
top of the script. The script runs a base case without EV chargers, then adds EV chargers.


"""
import random
import os
import importlib
from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

try:
    dss = importlib.import_module("opendssdirect")
except ModuleNotFoundError as exc:
    raise ModuleNotFoundError(
        "OpenDSSDirect.py is not installed in the active environment. "
        "Install it with: pip install OpenDSSDirect.py"
    ) from exc


# ============================================
# Configuration
# ============================================
EV_CHARGER_KW = 60          # kW rating of each EV charger
EV_CHARGER_PF = 0.95        # Power factor of EV charger
PERCENTAGE_TRANSFORMERS = 10  # Percentage of transformers to add EV chargers
RANDOM_SEED = 42            # For reproducibility

# File paths — relative to project root (one level above scripts/)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
DSS_FILE = os.path.join(_PROJECT_ROOT, "dss", "combined_network.dss")
RESULTS_DIR = os.path.join(_PROJECT_ROOT, "results", "Chargers", f"EV_Impact__{EV_CHARGER_KW}kw_{PERCENTAGE_TRANSFORMERS}%")

# Create results directory if it doesn't exist
os.makedirs(RESULTS_DIR, exist_ok=True)


def initialize_opendss():
    """Initialize OpenDSS and compile the base circuit."""
    dss.Basic.Start(0)                                       #Start OpenDSS engine
    dss.Text.Command(f'Compile [{DSS_FILE}]')                #Compile the specified DSS file
    print(f"Circuit Name: {dss.Circuit.Name()}")
    print(f"Number of Buses: {dss.Circuit.NumBuses()}")
    print(f"Number of Elements: {dss.Circuit.NumCktElements()}")
    return True


def get_all_transformers():
    """Get list of all distribution transformers (excluding substation transformers)."""
    transformers = []           #List to store transformer names
    transformer_info = []       #List to store detailed transformer info (name, buses, kVA)
    
    dss.Circuit.SetActiveClass("Transformer")  #Filters for Transformers only
    flag = dss.ActiveClass.First()             #Iterate through all transformers in the circuit
    
    while flag > 0:                            #While there are still transformers to process
        name = dss.CktElement.Name()           #Get the name of the current transformer
        buses = dss.CktElement.BusNames()      #Get the bus names associated with the transformer (primary and secondary)
        kva = dss.Transformers.kVA()           #Get the kVA rating of the transformer
        
        # Get the LV bus (secondary side) - typically the second bus
        if len(buses) >= 2:                   #if length of buses is greater than or equal to 2 (to ensure we have both primary and secondary)
            lv_bus = buses[1].split('.')[0]  # Remove phase designations
            hv_bus = buses[0].split('.')[0]    
            
            transformer_info.append({        #Stores in list of dictionary
                'name': name,
                'hv_bus': hv_bus,
                'lv_bus': lv_bus,
                'kva': kva
            })
            transformers.append(name)      #Stores in a list of transformer names
        
        flag = dss.ActiveClass.Next()      #Move to the next transformer in the circuit.

        #When flag becomes 0, it means we have processed all transformers and the loop will exit.
    
    print(f"\nTotal Transformers Found: {len(transformers)}")      
    return transformers, transformer_info


def select_transformers_for_ev(transformer_info, percentage=10, seed=42):      #Default. Change when calling.
    """Randomly select a percentage of transformers for EV charger installation."""
    random.seed(seed)                     #Set random seed for reproducibility
    
    num_to_select = max(1, int(len(transformer_info) * percentage / 100))   #Calculate number of transformers to select based on percentage
    selected = random.sample(transformer_info, num_to_select)    #Randomly select transformers from the list of transformer info
    
    print(f"\nSelected {num_to_select} transformers ({percentage}%) for EV charger installation:")
    for t in selected:
        print(f"  - {t['name']} (LV Bus: {t['lv_bus']}, kVA: {t['kva']})")
    
    return selected


def run_base_case():
    """Run simulation without EV chargers and collect results."""
    print("\n" + "="*60)                              #
    print("RUNNING BASE CASE (Without EV Chargers)")
    print("="*60)
    
    # Recompile to ensure clean state
    dss.Text.Command(f'Compile [{DSS_FILE}]')
    
    # Run daily simulation
    dss.Text.Command('Set mode=daily')
    dss.Text.Command('Set stepsize=1h')
    dss.Text.Command('Set number=24')
    dss.Text.Command('Solve')
    
    # Collect results
    results = collect_results("Base Case")
    return results


def add_ev_chargers(selected_transformers, ev_kw=60, pf=0.95):
    """Add EV charger loads to selected transformer LV buses."""
    print("\n" + "="*60)
    print("ADDING EV CHARGERS")
    print("="*60)
    
    # Calculate kvar from power factor
    kvar = ev_kw * np.tan(np.arccos(pf))
    
    # EV Charger Loadshape - Typical evening charging pattern (peak 6 PM - 10 PM)
    # Hours: 12AM 1AM 2AM 3AM 4AM 5AM 6AM 7AM 8AM 9AM 10AM 11AM 12PM 1PM 2PM 3PM 4PM 5PM 6PM 7PM 8PM 9PM 10PM 11PM
    ev_loadshape = "[0.15 0.10 0.08 0.08 0.08 0.10 0.15 0.20 0.15 0.10 0.08 0.08 0.10 0.15 0.20 0.25 0.40 0.60 0.85 1.00 0.95 0.80 0.50 0.30]"
    
    # Define loadshape in OpenDSS with 24 hourly points representing typical evening charging pattern
    # with higher loads during peak hours (6 PM - 10 PM) when most EVs are likely to be charging
    dss.Text.Command(f'New Loadshape.EV_Charging npts=24 interval=1.0 mult={ev_loadshape}')  
    print("Created EV charging loadshape (evening peak pattern)")
    
    # Add EV charger loads to selected transformers
    ev_chargers_added = []
    for i, transformer in enumerate(selected_transformers):  #
        lv_bus = transformer['lv_bus']
        ev_name = f"EV_Charger_{i+1}"
        
        # Add EV charger as a 3-phase load on the LV bus
        cmd = f'New Load.{ev_name} bus1={lv_bus} phases=3 conn=wye kv=0.415 kW={ev_kw} kvar={kvar:.2f} daily=EV_Charging'
        dss.Text.Command(cmd)
        
        ev_chargers_added.append({
            'name': ev_name,
            'bus': lv_bus,
            'transformer': transformer['name'],
            'kW': ev_kw,
            'kvar': round(kvar, 2)
        })
        print(f"  Added {ev_name} at bus {lv_bus} ({ev_kw} kW, {kvar:.2f} kvar)")
    
    return ev_chargers_added


def run_ev_case():
    """Run simulation with EV chargers and collect results."""
    print("\n" + "="*60)
    print("RUNNING EV CHARGER CASE")
    print("="*60)
    
    # Run daily simulation
    dss.Text.Command('Set mode=daily')
    dss.Text.Command('Set stepsize=1h')
    dss.Text.Command('Set number=24')
    dss.Text.Command('Solve')
    
    # Collect results
    results = collect_results("With EV Chargers")
    return results


def collect_results(case_name):
    """Collect simulation results."""
    results = {
        'case_name': case_name,
        'total_load_kw': 0,
        'total_load_kvar': 0,
        'total_losses_kw': 0,
        'total_losses_kvar': 0,           #Initialize total losses in kW and kvar
        'min_voltage_pu': float('inf'),   #Initialize min voltage to infinity for comparison
        'max_voltage_pu': 0,
        'buses_under_voltage': [],        #List to store buses that are under-voltage (below 0.95 pu)
        'buses_over_voltage': [],
        'transformer_loading': []         #List to store transformer loading information (name, kVA rating, loading in kVA and percentage)
    }
    
    # Get total power from the circuit
    total_power = dss.Circuit.TotalPower()           #Returns total power in watts and vars (P_total, Q_total)
    results['total_load_kw'] = abs(total_power[0])
    results['total_load_kvar'] = abs(total_power[1])
    
    # Get losses from the circuit (returns losses in watts and vars)
    losses = dss.Circuit.Losses()
    results['total_losses_kw'] = losses[0] / 1000  # Convert to kW
    results['total_losses_kvar'] = losses[1] / 1000  # Convert to kvar
    
    # Get all bus voltages
    bus_voltages = []
    for i in range(dss.Circuit.NumBuses()):
        dss.Circuit.SetActiveBusi(i)        #Set active bus by index to get its properties
        bus_name = dss.Bus.Name()
        pu_voltages = dss.Bus.puVmagAngle()     #Returns list of voltage magnitudes and angles in pu (V1_mag, V1_angle, V2_mag, V2_angle, ...)
        
        if len(pu_voltages) > 0:
            # Get magnitude values (every other value starting from 0)
            magnitudes = [pu_voltages[j] for j in range(0, len(pu_voltages), 2)]
            avg_voltage = np.mean([v for v in magnitudes if v > 0.01])  # Filter out zeros by only averaging valid voltages above 0.01 pu
            
            if avg_voltage > 0.01:  # Valid voltage
                bus_voltages.append({'bus': bus_name, 'voltage_pu': avg_voltage})
                
                if avg_voltage < results['min_voltage_pu']:
                    results['min_voltage_pu'] = avg_voltage
                if avg_voltage > results['max_voltage_pu']:
                    results['max_voltage_pu'] = avg_voltage
                
                # Check voltage limits (0.95 - 1.05 pu)
                if avg_voltage < 0.95:
                    results['buses_under_voltage'].append((bus_name, avg_voltage))
                elif avg_voltage > 1.05:
                    results['buses_over_voltage'].append((bus_name, avg_voltage))
    
    # Get transformer loading
    dss.Circuit.SetActiveClass("Transformer")    #Set active class to Transformer to iterate through all transformers and get their loading information
    flag = dss.ActiveClass.First()
    while flag > 0:
        name = dss.CktElement.Name()
        powers = dss.CktElement.Powers()      #Returns list of powers for each phase (P1, Q1, P2, Q2, P3, Q3) in watts and vars
        kva_rating = dss.Transformers.kVA()
        
        # Calculate apparent power (first 3 phases on primary)
        if len(powers) >= 6:
            s_total = 0
            for j in range(0, 6, 2):  # P values
                p = powers[j]                           #Active power for the phase
                q = powers[j+1] if j+1 < len(powers) else 0    #Reactive power for the phase (if available)
                s_total += np.sqrt(p**2 + q**2)            #Calculate apparent power for the phase and add to total    
            
            loading_pct = (s_total / kva_rating) * 100 if kva_rating > 0 else 0  #Calculate loading percentage based on kVA rating
            results['transformer_loading'].append({
                'name': name,
                'kva_rating': kva_rating,
                'loading_kva': s_total,
                'loading_pct': loading_pct
            })
        
        flag = dss.ActiveClass.Next() 
    
    results['bus_voltages'] = bus_voltages  #Store bus voltage information in results for later analysis and plotting
    
    return results


def compare_results(base_results, ev_results):
    """Compare and display results between base case and EV case."""
    print("\n" + "="*70)
    print("COMPARISON: BASE CASE vs EV CHARGER CASE")
    print("="*70)
    
    print("\n📊 SYSTEM SUMMARY")
    print("-"*70)
    print(f"{'Metric':<35} {'Base Case':>15} {'With EV':>15} {'Change':>15}")  #Header for comparison table
    print("-"*70)
    
    # Total Load
    load_change = ev_results['total_load_kw'] - base_results['total_load_kw']
    load_change_pct = (load_change / base_results['total_load_kw']) * 100
    print(f"{'Total Load (kW)':<35} {base_results['total_load_kw']:>15.2f} {ev_results['total_load_kw']:>15.2f} {f'+{load_change:.2f} ({load_change_pct:+.1f}%)':>15}")
    
    # Losses
    loss_change = ev_results['total_losses_kw'] - base_results['total_losses_kw']
    loss_change_pct = (loss_change / base_results['total_losses_kw']) * 100 if base_results['total_losses_kw'] > 0 else 0
    print(f"{'Total Losses (kW)':<35} {base_results['total_losses_kw']:>15.2f} {ev_results['total_losses_kw']:>15.2f} {f'+{loss_change:.2f} ({loss_change_pct:+.1f}%)':>15}")
    
    # Voltage
    print(f"\n{'Minimum Voltage (p.u.)':<35} {base_results['min_voltage_pu']:>15.4f} {ev_results['min_voltage_pu']:>15.4f} {(ev_results['min_voltage_pu'] - base_results['min_voltage_pu']):>+15.4f}")
    print(f"{'Maximum Voltage (p.u.)':<35} {base_results['max_voltage_pu']:>15.4f} {ev_results['max_voltage_pu']:>15.4f} {(ev_results['max_voltage_pu'] - base_results['max_voltage_pu']):>+15.4f}")
    
    # Voltage violations
    print(f"\n{'Buses Under-voltage (<0.95 pu)':<35} {len(base_results['buses_under_voltage']):>15} {len(ev_results['buses_under_voltage']):>15}")
    print(f"{'Buses Over-voltage (>1.05 pu)':<35} {len(base_results['buses_over_voltage']):>15} {len(ev_results['buses_over_voltage']):>15}")
    
    # Show problematic buses with EV chargers
    if ev_results['buses_under_voltage']:
        print("\n⚠️  BUSES WITH UNDER-VOLTAGE (With EV Chargers):")
        for bus, voltage in sorted(ev_results['buses_under_voltage'], key=lambda x: x[1])[:10]:  #Show top 10 worst cases
            print(f"    {bus}: {voltage:.4f} p.u.")   #Print bus name and voltage for buses that are under-voltage in the EV case, sorted by voltage (worst first)
    
    return {
        'load_increase_kw': load_change,
        'load_increase_pct': load_change_pct,
        'loss_increase_kw': loss_change,
        'loss_increase_pct': loss_change_pct,
        'min_voltage_drop': base_results['min_voltage_pu'] - ev_results['min_voltage_pu'],
        'new_undervoltage_buses': len(ev_results['buses_under_voltage']) - len(base_results['buses_under_voltage'])
    }


def plot_voltage_comparison(base_results, ev_results, ev_chargers):
    """Create voltage comparison plots."""
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))  #Create a 1x3 grid of subplots for voltage and summary visualizations
    fig.suptitle('EV Charger Impact Analysis - Voltage Comparison', fontsize=14, fontweight='bold')
    
    # Plot 1: Voltage Distribution Histogram
    ax1 = axes[0]
    base_voltages = [v['voltage_pu'] for v in base_results['bus_voltages'] if 0.8 < v['voltage_pu'] < 1.1] #Filter out extreme values for better visualization (only show voltages between 0.8 and 1.1 pu)
    ev_voltages = [v['voltage_pu'] for v in ev_results['bus_voltages'] if 0.8 < v['voltage_pu'] < 1.1]     #Filter out extreme values for better visualization (only show voltages between 0.8 and 1.1 pu)
    
    ax1.hist(base_voltages, bins=30, alpha=0.6, label='Base Case', color='blue', edgecolor='black')        #Plot histogram of bus voltages for base case
    ax1.hist(ev_voltages, bins=30, alpha=0.6, label='With EV Chargers', color='red', edgecolor='black')    #Plot histogram of bus voltages for EV case
    ax1.axvline(x=0.95, color='orange', linestyle='--', linewidth=2, label='Lower Limit (0.95 pu)')        #Add vertical line to indicate lower voltage limit (0.95 pu)
    ax1.axvline(x=1.05, color='orange', linestyle='--', linewidth=2, label='Upper Limit (1.05 pu)')        #Add vertical line to indicate upper voltage limit (1.05 pu)
    ax1.set_xlabel('Voltage (p.u.)')          #Set x-axis label for voltage histogram
    ax1.set_ylabel('Number of Buses')         #Set y-axis label for voltage histogram
    ax1.set_title('Bus Voltage Distribution')   #Set title for voltage histogram
    ax1.legend()                                #Add legend to voltage histogram
    ax1.grid(True, alpha=0.3)          #Add grid to voltage histogram for better readability (with some transparency)
    
    # Plot 2: Voltage Profile (sorted)
    ax2 = axes[1]
    base_sorted = sorted(base_voltages)
    ev_sorted = sorted(ev_voltages)
    ax2.plot(range(len(base_sorted)), base_sorted, 'b-', linewidth=1.5, label='Base Case')    #Plot voltage profile for base case (sorted by voltage)
    ax2.plot(range(len(ev_sorted)), ev_sorted, 'r-', linewidth=1.5, label='With EV Chargers')  #Plot voltage profile for EV case (sorted by voltage)
    ax2.axhline(y=0.95, color='orange', linestyle='--', linewidth=2)
    ax2.axhline(y=1.05, color='orange', linestyle='--', linewidth=2)
    ax2.fill_between(range(len(base_sorted)), 0.95, 1.05, alpha=0.1, color='green')
    ax2.set_xlabel('Bus Index (sorted by voltage)')
    ax2.set_ylabel('Voltage (p.u.)')
    ax2.set_title('Voltage Profile (Sorted)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(0.90, 1.06)
    
    # Plot 3: Summary Bar Chart
    ax4 = axes[2]
    metrics = ['Total Load\n(MW)', 'Losses\n(kW)', 'Min Voltage\n(p.u.)', 'Under-voltage\nBuses']
    base_values = [
        base_results['total_load_kw'] / 1000,
        base_results['total_losses_kw'],
        base_results['min_voltage_pu'],
        len(base_results['buses_under_voltage'])
    ]
    ev_values = [
        ev_results['total_load_kw'] / 1000,
        ev_results['total_losses_kw'],
        ev_results['min_voltage_pu'],
        len(ev_results['buses_under_voltage'])
    ]
    
    x = np.arange(len(metrics))
    width = 0.35
    
    ax4.bar(x - width/2, base_values, width, label='Base Case', color='blue', alpha=0.7)
    ax4.bar(x + width/2, ev_values, width, label='With EV Chargers', color='red', alpha=0.7)
    ax4.set_ylabel('Value')
    ax4.set_title('System Metrics Comparison')
    ax4.set_xticks(x)
    ax4.set_xticklabels(metrics)
    ax4.legend()
    ax4.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    
    # Save plot
    plot_path = os.path.join(RESULTS_DIR, 'EV_Charger_Impact_Analysis.png')
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    print(f"\n📈 Plot saved to: {plot_path}")
    
    plt.show()
    
    # --- Separate Transformer Loading Plot (scales with number of transformers) ---
    plot_transformer_loading(base_results, ev_results, ev_chargers)


def plot_transformer_loading(base_results, ev_results, ev_chargers):
    """Create a separate, dynamically-sized transformer loading comparison plot."""
    # Get transformers that have EV chargers
    ev_transformer_names = [ec['transformer'] for ec in ev_chargers]
    
    base_loading = {t['name']: t['loading_pct'] for t in base_results['transformer_loading']}
    ev_loading = {t['name']: t['loading_pct'] for t in ev_results['transformer_loading']}
    
    # Filter to transformers with EV chargers
    ev_trans_loading_base = [base_loading.get(name, 0) for name in ev_transformer_names if name in base_loading]
    ev_trans_loading_ev = [ev_loading.get(name, 0) for name in ev_transformer_names if name in ev_loading]
    labels = [name.replace('Transformer.', '')[:20] for name in ev_transformer_names if name in base_loading]
    
    n = len(labels)
    # Dynamic figure width: ~0.9 inch per transformer, min 8, max 30
    fig_width = max(8, min(30, n * 0.9 + 3))
    fig, ax = plt.subplots(figsize=(fig_width, 6))
    
    x = np.arange(n)
    width = 0.35
    
    ax.bar(x - width/2, ev_trans_loading_base, width, label='Base Case', color='blue', alpha=0.7)
    ax.bar(x + width/2, ev_trans_loading_ev, width, label='With EV Chargers', color='red', alpha=0.7)
    ax.axhline(y=100, color='orange', linestyle='--', linewidth=2, label='Rated Capacity')
    ax.set_xlabel('Transformer')
    ax.set_ylabel('Loading (%)')
    ax.set_title(f'Transformer Loading at EV Charger Locations ({n} transformers)')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha='right')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    
    plot_path = os.path.join(RESULTS_DIR, 'Transformer_Loading_Comparison.png')
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    print(f"📈 Transformer loading plot saved to: {plot_path}")
    
    plt.show()


def save_results_to_csv(base_results, ev_results, ev_chargers, comparison):
    """Save detailed results to CSV files."""
    
    # Save EV Charger locations
    ev_df = pd.DataFrame(ev_chargers)
    ev_path = os.path.join(RESULTS_DIR, 'EV_Charger_Locations.csv')
    ev_df.to_csv(ev_path, index=False)
    print(f"📄 EV Charger locations saved to: {ev_path}")
    
    # Save voltage comparison
    base_voltages_df = pd.DataFrame(base_results['bus_voltages'])
    base_voltages_df.columns = ['bus', 'base_voltage_pu']
    ev_voltages_df = pd.DataFrame(ev_results['bus_voltages'])
    ev_voltages_df.columns = ['bus', 'ev_voltage_pu']
    
    voltage_comparison = pd.merge(base_voltages_df, ev_voltages_df, on='bus', how='outer')
    voltage_comparison['voltage_drop_pu'] = voltage_comparison['base_voltage_pu'] - voltage_comparison['ev_voltage_pu']
    voltage_comparison = voltage_comparison.sort_values('voltage_drop_pu', ascending=False)
    
    voltage_path = os.path.join(RESULTS_DIR, 'Voltage_Comparison.csv')
    voltage_comparison.to_csv(voltage_path, index=False)
    print(f"📄 Voltage comparison saved to: {voltage_path}")
    
    # Save summary
    summary = {
        'Metric': [
            'Total Load Base (kW)',
            'Total Load with EV (kW)',
            'Load Increase (kW)',
            'Load Increase (%)',
            'Total Losses Base (kW)',
            'Total Losses with EV (kW)',
            'Loss Increase (kW)',
            'Loss Increase (%)',
            'Min Voltage Base (p.u.)',
            'Min Voltage with EV (p.u.)',
            'Voltage Drop (p.u.)',
            'Under-voltage Buses Base',
            'Under-voltage Buses with EV',
            'Number of EV Chargers',
            'EV Charger Rating (kW)',
            'Total EV Load (kW)'
        ],
        'Value': [
            base_results['total_load_kw'],
            ev_results['total_load_kw'],
            comparison['load_increase_kw'],
            comparison['load_increase_pct'],
            base_results['total_losses_kw'],
            ev_results['total_losses_kw'],
            comparison['loss_increase_kw'],
            comparison['loss_increase_pct'],
            base_results['min_voltage_pu'],
            ev_results['min_voltage_pu'],
            comparison['min_voltage_drop'],
            len(base_results['buses_under_voltage']),
            len(ev_results['buses_under_voltage']),
            len(ev_chargers),
            EV_CHARGER_KW,
            len(ev_chargers) * EV_CHARGER_KW
        ]
    }
    
    summary_df = pd.DataFrame(summary)
    summary_path = os.path.join(RESULTS_DIR, 'EV_Impact_Summary.csv')
    summary_df.to_csv(summary_path, index=False)
    print(f"📄 Summary saved to: {summary_path}")


def main():
    """Main execution function."""
    print("\n" + "="*70)
    print("  EV CHARGER IMPACT ANALYSIS")
    print(f" {EV_CHARGER_KW} kW EV Chargers on {PERCENTAGE_TRANSFORMERS}% of Distribution Transformers")
    print("="*70)
    print(f"\nConfiguration:")
    print(f"  - EV Charger Rating: {EV_CHARGER_KW} kW")
    print(f"  - EV Charger Power Factor: {EV_CHARGER_PF}")
    print(f"  - Percentage of Transformers: {PERCENTAGE_TRANSFORMERS}%")
    print(f"  - Random Seed: {RANDOM_SEED}")
    print(f"  - DSS File: {DSS_FILE}")
    
    # Initialize OpenDSS
    print("\n" + "="*60)
    print("INITIALIZING OPENDSS")
    print("="*60)
    initialize_opendss()
    
    # Get all transformers
    transformers, transformer_info = get_all_transformers()
    
    # Run base case first
    base_results = run_base_case()
    
    # Re-initialize for EV case
    initialize_opendss()
    
    # Select transformers for EV charger installation
    selected_transformers = select_transformers_for_ev(
        transformer_info, 
        percentage=PERCENTAGE_TRANSFORMERS,
        seed=RANDOM_SEED
    )
    
    # Add EV chargers
    ev_chargers = add_ev_chargers(
        selected_transformers, 
        ev_kw=EV_CHARGER_KW, 
        pf=EV_CHARGER_PF
    )
    
    # Run EV case
    ev_results = run_ev_case()
    
    # Compare results
    comparison = compare_results(base_results, ev_results)
    
    # Save results to CSV
    save_results_to_csv(base_results, ev_results, ev_chargers, comparison)
    
    # Create plots
    plot_voltage_comparison(base_results, ev_results, ev_chargers)
    
    print("\n" + "="*70)
    print("  ANALYSIS COMPLETE")
    print("="*70)
    print(f"\n✅ All results saved to: {RESULTS_DIR}")
    
    return base_results, ev_results, comparison


if __name__ == "__main__":
    base_results, ev_results, comparison = main()
