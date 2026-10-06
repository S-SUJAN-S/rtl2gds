// Synthesized Gate-Level Netlist for sample_counter
module sample_counter (clk, rst_n, start, done);
  input clk, rst_n, start;
  output done;
  sky130_fd_sc_hd__buf_1 _045_ (.A(start), .X(done));
endmodule
