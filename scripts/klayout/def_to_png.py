import sys
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import re

if len(sys.argv) < 3:
    print("Usage: python3 def_to_png.py <input.def> <output.png>")
    sys.exit(1)

in_file = sys.argv[1]
out_file = sys.argv[2]

components = []
die_area = (0, 0, 100, 100)
units = 1000

with open(in_file, 'r') as f:
    lines = f.readlines()

in_components = False
for line in lines:
    line = line.strip()
    if line.startswith('UNITS DISTANCE MICRONS'):
        parts = line.split()
        if len(parts) >= 4:
            units = int(parts[3])
    elif line.startswith('DIEAREA'):
        # DIEAREA ( 0 0 ) ( 38640 27200 ) ;
        m = re.search(r'\(\s*(\d+)\s+(\d+)\s*\)\s*\(\s*(\d+)\s+(\d+)\s*\)', line)
        if m:
            die_area = (int(m.group(1))/units, int(m.group(2))/units, int(m.group(3))/units, int(m.group(4))/units)
    elif line.startswith('COMPONENTS'):
        in_components = True
    elif in_components and line.startswith('END COMPONENTS'):
        in_components = False
    elif in_components and line.startswith('-'):
        # - _09_ sky130_fd_sc_hd__a21o_1 + PLACED ( 15640 5440 ) N ;
        m = re.search(r'-\s+(\S+)\s+(\S+).*?\(\s*(\d+)\s+(\d+)\s*\)', line)
        if m:
            name = m.group(1)
            cell = m.group(2)
            x = int(m.group(3)) / units
            y = int(m.group(4)) / units
            components.append({'name': name, 'cell': cell, 'x': x, 'y': y})

fig, ax = plt.subplots(figsize=(10, 10))
ax.set_xlim(die_area[0], die_area[2])
ax.set_ylim(die_area[1], die_area[3])
ax.set_aspect('equal')
ax.set_facecolor('#1e1e1e')
fig.patch.set_facecolor('#1e1e1e')

# Draw die area
rect = patches.Rectangle((die_area[0], die_area[1]), die_area[2]-die_area[0], die_area[3]-die_area[1], 
                         linewidth=2, edgecolor='white', facecolor='none')
ax.add_patch(rect)

# Draw components
for comp in components:
    # Approximate cell size 2x2 um
    w, h = 2.0, 2.72
    rect = patches.Rectangle((comp['x'], comp['y']), w, h, 
                             linewidth=1, edgecolor='#00ff00', facecolor='#004400', alpha=0.7)
    ax.add_patch(rect)
    ax.text(comp['x']+w/2, comp['y']+h/2, comp['cell'].split('__')[-1], 
            color='white', fontsize=6, ha='center', va='center', rotation=45)

plt.title(f"DEF Layout: {in_file.split('/')[-1]}", color='white')
plt.xlabel("X (um)", color='white')
plt.ylabel("Y (um)", color='white')
ax.tick_params(colors='white')
plt.grid(color='#333333', linestyle='--', linewidth=0.5)

plt.savefig(out_file, dpi=300, bbox_inches='tight', facecolor='#1e1e1e')
print(f"Saved {out_file}")
