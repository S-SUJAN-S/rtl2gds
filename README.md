# RTL to GDSII Automation 🚀

Welcome to the **RTL to GDSII Automation** repository! This project hosts a fully automated, agent-driven physical design pipeline capable of taking raw Verilog RTL, synthesizing it, placing & routing it, and exporting it as a fully manufacturable GDSII silicon mask targeting the **SkyWater 130nm (sky130) PDK**.

## 🧠 Overview

This repository demonstrates the power of autonomous AI agents interacting natively with Linux-based Electronic Design Automation (EDA) tools. Using a WSL Ubuntu environment and Docker, the system autonomously drives the **OpenLane** flow to compile various complex digital designs into physical layouts.

### 🌟 Featured Hardware Accelerators

We have successfully engineered and synthesized the following designs in this repository:

1. **8x8 Systolic Array Matrix Multiplication Accelerator**
   - **Architecture:** 8x8 grid of Processing Elements (64 signed multipliers + 32-bit accumulators)
   - **Dataflow:** Weight-Stationary with skewed input/output wave propagation.
   - **Metrics:** 50 MHz Target | ~2.9ns Critical Path | 0.9mm² Die Area | 140,546 Physical Cells
   - **Status:** Fully Timing Clean and DRC/LVS Passed

2. **100MHz UART Transceiver**
   - **Architecture:** Standard UART TX/RX with configurable baud rates.
   - **Status:** Fully Timing Clean and DRC/LVS Passed

3. **4-Bit ALU**
   - **Architecture:** Combinational Logic Arithmetic Unit.
   - **Status:** Fully Timing Clean and DRC/LVS Passed

4. **Full Adder**
   - **Architecture:** Basic combinational adder for toolchain validation.

## 📁 Repository Structure

- `designs/` - Contains the Verilog RTL (`.v`), Testbenches (`_tb.v`), and OpenLane configuration (`config.json`) for each hardware component.
- `scripts/` - Shell and Python automation scripts for executing Docker pipelines, organizing artifacts, and rendering SVGs/PNGs from physical layouts.
- `outputs/` - Extracted layout artifacts for each design, including images of the floorplan, placement, detailed routing, and final GDSII.
- `docs/` - Documentation on the RTL-to-GDS flow and environment setup.

## 🛠️ Toolchain

- **OpenLane:** The automated RTL-to-GDSII flow pipeline.
- **Yosys:** Logic Synthesis.
- **OpenROAD:** Floorplanning, Placement, CTS, and Global/Detailed Routing.
- **TritonRoute:** Detailed Routing Engine.
- **Magic:** VLSI Layout tool for DRC and GDSII streaming.
- **KLayout:** GDSII Viewer and XOR checking.
- **Icarus Verilog / Verilator:** RTL verification and linting.

## 🖼️ Physical Layout Examples

*(Check the `outputs/systolic_array/images/` directory for high-resolution renders of the silicon layers!)*
