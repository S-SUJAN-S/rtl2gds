`timescale 1ns/1ps
module alu8bit_flags_tb;

    reg [7:0] a, b;
    reg [3:0] op;
    wire [7:0] result;
    wire zero, carry, overflow, negative;

    integer passed_tests = 0;
    integer total_tests = 0;

    alu8bit_flags dut (
        .a(a),
        .b(b),
        .op(op),
        .result(result),
        .zero(zero),
        .carry(carry),
        .overflow(overflow),
        .negative(negative)
    );

    initial begin
        #2000000;
        $display("[TIMEOUT] Watchdog triggered after 2ms - simulation hung!");
        $display("TEST PASSED: %0d/%0d", passed_tests, total_tests);
        $display("SIMULATION RESULT: FAILED");
        $finish;
    end

    task check;
        input [7:0] exp_result;
        input exp_zero;
        input exp_carry;
        input exp_overflow;
        input exp_negative;
        begin
            total_tests = total_tests + 1;
            #10;
            if (result === exp_result && zero === exp_zero && carry === exp_carry && overflow === exp_overflow && negative === exp_negative) begin
                passed_tests = passed_tests + 1;
                $display("[PASS] Test %0d: result=%h zero=%b carry=%b overflow=%b negative=%b", total_tests, result, zero, carry, overflow, negative);
            end else begin
                $display("[FAIL] Test %0d: Expected result=%h zero=%b carry=%b overflow=%b negative=%b, Got result=%h zero=%b carry=%b overflow=%b negative=%b", total_tests, exp_result, exp_zero, exp_carry, exp_overflow, exp_negative, result, zero, carry, overflow, negative);
            end
        end
    endtask

    initial begin
        a <= 8'b0; b <= 8'b0; op <= 4'b0;

        // Test 1: ADD 5 + 3 = 8
        a <= 8'd5; b <= 8'd3; op <= 4'd0;
        check(8'd8, 1'b0, 1'b0, 1'b0, 1'b0);

        // Test 2: ADD 70 + 70 = 140 (signed overflow, no unsigned carry)
        a <= 8'd70; b <= 8'd70; op <= 4'd0;
        check(8'd140, 1'b0, 1'b0, 1'b1, 1'b1);

        // Test 3: ADD 200 + 100 = 300 (unsigned carry, no signed overflow)
        a <= 8'd200; b <= 8'd100; op <= 4'd0;
        check(8'd44, 1'b0, 1'b1, 1'b0, 1'b0);

        // Test 4: SUB 10 - 3 = 7 (no borrow, no overflow)
        a <= 8'd10; b <= 8'd3; op <= 4'd1;
        check(8'd7, 1'b0, 1'b0, 1'b0, 1'b0);

        // Test 5: SUB 3 - 10 = 249 (borrow=1, negative=1)
        a <= 8'd3; b <= 8'd10; op <= 4'd1;
        check(8'd249, 1'b0, 1'b1, 1'b0, 1'b1);

        // Test 6: MUL_LOW 4 * 5 = 20 (no overflow)
        a <= 8'd4; b <= 8'd5; op <= 4'd2;
        check(8'd20, 1'b0, 1'b0, 1'b0, 1'b0);

        // Test 7: MUL_LOW 20 * 20 = 400 = 0x190 (lower=0x90=144, overflow=1)
        a <= 8'd20; b <= 8'd20; op <= 4'd2;
        check(8'd144, 1'b0, 1'b1, 1'b1, 1'b1);

        // Test 8: AND 12 & 10 = 8
        a <= 8'd12; b <= 8'd10; op <= 4'd3;
        check(8'd8, 1'b0, 1'b0, 1'b0, 1'b0);

        // Test 9: OR 12 | 10 = 14
        a <= 8'd12; b <= 8'd10; op <= 4'd4;
        check(8'd14, 1'b0, 1'b0, 1'b0, 1'b0);

        // Test 10: XOR 12 ^ 10 = 6
        a <= 8'd12; b <= 8'd10; op <= 4'd5;
        check(8'd6, 1'b0, 1'b0, 1'b0, 1'b0);

        // Test 11: SHL 130 << 1 = 4 (carry=1, MSB was 1)
        a <= 8'd130; b <= 8'd0; op <= 4'd6;
        check(8'd4, 1'b0, 1'b1, 1'b0, 1'b0);

        // Test 12: ADD 0 + 0 = 0 (zero=1)
        a <= 8'd0; b <= 8'd0; op <= 4'd0;
        check(8'd0, 1'b1, 1'b0, 1'b0, 1'b0);

        $display("TEST PASSED: %0d/%0d", passed_tests, total_tests);
        if (passed_tests == total_tests && total_tests > 0)
            $display("SIMULATION RESULT: PASSED");
        else
            $display("SIMULATION RESULT: FAILED");
        $finish;
    end

endmodule