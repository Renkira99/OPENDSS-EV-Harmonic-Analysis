"""
Feeder Runner Script
====================
Compiles and solves OpenDSS feeder files, then saves all export results
to a properly structured output folder.

Usage:
    python scripts/run_feeder.py

Configuration:
    Edit FEEDERS_TO_RUN below to choose which feeders to simulate.

Output structure:
    output/
    ├── Khadpabandh/
    │   ├── Voltages.csv
    │   ├── Currents.csv
    │   ├── Powers.csv
    │   ├── Losses.csv
    │   ├── Meters.csv
    │   ├── Summary.csv
    │   └── Capacity.csv
    ├── Curti/
    ├── Farmagudi/
    ├── Ponda1/
    ├── Undir/
    └── Combined/
"""

import os
import shutil
import importlib

try:
    dss = importlib.import_module("opendssdirect")
except ModuleNotFoundError as exc:
    raise ModuleNotFoundError(
        "OpenDSSDirect.py is not installed. Install it with: pip install OpenDSSDirect.py"
    ) from exc

# ============================================================
# CONFIGURATION — choose which feeders to run
# ============================================================
# Options: "all", "Khadpabandh", "Curti", "Farmagudi", "Ponda1", "Undir", "Combined"
FEEDERS_TO_RUN = ["all"]


# ============================================================
# FEEDER REGISTRY — maps name → DSS file path (relative to project root)
# ============================================================
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FEEDER_MAP = {
    "Khadpabandh": os.path.join(_PROJECT_ROOT, "dss", "feeders", "Khadpabandh_Feeder.dss"),
    "Curti":       os.path.join(_PROJECT_ROOT, "dss", "feeders", "Curti_Feeder.dss"),
    "Farmagudi":   os.path.join(_PROJECT_ROOT, "dss", "feeders", "Farmagudi_Feeder.dss"),
    "Ponda1":      os.path.join(_PROJECT_ROOT, "dss", "feeders", "Ponda1_Feeder.dss"),
    "Undir":       os.path.join(_PROJECT_ROOT, "dss", "feeders", "Undir_Feeder.dss"),
    "Combined":    os.path.join(_PROJECT_ROOT, "dss", "combined_network.dss"),
}

# Exports to run and their clean output filenames
# Combined feeder also gets Currents and Powers
BASE_EXPORTS = ["Voltages", "Losses", "Meters", "Summary", "Capacity"]
COMBINED_EXTRAS = ["Currents", "Powers"]


def _resolve_feeders():
    """Return the list of feeder names to run based on FEEDERS_TO_RUN config."""
    if "all" in FEEDERS_TO_RUN:
        return list(FEEDER_MAP.keys())
    unknown = [f for f in FEEDERS_TO_RUN if f not in FEEDER_MAP]
    if unknown:
        raise ValueError(
            f"Unknown feeder(s): {unknown}\n"
            f"Valid options: {list(FEEDER_MAP.keys()) + ['all']}"
        )
    return FEEDERS_TO_RUN


def _run_export(export_type, output_dir, dss_dir):
    """
    Issue an Export command, find the file OpenDSS created, move it to output_dir
    with a clean name. Returns the destination path or None if export failed.
    """
    dss.Text.Command(f"Export {export_type}")
    raw_path = dss.Text.Result().strip()

    if not raw_path or not os.path.isfile(raw_path):
        # OpenDSS sometimes returns a relative path — try resolving from dss_dir
        candidate = os.path.join(dss_dir, raw_path) if raw_path else None
        if candidate and os.path.isfile(candidate):
            raw_path = candidate
        else:
            print(f"    [WARN] Could not locate exported file for '{export_type}' (result: '{raw_path}')")
            return None

    dest = os.path.join(output_dir, f"{export_type}.csv")
    shutil.move(raw_path, dest)
    return dest


def run_feeder(name, dss_file):
    """Compile, solve, export and save results for a single feeder."""
    print(f"\n{'='*60}")
    print(f"  Feeder : {name}")
    print(f"  File   : {dss_file}")
    print(f"{'='*60}")

    if not os.path.isfile(dss_file):
        print(f"  [ERROR] DSS file not found: {dss_file}")
        return

    # Output directory — overwritten on each run (results are deterministic)
    output_dir = os.path.join(_PROJECT_ROOT, "output", name)
    os.makedirs(output_dir, exist_ok=True)

    # Compile & solve
    dss.Basic.Start(0)
    dss.Text.Command(f"Compile [{dss_file}]")
    print(f"  Circuit : {dss.Circuit.Name()}")
    print(f"  Buses   : {dss.Circuit.NumBuses()}")
    dss.Solution.Solve()

    if dss.Solution.Converged():
        print("  Solve   : CONVERGED")
    else:
        print("  Solve   : [WARN] Did not converge — results may be unreliable")

    # Determine which exports to run
    exports = BASE_EXPORTS + (COMBINED_EXTRAS if name == "Combined" else [])

    dss_dir = os.path.dirname(dss_file)
    saved = []
    for exp in exports:
        dest = _run_export(exp, output_dir, dss_dir)
        if dest:
            saved.append(os.path.basename(dest))

    print(f"\n  Output  : {output_dir}")
    print(f"  Saved   : {', '.join(saved) if saved else 'none'}")


def main():
    feeders = _resolve_feeders()
    print(f"Running {len(feeders)} feeder(s): {', '.join(feeders)}")

    for name in feeders:
        run_feeder(name, FEEDER_MAP[name])

    print(f"\n{'='*60}")
    print("  All runs complete.")
    print(f"  Results are in: {os.path.join(_PROJECT_ROOT, 'output')}/")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
