#!/bin/bash
cd ~/rtl2gds
cp /mnt/c/Users/ssuja/OneDrive/Desktop/Learn_Antigravity_Advance/rtl-2-gds-automation/klayout_render_def.py .

RUN_DIR=$(ls -td ~/rtl2gds/OpenLane/designs/full_adder/runs/RUN_* | head -n 1)
export TECH_LEF="$RUN_DIR/tmp/merged.nom.lef"

for step in floorplan placement routing; do
  export INPUT_DEF=$(ls $RUN_DIR/results/$step/*.def | head -n 1)
  export OUTPUT_PNG="/mnt/c/Users/ssuja/OneDrive/Desktop/Learn_Antigravity_Advance/rtl-2-gds-automation/full-adder-test/images/${step}_full_adder.png"
  
  echo "Rendering $step: $INPUT_DEF to $OUTPUT_PNG"
  xvfb-run -a klayout -z -r klayout_render_def.py
done
