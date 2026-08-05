#!/bin/bash
cd ~/rtl2gds

TEST_DIR="/mnt/c/Users/ssuja/OneDrive/Desktop/Learn_Antigravity_Advance/rtl-2-gds-automation/systolic-test"
mkdir -p $TEST_DIR/{src,images,outputs/gds,outputs/lef,outputs/mag,outputs/spice,outputs/netlists,reports}

cp systolic_mm_accel.v systolic_tb.v $TEST_DIR/src/
cp OpenLane/designs/systolic/config.json $TEST_DIR/src/

RUN_DIR=$(ls -td ~/rtl2gds/OpenLane/designs/systolic/runs/RUN_* | head -n 1)

cp $RUN_DIR/results/signoff/systolic_mm_accel.gds $TEST_DIR/outputs/gds/
cp $RUN_DIR/results/signoff/systolic_mm_accel.lef $TEST_DIR/outputs/lef/
cp $RUN_DIR/results/signoff/systolic_mm_accel.mag $TEST_DIR/outputs/mag/
cp $RUN_DIR/results/signoff/systolic_mm_accel.spice $TEST_DIR/outputs/spice/

cp $RUN_DIR/reports/metrics.csv $TEST_DIR/reports/
cp -r $RUN_DIR/reports/signoff $TEST_DIR/reports/

# Physical layouts (just placement and routing and GDS)
export TECH_LEF="$RUN_DIR/tmp/merged.nom.lef"

for step in floorplan placement routing; do
  export INPUT_DEF=$(ls $RUN_DIR/results/$step/*.def | head -n 1)
  export OUTPUT_PNG="$TEST_DIR/images/${step}_systolic.png"
  xvfb-run -a klayout -z -r klayout_render_def.py
done

export INPUT_DEF="$RUN_DIR/results/signoff/systolic_mm_accel.gds"
export OUTPUT_PNG="$TEST_DIR/images/systolic_gds_real.png"
xvfb-run -a klayout -z -r klayout_render.py

echo "Systolic artifact organization complete."
