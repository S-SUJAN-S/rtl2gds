#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/run_openlane_physical_flow.py
====================================
Autonomous OpenLane Physical Implementation & KLayout GDSII Signoff Bridge.
Executes the physical RTL-to-GDSII flow in WSL2 Docker:
  1. Copies synthesizable Verilog into ~/rtl2gds/OpenLane/designs/<design>/src/<design>.v
  2. Generates OpenLane config.json with target PPA constraints
  3. Executes flow.tcl (-design <design> -tag tapeout_validation -overwrite)
  4. Audits physical metrics (DRC violations, LVS match, wirelength, cell count, WNS)
  5. Renders high-resolution KLayout layout PNGs with Sky130A layer stipples
  6. Copies .gds and .def deliverables into outputs/<design>/outputs/
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
DESIGNS_DIR = PROJECT_ROOT / "designs"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

OPENLANE_WSL_ROOT = "/home/sujan123/rtl2gds/OpenLane"
SKY130_LYP_WSL = "/home/sujan123/.ciel/ciel/sky130/versions/0fe599b2afb6708d281543108caf8310912f54af/sky130A/libs.tech/klayout/tech/sky130A.lyp"

PHYSICAL_CONFIGS = {
    "alu4bit": {
        "clock_port": None,
        "clock_period": 10.0,
        "run_cts": False,
        "die_area": "0 0 75 75",
        "core_box": [12, 12, 62, 62],
    },
    "uart_tx": {
        "clock_port": "clk",
        "clock_period": 10.0,
        "run_cts": True,
        "die_area": "0 0 100 100",
        "core_box": [15, 15, 85, 85],
    },
    "sync_fifo": {
        "clock_port": "clk",
        "clock_period": 10.0,
        "run_cts": True,
        "die_area": "0 0 160 160",
        "core_box": [20, 20, 140, 140],
    },
    "counter_sync": {
        "clock_port": "clk",
        "clock_period": 10.0,
        "run_cts": True,
        "die_area": "0 0 90 90",
        "core_box": [15, 15, 75, 75],
    },
    "pwm_generator": {
        "clock_port": "clk",
        "clock_period": 10.0,
        "run_cts": True,
        "die_area": "0 0 100 100",
        "core_box": [15, 15, 85, 85],
    },
}


def run_wsl_cmd(cmd_str: str, check: bool = True) -> subprocess.CompletedProcess:
    full_cmd = ["wsl", "-e", "bash", "-c", cmd_str]
    return subprocess.run(full_cmd, text=True, capture_output=True, check=check)


def setup_openlane_design(design_name: str, rtl_path: Path, cfg: Dict[str, Any]):
    print(f"[*] Setting up OpenLane workspace for '{design_name}'...")
    wsl_design_dir = f"{OPENLANE_WSL_ROOT}/designs/{design_name}"
    run_wsl_cmd(f"mkdir -p {wsl_design_dir}/src", check=True)

    # Convert Windows RTL path to WSL and copy
    wsl_rtl_src = run_wsl_cmd(f"wslpath -u '{str(rtl_path)}'").stdout.strip()
    run_wsl_cmd(f"cp {wsl_rtl_src} {wsl_design_dir}/src/{design_name}.v", check=True)

    # Generate config.json
    openlane_config = {
        "DESIGN_NAME": design_name,
        "VERILOG_FILES": f"dir::src/{design_name}.v",
        "CLOCK_PORT": cfg.get("clock_port"),
        "CLOCK_PERIOD": cfg.get("clock_period", 10.0),
        "RUN_CTS": cfg.get("run_cts", True),
        "FP_SIZING": "absolute",
        "DIE_AREA": cfg.get("die_area", "0 0 100 100"),
        "DESIGN_IS_CORE": 0,
        "FP_PDN_CORE_RING": 0,
        "RT_MAX_LAYER": "met4",
        "DIODE_INSERTION_STRATEGY": 4 if cfg.get("run_cts") else 0,
    }

    config_json_str = json.dumps(openlane_config, indent=4).replace('"', '\\"')
    run_wsl_cmd(f"cat << 'EOF' > {wsl_design_dir}/config.json\n{json.dumps(openlane_config, indent=4)}\nEOF", check=True)
    print(f"  [OK] OpenLane config written: DIE_AREA={openlane_config['DIE_AREA']}, CLK={openlane_config['CLOCK_PORT']}")


