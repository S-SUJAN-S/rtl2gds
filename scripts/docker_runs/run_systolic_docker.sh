#!/bin/bash
cd ~/rtl2gds/OpenLane
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
    ./flow.tcl -design systolic
