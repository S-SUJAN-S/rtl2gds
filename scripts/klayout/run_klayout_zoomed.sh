#!/bin/bash
cd ~/rtl2gds
cp /mnt/c/Users/ssuja/OneDrive/Desktop/Learn_Antigravity_Advance/rtl-2-gds-automation/klayout_zoomed.py .

RUN_DIR=$(ls -td ~/rtl2gds/OpenLane/designs/full_adder/runs/RUN_* | head -n 1)
export TECH_LEF="$RUN_DIR/tmp/merged.nom.lef"

for step in floorplan placement; do
  export INPUT_DEF=$(ls $RUN_DIR/results/$step/*.def | head -n 1)
  export OUTPUT_PNG="/mnt/c/Users/ssuja/OneDrive/Desktop/Learn_Antigravity_Advance/rtl-2-gds-automation/full-adder-test/images/${step}_zoomed.png"
  
  echo "Rendering $step zoomed: $INPUT_DEF to $OUTPUT_PNG"
  xvfb-run -a klayout -z -r klayout_zoomed.py
done
