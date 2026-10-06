"""
agents/dashboard_generator.py
==============================
Generates standalone, responsive, dark-mode HTML5/CSS3 Interactive PPA Dashboards
for enterprise silicon signoff. Operates 100% offline with embedded vector graphics.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


def generate_html_dashboard(
    design_name: str,
    pipeline_results: Dict[str, Any],
    output_path: str,
) -> str:
    """
    Generate an offline dark-mode HTML dashboard visualizing all pipeline stages,
    cell distribution, static timing slack, verification assertions, and PPA metrics.
    """
    stages = pipeline_results.get("stages", {})
    s1 = stages.get("stage1", {})
    s2 = stages.get("stage2", {})
    s3 = stages.get("stage3", {})
    s4 = stages.get("stage4", {})

    overall_verdict = pipeline_results.get("overall_verdict", "INCOMPLETE")
    is_tapeout_ready = "READY" in overall_verdict or "PASS" in overall_verdict

    # Metrics
    cell_count = s2.get("cell_count", 0)
    wire_count = s2.get("wire_count", 0)
    area_estimate = s2.get("area_estimate", "~0 um²")
    cell_breakdown = s2.get("cell_breakdown", {})

    # Timing metrics
    sta_data = s2.get("sta", {})
    wns = sta_data.get("wns", 0.0)
    tns = sta_data.get("tns", 0.0)
    freq_mhz = sta_data.get("target_freq_mhz", 100.0)
    crit_delay = sta_data.get("critical_path_delay", 1.0)
    timing_met = sta_data.get("timing_met", True)

    # Verification metrics
    sim_passed = s1.get("sim_passed", False)
    lint_passed = s1.get("lint_passed", False)
    sim_attempts = s1.get("sim_attempts", 1)
    lint_attempts = s1.get("lint_attempts", 1)

    # Power Estimate (roughly ~0.015 mW per cell @ 100MHz for Sky130)
    dynamic_power_mw = round(cell_count * 0.012 * (freq_mhz / 100.0), 3)
    leakage_power_uw = round(cell_count * 0.08, 2)

    # Build Cell Breakdown Bars
    max_cells = max(cell_breakdown.values()) if cell_breakdown else 1
    cell_bars_html = ""
    for cell_name, count in list(cell_breakdown.items())[:8]:
        pct = max(int((count / max_cells) * 100), 5)
        cell_bars_html += f"""
        <div class="bar-row">
            <span class="bar-label">{cell_name}</span>
            <div class="bar-track">
                <div class="bar-fill" style="width: {pct}%;"></div>
            </div>
            <span class="bar-val">{count}</span>
        </div>
        """
    if not cell_bars_html:
        cell_bars_html = "<div class='text-muted'>No gate-level breakdown available</div>"

    verdict_badge_class = "badge-success" if is_tapeout_ready else "badge-danger"
    verdict_icon = "&#10004;" if is_tapeout_ready else "&#9888;"

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EDA Signoff Dashboard | {design_name}</title>
    <style>
        :root {{
            --bg-primary: #0a0e17;
            --bg-card: #131b2e;
            --bg-card-hover: #1a253f;
            --text-main: #e2e8f0;
            --text-muted: #94a3b8;
            --accent-blue: #38bdf8;
            --accent-cyan: #06b6d4;
            --accent-green: #10b981;
            --accent-amber: #f59e0b;
            --accent-red: #ef4444;
            --border-color: #1e293b;
            --font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background-color: var(--bg-primary);
            color: var(--text-main);
            font-family: var(--font-family);
            line-height: 1.5;
            padding: 24px;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        
        /* Header */
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 20px;
            border-bottom: 1px solid var(--border-color);
            margin-bottom: 24px;
        }}
        .title-group h1 {{ font-size: 24px; font-weight: 700; color: #fff; }}
        .title-group p {{ color: var(--text-muted); font-size: 14px; margin-top: 4px; }}
        .badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 8px 16px;
            border-radius: 9999px;
            font-size: 14px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .badge-success {{ background: rgba(16, 185, 129, 0.15); color: var(--accent-green); border: 1px solid var(--accent-green); }}
        .badge-danger {{ background: rgba(239, 68, 68, 0.15); color: var(--accent-red); border: 1px solid var(--accent-red); }}
        .badge-info {{ background: rgba(56, 189, 248, 0.15); color: var(--accent-blue); border: 1px solid var(--accent-blue); }}

        /* KPI Grid */
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}
        .kpi-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 20px;
            transition: transform 0.2s, background 0.2s;
        }}
        .kpi-card:hover {{ transform: translateY(-2px); background: var(--bg-card-hover); }}
        .kpi-title {{ font-size: 13px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; }}
        .kpi-value {{ font-size: 26px; font-weight: 700; color: #fff; margin-top: 6px; }}
        .kpi-sub {{ font-size: 12px; color: var(--accent-cyan); margin-top: 4px; }}

        /* Main Grid */
        .main-grid {{
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 20px;
            margin-bottom: 24px;
        }}
        @media (max-width: 900px) {{ .main-grid {{ grid-template-columns: 1fr; }} }}

        .card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 24px;
        }}
        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 18px;
        }}
        .card-title {{ font-size: 16px; font-weight: 600; color: #fff; }}

        /* Stage Pipeline Flow */
        .stage-flow {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 12px;
            margin-bottom: 24px;
        }}
        @media (max-width: 768px) {{ .stage-flow {{ grid-template-columns: 1fr 1fr; }} }}
        .stage-item {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 14px;
            position: relative;
        }}
        .stage-item.pass {{ border-left: 4px solid var(--accent-green); }}
        .stage-item.fail {{ border-left: 4px solid var(--accent-red); }}
        .stage-name {{ font-size: 12px; color: var(--text-muted); font-weight: 600; text-transform: uppercase; }}
        .stage-desc {{ font-size: 14px; font-weight: 600; color: #fff; margin-top: 4px; }}
        .stage-status {{ font-size: 12px; margin-top: 6px; font-weight: 600; }}
        .text-green {{ color: var(--accent-green); }}
        .text-red {{ color: var(--accent-red); }}

        /* Bar Chart */
        .bar-row {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 10px;
            font-size: 13px;
        }}
        .bar-label {{ width: 110px; font-family: monospace; color: var(--text-muted); }}
        .bar-track {{
            flex: 1;
            height: 10px;
            background: #1e293b;
            border-radius: 5px;
            overflow: hidden;
        }}
        .bar-fill {{
            height: 100%;
            background: linear-gradient(90deg, var(--accent-cyan), var(--accent-blue));
            border-radius: 5px;
        }}
        .bar-val {{ width: 35px; text-align: right; font-weight: 600; color: #fff; }}

        /* Timing Slack Diagram */
        .slack-box {{
            background: #0f172a;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 16px;
        }}
        .slack-row {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
            font-size: 13px;
        }}
        .slack-row span:first-child {{ color: var(--text-muted); }}
        .slack-row span:last-child {{ font-weight: 600; font-family: monospace; }}

        /* Script Links */
        .script-list {{ list-style: none; }}
        .script-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid var(--border-color);
            font-size: 13px;
        }}
        .script-item:last-child {{ border-bottom: none; }}
        .script-badge {{
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            background: rgba(56, 189, 248, 0.1);
            color: var(--accent-blue);
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <div class="title-group">
                <h1>Autonomous Silicon Signoff Dashboard</h1>
                <p>Design: <strong>{design_name}</strong> | PDK: <strong>SkyWater 130nm (sky130_fd_sc_hd)</strong> | Generated: {ts}</p>
            </div>
            <div class="badge {verdict_badge_class}">
                <span>{verdict_icon}</span>
                <span>{overall_verdict}</span>
            </div>
        </div>

        <!-- Stage Pipeline Execution Flow -->
        <div class="stage-flow">
            <div class="stage-item {'pass' if lint_passed else 'fail'}">
                <div class="stage-name">Stage 1.1 - 1.3</div>
                <div class="stage-desc">Frontend RTL & Lint</div>
                <div class="stage-status {'text-green' if lint_passed else 'text-red'}">
                    {'[OK] Verilator Clean' if lint_passed else '[FAIL] Lint Errors'} ({lint_attempts} iter)
                </div>
            </div>
            <div class="stage-item {'pass' if sim_passed else 'fail'}">
                <div class="stage-name">Stage 1.4 - 1.5</div>
                <div class="stage-desc">Verification & TB</div>
                <div class="stage-status {'text-green' if sim_passed else 'text-red'}">
                    {'[OK] 100% Passed' if sim_passed else '[FAIL] Sim Mismatch'} ({sim_attempts} iter)
                </div>
            </div>
            <div class="stage-item {'pass' if cell_count > 0 else 'fail'}">
                <div class="stage-name">Stage 2.1</div>
                <div class="stage-desc">Yosys Synthesis</div>
                <div class="stage-status {'text-green' if cell_count > 0 else 'text-red'}">
                    {'[OK] ' + str(cell_count) + ' Standard Cells' if cell_count > 0 else '[FAIL] Unmapped'}
                </div>
            </div>
            <div class="stage-item {'pass' if timing_met else 'fail'}">
                <div class="stage-name">Stage 2.2 - 3.0</div>
                <div class="stage-desc">STA Timing & Cadence</div>
                <div class="stage-status {'text-green' if timing_met else 'text-red'}">
                    {'[OK] WNS ' + f'{wns:+.2f}ns' if timing_met else '[WARN] Timing Violation'}
                </div>
            </div>
        </div>

        <!-- Top Level PPA KPI Cards -->
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-title">Core Area (Estimated)</div>
                <div class="kpi-value">{area_estimate.split()[0]}</div>
                <div class="kpi-sub">{cell_count} standard cells</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">Target Frequency</div>
                <div class="kpi-value">{freq_mhz:.1f} MHz</div>
                <div class="kpi-sub">Clock Period: {1000.0/freq_mhz:.2f} ns</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">Worst Negative Slack</div>
                <div class="kpi-value {'text-green' if wns >= 0 else 'text-red'}">{wns:+.3f} ns</div>
                <div class="kpi-sub">Critical Path: {crit_delay:.3f} ns</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">Dynamic Power (Est.)</div>
                <div class="kpi-value">{dynamic_power_mw:.3f} mW</div>
                <div class="kpi-sub">Leakage: {leakage_power_uw:.2f} &mu;W</div>
            </div>
        </div>

        <!-- Main Analytics Grid -->
        <div class="main-grid">
            <!-- Left: Cell Breakdown -->
            <div class="card">
                <div class="card-header">
                    <div class="card-title">Standard Cell Type Breakdown</div>
                    <span class="badge badge-info">{len(cell_breakdown)} Unique Gates</span>
                </div>
                {cell_bars_html}
            </div>

            <!-- Right: Timing & EDA Bundles -->
            <div class="card">
                <div class="card-header">
                    <div class="card-title">STA Timing Summary</div>
                    <span class="badge {'badge-success' if timing_met else 'badge-danger'}">
                        {'Met' if timing_met else 'Violated'}
                    </span>
                </div>
                <div class="slack-box">
                    <div class="slack-row">
                        <span>WNS (Worst Slack):</span>
                        <span class="{'text-green' if wns >= 0 else 'text-red'}">{wns:+.3f} ns</span>
                    </div>
                    <div class="slack-row">
                        <span>TNS (Total Slack):</span>
                        <span>{tns:+.3f} ns</span>
                    </div>
                    <div class="slack-row">
                        <span>Path Delay:</span>
                        <span>{crit_delay:.3f} ns</span>
                    </div>
                </div>

                <div class="card-header" style="margin-top: 16px;">
                    <div class="card-title">Production EDA Bundles</div>
                </div>
                <ul class="script-list">
                    <li class="script-item">
                        <span>Cadence Genus Synthesis</span>
                        <span class="script-badge">genus.tcl</span>
                    </li>
                    <li class="script-item">
                        <span>Cadence Innovus P&R</span>
                        <span class="script-badge">innovus.tcl</span>
                    </li>
                    <li class="script-item">
                        <span>OpenROAD Physical Flow</span>
                        <span class="script-badge">openroad.tcl</span>
                    </li>
                    <li class="script-item">
                        <span>Synopsys / Cadence SDC</span>
                        <span class="script-badge">{design_name}.sdc</span>
                    </li>
                </ul>
            </div>
        </div>
    </div>
</body>
</html>
"""
    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(html_content, encoding="utf-8")
    return str(p)
