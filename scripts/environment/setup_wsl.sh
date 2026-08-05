#!/bin/bash

echo "===================================================="
echo " RTL-to-GDSII & LLM Agent - WSL Environment Setup"
echo "===================================================="

# Update package lists
sudo apt-get update

# Install basic EDA tools available in Ubuntu repositories
echo "[*] Installing Verilator, Icarus Verilog, Yosys, KLayout, and Magic..."
sudo apt-get install -y verilator iverilog yosys klayout magic

# Install Python and essential build tools
echo "[*] Installing Python 3 and build essentials..."
sudo apt-get install -y python3 python3-pip python3-venv build-essential git curl

# Set up Python virtual environment for the LLM agent
echo "[*] Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies (Cocotb, Pyverilog, Google GenAI SDK, etc.)
echo "[*] Installing Python dependencies..."
pip install --upgrade pip
COCOTB_IGNORE_PYTHON_REQUIRES=1 pip install cocotb pyverilog google-generativeai pydantic networkx matplotlib

echo "===================================================="
echo " Setup Complete!"
echo " To activate your python environment, run:"
echo "   source venv/bin/activate"
echo " Note: Advanced tools like OpenROAD and OpenSTA are best run via OpenLane's Docker container."
echo "===================================================="
