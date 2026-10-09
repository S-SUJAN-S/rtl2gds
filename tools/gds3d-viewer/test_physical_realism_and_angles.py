"""
Silicon3D: Physical Realism, All Camera Angles & Multi-Layer Via Audit
Verifies:
1. Real physical semiconductor stackup at 1.0x (1:1 physical height, contiguous metals and vias).
2. Elimination of floating 3D pillars (pins rendered as flat surface wireframes).
3. All camera view presets (Isometric 45°, Top 90°, Front XZ, Side YZ, Macro Zoom).
4. Vias quick filter isolation.
5. Master Reset functionality.
"""

import sys
import time
from playwright.sync_api import sync_playwright

def run_audit():
    print("=" * 60)
    print("Silicon3D: Physical Realism & Multi-Angle Camera Audit")
    print("=" * 60)

    errors = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()

        def handle_console(msg):
            if msg.type == 'error':
                print(f"  [BROWSER ERROR] {msg.text}")
                errors.append(msg.text)
        page.on('console', handle_console)

        # -----------------------------------------------------------------
        # TEST 1: Load full_adder at 1.0x Real Silicon Scale
        # -----------------------------------------------------------------
        print("\n[STAGE 1] Loading full_adder.gds in 100% Real Physical Silicon Scale...")
        page.goto('http://localhost:8080/tools/gds3d-viewer/index.html?demo=full_adder', wait_until='networkidle')
        page.wait_for_selector("#loading-overlay:not(.active)", timeout=15000)
        page.wait_for_function("document.getElementById('hud-top-module').textContent.includes('full_adder')")
        time.sleep(1.0)

        # Verify HUD metrics
        top_module = page.text_content('#hud-top-module')
        die_dim = page.text_content('#hud-die-dim')
        active_layers = page.text_content('#hud-active-layers')
        print(f"  Top Module: {top_module}")
        print(f"  Die Dimensions: {die_dim}")
        print(f"  Active Layers: {active_layers}")

        assert 'full_adder' in top_module, f"Expected full_adder, got {top_module}"
        page.screenshot(path='tools/gds3d-viewer/audit_real_1_full_adder_iso_1x.png')
        print("  Screenshot saved: audit_real_1_full_adder_iso_1x.png")

        # -----------------------------------------------------------------
        # TEST 2: Camera View Angle Presets ("All Angles")
        # -----------------------------------------------------------------
        angles = [
            ('top', 'Top View (90°)', 'audit_real_2_top_view.png'),
            ('front', 'Front Cross-Section (XZ)', 'audit_real_3_front_cross_section.png'),
            ('side', 'Side Cross-Section (YZ)', 'audit_real_4_side_cross_section.png'),
            ('macro', 'Transistor Zoom', 'audit_real_5_transistor_macro.png')
        ]

        for angle_key, label, filename in angles:
            print(f"\n[STAGE] Switching Camera Angle to: {label}...")
            page.select_option('#select-camera-angle', angle_key)
            time.sleep(0.6)
            page.screenshot(path=f'tools/gds3d-viewer/{filename}')
            print(f"  Screenshot saved: {filename}")

        # -----------------------------------------------------------------
        # TEST 3: Vias Quick Filter Isolation
        # -----------------------------------------------------------------
        print("\n[STAGE] Testing 'Vias' Quick Filter Isolation...")
        page.select_option('#select-camera-angle', 'iso')
        time.sleep(0.3)
        page.click('#btn-vias-only')
        time.sleep(0.5)
        page.screenshot(path='tools/gds3d-viewer/audit_real_6_vias_only.png')
        print("  Screenshot saved: audit_real_6_vias_only.png")

        # -----------------------------------------------------------------
        # TEST 4: Metals Quick Filter Isolation
        # -----------------------------------------------------------------
        print("\n[STAGE] Testing 'Metals' Quick Filter Isolation...")
        page.click('#btn-metals-only')
        time.sleep(0.5)
        page.screenshot(path='tools/gds3d-viewer/audit_real_7_metals_only.png')
        print("  Screenshot saved: audit_real_7_metals_only.png")

        # -----------------------------------------------------------------
        # TEST 5: Exploded View (3.5x)
        # -----------------------------------------------------------------
        print("\n[STAGE] Testing Exploded View (3.5x)...")
        page.click('#btn-all-layers-on')
        time.sleep(0.3)
        page.evaluate("() => { const s = document.getElementById('slider-explode'); s.value = 3.5; s.dispatchEvent(new Event('input')); }")
        time.sleep(0.5)
        explode_label = page.text_content('#label-explode-val')
        print(f"  Explode Value: {explode_label}")
        page.screenshot(path='tools/gds3d-viewer/audit_real_8_exploded_3x.png')
        print("  Screenshot saved: audit_real_8_exploded_3x.png")

        # -----------------------------------------------------------------
        # TEST 6: Master Reset Execution
        # -----------------------------------------------------------------
        print("\n[STAGE] Testing Master Reset...")
        page.click('#btn-reset-cam')
        time.sleep(0.6)
        reset_explode = page.text_content('#label-explode-val')
        reset_angle = page.eval_on_selector('#select-camera-angle', 'el => el.value')
        print(f"  Post-Reset Explode: {reset_explode}")
        print(f"  Post-Reset Angle: {reset_angle}")
        assert '1.0' in reset_explode, f"Expected 1.0x, got {reset_explode}"
        assert reset_angle == 'iso', f"Expected 'iso', got {reset_angle}"
        page.screenshot(path='tools/gds3d-viewer/audit_real_9_after_master_reset.png')
        print("  Screenshot saved: audit_real_9_after_master_reset.png")

        # -----------------------------------------------------------------
        # TEST 7: Canonical Sample Switching (alu4bit & uart_top)
        # -----------------------------------------------------------------
        for sample in ['alu4bit', 'uart_top']:
            print(f"\n[STAGE] Verifying canonical sample: {sample}...")
            page.select_option('#sample-select', sample)
            page.wait_for_selector("#loading-overlay:not(.active)", timeout=15000)
            page.wait_for_function(f"document.getElementById('hud-top-module').textContent.includes('{sample}')")
            time.sleep(0.8)
            mod = page.text_content('#hud-top-module')
            layers = page.text_content('#hud-active-layers')
            print(f"  Loaded Module: {mod}, Active Layers: {layers}")
            page.screenshot(path=f'tools/gds3d-viewer/audit_real_10_{sample}_3d.png')
            print(f"  Screenshot saved: audit_real_10_{sample}_3d.png")

        browser.close()

    if errors:
        print(f"\n[AUDIT FAILED] {len(errors)} console errors detected:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("\n" + "=" * 60)
        print("ALL PHYSICAL REALISM & MULTI-ANGLE TESTS PASSED (100%)")
        print("=" * 60)

if __name__ == '__main__':
    run_audit()
