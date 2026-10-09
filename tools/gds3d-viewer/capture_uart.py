import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=['--enable-webgl', '--ignore-gpu-blocklist', '--use-gl=angle', '--use-angle=swiftshader']
    )
    page = browser.new_page(viewport={'width': 1600, 'height': 900})
    page.goto('http://localhost:8080/tools/gds3d-viewer/?demo=uart_top', wait_until='networkidle')
    page.wait_for_selector('#loading-overlay:not(.active)', timeout=25000)
    page.wait_for_function("document.getElementById('hud-top-module').textContent.includes('uart_top')")
    time.sleep(3)
    page.screenshot(path='tools/gds3d-viewer/screenshot_uart_top_3d.png')
    print('UART top screenshot captured')
    browser.close()
