import time
from playwright.sync_api import sync_playwright

def verify_visuals():
    with sync_playwright() as p:
        # Launch Chromium with hardware/software WebGL support enabled
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--enable-webgl',
                '--ignore-gpu-blocklist',
                '--use-gl=angle',
                '--use-angle=swiftshader',
                '--enable-accelerated-2d-canvas'
            ]
        )
        context = browser.new_context(viewport={'width': 1600, 'height': 900})
        page = context.new_page()

        console_logs = []
        page.on('console', lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))
        page_errors = []
        page.on('pageerror', lambda err: page_errors.append(str(err)))

        print("Navigating to Silicon3D portal...")
        page.goto("http://localhost:8080/tools/gds3d-viewer/?demo=alu4bit", wait_until="networkidle")

        # Wait for loading overlay to disappear
        page.wait_for_selector("#loading-overlay:not(.active)", timeout=15000)
        page.wait_for_function("document.getElementById('hud-top-module').textContent.includes('alu4bit')")
        
        # Give WebGL render loop time to draw frames
        time.sleep(2)

        # Collect HUD metrics
        top_module = page.inner_text("#hud-top-module")
        die_dim = page.inner_text("#hud-die-dim")
        die_area = page.inner_text("#hud-die-area")
        polys = page.inner_text("#hud-polys")
        layers = page.inner_text("#hud-active-layers")
        fps = page.inner_text("#hud-fps")

        print("--- ALU 4-BIT TELEMETRY ---")
        print(f"Top Module: {top_module}")
        print(f"Die Size:   {die_dim}")
        print(f"Core Area:  {die_area}")
        print(f"Polygons:   {polys}")
        print(f"Layers:     {layers}")
        print(f"FPS:        {fps}")

        # Capture 3D view screenshot
        page.screenshot(path="tools/gds3d-viewer/screenshot_alu4bit_3d.png")
        print("Captured screenshot_alu4bit_3d.png")

        # Switch to 2D mode
        page.click("#btn-toggle-2d3d")
        time.sleep(1.5)
        page.screenshot(path="tools/gds3d-viewer/screenshot_alu4bit_2d.png")
        print("Captured screenshot_alu4bit_2d.png")

        # Switch to Full Adder
        page.select_option("#sample-select", "full_adder")
        page.wait_for_selector("#loading-overlay:not(.active)", timeout=15000)
        page.wait_for_function("document.getElementById('hud-top-module').textContent.includes('full_adder')")
        time.sleep(2)

        fa_top = page.inner_text("#hud-top-module")
        fa_dim = page.inner_text("#hud-die-dim")
        fa_polys = page.inner_text("#hud-polys")
        print("--- FULL ADDER TELEMETRY ---")
        print(f"Top Module: {fa_top}")
        print(f"Die Size:   {fa_dim}")
        print(f"Polygons:   {fa_polys}")

        page.screenshot(path="tools/gds3d-viewer/screenshot_full_adder_3d.png")
        print("Captured screenshot_full_adder_3d.png")

        print("\nConsole errors:", [e for e in console_logs if '[error]' in e] + page_errors)
        browser.close()

if __name__ == '__main__':
    verify_visuals()
