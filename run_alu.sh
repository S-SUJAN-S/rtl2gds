#!/bin/bash
cd ~/rtl2gds/OpenLane
make mount << 'EOF'
./flow.tcl -design alu4bit
exit
EOF
