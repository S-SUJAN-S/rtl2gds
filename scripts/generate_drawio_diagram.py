#!/usr/bin/env python3
"""
Draw.io Clean Diagram Generator for RTL-to-GDSII Flow & LLM Automation
Generates an uncompressed, perfectly styled .drawio XML diagram with exact grid layout.
"""

import xml.etree.ElementTree as ET
import xml.dom.minidom

def build_drawio_xml() -> str:
    mxfile = ET.Element("mxfile", host="Electron", agent="Antigravity", version="21.6.8", type="device")
    diagram = ET.SubElement(mxfile, "diagram", id="rtl_to_gds_flow", name="RTL-to-GDSII Flow & LLM Agent")
    mxGraphModel = ET.SubElement(
        diagram, "mxGraphModel", 
        dx="1400", dy="1400", grid="1", gridSize="10", guides="1", tooltips="1", connect="1", 
        arrows="1", fold="1", page="1", pageScale="1", pageWidth="1400", pageHeight="1400", math="0", shadow="0"
    )
    root = ET.SubElement(mxGraphModel, "root")
    
    # Base cells
    ET.SubElement(root, "mxCell", id="0")
    ET.SubElement(root, "mxCell", id="1", parent="0")

    # Color Palette & Styles
    COLOR_BG = "#0F172A"       # Dark Slate Blue Background
    STYLE_HEADER = "text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontSize=22;fontStyle=1;fontColor=#F8FAFC;"
    
    # Background rectangle to cover the whole page
    bg_box = ET.SubElement(root, "mxCell", id="bg_rect", value="", style=f"rounded=0;whiteSpace=wrap;html=1;fillColor={COLOR_BG};strokeColor=none;", parent="1", vertex="1")
    geom_bg = ET.SubElement(bg_box, "mxGeometry", x="0", y="0", width="1400", height="1350")
    geom_bg.set("as", "geometry")

    # Phase Colors
    PHASES = [
        {"title": "PHASE 0: FRONT-END DESIGN & VERIFICATION", "color": "#1E293B", "border": "#3B82F6", "text_color": "#60A5FA", "steps": [
            ("01", "RTL Coding & Spec\n(SystemVerilog / Pyverilog)", "#1E3A8A"),
            ("02", "Static Linting\n(Verilator --lint-only)", "#1E3A8A"),
            ("03", "Functional Simulation\n(Cocotb + Icarus)", "#1E3A8A"),
            ("04", "CDC & RDC Analysis\n(Pyverilog AST)", "#1E3A8A")
        ]},
        {"title": "PHASE 1: LOGIC SYNTHESIS & DFT", "color": "#1E293B", "border": "#8B5CF6", "text_color": "#C084FC", "steps": [
            ("05", "RTL Elaboration\n(Yosys AST JSON)", "#4C1D95"),
            ("06", "Logic Optimization\n(Yosys opt / fsm)", "#4C1D95"),
            ("07", "Technology Mapping\n(Yosys + ABC .lib)", "#4C1D95"),
            ("08", "DFT Scan & ATPG\n(Fault Python API)", "#4C1D95")
        ]},
        {"title": "PHASE 2: FORMAL VERIFICATION & FLOORPLANNING", "color": "#1E293B", "border": "#EC4899", "text_color": "#F472B6", "steps": [
            ("09", "Formal LEC Proof\n(SymbiYosys / EQY)", "#831843"),
            ("10", "Die & Core Sizing\n(PyOpenROAD)", "#831843"),
            ("11", "IO Pin Placement\n(ioPlacer)", "#831843"),
            ("12", "Macro Placement\n(mpl2 Halos)", "#831843"),
            ("13", "Power Grid PGN\n(pdn Mesh)", "#831843")
        ]},
        {"title": "PHASE 3: PLACEMENT, CTS & ROUTING", "color": "#1E293B", "border": "#10B981", "text_color": "#34D399", "steps": [
            ("14", "Tap & Endcaps\n(tapcell)", "#064E3B"),
            ("15", "Global Placement\n(ePlace / gpl)", "#064E3B"),
            ("16", "Legalization\n(dpl)", "#064E3B"),
            ("17", "Clock Tree CTS\n(TritonCTS)", "#064E3B"),
            ("18", "Hold Repair\n(repair_hold)", "#064E3B"),
            ("19", "Global Routing\n(fastroute)", "#064E3B"),
            ("20", "Detailed Routing\n(TritonRoute)", "#064E3B")
        ]},
        {"title": "PHASE 4: PARASITICS, STA, PHYSICAL VERIFICATION & TAPEOUT", "color": "#1E293B", "border": "#F59E0B", "text_color": "#FBBF24", "steps": [
            ("21", "Antenna Diodes\n(antenna_checker)", "#78350F"),
            ("22", "RC Extraction\n(OpenRCX SPEF)", "#78350F"),
            ("23", "Signoff STA\n(OpenSTA Python)", "#78350F"),
            ("24", "IR Drop Analysis\n(psm Engine)", "#78350F"),
            ("25", "LVS Verification\n(Netgen / Magic)", "#78350F"),
            ("26", "DRC Verification\n(KLayout / Magic)", "#78350F"),
            ("27", "Metal Dummy Fill\n(KLayout Fill)", "#78350F"),
            ("28", "GDSII Tapeout\n(KLayout Stream)", "#B45309")
        ]}
    ]

    # Main Title
    title_box = ET.SubElement(root, "mxCell", id="title", value="<b>RTL-TO-GDSII ASIC FLOW & LLM AGENT ARCHITECTURE</b>", style=STYLE_HEADER, parent="1", vertex="1")
    geom = ET.SubElement(title_box, "mxGeometry", x="50", y="20", width="1300", height="40")
    geom.set("as", "geometry")

    current_y = 80
    cell_id = 100
    prev_step_id = None
    prev_y_pos = -1

    for p_idx, phase in enumerate(PHASES):
        num_steps = len(phase["steps"])
        # Determine container height based on steps wrapping into rows
        steps_per_row = 4
        num_rows = (num_steps + steps_per_row - 1) // steps_per_row
        container_h = 60 + num_rows * 90
        
        # Phase Container Box
        p_box_id = f"phase_{p_idx}"
        p_style = f"rounded=1;whiteSpace=wrap;html=1;fillColor={phase['color']};strokeColor={phase['border']};strokeWidth=2;arcSize=8;collapsible=0;"
        p_box = ET.SubElement(root, "mxCell", id=p_box_id, value="", style=p_style, parent="1", vertex="1")
        geom = ET.SubElement(p_box, "mxGeometry", x="50", y=str(current_y), width="920", height=str(container_h))
        geom.set("as", "geometry")
        
        # Phase Label
        lbl_style = f"text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontSize=14;fontStyle=1;fontColor={phase['text_color']};"
        lbl_box = ET.SubElement(root, "mxCell", id=f"lbl_{p_idx}", value=f"  {phase['title']}", style=lbl_style, parent="1", vertex="1")
        geom = ET.SubElement(lbl_box, "mxGeometry", x="60", y=str(current_y + 10), width="800", height="30")
        geom.set("as", "geometry")

        # Step Nodes inside Phase
        for s_idx, (num, name, fill) in enumerate(phase["steps"]):
            row = s_idx // steps_per_row
            col = s_idx % steps_per_row
            
            x_pos = 75 + col * 215
            y_pos = current_y + 50 + row * 90
            
            step_node_id = f"step_{num}"
            node_label = f"<b>[{num}]</b><br/>{name}"
            node_style = f"rounded=1;whiteSpace=wrap;html=1;fillColor={fill};strokeColor={phase['border']};fontColor=#FFFFFF;fontSize=11;align=center;verticalAlign=middle;strokeWidth=1.5;"
            
            node_cell = ET.SubElement(root, "mxCell", id=step_node_id, value=node_label, style=node_style, parent="1", vertex="1")
            geom = ET.SubElement(node_cell, "mxGeometry", x=str(x_pos), y=str(y_pos), width="195", height="70")
            geom.set("as", "geometry")
            
            # Connect previous step to this step
            if prev_step_id:
                edge_id = f"edge_{cell_id}"
                cell_id += 1
                
                if y_pos != prev_y_pos:
                    # Wrap around or phase transition
                    edge_style = f"edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor={phase['border']};strokeWidth=2;endArrow=classic;endFill=1;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;"
                else:
                    # Same row
                    edge_style = f"edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor={phase['border']};strokeWidth=2;endArrow=classic;endFill=1;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;"
                
                edge = ET.SubElement(root, "mxCell", id=edge_id, value="", style=edge_style, parent="1", source=prev_step_id, target=step_node_id, edge="1")
                geom = ET.SubElement(edge, "mxGeometry", relative="1")
                geom.set("as", "geometry")
                
            prev_step_id = step_node_id
            prev_y_pos = y_pos

        current_y += container_h + 25

    # LLM Agent Closed-Loop Side Container Box
    llm_box_id = "llm_agent_box"
    llm_style = "rounded=1;whiteSpace=wrap;html=1;fillColor=#1E1B4B;strokeColor=#818CF8;strokeWidth=3;arcSize=6;"
    llm_box = ET.SubElement(root, "mxCell", id=llm_box_id, value="", style=llm_style, parent="1", vertex="1")
    geom = ET.SubElement(llm_box, "mxGeometry", x="1000", y="80", width="350", height="1180")
    geom.set("as", "geometry")

    # LLM Header
    llm_hdr_style = "text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontSize=16;fontStyle=1;fontColor=#A5B4FC;"
    llm_hdr = ET.SubElement(root, "mxCell", id="llm_hdr", value="<b>AUTONOMOUS LLM AGENT</b><br/>Closed-Loop Control Engine", style=llm_hdr_style, parent="1", vertex="1")
    geom = ET.SubElement(llm_hdr, "mxGeometry", x="1010", y="100", width="330", height="40")
    geom.set("as", "geometry")

    # LLM Sub-modules inside side box
    llm_cards = [
        ("Agent Orchestrator", "Parses JSON AST, OpenSTA reports & KLayout DRC logs via OpenLane 2 Python API", "160", "#312E81"),
        ("Timing ECO Engine", "Detects setup/hold slack < 0. Dynamically invokes PyOpenROAD `size_cell` & `repair_timing`", "340", "#312E81"),
        ("DRC Repair Engine", "Reads DRC error coordinates from TritonRoute. Triggers localized rip-up & re-route", "520", "#312E81"),
        ("AST & Code Refactor", "Analyzes Verilator warnings & SBY counter-examples to auto-patch Verilog source", "700", "#312E81")
    ]

    for card_title, card_desc, y_offset, card_fill in llm_cards:
        c_id = f"llm_card_{y_offset}"
        c_val = f"<b>{card_title}</b><br/><font color='#C7D2FE' size='1'>{card_desc}</font>"
        c_style = f"rounded=1;whiteSpace=wrap;html=1;fillColor={card_fill};strokeColor=#6366F1;fontColor=#FFFFFF;fontSize=12;align=center;verticalAlign=middle;strokeWidth=1.5;"
        c_cell = ET.SubElement(root, "mxCell", id=c_id, value=c_val, style=c_style, parent="1", vertex="1")
        geom = ET.SubElement(c_cell, "mxGeometry", x="1025", y=str(int(y_offset) + 20), width="300", height="120")
        geom.set("as", "geometry")

    # --- Feedback Arrows from STA (Step 23) and DRC (Step 26) to LLM Agent ---
    
    # 1. Step 23 -> LLM Card 340 (Timing ECO Engine)
    edge_sta_llm = ET.SubElement(root, "mxCell", id="edge_sta_llm", value="Slack &lt; 0 ns", style="edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;strokeColor=#F43F5E;strokeWidth=2.5;dashed=1;endArrow=classic;fontColor=#F8FAFC;labelBackgroundColor=none;verticalAlign=bottom;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;", parent="1", source="step_23", target="llm_card_340", edge="1")
    geom_sta = ET.SubElement(edge_sta_llm, "mxGeometry", relative="1")
    geom_sta.set("as", "geometry")
    arr_sta = ET.SubElement(geom_sta, "Array")
    arr_sta.set("as", "points")
    # Step 23 Center X = 75 + 2*215 + 195/2 = 602.5
    ET.SubElement(arr_sta, "mxPoint", x="602.5", y="1220") # Go down below Phase 4 container
    ET.SubElement(arr_sta, "mxPoint", x="980", y="1220")   # Go right to the gap between phases and LLM panel
    ET.SubElement(arr_sta, "mxPoint", x="980", y="420")    # Go up to the left side of LLM ECO Card

    # 2. Step 26 -> LLM Card 520 (DRC Repair Engine)
    edge_drc_llm = ET.SubElement(root, "mxCell", id="edge_drc_llm", value="DRC Violations", style="edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;strokeColor=#F59E0B;strokeWidth=2.5;dashed=1;endArrow=classic;fontColor=#F8FAFC;labelBackgroundColor=none;verticalAlign=bottom;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;", parent="1", source="step_26", target="llm_card_520", edge="1")
    geom_drc = ET.SubElement(edge_drc_llm, "mxGeometry", relative="1")
    geom_drc.set("as", "geometry")
    arr_drc = ET.SubElement(geom_drc, "Array")
    arr_drc.set("as", "points")
    # Step 26 Center X = 75 + 1*215 + 195/2 = 387.5
    ET.SubElement(arr_drc, "mxPoint", x="387.5", y="1240") # Go down below Phase 4 container (further down)
    ET.SubElement(arr_drc, "mxPoint", x="960", y="1240")   # Go right to the gap
    ET.SubElement(arr_drc, "mxPoint", x="960", y="600")    # Go up to the left side of LLM DRC Card

    # 3. LLM Card 340 (Timing ECO Engine) -> Step 17 (Clock Tree CTS)
    edge_eco_fix = ET.SubElement(root, "mxCell", id="edge_eco_fix", value="PyOpenROAD ECO Sizing", style="edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;strokeColor=#10B981;strokeWidth=2.5;dashed=1;endArrow=classic;fontColor=#F8FAFC;labelBackgroundColor=none;verticalAlign=bottom;exitX=0;exitY=0.5;exitDx=0;exitDy=0;entryX=1;entryY=0.5;entryDx=0;entryDy=0;", parent="1", source="llm_card_340", target="step_17", edge="1")
    geom_eco = ET.SubElement(edge_eco_fix, "mxGeometry", relative="1")
    geom_eco.set("as", "geometry")
    arr_eco = ET.SubElement(geom_eco, "Array")
    arr_eco.set("as", "points")
    # LLM Card Exit Left = 1025, Center Y = 420.
    # Step 17 Center Y = 695 + 50 + 70/2 = 780. Right Edge X = 75 + 3*215 + 195 = 915.
    ET.SubElement(arr_eco, "mxPoint", x="940", y="420") # Go slightly left out of LLM card
    ET.SubElement(arr_eco, "mxPoint", x="940", y="780") # Go down to match Step 17 Y-level

    # Pretty-print XML
    raw_xml = ET.tostring(mxfile, encoding="utf-8")
    dom = xml.dom.minidom.parseString(raw_xml)
    return dom.toprettyxml(indent="  ")

if __name__ == "__main__":
    xml_str = build_drawio_xml()
    out_path = "rtl_to_gds_flow.drawio"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(xml_str)
    print(f"Clean Draw.io XML generated successfully at {out_path}")
