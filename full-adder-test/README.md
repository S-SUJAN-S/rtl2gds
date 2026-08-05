# Full Adder RTL-to-GDSII Test

This directory contains the complete end-to-end output of the `full_adder.v` test run using the OpenLane autonomous physical design flow and the SkyWater 130nm PDK.

## Directory Structure
- **`/source/`**: Contains the raw Verilog HDL logic (`full_adder.v`) and the OpenLane configuration (`full_adder_config.json`) used to drive the tools.
- **`/images/`**: Visual snapshots of the logic synthesis and physical layout process:
  - `full_adder_netlist.png`: The Yosys AST logic schematic extracted from your Verilog.
  - `floorplan_full_adder.png`: The initial silicon die canvas mapping with standard cells instantiated.
  - `placement_full_adder.png`: The highly optimized gate placement mapping minimizing congestion and wire length.
  - `routing_full_adder.png`: The final TritonRoute metal routing layer visualization.
- **`/outputs/`**: The final manufacturable sign-off artifacts.
  - `full_adder.gds`: The GDSII stream file. This is the ultimate output of the pipeline—the exact polygon geometries that a foundry (like TSMC or SkyWater) uses to print the masks. You can open this in KLayout to see the physical metals!
  - `full_adder.lef`: The Library Exchange Format (abstracted geometry) for hierarchical integration.
  - `full_adder.mag`: The Magic Layout database file.
  - `full_adder.spice`: The final extracted transistor-level SPICE netlist, including physical parasitics for analog simulation.
- **`/reports/`**: Logs and metric CSVs detailing the area, power, timing delay, and DRC violation counts (which are 0!).

To view the final chip layout natively in Windows, just double-click `full_adder.gds` if you have KLayout installed!
