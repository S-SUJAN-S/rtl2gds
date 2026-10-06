module full_adder_tb;
  
  // Inputs
  reg a, b, cin;
  
  // Outputs
  wire sum, cout;
  
  // Instantiate the DUT
  full_adder dut (
    .a(a),
    .b(b),
    .cin(cin),
    .sum(sum),
    .cout(cout)
  );
  
  initial begin
    // Stimulus for a = 0, b = 0, cin = 0
    a = 1'b0;
    b = 1'b0;
    cin = 1'b0;
    #10;
    
    // Check the outputs
    if (sum !== 1'b0 || cout !== 1'b0) begin
      $display("Test failed: a=%b, b=%b, cin=%b", a, b, cin);
      $finish;
    end
    
    // Stimulus for a = 1, b = 0, cin = 0
    a = 1'b1;
    b = 1'b0;
    cin = 1'b0;
    #10;
    
    // Check the outputs
    if (sum !== 1'b1 || cout !== 1'b0) begin
      $display("Test failed: a=%b, b=%b, cin=%b", a, b, cin);
      $finish;
    end
    
    // Stimulus for a = 0, b = 1, cin = 0
    a = 1'b0;
    b = 1'b1;
    cin = 1'b0;
    #10;
    
    // Check the outputs
    if (sum !== 1'b1 || cout !== 1'b0) begin
      $display("Test failed: a=%b, b=%b, cin=%b", a, b, cin);
      $finish;
    end
    
    // Stimulus for a = 1, b = 1, cin = 0
    a = 1'b1;
    b = 1'b1;
    cin = 1'b0;
    #10;
    
    // Check the outputs
    if (sum !== 1'b0 || cout !== 1'b1) begin
      $display("Test failed: a=%b, b=%b, cin=%b", a, b, cin);
      $finish;
    end
    
    $display("All tests passed");
    $finish;
  end
  
endmodule