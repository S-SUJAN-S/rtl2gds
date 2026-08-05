#!/bin/bash
cd /mnt/c/Users/ssuja/OneDrive/Desktop/Learn_Antigravity_Advance/rtl-2-gds-automation
mkdir -p full-adder-test/images
mkdir -p full-adder-test/source
mkdir -p full-adder-test/outputs
mkdir -p full-adder-test/reports

# Copy source
cp full_adder.v full-adder-test/source/
cp full_adder_config.json full-adder-test/source/

# Copy images
cp /mnt/c/Users/ssuja/.gemini/antigravity/brain/2b36d849-7095-4862-916d-9f895f1b40c8/floorplan_full_adder.png full-adder-test/images/
cp /mnt/c/Users/ssuja/.gemini/antigravity/brain/2b36d849-7095-4862-916d-9f895f1b40c8/placement_full_adder.png full-adder-test/images/
cp /mnt/c/Users/ssuja/.gemini/antigravity/brain/2b36d849-7095-4862-916d-9f895f1b40c8/routing_full_adder.png full-adder-test/images/
cp /mnt/c/Users/ssuja/.gemini/antigravity/brain/2b36d849-7095-4862-916d-9f895f1b40c8/full_adder_netlist.png full-adder-test/images/ 2>/dev/null || true

# Get latest run dir
RUN_DIR=$(ls -td ~/rtl2gds/OpenLane/designs/full_adder/runs/RUN_* | head -n 1)

# Copy outputs
cp "$RUN_DIR"/results/signoff/full_adder.gds full-adder-test/outputs/
cp "$RUN_DIR"/results/signoff/full_adder.lef full-adder-test/outputs/
cp "$RUN_DIR"/results/signoff/full_adder.mag full-adder-test/outputs/
cp "$RUN_DIR"/results/signoff/full_adder.spice full-adder-test/outputs/

# Copy reports
cp "$RUN_DIR"/reports/metrics.csv full-adder-test/reports/
cp "$RUN_DIR"/reports/manufacturability.rpt full-adder-test/reports/

echo "Done"
