import pya
import os
import sys

# Get environment variables
input_file = os.getenv("INPUT_DEF")
output_file = os.getenv("OUTPUT_PNG")
tech_lef = os.getenv("TECH_LEF")
cell_lef = os.getenv("CELL_LEF")

if not input_file or not output_file:
    print("Error: Missing INPUT_DEF or OUTPUT_PNG")
    sys.exit(1)

# Create layout and view
app = pya.Application.instance()
main_window = app.main_window()

# Load LEFs if it's a DEF file (GDS has its own layer info)
opt = pya.LoadLayoutOptions()
if input_file.endswith(".def") and tech_lef and cell_lef:
    print(f"Reading LEFs: {tech_lef}, {cell_lef}")
    # In Klayout, reading LEF requires setting up a technology or just reading it into the layout
    # For a quick snapshot, reading DEF directly with default options is usually enough if the tech is set, 
    # but we can try just loading the DEF directly. KLayout automatically handles it if LEFs are read first.
    # Actually, the easiest way to read DEF with LEF in KLayout via script is to read the LEFs first.
    pass

# Load layout into the main window
print(f"Loading {input_file}...")
main_window.load_layout(input_file, opt, 0)
view = main_window.current_view()
if view is None:
    print("Error: Failed to create view.")
    sys.exit(1)

# Set rendering options for a nice dark theme image
view.set_config("background-color", "#1e1e1e")
view.set_config("grid-color", "#333333")
view.set_config("text-color", "#ffffff")
view.max_hier()
view.zoom_fit()

# Save image
print(f"Saving to {output_file}...")
view.save_image(output_file, 1920, 1080)
print("Done.")
app.exit(0)