def execute_physical_flow(design_name: str) -> Dict[str, Any]:
    print(f"[*] Executing OpenLane physical implementation flow for '{design_name}'...")
    flow_cmd = f"cd {OPENLANE_WSL_ROOT} && ./flow.tcl -design {design_name} -tag tapeout_validation -overwrite"
    p = run_wsl_cmd(flow_cmd, check=False)
    
    if p.returncode != 0:
        print(f"  [FAIL] OpenLane flow returned code {p.returncode}:")
        print(p.stderr[-500:] if p.stderr else p.stdout[-500:])
        return {"success": False, "error": p.stderr or p.stdout}

    print(f"  [OK] OpenLane physical flow completed successfully!")
    return {"success": True}


def audit_and_export_deliverables(design_name: str, cfg: Dict[str, Any]) -> Dict[str, Any]:
    print(f"[*] Auditing physical signoff deliverables for '{design_name}'...")
    run_dir = f"{OPENLANE_WSL_ROOT}/designs/{design_name}/runs/tapeout_validation"
    out_design_dir = OUTPUTS_DIR / design_name
    out_outputs_dir = out_design_dir / "outputs"
    out_images_dir = out_design_dir / "images"
    out_outputs_dir.mkdir(parents=True, exist_ok=True)
    out_images_dir.mkdir(parents=True, exist_ok=True)

    gds_wsl = f"{run_dir}/results/final/gds/{design_name}.gds"
    def_wsl = f"{run_dir}/results/final/def/{design_name}.def"
    metrics_wsl = f"{run_dir}/reports/metrics.csv"
    mfg_wsl = f"{run_dir}/reports/manufacturability.rpt"

    # Copy deliverables to Windows output folder
    out_outputs_wsl = run_wsl_cmd(f"wslpath -u '{str(out_outputs_dir)}'").stdout.strip()
    run_wsl_cmd(f"cp {gds_wsl} {out_outputs_wsl}/{design_name}.gds", check=True)
    run_wsl_cmd(f"cp {def_wsl} {out_outputs_wsl}/{design_name}.def", check=True)

    # Read manufacturability report for DRC & LVS
    mfg_rpt = run_wsl_cmd(f"cat {mfg_wsl}").stdout
    drc_clean = "Total Magic DRC violations is 0" in mfg_rpt or "violations is 0" in mfg_rpt
    lvs_clean = "Design is LVS clean" in mfg_rpt or "Total errors = 0" in mfg_rpt

    # Read metrics.csv
    metrics_content = run_wsl_cmd(f"cat {metrics_wsl}").stdout.strip().splitlines()
    metrics = {}
    if len(metrics_content) >= 2:
        keys = [k.strip() for k in metrics_content[0].split(",")]
        vals = [v.strip() for v in metrics_content[1].split(",")]
        metrics = dict(zip(keys, vals))

    # Trigger Headless KLayout rendering
    render_layout_images(design_name, gds_wsl, out_images_dir, cfg)

    summary = {
        "design": design_name,
        "gds_path": str(out_outputs_dir / f"{design_name}.gds"),
        "def_path": str(out_outputs_dir / f"{design_name}.def"),
        "layout_png": str(out_images_dir / f"{design_name}_layout.png"),
        "drc_violations": int(metrics.get("Magic_violations", 0) or 0),
        "lvs_clean": lvs_clean,
        "wirelength_um": float(metrics.get("wire_length", 0.0) or 0.0),
        "via_count": int(metrics.get("vias", 0) or 0),
        "synth_cells": int(metrics.get("synth_cell_count", 0) or 0),
        "total_cells": int(metrics.get("TotalCells", 0) or 0),
        "core_area_um2": float(metrics.get("CoreArea_um^2", 0.0) or 0.0),
        "wns_ns": float(metrics.get("wns", 0.0) or 0.0),
        "clock_freq_mhz": float(metrics.get("suggested_clock_frequency", 100.0) or 100.0),
    }

    print(f"  [OK] Physical Signoff Metrics:")
    print(f"       - Standard Cells : {summary['synth_cells']} logic ({summary['total_cells']} total placed)")
    print(f"       - Core Area      : {summary['core_area_um2']} um²")
    print(f"       - Wirelength     : {summary['wirelength_um']} um ({summary['via_count']} vias)")
    print(f"       - DRC Violations : {summary['drc_violations']}")
    print(f"       - LVS Status     : {'CLEAN' if summary['lvs_clean'] else 'FAILED'}")
    print(f"       - GDS Deliverable: {summary['gds_path']}")
    return summary


