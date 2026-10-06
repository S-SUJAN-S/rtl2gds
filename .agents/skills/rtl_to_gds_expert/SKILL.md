---
name: rtl_to_gds_expert
description: Specialized domain expert skill for driving digital ASIC RTL-to-GDSII physical design flow targeting SkyWater 130nm (sky130) PDK using OpenLane, Yosys, OpenROAD, OpenSTA, Verilator, Magic, KLayout, and Netgen.
---

# RTL-to-GDSII Physical Design Expert Skill

This skill equips Antigravity with the deep domain knowledge required to autonomously lint, synthesize, place, route, perform Static Timing Analysis (STA), execute closed-loop Engineering Change Orders (ECOs), and stream out GDSII silicon masks.

## 🛠️ Toolchain Capabilities & Workflow

1. **Static Linting (Verilator / Icarus)**
   - Audit Verilog RTL for syntax errors, bus width mismatches, inferenced latches, wire range truncations, and sensitivity list omissions.
   - Automatically propose and apply non-destructive RTL patches.

2. **Logic Synthesis & Technology Mapping (Yosys)**
   - Formulate Yosys scripts to compile hierarchical Verilog RTL into Sky130 cell library components (`sky130_fd_sc_hd`).
   - Optimize for target frequency, area, and clock gating.

3. **Floorplanning, Power Grid & Placement (OpenROAD / PyOpenROAD)**
   - Configure core utilization (`core_utilization`), aspect ratio (`aspect_ratio`), and core margins (`core_space_um`).
   - Insert tap cells and decap endcaps (`tapcell`, `decap`).
   - Place pins cleanly on Met2 / Met3 metal layers.
   - Execute global and detailed placement with density tuning.

4. **Clock Tree Synthesis & Routing (TritonRoute)**
   - Synthesize balanced clock trees using designated buffers (`sky130_fd_sc_hd__clkbuf_*`).
   - Perform global and detailed routing while minimizing crosstalk and antenna violations.

5. **Static Timing Analysis & Closed-Loop ECO (OpenSTA)**
   - Parse setup and hold timing reports (`WNS` - Worst Negative Slack, `TNS` - Total Negative Slack).
   - Trace critical paths back to driving cells.
   - Generate precise Tcl ECO commands:
     * Gate Sizing: `size_cell <inst_name> <higher_drive_cell>`
     * Design Repair: `repair_timing -setup -hold`, `repair_design`
     * Buffer Insertion: `insert_buffer <pin_name> <buffer_cell>`

6. **Signoff, DRC, LVS & Layout Rendering (Magic, Netgen, KLayout)**
   - Verify DRC cleanliness in Magic and KLayout.
   - Run Layout-vs-Schematic (LVS) with Netgen.
   - Generate high-resolution layout PNG renders and SVG logic schematics.

## 📋 Common ECO Playbook

- **Negative Setup Slack (WNS < 0):**
  1. Identify high-fanout nets along the critical path.
  2. Increase drive strength of critical path drivers (e.g. `buf_1` -> `buf_4`, `nand2_1` -> `nand2_2`).
  3. Increase core space or decrease target utilization if local density congestion causes routing delays.
- **Negative Hold Slack (WNS < 0):**
  1. Insert delay buffers on early data arrival paths.
- **DRC / Routing Congestion:**
  1. Lower `placement_density` (e.g. 0.65 -> 0.55).
  2. Adjust layer directions or metal target utilization.
