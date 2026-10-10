"""
Silicon3D: 28-Point Physical Digital Twin Visual Audit Suite
Systematically captures and validates 28 distinct visual inspections
across full_adder, alu4bit, and uart_top at varying angles, zoom levels,
layer filters, and cross-section slices.
"""

import asyncio
import os
import sys
from playwright.async_api import async_playwright

AUDIT_DIR = os.path.join(os.path.dirname(__file__), '..', 'tools', 'gds3d-viewer', 'digital_twin_audit')
os.makedirs(AUDIT_DIR, exist_ok=True)

SHOTS = [
    # --- FULL ADDER (Foundry Reference Cell) ---
    {
        "id": "01_full_adder_iso_1x_real",
        "demo": "full_adder",
        "desc": "Full Adder: 3D Isometric Overview (1.0x Real Silicon Scale)",
        "angle": "iso",
        "explode": "1.0",
        "filter": "all"
    },
    {
        "id": "02_full_adder_top_cad_90deg",
        "demo": "full_adder",
        "desc": "Full Adder: Top-Down Overhead View (90 deg Planar CAD)",
        "angle": "top",
        "explode": "1.0",
        "filter": "all"
    },
    {
        "id": "03_full_adder_front_xz_cross_section",
        "demo": "full_adder",
        "desc": "Full Adder: Front Cross-Section (XZ Stackup: Substrate to M5)",
        "angle": "front",
        "explode": "1.0",
        "filter": "all"
    },
    {
        "id": "04_full_adder_side_yz_cross_section",
        "demo": "full_adder",
        "desc": "Full Adder: Side Cross-Section (YZ Stackup: Orthogonal Routing)",
        "angle": "side",
        "explode": "1.0",
        "filter": "all"
    },
    {
        "id": "05_full_adder_transistor_macro_zoom",
        "demo": "full_adder",
        "desc": "Full Adder: Transistor Level Macro Zoom (Standard Cell Gates)",
        "angle": "macro",
        "explode": "1.0",
        "filter": "all"
    },
    {
        "id": "06_full_adder_vias_only_network",
        "demo": "full_adder",
        "desc": "Full Adder: Isolated 3D Via Plug Network (LICON to VIA4)",
        "angle": "iso",
        "explode": "1.0",
        "filter": "vias"
    },
    {
        "id": "07_full_adder_metals_only_interconnect",
        "demo": "full_adder",
        "desc": "Full Adder: Isolated Metals (M1 through M5 Routing Rails)",
        "angle": "iso",
        "explode": "1.0",
        "filter": "metals"
    },
    {
        "id": "08_full_adder_frontend_transistors_only",
        "demo": "full_adder",
        "desc": "Full Adder: Front-End FEOL Only (Active Diff, Poly Gates, Taps)",
        "angle": "iso",
        "explode": "1.0",
        "filter": "frontend"
    },
    {
        "id": "09_full_adder_exploded_2x_routing",
        "demo": "full_adder",
        "desc": "Full Adder: Exploded View (2.5x Z-Separation for Channel Tracing)",
        "angle": "iso",
        "explode": "2.5",
        "filter": "all"
    },
    {
        "id": "10_full_adder_exploded_5x_stack_inspection",
        "demo": "full_adder",
        "desc": "Full Adder: High Exploded View (5.0x Z-Separation)",
        "angle": "iso",
        "explode": "5.0",
        "filter": "all"
    },
    {
        "id": "11_full_adder_slice_x_50pct",
        "demo": "full_adder",
        "desc": "Full Adder: 50% X-Axis Internal Silicon FIB Cutaway",
        "angle": "iso",
        "explode": "1.0",
        "filter": "all",
        "slice": {"x": "0.1"}
    },
    {
        "id": "12_full_adder_slice_z_delayering",
        "demo": "full_adder",
        "desc": "Full Adder: Z-Axis Delayering (Exposing Standard Cell Core)",
        "angle": "iso",
        "explode": "1.0",
        "filter": "all",
        "slice": {"z": "0.35"}
    },
    {
        "id": "13_full_adder_2d_cad_mode",
        "demo": "full_adder",
        "desc": "Full Adder: 2D Orthographic CAD Layout Mode",
        "angle": "top",
        "explode": "1.0",
        "filter": "all",
        "mode2d": True
    },

    # --- 4-BIT ALU (Arithmetic Logic Unit Core) ---
    {
        "id": "14_alu4bit_iso_overview_1x",
        "demo": "alu4bit",
        "desc": "4-bit ALU: 3D Isometric Layout Overview (75um x 75um Core)",
        "angle": "iso",
        "explode": "1.0",
        "filter": "all"
    },
    {
        "id": "15_alu4bit_top_view_90deg",
        "demo": "alu4bit",
        "desc": "4-bit ALU: Top-Down Overhead View (90 deg CAD Projection)",
        "angle": "top",
        "explode": "1.0",
        "filter": "all"
    },
    {
        "id": "16_alu4bit_front_cross_section",
        "demo": "alu4bit",
        "desc": "4-bit ALU: Front Cross-Section (XZ Physical Metallization)",
        "angle": "front",
        "explode": "1.0",
        "filter": "all"
    },
    {
        "id": "17_alu4bit_transistor_macro",
        "demo": "alu4bit",
        "desc": "4-bit ALU: Macro Zoom on Arithmetic Adder / Logic Cells",
        "angle": "macro",
        "explode": "1.0",
        "filter": "all"
    },
    {
        "id": "18_alu4bit_vias_only_grid",
        "demo": "alu4bit",
        "desc": "4-bit ALU: Isolated Via Plug Grid (5,559 MCON, 668 VIA1, 338 VIA2)",
        "angle": "iso",
        "explode": "1.0",
        "filter": "vias"
    },
    {
        "id": "19_alu4bit_metals_only_bus",
        "demo": "alu4bit",
        "desc": "4-bit ALU: Multi-Bit Operand Bus Routing (Metals Only)",
        "angle": "iso",
        "explode": "1.0",
        "filter": "metals"
    },
    {
        "id": "20_alu4bit_exploded_3x",
        "demo": "alu4bit",
        "desc": "4-bit ALU: Exploded View (3.5x Layer Elevation)",
        "angle": "iso",
        "explode": "3.5",
        "filter": "all"
    },
    {
        "id": "21_alu4bit_slice_y_core_cut",
        "demo": "alu4bit",
        "desc": "4-bit ALU: Y-Axis Slicing Cutaway into Carry-Lookahead Core",
        "angle": "iso",
        "explode": "1.0",
        "filter": "all",
        "slice": {"y": "0.1"}
    },

    # --- UART TOP (Complex 100k+ Polygon SoC Macro) ---
    {
        "id": "22_uart_top_iso_overview_1x",
        "demo": "uart",
        "desc": "UART Core: 3D Isometric SoC Overview (150um x 150um, 102k Polys)",
        "angle": "iso",
        "explode": "1.0",
        "filter": "all"
    },
    {
        "id": "23_uart_top_top_view_90deg",
        "demo": "uart",
        "desc": "UART Core: Top-Down 90 deg Overhead View",
        "angle": "top",
        "explode": "1.0",
        "filter": "all"
    },
    {
        "id": "24_uart_top_front_cross_section",
        "demo": "uart",
        "desc": "UART Core: Front Cross-Section (High-Density Interconnect Stack)",
        "angle": "front",
        "explode": "1.0",
        "filter": "all"
    },
    {
        "id": "25_uart_top_macro_transistor_cells",
        "demo": "uart",
        "desc": "UART Core: Transistor Macro Zoom on Baud Rate Generator Registers",
        "angle": "macro",
        "explode": "1.0",
        "filter": "all"
    },
    {
        "id": "26_uart_top_vias_only_array",
        "demo": "uart",
        "desc": "UART Core: Massive Via Array (29,744 MCON, 1,819 VIA1 Plugs)",
        "angle": "iso",
        "explode": "1.0",
        "filter": "vias"
    },
    {
        "id": "27_uart_top_exploded_3x_routing_mesh",
        "demo": "uart",
        "desc": "UART Core: Exploded View (3.5x Dense Multi-Layer Routing Mesh)",
        "angle": "iso",
        "explode": "3.5",
        "filter": "all"
    },
    {
        "id": "28_uart_top_deep_x_slicing_cut",
        "demo": "uart",
        "desc": "UART Core: Deep Internal Slicing Cutaway",
        "angle": "iso",
        "explode": "1.0",
        "filter": "all",
        "slice": {"x": "0.0"}
    }
]

