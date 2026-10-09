#!/usr/bin/env python3
"""
Comprehensive empirical metrics extractor for all 5 SiliconFlow-AI benchmark designs.
"""
import subprocess
import csv
import io
import json

DESIGNS = ["alu4bit", "uart_tx", "sync_fifo", "counter_sync", "pwm_generator"]

def extract_all():
    summary = {}
    for d in DESIGNS:
        wsl_path = f"/home/sujan123/rtl2gds/OpenLane/designs/{d}/runs/tapeout_validation/reports/metrics.csv"
        res = subprocess.run(["wsl", "-e", "cat", wsl_path], capture_output=True, text=True)
        if res.returncode != 0:
            print(f"Error reading {d}: {res.stderr}")
            continue
        reader = csv.reader(io.StringIO(res.stdout))
        headers = next(reader)
        row = next(reader)
        data = dict(zip(headers, row))
        
        # Also get synthesis report if available or gate count from yosys
        d_summary = {
            "design": d,
            "flow_status": data.get("flow_status", "completed"),
            "runtime": data.get("total_runtime", "N/A"),
            "routed_runtime": data.get("routed_runtime", "N/A"),
            "synth_cells": int(data.get("synth_cell_count", 0)),
            "total_physical_cells": int(data.get("TotalCells", 0)),
            "core_area_um2": float(data.get("CoreArea_um^2", 0.0)),
            "die_area_mm2": float(data.get("DIEAREA_mm^2", 0.0)),
            "wire_length_um": float(data.get("wire_length", 0.0)),
            "via_count": int(data.get("vias", 0)),
            "wns_ns": float(data.get("wns", 0.0)),
            "tns_ns": float(data.get("tns", 0.0)),
            "critical_path_ns": float(data.get("critical_path_ns", 0.0)) if data.get("critical_path_ns") not in (None, "", "None") else 0.0,
            "target_clock_mhz": float(data.get("suggested_clock_frequency", 100.0)),
            "drc_violations": int(data.get("tritonRoute_violations", 0)) + int(data.get("Magic_violations", 0)),
            "magic_violations": int(data.get("Magic_violations", 0)),
            "antenna_violations": int(data.get("pin_antenna_violations", 0)) + int(data.get("net_antenna_violations", 0)),
            "lvs_errors": int(data.get("lvs_total_errors", 0)),
            "peak_memory_mb": float(data.get("Peak_Memory_Usage_MB", 0.0)),
            "internal_power_uW": data.get("power_typical_internal_uW", "N/A"),
            "switching_power_uW": data.get("power_typical_switching_uW", "N/A"),
            "leakage_power_uW": data.get("power_typical_leakage_uW", "N/A"),
            "openlane_tag": "tapeout_validation",
            "pdk": "sky130A (sky130_fd_sc_hd)"
        }
        summary[d] = d_summary
        
    print(json.dumps(summary, indent=2))
    with open("docs/benchmark_results.json", "w") as f:
        json.dump(summary, f, indent=2)
    print("Saved to docs/benchmark_results.json")

if __name__ == "__main__":
    extract_all()
