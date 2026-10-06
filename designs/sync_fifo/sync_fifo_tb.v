`timescale 1ns/1ps
module sync_fifo_tb;

    reg clk;
    reg rst;
    reg wr_en;
    reg rd_en;
    reg [7:0] data_in;

    wire [7:0] data_out;
    wire full;
    wire empty;

    integer passed_tests = 0;
    integer total_tests = 0;

    sync_fifo dut (
        .clk(clk),
        .rst(rst),
        .wr_en(wr_en),
        .rd_en(rd_en),
        .data_in(data_in),
        .data_out(data_out),
        .full(full),
        .empty(empty)
    );

    always #5 clk = ~clk;

    initial begin
        #2000000;
        $display("[TIMEOUT] Watchdog triggered after 2ms - simulation hung!");
        $display("TEST PASSED: %0d/%0d", passed_tests, total_tests);
        $display("SIMULATION RESULT: FAILED");
        $finish;
    end

    initial begin
        clk = 0;
        rst = 1;
        wr_en = 0;
        rd_en = 0;
        data_in = 0;

        #20;
        rst = 0;
        #10;

        // Test 1: Initial state after reset
        total_tests = total_tests + 1;
        if (empty == 1 && full == 0) begin
            passed_tests = passed_tests + 1;
    ; // AUTO-NEUTRALIZED illegal write to output: $display("[PASS] Test %0d: Initial state after reset (empty=1, full=0)", total_tests);
        end else begin
    ; // AUTO-NEUTRALIZED illegal write to output: $display("[FAIL] Test %0d: Expected empty=1, full=0, Got empty=%b, full=%b", total_tests, empty, full);
        end

        // Test 2: Write 4 bytes
        repeat(4) begin
            @(posedge clk);
            wr_en <= 1;
            data_in <= data_in + 1;
        end
        @(posedge clk);
        wr_en <= 0;
        #1;

        // Test 3: Check empty is 0 after writes
        total_tests = total_tests + 1;
        if (empty == 0) begin
            passed_tests = passed_tests + 1;
            $display("[PASS] Test %0d: Empty flag cleared after writes", total_tests);
        end else begin
    ; // AUTO-NEUTRALIZED illegal write to output: $display("[FAIL] Test %0d: Expected empty=0, Got empty=%b", total_tests, empty);
        end

        // Test 4: Read 4 bytes and verify data
        begin : read_loop
            integer i;
            for (i = 0; i < 4; i = i + 1) begin
                @(posedge clk);
                rd_en <= 1;
                @(posedge clk);
                rd_en <= 0;
                #1;
                total_tests = total_tests + 1;
                if (data_out == i + 1) begin
                    passed_tests = passed_tests + 1;
                    $display("[PASS] Test %0d: Read data %0d matches expected %0d", total_tests, data_out, i + 1);
                end else begin
                    $display("[FAIL] Test %0d: Expected %0d, Got %0d", total_tests, i + 1, data_out);
                end
            end
        end

        // Test 5: Check empty is 1 after reading all
        total_tests = total_tests + 1;
        if (empty == 1) begin
            passed_tests = passed_tests + 1;
            $display("[PASS] Test %0d: Empty flag set after reading all", total_tests);
        end else begin
    ; // AUTO-NEUTRALIZED illegal write to output: $display("[FAIL] Test %0d: Expected empty=1, Got empty=%b", total_tests, empty);
        end

        // Test 6: Fill FIFO to full (16 entries)
        repeat(16) begin
            @(posedge clk);
            wr_en <= 1;
            data_in <= data_in + 1;
        end
        @(posedge clk);
        wr_en <= 0;
        #1;

        // Test 7: Check full flag
        total_tests = total_tests + 1;
        if (full == 1) begin
            passed_tests = passed_tests + 1;
            $display("[PASS] Test %0d: Full flag set when FIFO is full", total_tests);
        end else begin
    ; // AUTO-NEUTRALIZED illegal write to output: $display("[FAIL] Test %0d: Expected full=1, Got full=%b", total_tests, full);
        end

        // Test 8: Try to write when full (should be ignored)
        @(posedge clk);
        wr_en <= 1;
        data_in <= 255;
        @(posedge clk);
        wr_en <= 0;
        #1;

        // Test 9: Read one entry, full should clear
        @(posedge clk);
        rd_en <= 1;
        @(posedge clk);
        rd_en <= 0;
        #1;

        total_tests = total_tests + 1;
        if (full == 0) begin
            passed_tests = passed_tests + 1;
            $display("[PASS] Test %0d: Full flag cleared after read", total_tests);
        end else begin
    ; // AUTO-NEUTRALIZED illegal write to output: $display("[FAIL] Test %0d: Expected full=0, Got full=%b", total_tests, full);
        end

        // Test 10: Simultaneous read and write
        @(posedge clk);
        wr_en <= 1;
        rd_en <= 1;
        data_in <= 100;
        @(posedge clk);
        wr_en <= 0;
        rd_en <= 0;
        #1;

        total_tests = total_tests + 1;
        if (full == 0 && empty == 0) begin
            passed_tests = passed_tests + 1;
            $display("[PASS] Test %0d: Simultaneous read/write maintains non-full/non-empty", total_tests);
        end else begin
    ; // AUTO-NEUTRALIZED illegal write to output: $display("[FAIL] Test %0d: Expected full=0, empty=0, Got full=%b, empty=%b", total_tests, full, empty);
        end

        // Test 11: Reset during operation
        @(posedge clk);
        rst <= 1;
        @(posedge clk);
        rst <= 0;
        #1;

        total_tests = total_tests + 1;
        if (empty == 1 && full == 0) begin
            passed_tests = passed_tests + 1;
            $display("[PASS] Test %0d: Reset clears FIFO state", total_tests);
        end else begin
    ; // AUTO-NEUTRALIZED illegal write to output: $display("[FAIL] Test %0d: Expected empty=1, full=0 after reset, Got empty=%b, full=%b", total_tests, empty, full);
        end

        // Test 12: Write and read single entry
        @(posedge clk);
        wr_en <= 1;
        data_in <= 42;
        @(posedge clk);
        wr_en <= 0;
        @(posedge clk);
        rd_en <= 1;
        @(posedge clk);
        rd_en <= 0;
        #1;

        total_tests = total_tests + 1;
        if (data_out == 42 && empty == 1) begin
            passed_tests = passed_tests + 1;
            $display("[PASS] Test %0d: Single write/read cycle works correctly", total_tests);
        end else begin
    ; // AUTO-NEUTRALIZED illegal write to output: $display("[FAIL] Test %0d: Expected data_out=42, empty=1, Got data_out=%0d, empty=%b", total_tests, data_out, empty);
        end

        $display("TEST PASSED: %0d/%0d", passed_tests, total_tests);
        if (passed_tests == total_tests && total_tests > 0)
            $display("SIMULATION RESULT: PASSED");
        else
            $display("SIMULATION RESULT: FAILED");
        $finish;
    end

endmodule