`timescale 1ns/1ps
module gray_counter_8bit_tb;

    reg clk;
    reg rst;
    reg enable;
    wire [7:0] gray_count;

    integer passed_tests = 0;
    integer total_tests = 0;

    // DUT instantiation
    gray_counter_8bit dut (
        .clk(clk),
        .rst(rst),
        .enable(enable),
        .gray_count(gray_count)
    );

    // Clock generator: 10ns period
    initial clk = 0;
    always #5 clk = ~clk;

    // Watchdog timer
    initial begin
        #2000000;
        $display("[TIMEOUT] Watchdog triggered after 2ms - simulation hung!");
        $display("TEST PASSED: %0d/%0d", passed_tests, total_tests);
        $display("SIMULATION RESULT: FAILED");
        $finish;
    end

    // Helper task to check a value
    task check_gray(input [7:0] expected, input [7:0] actual, input integer test_num, input [255:0] desc);
        begin
            total_tests = total_tests + 1;
            if (actual === expected) begin
                passed_tests = passed_tests + 1;
                $display("[PASS] Test %0d: %0s", test_num, desc);
            end else begin
                $display("[FAIL] Test %0d: Expected %h, Got %h", test_num, expected, actual);
            end
        end
    endtask

    // Main test sequence
    initial begin
        // Initialize all stimulus regs
        rst <= 0;
        enable <= 0;

        // Apply reset
        rst <= 1;
        #10;
        rst <= 0;
        #10;

        // Test 1: After reset, gray_count should be 0
        @(posedge clk);
        #1; // Wait for non-blocking assignments to settle
        check_gray(8'h00, gray_count, 1, "Reset value is 0");

        // Test 2: Enable counter, count to 1 (binary 1 -> gray 1)
        enable <= 1;
        @(posedge clk);
        #1; // Wait for non-blocking assignments to settle
        check_gray(8'h01, gray_count, 2, "Count 1: gray = 00000001");

        // Test 3: Count to 2 (binary 2 -> gray 3)
        @(posedge clk);
        #1; // Wait for non-blocking assignments to settle
        check_gray(8'h03, gray_count, 3, "Count 2: gray = 00000011");

        // Test 4: Count to 3 (binary 3 -> gray 2)
        @(posedge clk);
        #1; // Wait for non-blocking assignments to settle
        check_gray(8'h02, gray_count, 4, "Count 3: gray = 00000010");

        // Test 5: Count to 4 (binary 4 -> gray 6)
        @(posedge clk);
        #1; // Wait for non-blocking assignments to settle
        check_gray(8'h06, gray_count, 5, "Count 4: gray = 00000110");

        // Test 6: Disable counter, value should hold
        enable <= 0;
        @(posedge clk);
        #1; // Wait for non-blocking assignments to settle
        check_gray(8'h06, gray_count, 6, "Disabled: value holds at 6");

        // Test 7: Re-enable, count to 5 (binary 5 -> gray 7)
        enable <= 1;
        @(posedge clk);
        #1; // Wait for non-blocking assignments to settle
        check_gray(8'h07, gray_count, 7, "Count 5: gray = 00000111");

        // Test 8: Count to 6 (binary 6 -> gray 5)
        @(posedge clk);
        #1; // Wait for non-blocking assignments to settle
        check_gray(8'h05, gray_count, 8, "Count 6: gray = 00000101");

        // Test 9: Count to 7 (binary 7 -> gray 4)
        @(posedge clk);
        #1; // Wait for non-blocking assignments to settle
        check_gray(8'h04, gray_count, 9, "Count 7: gray = 00000100");

        // Test 10: Reset mid-count
        rst <= 1;
        @(posedge clk);
        #1; // Wait for non-blocking assignments to settle
        check_gray(8'h00, gray_count, 10, "Reset mid-count: value is 0");

        // Test 11: After reset, enable and count to 1
        rst <= 0;
        enable <= 1;
        @(posedge clk);
        #1; // Wait for non-blocking assignments to settle
        check_gray(8'h01, gray_count, 11, "Post-reset count 1: gray = 1");

        // Test 12: Count to 15 (binary 15 -> gray 8)
        repeat(14) @(posedge clk);
        #1; // Wait for non-blocking assignments to settle
        check_gray(8'h08, gray_count, 12, "Count 15: gray = 00001000");

        // Final summary
        $display("TEST PASSED: %0d/%0d", passed_tests, total_tests);
        if (passed_tests == total_tests && total_tests > 0)
            $display("SIMULATION RESULT: PASSED");
        else
            $display("SIMULATION RESULT: FAILED");

        $finish;
    end

endmodule