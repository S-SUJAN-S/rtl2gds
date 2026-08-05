import pya
import os
import sys

input_file = os.getenv("INPUT_DEF")
output_file = os.getenv("OUTPUT_PNG")
tech_lef = os.getenv("TECH_LEF")

app = pya.Application.instance()
main_window = app.main_window()

opt = pya.LoadLayoutOptions()
if tech_lef:
    opt.lefdef_config.lef_files = [tech_lef]
    opt.lefdef_config.read_lef_with_def = False

main_window.load_layout(input_file, opt, 0)
view = main_window.current_view()
view.set_config("background-color", "#1e1e1e")

# Zoom in to the center 20x20 um area where the logic gates are placed
box = pya.DBox(15, 15, 35, 35)
view.zoom_box(box)

view.save_image(output_file, 1920, 1080)
app.exit(0)
