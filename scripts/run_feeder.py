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
    ├── Curti/
    │   ├── csv/
    │   │   ├── Voltages.csv
    │   │   ├── Losses.csv
    │   │   ├── Meters.csv
    │   │   ├── Summary.csv
    │   │   └── Capacity.csv
    │   └── plots/
    │       ├── Voltage_Profile.png
    │       ├── Voltage_Profile_Interactive.html
    │       ├── Line_Loading.png
    │       ├── Losses_Breakdown.png
    │       └── Voltage_Histogram.png
    └── Combined/
        └── plots/Power_Flow.png (plus the 4 standard plots)
"""

import os
import shutil
import importlib
import json
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # headless backend — no display required
import matplotlib.pyplot as plt

try:
    dss = importlib.import_module("opendssdirect")
except ModuleNotFoundError as exc:
    raise ModuleNotFoundError(
        "OpenDSSDirect.py is not installed. Install it with: pip install OpenDSSDirect.py"
    ) from exc

try:
    go = importlib.import_module("plotly.graph_objects")
    pio = importlib.import_module("plotly.io")
except ModuleNotFoundError:
    go = None
    pio = None

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


def _normalize_bus_name(bus):
    if bus is None or pd.isna(bus):
        return None
    name = str(bus).strip().strip('"').upper()
    if not name:
        return None
    return name.split('.')[0]


def _extract_topology():
    edges = []
    seen = set()

    def _add_edge(bus1, bus2):
        b1 = _normalize_bus_name(bus1)
        b2 = _normalize_bus_name(bus2)
        if not b1 or not b2 or b1 == b2:
            return
        key_bus1, key_bus2 = sorted([b1, b2])
        key = (key_bus1, key_bus2)
        if key in seen:
            return
        seen.add(key)
        edges.append((b1, b2))

    dss.Circuit.SetActiveClass("Line")
    flag = dss.ActiveClass.First()

    while flag > 0:
        buses = dss.CktElement.BusNames()
        if len(buses) >= 2:
            _add_edge(buses[0], buses[1])
        flag = dss.ActiveClass.Next()

    return edges


def _extract_line_map():
    line_map = {}
    seen = set()
    dss.Circuit.SetActiveClass("Line")
    flag = dss.ActiveClass.First()
    while flag > 0:
        buses = dss.CktElement.BusNames()
        line_name = dss.CktElement.Name().strip()
        if len(buses) >= 2:
            b1 = _normalize_bus_name(buses[0])
            b2 = _normalize_bus_name(buses[1])
            if b1 and b2 and b1 != b2:
                key = tuple(sorted((b1, b2)))
                if key not in seen:
                    seen.add(key)
                    line_map[key] = line_name
        flag = dss.ActiveClass.Next()
    return line_map


def _generate_interactive_voltage_profile(name, df_v, edges, line_map, plots_dir):
    if go is None or pio is None:
        print("    [WARN] Interactive voltage profile skipped: plotly not installed "
              "(pip install plotly)")
        return None
    if df_v is None or df_v.empty:
        return None

    node_df = df_v[['Bus', 'dist', 'pu1', 'BasekV']].copy()
    node_df = node_df.drop_duplicates(subset=['Bus'], keep='first')
    node_df['is_hv'] = node_df['BasekV'] >= 1.0
    node_df['ansi_low'] = node_df['pu1'] < 0.95
    node_df['ansi_high'] = node_df['pu1'] > 1.05
    node_df['ansi_violation'] = node_df['ansi_low'] | node_df['ansi_high']

    bus_meta = {
        row['Bus']: {
            'dist': float(row['dist']),
            'pu': float(row['pu1']),
            'basekv': float(row['BasekV']),
            'is_hv': bool(row['is_hv']),
            'ansi_violation': bool(row['ansi_violation']),
        }
        for _, row in node_df.iterrows()
    }

    adjacency = {bus: [] for bus in bus_meta}
    edge_rows = []
    for bus1, bus2 in edges or []:
        if bus1 not in bus_meta or bus2 not in bus_meta:
            continue
        adjacency.setdefault(bus1, []).append(bus2)
        adjacency.setdefault(bus2, []).append(bus1)
        m1 = bus_meta[bus1]
        m2 = bus_meta[bus2]
        key = tuple(sorted((bus1, bus2)))
        line_name = line_map.get(key, '')
        dv = abs(m1['pu'] - m2['pu'])
        edge_rows.append({
            'line': line_name,
            'from_bus': bus1,
            'to_bus': bus2,
            'x1': m1['dist'],
            'y1': m1['pu'],
            'x2': m2['dist'],
            'y2': m2['pu'],
            'dvpu': dv,
            'is_hv': m1['is_hv'] and m2['is_hv'],
        })

    node_df['neighbors'] = node_df['Bus'].map(
        lambda b: sorted(set(adjacency.get(b, []))))
    node_df['degree'] = node_df['neighbors'].map(len)
    node_df['neighbor_str'] = node_df['neighbors'].map(
        lambda ns: ', '.join(ns) if ns else '(none)')

    edge_loading = {}
    cap_path = os.path.join(os.path.dirname(plots_dir), 'csv', 'Capacity.csv')
    if os.path.isfile(cap_path):
        cap = pd.read_csv(cap_path)
        cap.columns = cap.columns.str.strip()
        if 'Name' in cap.columns and '%normal' in cap.columns:
            cap['Name'] = cap['Name'].astype(str).str.strip()
            cap['%normal'] = pd.to_numeric(cap['%normal'], errors='coerce')
            edge_loading = {
                n.strip().upper(): float(v)
                for n, v in zip(cap['Name'], cap['%normal']) if pd.notna(v)
            }

    for e in edge_rows:
        key_name = e['line'].strip().upper()
        e['loading_pct'] = edge_loading.get(key_name)

    hv_nodes = node_df[node_df['is_hv']]
    lv_nodes = node_df[~node_df['is_hv']]
    vio_nodes = node_df[node_df['ansi_violation']]

    fig = go.Figure()

    hv_x = []
    hv_y = []
    hv_text = []
    hv_custom = []
    lv_x = []
    lv_y = []
    lv_text = []
    lv_custom = []
    vio_x = []
    vio_y = []
    vio_text = []
    vio_custom = []

    for _, r in hv_nodes.iterrows():
        hv_x.append(float(r['dist']))
        hv_y.append(float(r['pu1']))
        hv_text.append(
            f"<b>{r['Bus']}</b><br>"
            f"Distance: {r['dist']:.3f} km<br>"
            f"Voltage: {r['pu1']:.4f} pu<br>"
            f"Base kV: {r['BasekV']:.3f}<br>"
            f"Degree: {int(r['degree'])}<br>"
            f"Neighbors: {r['neighbor_str']}"
        )
        hv_custom.append(r['Bus'])

    for _, r in lv_nodes.iterrows():
        lv_x.append(float(r['dist']))
        lv_y.append(float(r['pu1']))
        lv_text.append(
            f"<b>{r['Bus']}</b><br>"
            f"Distance: {r['dist']:.3f} km<br>"
            f"Voltage: {r['pu1']:.4f} pu<br>"
            f"Base kV: {r['BasekV']:.3f}<br>"
            f"Degree: {int(r['degree'])}<br>"
            f"Neighbors: {r['neighbor_str']}"
        )
        lv_custom.append(r['Bus'])

    for _, r in vio_nodes.iterrows():
        vio_x.append(float(r['dist']))
        vio_y.append(float(r['pu1']))
        vio_text.append(
            f"<b>{r['Bus']}</b><br>"
            f"Voltage violation<br>"
            f"Distance: {r['dist']:.3f} km<br>"
            f"Voltage: {r['pu1']:.4f} pu"
        )
        vio_custom.append(r['Bus'])

    hv_line_x = []
    hv_line_y = []
    hv_line_text = []
    hv_line_custom = []
    lv_line_x = []
    lv_line_y = []
    lv_line_text = []
    lv_line_custom = []

    for e in edge_rows:
        hover = (
            f"<b>{e['line'] or 'Line edge'}</b><br>"
            f"{e['from_bus']} ↔ {e['to_bus']}<br>"
            f"ΔV: {e['dvpu']:.5f} pu"
        )
        if e['loading_pct'] is not None:
            hover += f"<br>Loading: {e['loading_pct']:.2f}%"
        if e['is_hv']:
            hv_line_x.extend([e['x1'], e['x2'], None])
            hv_line_y.extend([e['y1'], e['y2'], None])
            hv_line_text.extend([hover, hover, None])
            hv_line_custom.extend([
                json.dumps({'type': 'edge', 'line': e['line'],
                            'from': e['from_bus'], 'to': e['to_bus']}),
                json.dumps({'type': 'edge', 'line': e['line'],
                            'from': e['from_bus'], 'to': e['to_bus']}),
                None,
            ])
        else:
            lv_line_x.extend([e['x1'], e['x2'], None])
            lv_line_y.extend([e['y1'], e['y2'], None])
            lv_line_text.extend([hover, hover, None])
            lv_line_custom.extend([
                json.dumps({'type': 'edge', 'line': e['line'],
                            'from': e['from_bus'], 'to': e['to_bus']}),
                json.dumps({'type': 'edge', 'line': e['line'],
                            'from': e['from_bus'], 'to': e['to_bus']}),
                None,
            ])

    fig.add_trace(go.Scatter(
        x=hv_line_x, y=hv_line_y, mode='lines', name='HV connections',
        line=dict(color='steelblue', width=1), opacity=0.55,
        hovertemplate='%{text}<extra></extra>', text=hv_line_text,
        customdata=hv_line_custom
    ))
    fig.add_trace(go.Scatter(
        x=lv_line_x, y=lv_line_y, mode='lines', name='LV connections',
        line=dict(color='darkorange', width=1), opacity=0.55,
        hovertemplate='%{text}<extra></extra>', text=lv_line_text,
        customdata=lv_line_custom
    ))
    fig.add_trace(go.Scatter(
        x=hv_x, y=hv_y, mode='markers', name='11 kV buses',
        marker=dict(color='steelblue', size=9, opacity=1.0),
        text=hv_text, customdata=hv_custom,
        hovertemplate='%{text}<extra></extra>'
    ))
    fig.add_trace(go.Scatter(
        x=lv_x, y=lv_y, mode='markers', name='0.415 kV buses',
        marker=dict(color='darkorange', size=9, symbol='triangle-up', opacity=1.0),
        text=lv_text, customdata=lv_custom,
        hovertemplate='%{text}<extra></extra>'
    ))
    fig.add_trace(go.Scatter(
        x=vio_x, y=vio_y, mode='markers', name='ANSI violations',
        visible='legendonly',
        marker=dict(color='crimson', size=12, symbol='x'),
        text=vio_text, customdata=vio_custom,
        hovertemplate='%{text}<extra></extra>'
    ))
    fig.add_hline(y=0.95, line_dash='dash', line_color='red',
                  annotation_text='ANSI lower (0.95 pu)', annotation_position='bottom right')
    fig.add_hline(y=1.05, line_dash='dash', line_color='red',
                  annotation_text='ANSI upper (1.05 pu)', annotation_position='top right')

    fig.update_layout(
        title=f"{name} — Interactive Voltage Profile",
        xaxis_title='Distance from Substation (km)',
        yaxis_title='Voltage (pu)',
        template='plotly_white',
        hovermode='closest',
        legend=dict(orientation='h', yanchor='bottom', y=1.01, xanchor='left', x=0),
        margin=dict(l=55, r=340, t=70, b=50),
        height=650,
    )

    plot_div = pio.to_html(fig, include_plotlyjs='cdn',
                           full_html=False, div_id='vp_plot')
    node_payload = {
        row['Bus']: {
            'bus': row['Bus'],
            'dist': float(row['dist']),
            'pu1': float(row['pu1']),
            'basekv': float(row['BasekV']),
            'degree': int(row['degree']),
            'neighbors': row['neighbors'],
            'ansi_violation': bool(row['ansi_violation']),
        }
        for _, row in node_df.iterrows()
    }
    edge_payload = [
        {
            'line': e['line'],
            'from': e['from_bus'],
            'to': e['to_bus'],
            'dvpu': float(e['dvpu']),
            'loading_pct': e['loading_pct'],
            'is_hv': bool(e['is_hv']),
        }
        for e in edge_rows
    ]

    html_path = os.path.join(plots_dir, 'Voltage_Profile_Interactive.html')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{name} - Interactive Voltage Profile</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 0; padding: 12px; background: #f7f7f7; }}
    .container {{ display: flex; gap: 10px; align-items: flex-start; }}
    .left {{ flex: 1 1 auto; min-width: 0; }}
    .panel {{
      width: 310px; background: #fff; border: 1px solid #ddd; border-radius: 6px;
      padding: 12px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); position: sticky; top: 10px;
    }}
    .controls {{ margin-bottom: 10px; display: grid; grid-template-columns: 1fr; gap: 6px; }}
    .controls input, .controls button {{
      padding: 6px 8px; border: 1px solid #bbb; border-radius: 4px; font-size: 13px;
    }}
    .controls button {{ cursor: pointer; background: #f1f1f1; }}
    .controls button:hover {{ background: #e5e5e5; }}
    .meta-row {{ margin: 4px 0; font-size: 13px; }}
    .small {{ color: #666; font-size: 12px; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="left">
      <div class="controls">
        <input id="busSearch" type="text" placeholder="Search bus name..." />
        <button id="btnFindBus">Find bus</button>
        <button id="btnReset">Reset selection</button>
        <button id="btnViolOnly">Toggle ANSI-violations only</button>
      </div>
      {plot_div}
    </div>
    <div class="panel">
      <h3 style="margin:0 0 8px 0;">Inspection Panel</h3>
      <div id="infoContent" class="small">Click a node or line in the plot.</div>
    </div>
  </div>

  <script>
    const nodeData = {json.dumps(node_payload)};
    const edgeData = {json.dumps(edge_payload)};
    const plot = document.getElementById('vp_plot');
    let selectedBus = null;
    let violationsOnly = false;

    function setInfoHtml(html) {{
      document.getElementById('infoContent').innerHTML = html;
    }}

    function getNeighborEdges(bus) {{
      return edgeData.filter(e => e.from === bus || e.to === bus);
    }}

    function renderBusInfo(bus) {{
      const n = nodeData[bus];
      if (!n) {{
        setInfoHtml('<span class="small">Bus not found.</span>');
        return;
      }}
      const edges = getNeighborEdges(bus);
      const neighborLines = edges.map(e => {{
        const other = (e.from === bus) ? e.to : e.from;
        const loading = (e.loading_pct === null || e.loading_pct === undefined) ? 'n/a' : e.loading_pct.toFixed(2) + '%';
        return `<li>${{e.line || '(unnamed line)'}}: ${{bus}} ↔ ${{other}} (ΔV=${{e.dvpu.toFixed(5)}} pu, loading=${{loading}})</li>`;
      }}).join('');
      setInfoHtml(`
        <div class="meta-row"><b>Bus:</b> ${{n.bus}}</div>
        <div class="meta-row"><b>Distance:</b> ${{n.dist.toFixed(3)}} km</div>
        <div class="meta-row"><b>Voltage:</b> ${{n.pu1.toFixed(5)}} pu</div>
        <div class="meta-row"><b>Base kV:</b> ${{n.basekv.toFixed(3)}}</div>
        <div class="meta-row"><b>Degree:</b> ${{n.degree}}</div>
        <div class="meta-row"><b>ANSI violation:</b> ${{n.ansi_violation ? 'YES' : 'No'}}</div>
        <div class="meta-row"><b>Connected buses:</b> ${{n.neighbors.join(', ') || '(none)'}}</div>
        <div class="meta-row"><b>Connected lines:</b></div>
        <ul style="margin: 4px 0 0 16px; padding:0;">${{neighborLines || '<li>(none)</li>'}}</ul>
      `);
    }}

    function renderEdgeInfo(edgeLike) {{
      const e = edgeData.find(x => x.line === edgeLike.line && (
        (x.from === edgeLike.from && x.to === edgeLike.to) ||
        (x.from === edgeLike.to && x.to === edgeLike.from)
      ));
      if (!e) {{
        return;
      }}
      const loading = (e.loading_pct === null || e.loading_pct === undefined) ? 'n/a' : e.loading_pct.toFixed(2) + '%';
      setInfoHtml(`
        <div class="meta-row"><b>Line:</b> ${{e.line || '(unnamed line)'}} </div>
        <div class="meta-row"><b>From:</b> ${{e.from}}</div>
        <div class="meta-row"><b>To:</b> ${{e.to}}</div>
        <div class="meta-row"><b>ΔV:</b> ${{e.dvpu.toFixed(5)}} pu</div>
        <div class="meta-row"><b>Loading:</b> ${{loading}}</div>
      `);
    }}

    function updateSelectionVisuals() {{
      const hvNodeTrace = 2;
      const lvNodeTrace = 3;

      const hvCd = plot.data[hvNodeTrace].customdata || [];
      const lvCd = plot.data[lvNodeTrace].customdata || [];
      const hvBaseOpacity = hvCd.map(() => 1.0);
      const lvBaseOpacity = lvCd.map(() => 1.0);
      if (violationsOnly) {{
        hvCd.forEach((b, i) => {{
          if (!nodeData[b]?.ansi_violation) hvBaseOpacity[i] = 0.0;
        }});
        lvCd.forEach((b, i) => {{
          if (!nodeData[b]?.ansi_violation) lvBaseOpacity[i] = 0.0;
        }});
      }}

      const hvSize = hvCd.map(() => 9);
      const lvSize = lvCd.map(() => 9);
      const hvOpacity = hvBaseOpacity.map(v => v > 0 ? 0.35 : 0.0);
      const lvOpacity = lvBaseOpacity.map(v => v > 0 ? 0.35 : 0.0);

      if (!selectedBus) {{
        for (let i = 0; i < hvOpacity.length; i++) hvOpacity[i] = hvBaseOpacity[i] > 0 ? 1.0 : 0.0;
        for (let i = 0; i < lvOpacity.length; i++) lvOpacity[i] = lvBaseOpacity[i] > 0 ? 1.0 : 0.0;
      }} else {{
        const neighbors = new Set([selectedBus, ...(nodeData[selectedBus]?.neighbors || [])]);
        hvCd.forEach((b, i) => {{
          if (neighbors.has(b)) {{
            hvOpacity[i] = hvBaseOpacity[i] > 0 ? 1.0 : 0.0;
            hvSize[i] = (b === selectedBus) ? 15 : 12;
          }}
        }});
        lvCd.forEach((b, i) => {{
          if (neighbors.has(b)) {{
            lvOpacity[i] = lvBaseOpacity[i] > 0 ? 1.0 : 0.0;
            lvSize[i] = (b === selectedBus) ? 15 : 12;
          }}
        }});
      }}

      Plotly.restyle(plot, {{'marker.size': [hvSize], 'marker.opacity': [hvOpacity]}}, [hvNodeTrace]);
      Plotly.restyle(plot, {{'marker.size': [lvSize], 'marker.opacity': [lvOpacity]}}, [lvNodeTrace]);
    }}

    document.getElementById('btnFindBus').addEventListener('click', () => {{
      const v = (document.getElementById('busSearch').value || '').trim().toUpperCase();
      if (!v) return;
      if (!nodeData[v]) {{
        setInfoHtml(`<span class="small">Bus "${{v}}" not found.</span>`);
        return;
      }}
      selectedBus = v;
      renderBusInfo(v);
      updateSelectionVisuals();
    }});

    document.getElementById('busSearch').addEventListener('keydown', (ev) => {{
      if (ev.key === 'Enter') {{
        document.getElementById('btnFindBus').click();
      }}
    }});

    document.getElementById('btnReset').addEventListener('click', () => {{
      selectedBus = null;
      document.getElementById('busSearch').value = '';
      setInfoHtml('<span class="small">Click a node or line in the plot.</span>');
      updateSelectionVisuals();
    }});

    document.getElementById('btnViolOnly').addEventListener('click', () => {{
      violationsOnly = !violationsOnly;
      updateSelectionVisuals();
    }});

    plot.on('plotly_click', (ev) => {{
      const p = ev?.points?.[0];
      if (!p) return;
      const traceIndex = p.curveNumber;
      const cd = p.customdata;

      if (traceIndex === 2 || traceIndex === 3 || traceIndex === 4) {{
        if (cd && nodeData[cd]) {{
          selectedBus = cd;
          renderBusInfo(cd);
          updateSelectionVisuals();
        }}
        return;
      }}
      if (traceIndex === 0 || traceIndex === 1) {{
        if (!cd) return;
        try {{
          const e = JSON.parse(cd);
          renderEdgeInfo(e);
        }} catch (err) {{
          // no-op
        }}
      }}
    }});

    updateSelectionVisuals();
  </script>
</body>
</html>
""")
    return os.path.basename(html_path)


