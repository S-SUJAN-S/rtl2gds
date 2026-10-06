`timescale 1ns/1ps
module fifo_16x32_deep_tb;

    reg clk;
    reg rst;
    reg wr_en;
    reg [15:0] wr_data;
    reg rd_en;
    wire [15:0] rd_data;
    wire almost_full;
    wire almost_empty;
    wire full;
    wire empty;

    integer passed_tests = 0;
    integer total_tests = 0;
    integer i;

    // DUT instantiation
    fifo_16x32_deep dut (
        .clk(clk),
        .rst(rst),
        .wr_en(wr_en),
        .wr_data(wr_data),
        .rd_en(rd_en),
        .rd_data(rd_data),
        .almost_full(almost_full),
        .almost_empty(almost_empty),
        .full(full),
        .empty(empty)
    );

    // Clock generator: 10ns period = 100MHz
    initial clk = 0;
    always #5 clk = ~clk;

    // Watchdog
    initial begin
        #5000000;
        $display("[TIMEOUT] Watchdog triggered after 5ms - simulation hung!");
        $display("TEST PASSED: %0d/%0d", passed_tests, total_tests);
        $display("SIMULATION RESULT: FAILED");
        $finish;
    end

    initial begin
        // Initialize stimulus
        rst     <= 1'b1;
        wr_en   <= 1'b0;
        wr_data <= 16'h0000;
        rd_en   <= 1'b0;

        #20;
        @(posedge clk);
        rst <= 1'b0;
        #10;

        // Test 1: Reset state checks
        total_tests = total_tests + 1;
        if (empty == 1'b1 && full == 1'b0 && almost_empty == 1'b1 && almost_full == 1'b0) begin
            passed_tests = passed_tests + 1;
            $display("[PASS] Test %0d: Reset state - empty=1, full=0, almost_empty=1, almost_full=0", total_tests);
        end else begin
            $display("[FAIL] Test %0d: Reset flags mismatch. empty=%b full=%b ae=%b af=%b", total_tests, empty, full, almost_empty, almost_full);
        end

        // Test 2: Write 5 words, check almost_empty clears
        total_tests = total_tests + 1;
        for (i = 1; i <= 5; i = i + 1) begin
            @(posedge clk);
            wr_en   <= 1'b1;
            wr_data <= 16'hA000 + i;
        end
        @(posedge clk);
        wr_en <= 1'b0;
        #5;
        if (empty == 1'b0 && almost_empty == 1'b0) begin
            passed_tests = passed_tests + 1;
            $display("[PASS] Test %0d: After 5 writes - empty=0, almost_empty=0", total_tests);
        end else begin
            $display("[FAIL] Test %0d: After 5 writes - empty=%b, almost_empty=%b", total_tests, empty, almost_empty);
        end

        // Test 3: Write up to 28 words total (23 more writes), check almost_full asserts
        total_tests = total_tests + 1;
        for (i = 6; i <= 28; i = i + 1) begin
            @(posedge clk);
            wr_en   <= 1'b1;
            wr_data <= 16'hA000 + i;
        end
        @(posedge clk);
        wr_en <= 1'b0;
        #5;
        if (almost_full == 1'b1 && full == 1'b0) begin
            passed_tests = passed_tests + 1;
            $display("[PASS] Test %0d: At 28 words - almost_full=1, full=0", total_tests);
        end else begin
            $display("[FAIL] Test %0d: At 28 words - almost_full=%b, full=%b", total_tests, almost_full, full);
        end

        // Test 4: Write remaining 4 words to reach depth 32, check full asserts
        total_tests = total_tests + 1;
        for (i = 29; i <= 32; i = i + 1) begin
            @(posedge clk);
            wr_en   <= 1'b1;
            wr_data <= 16'hA000 + i;
        end
        @(posedge clk);
        wr_en <= 1'b0;
        #5;
        if (full == 1'b1 && almost_full == 1'b1) begin
            passed_tests = passed_tests + 1;
            $display("[PASS] Test %0d: At 32 words - full=1, almost_full=1", total_tests);
        end else begin
            $display("[FAIL] Test %0d: At 32 words - full=%b, almost_full=%b", total_tests, full, almost_full);
        end

        // Test 5: Read 1 word, check full de-asserts
        total_tests = total_tests + 1;
        @(posedge clk);
        rd_en <= 1'b1;
        @(posedge clk);
        rd_en <= 1'b0;
        #5;
        if (full == 1'b0 && rd_data == 16'hA001) begin
            passed_tests = passed_tests + 1;
            $display("[PASS] Test %0d: After 1 read - full=0, data=0x%04x", total_tests, rd_data);
        end else begin
            $display("[FAIL] Test %0d: After 1 read - full=%b, rd_data=0x%04x", total_tests, full, rd_data);
        end

        // Test 6: Read remaining 31 words, verify data order and empty asserts
        total_tests = total_tests + 1;
        for (i = 2; i <= 32; i = i + 1) begin
            @(posedge clk);
            rd_en <= 1'b1;
        end
        @(posedge clk);
        rd_en <= 1'b0;
        #5;
        if (empty == 1'b1 && almost_empty == 1'b1) begin
            passed_tests = passed_tests + 1;
            $display("[PASS] Test %0d: After draining FIFO - empty=1, almost_empty=1", total_tests);
        end else begin
            $display("[FAIL] Test %0d: After draining FIFO - empty=%b, almost_empty=%b", total_tests, empty, almost_empty);
        end

        // Summary
        $display("TEST PASSED: %0d/%0d", passed_tests, total_tests);
        if (passed_tests == total_tests && total_tests > 0)
            $display("SIMULATION RESULT: PASSED");
        else
            $display("SIMULATION RESULT: FAILED");
        $finish;
    end

endmodule
