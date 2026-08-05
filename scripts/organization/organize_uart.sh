#!/bin/bash
cd ~/rtl2gds

TEST_DIR="/mnt/c/Users/ssuja/OneDrive/Desktop/Learn_Antigravity_Advance/rtl-2-gds-automation/uart-test"
mkdir -p $TEST_DIR/{src,images,outputs/gds,outputs/lef,outputs/mag,outputs/spice,outputs/netlists,reports}

cp uart.v uart_tb.v $TEST_DIR/src/
cp OpenLane/designs/uart/config.json $TEST_DIR/src/

RUN_DIR=$(ls -td ~/rtl2gds/OpenLane/designs/uart/runs/RUN_* | head -n 1)

cp $RUN_DIR/results/signoff/uart_top.gds $TEST_DIR/outputs/gds/
cp $RUN_DIR/results/signoff/uart_top.lef $TEST_DIR/outputs/lef/
cp $RUN_DIR/results/signoff/uart_top.mag $TEST_DIR/outputs/mag/
cp $RUN_DIR/results/signoff/uart_top.spice $TEST_DIR/outputs/spice/

cp $RUN_DIR/reports/metrics.csv $TEST_DIR/reports/
cp $RUN_DIR/reports/manufacturability.rpt $TEST_DIR/reports/
cp -r $RUN_DIR/reports/signoff $TEST_DIR/reports/

# Logic schematic
echo "read_verilog uart.v; prep -top uart_top; write_json uart_top.json" > synth.ys
yosys synth.ys
netlistsvg uart_top.json -o $TEST_DIR/images/uart_logic.svg

# Physical layouts
export TECH_LEF="$RUN_DIR/tmp/merged.nom.lef"
for step in floorplan placement routing; do
  export INPUT_DEF=$(ls $RUN_DIR/results/$step/*.def | head -n 1)
  export OUTPUT_PNG="$TEST_DIR/images/${step}_uart.png"
  xvfb-run -a klayout -z -r klayout_render_def.py
done

# Final GDS
export INPUT_DEF="$RUN_DIR/results/signoff/uart_top.gds"
export OUTPUT_PNG="$TEST_DIR/images/uart_gds_real.png"
xvfb-run -a klayout -z -r klayout_render.py

echo "UART artifact organization complete."
