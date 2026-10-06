import os
import sys
import pya

gds_path = "/home/sujan123/rtl2gds/OpenLane/designs/alu4bit/runs/tapeout_validation/results/final/gds/alu4bit.gds"
lyp_path = "/home/sujan123/.ciel/ciel/sky130/versions/0fe599b2afb6708d281543108caf8310912f54af/sky130A/libs.tech/klayout/tech/sky130A.lyp"
out_dir = "/mnt/c/Users/ssuja/OneDrive/Desktop/Learn_Antigravity_Advance/rtl-2-gds-automation-local-llm/outputs/alu4bit/images"

app = pya.Application.instance()
main_window = app.main_window()

print(f"Loading GDS: {gds_path}...")
opt = pya.LoadLayoutOptions()
main_window.load_layout(gds_path, opt, 0)
view = main_window.current_view()
if view is None:
    print("Error: Could not get current view")
    sys.exit(1)

if os.path.exists(lyp_path):
    print(f"Loading SkyWater 130nm layer properties: {lyp_path}...")
    view.load_layer_props(lyp_path)

view.set_config("background-color", "#14171d")
view.set_config("grid-color", "#252830")
view.set_config("text-color", "#e2e8f0")
view.max_hier()
view.zoom_fit()

full_png = os.path.join(out_dir, "alu4bit_gds_real.png")
print(f"Saving full layout render: {full_png}...")
view.save_image(full_png, 2048, 1536)

core_box = pya.DBox(12, 12, 62, 62)
view.zoom_box(core_box)
zoomed_png = os.path.join(out_dir, "alu4bit_gds_zoomed.png")
print(f"Saving core zoom render: {zoomed_png}...")
view.save_image(zoomed_png, 2048, 1536)

print("KLayout rendering completed successfully.")
app.exit(0)
