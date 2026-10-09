`timescale 1ns/1ps
module barrel_shifter_8bit_tb;

    reg  [7:0] data_in;
    reg  [2:0] shift_amt;
    reg        shift_right;
    wire [7:0] data_out;

    integer passed_tests = 0;
    integer total_tests  = 0;

    barrel_shifter_8bit dut (
        .data_in     (data_in),
        .shift_amt   (shift_amt),
        .shift_right (shift_right),
        .data_out    (data_out)
    );

    // Watchdog
    initial begin
        #2000000;
        $display("[TIMEOUT] Watchdog triggered after 2ms - simulation hung!");
        $display("TEST PASSED: %0d/%0d", passed_tests, total_tests);
        $display("SIMULATION RESULT: FAILED");
        $finish;
    end

    task check(input [7:0] expected, input [7:0] actual, input [255:0] desc);
        begin
            total_tests = total_tests + 1;
            if (expected === actual) begin
                passed_tests = passed_tests + 1;
                $display("[PASS] Test %0d: %0s", total_tests, desc);
            end else begin
                $display("[FAIL] Test %0d: Expected %h, Got %h", total_tests, expected, actual);
            end
        end
    endtask

    initial begin
        // Initialize all stimulus regs to 0
        data_in <= 8'b0;
        shift_amt <= 3'b0;
        shift_right <= 1'b0;

        // Test 1: No shift (shift_amt=0), left shift
        data_in <= 8'b10101010; shift_amt <= 3'b000; shift_right <= 1'b0;
        #1;
        check(8'b10101010, data_out, "No shift left");

        // Test 2: No shift (shift_amt=0), right shift
        data_in <= 8'b10101010; shift_amt <= 3'b000; shift_right <= 1'b1;
        #1;
        check(8'b10101010, data_out, "No shift right");

        // Test 3: Left shift by 1
        data_in <= 8'b00000001; shift_amt <= 3'b001; shift_right <= 1'b0;
        #1;
        check(8'b00000010, data_out, "Left shift by 1");

        // Test 4: Right shift by 1
        data_in <= 8'b10000000; shift_amt <= 3'b001; shift_right <= 1'b1;
        #1;
        check(8'b01000000, data_out, "Right shift by 1");

        // Test 5: Left shift by 3
        data_in <= 8'b00000100; shift_amt <= 3'b011; shift_right <= 1'b0;
        #1;
        check(8'b00100000, data_out, "Left shift by 3");

        // Test 6: Right shift by 3
        data_in <= 8'b00100000; shift_amt <= 3'b011; shift_right <= 1'b1;
        #1;
        check(8'b00000100, data_out, "Right shift by 3");

        // Test 7: Left shift by 7 (max)
        data_in <= 8'b00000001; shift_amt <= 3'b111; shift_right <= 1'b0;
        #1;
        check(8'b10000000, data_out, "Left shift by 7");

        // Test 8: Right shift by 7 (max)
        data_in <= 8'b10000000; shift_amt <= 3'b111; shift_right <= 1'b1;
        #1;
        check(8'b00000001, data_out, "Right shift by 7");

        // Test 9: Left shift by 4 with all ones
        data_in <= 8'b11111111; shift_amt <= 3'b100; shift_right <= 1'b0;
        #1;
        check(8'b11110000, data_out, "Left shift by 4 all ones");

        // Test 10: Right shift by 4 with all ones
        data_in <= 8'b11111111; shift_amt <= 3'b100; shift_right <= 1'b1;
        #1;
        check(8'b00001111, data_out, "Right shift by 4 all ones");

        // Test 11: Left shift by 2 with alternating pattern
        data_in <= 8'b10101010; shift_amt <= 3'b010; shift_right <= 1'b0;
        #1;
        check(8'b10101000, data_out, "Left shift by 2 alternating");

        // Test 12: Right shift by 2 with alternating pattern
        data_in <= 8'b10101010; shift_amt <= 3'b010; shift_right <= 1'b1;
        #1;
        check(8'b00101010, data_out, "Right shift by 2 alternating");

        $display("TEST PASSED: %0d/%0d", passed_tests, total_tests);
        if (passed_tests == total_tests && total_tests > 0)
            $display("SIMULATION RESULT: PASSED");
        else
            $display("SIMULATION RESULT: FAILED");

        $finish;
    end

endmodule