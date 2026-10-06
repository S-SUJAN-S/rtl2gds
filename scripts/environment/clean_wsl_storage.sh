#!/bin/bash
# ==============================================================================
# clean_wsl_storage.sh
# Automated WSL & RTL-to-GDS Storage Optimization Utility
# ==============================================================================
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================================================${NC}"
echo -e "${BLUE}   WSL RTL-to-GDS Storage Optimization & Pruning Utility        ${NC}"
echo -e "${BLUE}================================================================${NC}"

# Check current usage
echo -e "\n${YELLOW}[1/4] Current WSL Root Filesystem Usage:${NC}"
df -h /

# Clean system caches
echo -e "\n${YELLOW}[2/4] Cleaning Package & System Log Caches...${NC}"
echo " -> Cleaning APT package archives..."
sudo apt-get clean 2>/dev/null || true
sudo apt-get autoremove -y 2>/dev/null || true

echo " -> Vacuuming systemd journal logs to max 50MB..."
sudo journalctl --vacuum-size=50M 2>/dev/null || true

echo " -> Purging pip and temporary caches..."
rm -rf ~/.cache/pip ~/.cache/Tectonic /tmp/rtl_sim_* /tmp/rtl_synth_* 2>/dev/null || true
echo -e "${GREEN}✓ System caches successfully pruned.${NC}"

# Clean corrupted EQY formal directory
if [ -d "/home/sujan123/simd_alu_v2/equiv" ]; then
    echo -e "\n${YELLOW}[3/4] Removing corrupted/obsolete EQY formal scratch directory (~5.9 GB)...${NC}"
    rm -rf /home/sujan123/simd_alu_v2/equiv
    echo -e "${GREEN}✓ Removed /home/sujan123/simd_alu_v2/equiv.${NC}"
fi

# Clean OpenLane intermediate design runs
echo -e "\n${YELLOW}[4/4] Pruning OpenLane intermediate runs (~30 GB)...${NC}"
DESIGNS_DIR="/home/sujan123/rtl2gds/OpenLane/designs"

if [ -d "$DESIGNS_DIR" ]; then
    for d in "$DESIGNS_DIR"/*; do
        if [ -d "$d/runs" ]; then
            design_name=$(basename "$d")
            run_size=$(du -sh "$d/runs" 2>/dev/null | cut -f1)
            echo " -> Cleaning $design_name/runs (was $run_size)..."
            rm -rf "$d/runs"/*
        fi
    done
    echo -e "${GREEN}✓ All intermediate OpenLane runs pruned!${NC}"
    echo -e "   (Note: Final signoff artifacts remain safely preserved in Windows outputs/)${NC}"
fi

echo -e "\n${GREEN}================================================================${NC}"
echo -e "${GREEN}   Cleanup Complete! New Filesystem Usage:                      ${NC}"
echo -e "${GREEN}================================================================${NC}"
df -h /

echo -e "\n${YELLOW}NEXT STEP (Crucial for reclaiming Windows C: drive space):${NC}"
echo "Exit WSL and run this command in Windows PowerShell (or run scripts/environment/compact_wsl_disk.ps1):"
echo "  wsl --shutdown"
echo "  wsl --manage Ubuntu --set-sparse true"
echo "================================================================"
