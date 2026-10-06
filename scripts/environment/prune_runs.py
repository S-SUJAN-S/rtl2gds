#!/usr/bin/env python3
import os
import shutil
from pathlib import Path

designs_base = Path("/home/sujan123/rtl2gds/OpenLane/designs")

# Explicit mapping of each design to the single final run to preserve
configs = {
    "alu4bit": "RUN_2026.08.05_12.32.49",
    "full_adder": "RUN_2026.08.05_06.40.00",
    "sdpa_accelerator": "RUN_2026.08.06_21.05.20",
    "simd_alu_v2": "g13_p11",
    "simd_alu_v2_syn": "synflat3",
}

print("=== Pruning Intermediate OpenLane Design Runs ===")
for design, keep_run in configs.items():
    runs_dir = designs_base / design / "runs"
    if not runs_dir.exists():
        continue
    for item in list(runs_dir.iterdir()):
        if item.is_dir() and item.name != keep_run:
            print(f"Removing intermediate run: {design}/runs/{item.name}")
            os.system(f"rm -rf '{item}'")
        elif item.name == keep_run:
            print(f"PRESERVING final run: {design}/runs/{keep_run}")

# Also check single-run designs to confirm preservation
for single_design in ["systolic", "uart", "spm"]:
    single_runs_dir = designs_base / single_design / "runs"
    if single_runs_dir.exists():
        for r in single_runs_dir.iterdir():
            print(f"PRESERVING final run: {single_design}/runs/{r.name}")

print("\n=== Pruning Obsolete Formal Equiv Runs in simd_alu_v2/equiv ===")
equiv_dir = Path("/home/sujan123/simd_alu_v2/equiv")
keep_equiv = {"eqy_routed_final", "eqy_synth_final", "s3sum"}

if equiv_dir.exists():
    for item in list(equiv_dir.iterdir()):
        if item.is_dir() and item.name not in keep_equiv:
            print(f"Removing obsolete equiv run: equiv/{item.name}")
            os.system(f"rm -rf '{item}'")
        elif item.is_dir() and item.name in keep_equiv:
            print(f"PRESERVING final equiv run: equiv/{item.name}")

print("\n=== Pruning simd_alu_v2 Sub-Variant Runs (_a, _b, _c, _d) ===")
# Note: simd_alu_v2_a..d each has one trial run (sign_a, sign_b, sign_c, sign_d)
# We can check if their designs are already integrated into simd_alu_v2 (g13_p11)
for var in ["a", "b", "c", "d"]:
    var_runs = designs_base / f"simd_alu_v2_{var}" / "runs"
    if var_runs.exists():
        for item in list(var_runs.iterdir()):
            print(f"Removing trial run: simd_alu_v2_{var}/runs/{item.name}")
            os.system(f"rm -rf '{item}'")

print("\nPruning complete!")
