#!/bin/bash
cd ~/rtl2gds

TEST_DIR="/mnt/c/Users/ssuja/OneDrive/Desktop/Learn_Antigravity_Advance/rtl-2-gds-automation/alu4bit-test"
mkdir -p $TEST_DIR/{src,images,outputs/gds,outputs/lef,outputs/mag,outputs/spice,outputs/netlists,reports}

cp alu4bit.v alu4bit_tb.v $TEST_DIR/src/
cp OpenLane/designs/alu4bit/config.json $TEST_DIR/src/

RUN_DIR=$(ls -td ~/rtl2gds/OpenLane/designs/alu4bit/runs/RUN_* | head -n 1)

cp $RUN_DIR/results/signoff/alu4bit.gds $TEST_DIR/outputs/gds/
cp $RUN_DIR/results/signoff/alu4bit.lef $TEST_DIR/outputs/lef/
cp $RUN_DIR/results/signoff/alu4bit.mag $TEST_DIR/outputs/mag/
cp $RUN_DIR/results/signoff/alu4bit.spice $TEST_DIR/outputs/spice/
cp $RUN_DIR/results/signoff/alu4bit.v $TEST_DIR/outputs/netlists/

cp $RUN_DIR/reports/metrics.csv $TEST_DIR/reports/
cp $RUN_DIR/reports/manufacturability.rpt $TEST_DIR/reports/
cp -r $RUN_DIR/reports/signoff $TEST_DIR/reports/

# Logic schematic
echo "read_verilog alu4bit.v; prep -top alu4bit; write_json alu4bit.json" > synth.ys
yosys synth.ys
netlistsvg alu4bit.json -o $TEST_DIR/images/alu4bit_logic.svg

# Physical layouts
export TECH_LEF="$RUN_DIR/tmp/merged.nom.lef"
for step in floorplan placement routing; do
  export INPUT_DEF=$(ls $RUN_DIR/results/$step/*.def | head -n 1)
  export OUTPUT_PNG="$TEST_DIR/images/${step}_alu4bit.png"
  xvfb-run -a klayout -z -r klayout_render_def.py
done

# Final GDS
export INPUT_DEF="$RUN_DIR/results/signoff/alu4bit.gds"
export OUTPUT_PNG="$TEST_DIR/images/alu4bit_gds_real.png"
xvfb-run -a klayout -z -r klayout_render.py

echo "ALU artifact organization complete."
