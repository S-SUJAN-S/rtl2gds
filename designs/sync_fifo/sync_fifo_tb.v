module sync_fifo_tb;

  // DUT ports
  reg  clk, rst, wr_en, rd_en;  // AUTO-FIXED: DUT inputs must be reg
  wire [7:0] data_out;
  reg  [7:0] data_in;  // AUTO-FIXED
  wire full, empty;
  
  // Testbench signals
  reg [7:0] data_to_write;
  reg [31:0] cycle_count = 0;
  integer i;
  
  // Instantiate DUT
  sync_fifo dut(
    .clk(clk),
    .rst(rst),
    .wr_en(wr_en),
    .rd_en(rd_en),
    .data_in(data_in),
    .data_out(data_out),
    .full(full),
    .empty(empty)
  );
  
  // Generate clock
  always #5 clk = ~clk;
  
  initial begin
    $display("[START] sync_fifo testbench");
    
    // Initialize inputs
    clk = 0;
    rst = 1;
    wr_en = 0;
    rd_en = 0;
    data_in = 'hx;
    
    // Apply reset for 2 cycles
    #10 rst = 0;
    #10 rst = 1;
    
    // Test: Reset test
    wr_en = 1;
    rd_en = 1;
    data_to_write = 'hAA;
    for (i=0; i<WIDTH+2; i++) begin
      @(posedge clk);
      cycle_count += 1;
      if (cycle_count == 3) $display("[FAIL] Reset test: Cycle count is not 3");
    end
    
    // Test: Fill test
    wr_en = 1;
    rd_en = 0;
    data_to_write = 'hAA;
    for (i=0; i<WIDTH+2; i++) begin
      @(posedge clk);
      cycle_count += 1;
      if (cycle_count == 3) $display("[FAIL] Fill test: Cycle count is not 3");
    end
    
    // Test: Drain test
    wr_en = 0;
    rd_en = 1;
    data_to_write = 'hAA;
    for (i=0; i<WIDTH+2; i++) begin
      @(posedge clk);
      cycle_count += 1;
      if (cycle_count == 3) $display("[FAIL] Drain test: Cycle count is not 3");
    end
    
    // Test: Simultaneous push/pop test
    wr_en = 1;
    rd_en = 1;
    data_to_write = 'hAA;
    for (i=0; i<WIDTH+2; i++) begin
      @(posedge clk);
      cycle_count += 1;
      if (cycle_count == 3) $display("[FAIL] Simultaneous push/pop test: Cycle count is not 3");
    end
    
    $display("[PASS] sync_fifo testbench");
    $finish;
  end
  
endmodule