
        # 1. Floorplan & Pin Placement
        read_verilog build/sample_counter_synth.v
        link_design sample_counter
        initialize_floorplan -utilization 65 -aspect_ratio 1.0 -core_space 10.0
        place_pins -hor_layers Met3 -ver_layers Met2

        # 2. Tap Cell & Global Placement
        tapcell -tapcell_master sky130_fd_sc_hd__tapvpwrvgnd_1 -endcap_master sky130_fd_sc_hd__decap_3
        global_placement -density 0.6
        detailed_placement

        # 3. Clock Tree Synthesis & Routing
        clock_tree_synthesis -buf_list "sky130_fd_sc_hd__clkbuf_1 sky130_fd_sc_hd__clkbuf_2 sky130_fd_sc_hd__clkbuf_4"
        global_route
        detail_route

        # 4. Export Routed Layout
        write_def build/sample_counter_routed.def
        