def _generate_plots(name, csv_dir, plots_dir, bus_names, bus_distances, edges=None):
    """Generate and save visualizations from exported CSV data."""

    dist_map = {}
    for bus, dist in zip(bus_names, bus_distances):
        norm_bus = _normalize_bus_name(bus)
        if norm_bus:
            dist_map[norm_bus] = dist
    saved_plots = []

    def _read_csv(filename):
        path = os.path.join(csv_dir, filename)
        if not os.path.isfile(path):
            return None
        df = pd.read_csv(path)
        df.columns = df.columns.str.strip()
        return df

    # ------------------------------------------------------------------
    # 1. Voltage Profile — pu voltage vs. electrical distance from source
    # ------------------------------------------------------------------
    try:
        df_v = _read_csv('Voltages.csv')
        if df_v is not None and not df_v.empty:
            df_v['Bus'] = df_v['Bus'].map(_normalize_bus_name)
            df_v['pu1'] = pd.to_numeric(df_v['pu1'], errors='coerce')
            df_v['BasekV'] = pd.to_numeric(df_v['BasekV'], errors='coerce')
            df_v['dist'] = df_v['Bus'].map(dist_map)
            df_v = df_v.dropna(subset=['Bus', 'dist', 'pu1', 'BasekV'])
            df_v = df_v[df_v['pu1'] > 0]  # drop open-circuit zero-voltage buses

            hv = df_v[df_v['BasekV'] >= 1.0]
            lv = df_v[df_v['BasekV'] < 1.0]

            fig, ax = plt.subplots(figsize=(10, 5))
            if edges:
                bus_pu = dict(zip(df_v['Bus'], df_v['pu1']))
                bus_dist = dict(zip(df_v['Bus'], df_v['dist']))
                bus_basekv = dict(zip(df_v['Bus'], df_v['BasekV']))
                hv_used = False
                lv_used = False

                for bus1, bus2 in edges:
                    dist1 = bus_dist.get(bus1)
                    dist2 = bus_dist.get(bus2)
                    pu1 = bus_pu.get(bus1)
                    pu2 = bus_pu.get(bus2)
                    base1 = bus_basekv.get(bus1)
                    base2 = bus_basekv.get(bus2)
                    if dist1 is None or dist2 is None or pu1 is None or pu2 is None:
                        continue
                    if base1 is None or base2 is None:
                        continue

                    is_hv = base1 >= 1.0 and base2 >= 1.0
                    color = 'steelblue' if is_hv else 'darkorange'
                    if is_hv:
                        hv_used = True
                    else:
                        lv_used = True
                    ax.plot([dist1, dist2], [pu1, pu2], color=color, linewidth=1.0,
                            alpha=0.5, zorder=2)

                if hv_used:
                    ax.plot([], [], color='steelblue', linewidth=1.0,
                            alpha=0.5, label='HV connections')
                if lv_used:
                    ax.plot([], [], color='darkorange', linewidth=1.0,
                            alpha=0.5, label='LV connections')
            ax.scatter(hv['dist'], hv['pu1'], color='steelblue', s=25,
                       label='11 kV buses', zorder=3)
            ax.scatter(lv['dist'], lv['pu1'], color='darkorange', s=25,
                       marker='^', label='0.415 kV buses', zorder=3)
            ax.axhline(0.95, color='red', linestyle='--', linewidth=1.2,
                       label='ANSI lower (0.95 pu)')
            ax.axhline(1.05, color='red', linestyle='--', linewidth=1.2,
                       label='ANSI upper (1.05 pu)')
            ax.set_xlabel('Distance from Substation (km)')
            ax.set_ylabel('Voltage (pu)')
            ax.set_title(f'{name} — Voltage Profile')
            ax.legend(fontsize=8)
            ax.grid(True, alpha=0.3)
            fig.tight_layout()
            out = os.path.join(plots_dir, 'Voltage_Profile.png')
            fig.savefig(out, dpi=150, bbox_inches='tight')
            plt.close(fig)
            saved_plots.append('Voltage_Profile.png')

            line_map = _extract_line_map()
            interactive_plot = _generate_interactive_voltage_profile(
                name=name,
                df_v=df_v,
                edges=edges or [],
                line_map=line_map,
                plots_dir=plots_dir,
            )
            if interactive_plot:
                saved_plots.append(interactive_plot)
                print(f"    Interactive: {interactive_plot}")
    except Exception as exc:
        print(f'    [WARN] Voltage_Profile.png skipped: {exc}')

    # ------------------------------------------------------------------
    # 2. Line Loading — % of normal ampacity rating per line
    # ------------------------------------------------------------------
    try:
        df_c = _read_csv('Capacity.csv')
        if df_c is not None and not df_c.empty:
            df_c['Name'] = df_c['Name'].str.strip()
            df_c['%normal'] = pd.to_numeric(df_c['%normal'], errors='coerce')
            lines = df_c[df_c['Name'].str.startswith('Line.')].copy()
            lines = lines.dropna(subset=['%normal'])
            lines = lines.sort_values('%normal', ascending=True)

            colors = [
                'red' if p > 100 else 'darkorange' if p > 80 else 'steelblue'
                for p in lines['%normal']
            ]
            labels = lines['Name'].str.replace('Line.', '', regex=False)

            fig_h = min(max(4, len(lines) * 0.35), 60)
            fig, ax = plt.subplots(figsize=(9, fig_h))
            ax.barh(labels, lines['%normal'], color=colors)
            ax.axvline(80, color='darkorange', linestyle='--',
                       linewidth=1.2, label='80% threshold')
            ax.axvline(100, color='red', linestyle='--',
                       linewidth=1.2, label='100% normal rating')
            ax.set_xlabel('Loading (% of normal rating)')
            ax.set_title(f'{name} — Line Loading')
            ax.legend(fontsize=8)
            ax.grid(True, alpha=0.3, axis='x')
            fig.tight_layout()
            out = os.path.join(plots_dir, 'Line_Loading.png')
            fig.savefig(out, dpi=150, bbox_inches='tight')
            plt.close(fig)
            saved_plots.append('Line_Loading.png')
    except Exception as exc:
        print(f'    [WARN] Line_Loading.png skipped: {exc}')

    # ------------------------------------------------------------------
    # 3. Losses Breakdown — pie (line vs transformer) + top-10 bar
    # ------------------------------------------------------------------
    try:
        df_l = _read_csv('Losses.csv')
        if df_l is not None and not df_l.empty:
            df_l['Element'] = df_l['Element'].str.strip()
            df_l['Total(W)'] = pd.to_numeric(df_l['Total(W)'], errors='coerce')
            df_l = df_l.dropna(subset=['Total(W)'])

            line_loss_w = df_l[df_l['Element'].str.startswith('Line.')]['Total(W)'].sum()
            xfmr_loss_w = df_l[df_l['Element'].str.startswith('Transformer.')]['Total(W)'].sum()
            total_w = line_loss_w + xfmr_loss_w

            top10 = df_l.nlargest(10, 'Total(W)')

            fig, (ax_pie, ax_bar) = plt.subplots(1, 2, figsize=(13, 5))

            if total_w > 0:
                pie_vals = [line_loss_w / 1000, xfmr_loss_w / 1000]
                pie_labels = [
                    f"Lines\n{line_loss_w/1000:.2f} kW",
                    f"Transformers\n{xfmr_loss_w/1000:.2f} kW",
                ]
                ax_pie.pie(pie_vals, labels=pie_labels,
                           colors=['steelblue', 'darkorange'],
                           autopct='%1.1f%%', startangle=90)
            else:
                ax_pie.text(0.5, 0.5, 'No loss data', ha='center', va='center',
                            transform=ax_pie.transAxes)
            ax_pie.set_title('Loss Share by Element Type')

            top10_labels = top10['Element'].str.replace(
                r'^(Line|Transformer)\.', '', regex=True)
            ax_bar.barh(top10_labels.values[::-1],
                        top10['Total(W)'].values[::-1] / 1000,
                        color='steelblue')
            ax_bar.set_xlabel('Total Losses (kW)')
            ax_bar.set_title('Top 10 Elements by Losses')
            ax_bar.grid(True, alpha=0.3, axis='x')

            fig.suptitle(f'{name} — Losses Breakdown', fontweight='bold')
            fig.tight_layout()
            out = os.path.join(plots_dir, 'Losses_Breakdown.png')
            fig.savefig(out, dpi=150, bbox_inches='tight')
            plt.close(fig)
            saved_plots.append('Losses_Breakdown.png')
    except Exception as exc:
        print(f'    [WARN] Losses_Breakdown.png skipped: {exc}')

    # ------------------------------------------------------------------
    # 4. Voltage Histogram — distribution of bus per-unit voltages
    # ------------------------------------------------------------------
    try:
        df_v2 = _read_csv('Voltages.csv')
        if df_v2 is not None and not df_v2.empty:
            df_v2['pu1'] = pd.to_numeric(df_v2['pu1'], errors='coerce')
            pu_vals = df_v2['pu1'].dropna()
            pu_vals = pu_vals[pu_vals > 0]

            fig, ax = plt.subplots(figsize=(8, 5))
            ax.hist(pu_vals, bins=30, color='steelblue',
                    edgecolor='white', alpha=0.85)
            ax.axvline(0.95, color='red', linestyle='--',
                       linewidth=1.5, label='ANSI lower (0.95 pu)')
            ax.axvline(1.05, color='red', linestyle='--',
                       linewidth=1.5, label='ANSI upper (1.05 pu)')
            ax.set_xlabel('Voltage (pu)')
            ax.set_ylabel('Number of Buses')
            ax.set_title(f'{name} — Voltage Distribution')
            ax.legend(fontsize=8)
            ax.grid(True, alpha=0.3)
            fig.tight_layout()
            out = os.path.join(plots_dir, 'Voltage_Histogram.png')
            fig.savefig(out, dpi=150, bbox_inches='tight')
            plt.close(fig)
            saved_plots.append('Voltage_Histogram.png')
    except Exception as exc:
        print(f'    [WARN] Voltage_Histogram.png skipped: {exc}')

    # ------------------------------------------------------------------
    # 5. Power Flow — top-15 elements by |P(kW)| (Combined feeder only)
    # ------------------------------------------------------------------
    if name == 'Combined':
        try:
            df_p = _read_csv('Powers.csv')
            if df_p is not None and not df_p.empty:
                df_p['Element'] = df_p['Element'].str.strip().str.strip('"')
                df_p['Terminal'] = pd.to_numeric(df_p['Terminal'], errors='coerce')
                df_p['P(kW)'] = pd.to_numeric(df_p['P(kW)'], errors='coerce')
                t1 = df_p[df_p['Terminal'] == 1].copy()
                t1 = t1.dropna(subset=['P(kW)'])
                t1['abs_P'] = t1['P(kW)'].abs()
                top15 = t1.nlargest(15, 'abs_P').sort_values('abs_P', ascending=True)

                labels = top15['Element'].str.replace(
                    r'^(Line|Transformer|Vsource)\.', '', regex=True)

                fig, ax = plt.subplots(figsize=(9, 6))
                ax.barh(labels, top15['P(kW)'], color='steelblue')
                ax.axvline(0, color='black', linewidth=0.8)
                ax.set_xlabel('Active Power at Terminal 1 (kW)')
                ax.set_title(f'{name} — Top 15 Elements by Power Flow')
                ax.grid(True, alpha=0.3, axis='x')
                fig.tight_layout()
                out = os.path.join(plots_dir, 'Power_Flow.png')
                fig.savefig(out, dpi=150, bbox_inches='tight')
                plt.close(fig)
                saved_plots.append('Power_Flow.png')
        except Exception as exc:
            print(f'    [WARN] Power_Flow.png skipped: {exc}')

    if saved_plots:
        print(f"  Plots   : {', '.join(saved_plots)}")
    else:
        print("  Plots   : none generated")


