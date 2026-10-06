#!/bin/bash
# Master RTL-to-GDSII Build Script
# Usage: ./build.sh <design_name>

set -e

if [ -z "$1" ]; then
    echo "Error: Please provide a design name."
    echo "Usage: ./build.sh <design_name>"
    exit 1
fi

DESIGN=$1
PROJECT_DIR=$(pwd)
OPENLANE_DIR="/home/sujan123/rtl2gds/OpenLane"

if [ ! -d "$PROJECT_DIR/designs/$DESIGN" ]; then
    echo "Error: Design '$DESIGN' not found in $PROJECT_DIR/designs/"
    exit 1
fi

echo "=========================================="
echo "🚀 Starting RTL-to-GDS Flow for: $DESIGN"
echo "=========================================="

# 1. Setup OpenLane Workspace
echo "[1/5] Setting up OpenLane workspace..."
mkdir -p $OPENLANE_DIR/designs/$DESIGN
cp $PROJECT_DIR/designs/$DESIGN/* $OPENLANE_DIR/designs/$DESIGN/

# 2. Run OpenLane Docker
echo "[2/5] Synthesizing and routing via OpenLane Docker..."
cd $OPENLANE_DIR
docker run --rm -v /home/sujan123/rtl2gds/OpenLane:/openlane \
    -v /home/sujan123/rtl2gds/OpenLane/designs:/openlane/install \
    -v /home/sujan123:/home/sujan123 \
    -v /home/sujan123/.ciel:/home/sujan123/.ciel \
    -e PDK_ROOT=/home/sujan123/.ciel \
    -e PDK=sky130A \
    --user 1000:1000 \
    --network host \
    --security-opt seccomp=unconfined \
    ghcr.io/the-openroad-project/openlane:ff5509f65b17bfa4068d5336495ab1718987ff69-amd64 \
    ./flow.tcl -design $DESIGN

cd $PROJECT_DIR

# 3. Extract Artifacts
echo "[3/5] Extracting physical design artifacts..."
OUTPUT_DIR="$PROJECT_DIR/outputs/$DESIGN"
mkdir -p $OUTPUT_DIR/{images,outputs/gds,outputs/lef,outputs/mag,outputs/spice,outputs/netlists,reports,src}

# Copy original sources
cp $PROJECT_DIR/designs/$DESIGN/* $OUTPUT_DIR/src/ 2>/dev/null || true

# Find latest run
RUN_DIR=$(ls -td $OPENLANE_DIR/designs/$DESIGN/runs/RUN_* | head -n 1)

if [ -z "$RUN_DIR" ]; then
    echo "Error: No OpenLane run directory found!"
    exit 1
fi

echo "Extracting from $RUN_DIR..."
# Note: For some designs the top-level module name might be different from the design folder name.
# The OpenLane output files usually take the name of the top-level module (or design name depending on config).
# We'll use a wildcard to grab the primary output files in signoff.
cp $RUN_DIR/results/signoff/*.gds $OUTPUT_DIR/outputs/gds/ 2>/dev/null || true
cp $RUN_DIR/results/signoff/*.lef $OUTPUT_DIR/outputs/lef/ 2>/dev/null || true
cp $RUN_DIR/results/signoff/*.mag $OUTPUT_DIR/outputs/mag/ 2>/dev/null || true
cp $RUN_DIR/results/signoff/*.spice $OUTPUT_DIR/outputs/spice/ 2>/dev/null || true
cp $RUN_DIR/results/signoff/*.v $OUTPUT_DIR/outputs/netlists/ 2>/dev/null || true

cp $RUN_DIR/reports/metrics.csv $OUTPUT_DIR/reports/ 2>/dev/null || true
cp $RUN_DIR/reports/manufacturability.rpt $OUTPUT_DIR/reports/ 2>/dev/null || true
cp -r $RUN_DIR/reports/signoff $OUTPUT_DIR/reports/ 2>/dev/null || true

# Extract top level name dynamically from config or assume it's the largest file
TOP_MODULE_FILE=$(ls -S $OUTPUT_DIR/outputs/gds/*.gds | head -n 1)
if [ ! -z "$TOP_MODULE_FILE" ]; then
    TOP_MODULE=$(basename "$TOP_MODULE_FILE" .gds)
else
    TOP_MODULE=$DESIGN
fi
echo "Detected top module as: $TOP_MODULE"

# 4. Logic Rendering
echo "[4/5] Generating Logic SVG schematic..."
# Find the primary verilog file (assuming it's either design_name.v or top_module.v)
V_FILE=$(ls $PROJECT_DIR/designs/$DESIGN/*.v | grep -v "_tb" | head -n 1)
if [ ! -f "synth.ys" ]; then
    echo "read_verilog $V_FILE; prep -top $TOP_MODULE; write_json $OUTPUT_DIR/images/${TOP_MODULE}.json" > synth.ys
    yosys synth.ys || true
    netlistsvg $OUTPUT_DIR/images/${TOP_MODULE}.json -o $OUTPUT_DIR/images/${TOP_MODULE}_logic.svg || true
    rm synth.ys $OUTPUT_DIR/images/${TOP_MODULE}.json || true
fi

# 5. Physical Layout Rendering
echo "[5/5] Rendering physical layout images via KLayout..."
export TECH_LEF="$RUN_DIR/tmp/merged.nom.lef"
for step in floorplan placement routing; do
  export INPUT_DEF=$(ls $RUN_DIR/results/$step/*.def | head -n 1)
  export OUTPUT_PNG="$OUTPUT_DIR/images/${step}_${TOP_MODULE}.png"
  if [ -f "$INPUT_DEF" ]; then
      xvfb-run -a klayout -z -r $PROJECT_DIR/scripts/klayout/klayout_render_def.py
  fi
done

export INPUT_DEF="$RUN_DIR/results/signoff/${TOP_MODULE}.gds"
export OUTPUT_PNG="$OUTPUT_DIR/images/${TOP_MODULE}_gds_real.png"
if [ -f "$INPUT_DEF" ]; then
    xvfb-run -a klayout -z -r $PROJECT_DIR/scripts/klayout/klayout_render.py
fi

echo "=========================================="
echo "✅ Pipeline Complete! Artifacts are in outputs/$DESIGN/"
echo "=========================================="
