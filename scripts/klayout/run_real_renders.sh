#!/bin/bash
cd ~/rtl2gds
cp /mnt/c/Users/ssuja/OneDrive/Desktop/Learn_Antigravity_Advance/rtl-2-gds-automation/klayout_render.py .

RUN_DIR=$(ls -td ~/rtl2gds/OpenLane/designs/full_adder/runs/RUN_* | head -n 1)

export INPUT_DEF="$RUN_DIR/results/signoff/full_adder.gds"
export OUTPUT_PNG="/mnt/c/Users/ssuja/.gemini/antigravity/brain/2b36d849-7095-4862-916d-9f895f1b40c8/full_adder_gds_real.png"

echo "Rendering $INPUT_DEF to $OUTPUT_PNG"
xvfb-run -a klayout -z -r klayout_render.py