def run_feeder(name, dss_file):
    """Compile, solve, export and save results for a single feeder."""
    print(f"\n{'='*60}")
    print(f"  Feeder : {name}")
    print(f"  File   : {dss_file}")
    print(f"{'='*60}")

    if not os.path.isfile(dss_file):
        print(f"  [ERROR] DSS file not found: {dss_file}")
        return

    # Output directories
    output_root = os.path.join(_PROJECT_ROOT, "output", name)
    csv_dir = os.path.join(output_root, "csv")
    plots_dir = os.path.join(output_root, "plots")
    os.makedirs(csv_dir, exist_ok=True)
    os.makedirs(plots_dir, exist_ok=True)

    # Compile & solve
    dss.Basic.Start(0)
    dss.Text.Command(f"Compile [{dss_file}]")
    print(f"  Circuit : {dss.Circuit.Name()}")
    print(f"  Buses   : {dss.Circuit.NumBuses()}")
    dss.Solution.Solve()
    bus_names = list(dss.Circuit.AllBusNames())
    bus_distances = list(dss.Circuit.AllBusDistances())

    if dss.Solution.Converged():
        print("  Solve   : CONVERGED")
    else:
        print("  Solve   : [WARN] Did not converge — results may be unreliable")

    # Determine which exports to run
    exports = BASE_EXPORTS + (COMBINED_EXTRAS if name == "Combined" else [])

    dss_dir = os.path.dirname(dss_file)
    saved = []
    for exp in exports:
        dest = _run_export(exp, csv_dir, dss_dir)
        if dest:
            saved.append(os.path.basename(dest))

    print(f"\n  CSV Dir : {csv_dir}")
    print(f"  Plots Dir: {plots_dir}")
    print(f"  Saved   : {', '.join(saved) if saved else 'none'}")
    edges = _extract_topology()
    _generate_plots(name, csv_dir, plots_dir, bus_names, bus_distances, edges=edges)


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
