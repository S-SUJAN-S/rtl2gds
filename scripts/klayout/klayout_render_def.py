import pya
import os
import sys

input_file = os.getenv("INPUT_DEF")
output_file = os.getenv("OUTPUT_PNG")
tech_lef = os.getenv("TECH_LEF")

if not input_file or not output_file:
    print("Error: Missing INPUT_DEF or OUTPUT_PNG")
    sys.exit(1)

app = pya.Application.instance()
main_window = app.main_window()

opt = pya.LoadLayoutOptions()
if tech_lef:
    opt.lefdef_config.lef_files = [tech_lef]
    opt.lefdef_config.read_lef_with_def = False

print(f"Loading {input_file} with LEF {tech_lef}...")
main_window.load_layout(input_file, opt, 0)
view = main_window.current_view()

if view is None:
    print("Error: Failed to create view.")
    sys.exit(1)

view.set_config("background-color", "#1e1e1e")
view.set_config("grid-color", "#333333")
view.set_config("text-color", "#ffffff")
view.max_hier()
view.zoom_fit()

print(f"Saving to {output_file}...")
view.save_image(output_file, 1920, 1080)
print("Done.")
app.exit(0)
