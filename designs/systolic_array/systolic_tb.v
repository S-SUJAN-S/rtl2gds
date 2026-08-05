module systolic_tb;
    reg clk;
    reg rst_n;
    
    reg weight_load_en;
    reg [7:0] weight_data;
    reg [5:0] weight_addr;
    
    reg act_valid;
    reg [63:0] act_data;
    wire act_ready;
    
    wire result_valid;
    wire [255:0] result_data;
    reg result_ready;
    
    systolic_mm_accel uut (
        .clk(clk),
        .rst_n(rst_n),
        .weight_load_en(weight_load_en),
        .weight_data(weight_data),
        .weight_addr(weight_addr),
        .act_valid(act_valid),
        .act_data(act_data),
        .act_ready(act_ready),
        .result_valid(result_valid),
        .result_data(result_data),
        .result_ready(result_ready)
    );
    
    always #10 clk = ~clk; // 50MHz clock

    integer i;

    initial begin
        $display("Starting 8x8 Systolic Array Testbench...");
        clk = 0;
        rst_n = 0;
        weight_load_en = 0;
        weight_data = 0;
        weight_addr = 0;
        act_valid = 0;
        act_data = 0;
        result_ready = 1;
        
        #45 rst_n = 1;
        
        // 1. Load Weights (All 1s)
        $display("Loading weights...");
        for (i = 0; i < 64; i = i + 1) begin
            @(posedge clk);
            weight_load_en = 1;
            weight_addr = i;
            weight_data = 8'd1;
        end
        @(posedge clk);
        weight_load_en = 0;
        
        // 2. Stream Activations (All 1s)
        $display("Streaming activations...");
        for (i = 0; i < 8; i = i + 1) begin
            @(posedge clk);
            act_valid = 1;
            // 8 lanes of 1s = 64'h01010101_01010101
            act_data = 64'h01010101_01010101;
            // Wait for act_ready if it wasn't ready
            while (!act_ready) begin
                @(posedge clk);
            end
        end
        @(posedge clk);
        act_valid = 0;
        
        // 3. Wait for results
        $display("Waiting for compute and drain...");
        wait(result_valid == 1'b1);
        @(posedge clk);
        
        // 4. Verify results
        if (result_data == 256'h00000008_00000008_00000008_00000008_00000008_00000008_00000008_00000008) begin
            $display("[SUCCESS] Output perfectly matches expected Matrix Multiplication! result=%h", result_data);
        end else begin
            $display("[ERROR] Output mismatch! Expected 8s, got result=%h", result_data);
        end
        
        $finish;
    end
endmodule