def render_layout_images(design_name: str, gds_wsl_path: str, out_images_dir: Path, cfg: Dict[str, Any]):
    print(f"[*] Generating KLayout layout snapshots for '{design_name}'...")
    out_images_wsl = run_wsl_cmd(f"wslpath -u '{str(out_images_dir)}'").stdout.strip()
    
    full_layout_png = f"{out_images_wsl}/{design_name}_layout.png"
    real_gds_png = f"{out_images_wsl}/{design_name}_gds_real.png"
    zoomed_png = f"{out_images_wsl}/{design_name}_gds_zoomed.png"
    box = cfg.get("core_box", [15, 15, 85, 85])

    py_render_script = f"""import pya
import os

app = pya.Application.instance()
main_window = app.main_window()

opt = pya.LoadLayoutOptions()
main_window.load_layout('{gds_wsl_path}', opt, 0)
view = main_window.current_view()

lyp_path = '{SKY130_LYP_WSL}'
if os.path.exists(lyp_path):
    view.load_layer_props(lyp_path)

view.set_config('background-color', '#12161f')
view.set_config('grid-color', '#222836')
view.set_config('text-color', '#e2e8f0')
view.max_hier()
view.zoom_fit()

view.save_image('{full_layout_png}', 2048, 1536)
view.save_image('{real_gds_png}', 2048, 1536)

core_box = pya.DBox({box[0]}, {box[1]}, {box[2]}, {box[3]})
view.zoom_box(core_box)
view.save_image('{zoomed_png}', 2048, 1536)
app.exit(0)
"""

    temp_script = f"/tmp/render_{design_name}.py"
    run_wsl_cmd(f"cat << 'EOF' > {temp_script}\n{py_render_script}\nEOF", check=True)
    run_wsl_cmd(f"klayout -z -r {temp_script}", check=True)
    print(f"  [OK] Saved renders to {out_images_dir / f'{design_name}_layout.png'}")


def main():
    import argparse
    import re
    parser = argparse.ArgumentParser(description="Run OpenLane Physical Flow")
    parser.add_argument("design_pos", nargs="?", default=None, help="Design name (positional)")
    parser.add_argument("--design", "-d", default=None, help="Design name (flag)")
    args = parser.parse_args()

    design = args.design or args.design_pos
    if not design:
        print("Usage: python scripts/run_openlane_physical_flow.py <design_name> OR --design <design_name>")
        sys.exit(1)

    rtl_path = DESIGNS_DIR / design / f"{design}.v"
    if not rtl_path.exists():
        print(f"Error: RTL not found at {rtl_path}")
        sys.exit(1)

    if design in PHYSICAL_CONFIGS:
        cfg = PHYSICAL_CONFIGS[design]
    else:
        # Dynamic fallback config for novel autonomous designs
        rtl_code = rtl_path.read_text(encoding="utf-8")
        has_clk = bool(re.search(r'\b(clk|clock)\b', rtl_code, re.I))
        cfg = {
            "clock_port": "clk" if has_clk else None,
            "clock_period": 10.0,
            "run_cts": has_clk,
            "die_area": "0 0 80 80",
            "core_box": [15, 15, 65, 65],
        }
        print(f"  [AutoConfig] Generated dynamic physical config for novel design '{design}': Clock={cfg['clock_port']}")

    setup_openlane_design(design, rtl_path, cfg)
    res = execute_physical_flow(design)
    if not res["success"]:
        sys.exit(1)
    audit_and_export_deliverables(design, cfg)


if __name__ == "__main__":
    main()
