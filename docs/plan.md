# RTL-to-GDSII ASIC Flow & LLM Agent Architecture

This document outlines the complete step-by-step open-source RTL-to-GDSII design flow, including the integration points for the Autonomous LLM Closed-Loop Control Engine.

## PHASE 0: FRONT-END DESIGN & VERIFICATION
The initial phase focuses on writing the hardware description, checking for syntax/design rules, and ensuring functional correctness before synthesis.

* **[01] RTL Coding & Spec**: Writing the core logic in SystemVerilog or Verilog. *Tools: Pyverilog, standard text editors.*
* **[02] Static Linting**: Checking the code for warnings, bad practices, and synthesis-blocking errors. *Tools: Verilator (`--lint-only`).*
* **[03] Functional Simulation**: Running testbenches to verify that the RTL behaves correctly according to the spec. *Tools: Icarus Verilog, Cocotb.*
* **[04] CDC & RDC Analysis**: Clock Domain Crossing and Reset Domain Crossing checks to ensure metastability is handled properly. *Tools: Pyverilog AST.*

## PHASE 1: LOGIC SYNTHESIS & DFT
Converts the human-readable RTL into a gate-level netlist of standard cells provided by the foundry.

* **[05] RTL Elaboration**: Parsing the RTL into an internal abstract syntax tree and mapping basic logic structures. *Tools: Yosys (generates AST JSON for the LLM).*
* **[06] Logic Optimization**: Simplifying boolean equations, optimizing state machines (FSMs), and removing dead logic. *Tools: Yosys (`opt`, `fsm`).*
* **[07] Technology Mapping**: Mapping the optimized generic logic to specific standard cells (AND, OR, DFF, etc.) from the foundry's `.lib` file. *Tools: Yosys + ABC.*
* **[08] DFT Scan & ATPG**: Design for Testability. Inserting scan chains into all flip-flops to allow for post-silicon manufacturing testing. *Tools: Fault Python API.*

## PHASE 2: FORMAL VERIFICATION & FLOORPLANNING
Proving the netlist is correct and setting up the physical dimensions and power grid of the chip.

* **[09] Formal LEC Proof**: Logic Equivalence Checking. Mathematically proving that the synthesized gate-level netlist exactly matches the original RTL logic. *Tools: SymbiYosys / EQY.*
* **[10] Die & Core Sizing**: Defining the physical width and height of the silicon die, and determining core utilization. *Tools: PyOpenROAD.*
* **[11] IO Pin Placement**: Placing the Input/Output pins around the perimeter of the die. *Tools: OpenROAD ioPlacer.*
* **[12] Macro Placement**: Placing large, pre-compiled IP blocks (like SRAMs, PLLs) with routing halos. *Tools: OpenROAD mpl2.*
* **[13] Power Grid PGN**: Generating the Power Delivery Network (PDN) metal mesh to distribute VDD and VSS evenly across the chip. *Tools: OpenROAD pdn.*

## PHASE 3: PLACEMENT, CTS & ROUTING
Placing the standard cells and routing the physical wires between them.

* **[14] Tap & Endcaps**: Inserting well-tap cells (to prevent latch-up) and physical boundary endcaps. *Tools: OpenROAD tapcell.*
* **[15] Global Placement**: Assigning a general location to all standard cells to minimize overall wirelength. *Tools: OpenROAD ePlace/gpl.*
* **[16] Legalization**: Snapping the globally placed cells to the standard cell rows without any overlaps. *Tools: OpenROAD dpl.*
* **[17] Clock Tree CTS**: Clock Tree Synthesis. Building a balanced buffer tree to distribute the clock signal to all flip-flops with minimal skew. *Tools: OpenROAD TritonCTS.*
* **[18] Hold Repair**: Fixing timing hold violations (data arriving too early) that arise after CTS by inserting delay buffers. *Tools: OpenROAD repair_hold.*
* **[19] Global Routing**: Creating a coarse routing grid and assigning nets to specific metal layers and regions to avoid congestion. *Tools: OpenROAD fastroute.*
* **[20] Detailed Routing**: The highly intensive task of drawing the exact geometric metal polygons and vias for every connection. *Tools: OpenROAD TritonRoute.*

## PHASE 4: PARASITICS, STA, PHYSICAL VERIFICATION & TAPEOUT
Extracting physical data, verifying timing and rules, and generating the final manufacturing file.

* **[21] Antenna Diodes**: Inserting diodes on long metal wires to prevent plasma-induced gate oxide breakdown during manufacturing. *Tools: OpenROAD antenna_checker.*
* **[22] RC Extraction**: Extracting the exact parasitic Resistance (R) and Capacitance (C) of the routed wires. *Tools: OpenRCX (outputs `.SPEF` file).*
* **[23] Signoff STA**: Static Timing Analysis. Using the extracted RC data to accurately calculate setup, hold, and transition timing. *Tools: OpenSTA Python.*
* **[24] IR Drop Analysis**: Simulating the power grid to ensure the voltage doesn't drop below acceptable levels across the chip. *Tools: OpenROAD PSM Engine.*
* **[25] LVS Verification**: Layout vs Schematic. Ensuring the physical routed layout matches the intended gate-level netlist exactly. *Tools: Netgen / Magic.*
* **[26] DRC Verification**: Design Rule Checking. Verifying that the layout passes all foundry manufacturing rules (spacing, width, density). *Tools: KLayout / Magic.*
* **[27] Metal Dummy Fill**: Filling empty spaces on metal layers with dummy polygons to ensure uniform chemical-mechanical polishing (CMP) during fabrication. *Tools: KLayout Fill.*
* **[28] GDSII Tapeout**: Streaming out the final, flattened layout database into the industry-standard GDSII binary format for the fab. *Tools: KLayout Stream.*

---

## AUTONOMOUS LLM AGENT: Closed-Loop Control Engine
The automation layer runs concurrently, intercepting errors and performing live Engineering Change Orders (ECOs) via Python APIs.

1. **Agent Orchestrator**: The central brain. It parses Yosys JSON ASTs, OpenSTA timing reports, and KLayout DRC logs using OpenLane 2 Python APIs to understand the current state.
2. **Timing ECO Engine**: 
   * **Trigger**: Signoff STA (Step 23) reports `Slack < 0 ns`.
   * **Action**: Dynamically invokes PyOpenROAD to upsize cells (`size_cell`) or insert buffers (`repair_timing`), routing feedback directly back to Clock Tree CTS (Step 17).
3. **DRC Repair Engine**:
   * **Trigger**: DRC Verification (Step 26) reports violations (e.g., metal shorts).
   * **Action**: Reads precise X/Y error coordinates from TritonRoute, triggering localized rip-up and re-route algorithms.
4. **AST & Code Refactor**:
   * **Trigger**: Static Linting (Step 02) or Formal LEC (Step 09) fails.
   * **Action**: Analyzes warnings and SBY counter-example traces to autonomously patch the underlying Verilog source code.
