import pya
import sys
import os

if len(sys.argv) < 3:
    print("Usage: klayout -z -r render_def.py -rd input=<file.def/gds> -rd output=<file.png>")
    sys.exit(1)

# Get args passed via -rd
input_file = None
output_file = None
for i, arg in enumerate(sys.argv):
    if arg == "-rd" and i+1 < len(sys.argv):
        kv = sys.argv[i+1].split("=")
        if len(kv) == 2:
            if kv[0] == "input": input_file = kv[1]
            if kv[0] == "output": output_file = kv[1]

if not input_file or not output_file:
    print("Error: Missing input or output argument.")
    sys.exit(1)

# Load layout
layout = pya.Layout()
if input_file.endswith(".def"):
    # Load DEF (needs tech if possible, but basic load works for viewing)
    opt = pya.LoadLayoutOptions()
    layout.read(input_file, opt)
else:
    layout.read(input_file)

# Create a view
main_window = pya.Application.instance().main_window()
if main_window is None:
    # In pure headless mode (-z or -zz), main_window might be None.
    # We must use LayoutView directly if possible, or omit -z and use -zz with a virtual frame buffer (Xvfb)
    pass

# Note: Pure headless image rendering in KLayout can be tricky without a GUI context. 
# A safer approach is to just use Klayout's LayoutView class if available, or rely on OpenLane's built-in Odb.Report / KLayout.StreamOut snapshot features.