async def run_audit():
    print("=" * 70)
    print("Silicon3D: Physical Digital Twin 28-Point Visual Audit")
    print("=" * 70)
    
    current_loaded = None

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})

        for idx, shot in enumerate(SHOTS, 1):
            shot_id = shot["id"]
            desc = shot["desc"]
            demo = shot["demo"]
            print(f"\n[{idx:02d}/28] {shot_id}")
            print(f"      {desc}")

            # Load demo if needed
            if current_loaded != demo:
                url = f"http://127.0.0.1:8080/tools/gds3d-viewer/?demo={demo}"
                await page.goto(url)
                await page.wait_for_selector(".layer-item", timeout=25000)
                await asyncio.sleep(2.0)
                current_loaded = demo

            # 1. Reset everything first for clean baseline
            btn_reset = await page.wait_for_selector("#btn-reset-cam")
            await btn_reset.click()
            await asyncio.sleep(0.3)

            # 2. Mode 2D/3D
            is_2d = shot.get("mode2d", False)
            if is_2d:
                btn_2d = await page.wait_for_selector("#btn-toggle-2d3d")
                await btn_2d.click()
                await asyncio.sleep(0.5)

            # 3. Apply Camera Angle Preset
            angle = shot.get("angle", "iso")
            await page.select_option("#select-camera-angle", angle)
            await asyncio.sleep(0.4)

            # 4. Apply Exploded View Slider
            explode_val = shot.get("explode", "1.0")
            if explode_val != "1.0":
                await page.evaluate("""(val) => {
                    const el = document.getElementById('slider-explode');
                    if (el) {
                        el.value = val;
                        el.dispatchEvent(new Event('input'));
                    }
                }""", explode_val)
                await asyncio.sleep(0.4)

            # 5. Apply Layer Isolation Filter
            flt = shot.get("filter", "all")
            if flt == "vias":
                btn = await page.wait_for_selector("#btn-vias-only")
                await btn.click()
            elif flt == "metals":
                btn = await page.wait_for_selector("#btn-metals-only")
                await btn.click()
            elif flt == "frontend":
                btn = await page.wait_for_selector("#btn-frontend-only")
                await btn.click()
            await asyncio.sleep(0.3)

            # 6. Apply Cross-Section Slicing if requested
            if "slice" in shot:
                btn_slice = await page.wait_for_selector("#btn-toggle-slicing")
                await btn_slice.click()
                chk = await page.wait_for_selector("#chk-slicing-enable")
                is_checked = await chk.is_checked()
                if not is_checked:
                    await chk.check()
                
                slice_cfg = shot["slice"]
                await page.evaluate("""(cfg) => {
                    if (cfg.x !== undefined) {
                        const el = document.getElementById('slider-slice-x');
                        if (el) { el.value = cfg.x; el.dispatchEvent(new Event('input')); }
                    }
                    if (cfg.y !== undefined) {
                        const el = document.getElementById('slider-slice-y');
                        if (el) { el.value = cfg.y; el.dispatchEvent(new Event('input')); }
                    }
                    if (cfg.z !== undefined) {
                        const el = document.getElementById('slider-slice-z');
                        if (el) { el.value = cfg.z; el.dispatchEvent(new Event('input')); }
                    }
                }""", slice_cfg)
                await asyncio.sleep(0.5)

            # Settle render frame
            await asyncio.sleep(0.6)

            # Save screenshot
            out_file = os.path.join(AUDIT_DIR, f"{shot_id}.png")
            await page.screenshot(path=out_file)
            print(f"      Saved: {out_file}")

        await browser.close()
        print("\n" + "=" * 70)
        print("ALL 28 PHYSICAL DIGITAL TWIN AUDIT SCREENSHOTS CAPTURED!")
        print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run_audit())
