read_lef $env(PDK_ROOT)/$env(PDK)/libs.ref/sky130_fd_sc_hd/techlef/sky130_fd_sc_hd__nom.tlef
read_lef $env(PDK_ROOT)/$env(PDK)/libs.ref/sky130_fd_sc_hd/lef/sky130_fd_sc_hd.lef
read_def $env(DEF_FILE)

# Set up GUI options for a nice render
gui::set_resolution 1920 1080
gui::set_color_scheme "dark"
gui::fit

# Save the image
gui::save_image $env(OUT_PNG)
exit
