#!/bin/bash
cd /home/sujan123/rtl2gds

cat << 'EOF' > render_def.tcl
read_lef $env(PDK_ROOT)/$env(PDK)/libs.ref/sky130_fd_sc_hd/techlef/sky130_fd_sc_hd__nom.tlef
read_lef $env(PDK_ROOT)/$env(PDK)/libs.ref/sky130_fd_sc_hd/lef/sky130_fd_sc_hd.lef
read_def $env(DEF_FILE)
gui::set_resolution 1920 1080
gui::set_color_scheme "dark"
gui::fit
gui::save_image $env(OUT_PNG)
exit
EOF

RUN_DIR=$(ls -td /home/sujan123/rtl2gds/OpenLane/designs/full_adder/runs/RUN_* | head -n 1)
RUN_BASENAME=$(basename $RUN_DIR)

for step in floorplan placement routing; do
  DEF_FILE=$(ls $RUN_DIR/results/$step/*.def | head -n 1)
  DEF_REL="designs/full_adder/runs/$RUN_BASENAME/results/$step/$(basename $DEF_FILE)"
  OUT_PNG="/rtl2gds/${step}_full_adder.png"
  
  echo "Rendering $step: $DEF_REL"
  
  xvfb-run -a docker run --rm \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -v /home/sujan123/rtl2gds:/rtl2gds \
    -v /home/sujan123/rtl2gds/OpenLane:/openlane \
    -v /home/sujan123/.ciel:/root/.ciel \
    -e PDK_ROOT=/root/.ciel \
    -e PDK=sky130A \
    -e DISPLAY=$DISPLAY \
    -e DEF_FILE=/openlane/$DEF_REL \
    -e OUT_PNG=$OUT_PNG \
    --network host \
    ghcr.io/the-openroad-project/openlane:ff5509f65b17bfa4068d5336495ab1718987ff69-amd64 openroad -gui -exit /rtl2gds/render_def.tcl
    
  cp "/home/sujan123/rtl2gds/${step}_full_adder.png" "/mnt/c/Users/ssuja/OneDrive/Desktop/Learn_Antigravity_Advance/rtl-2-gds-automation/full-adder-test/images/${step}_full_adder.png"
done
