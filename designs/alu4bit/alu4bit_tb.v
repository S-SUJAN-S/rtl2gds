`timescale 1ns/1ps
module alu4bit_tb;

    reg [3:0] a, b;
    reg [2:0] opcode;
    wire [3:0] result;
    wire zero;
    wire carry_out;

    integer passed_tests = 0;
    integer total_tests = 0;

    alu4bit dut (
        .a(a),
        .b(b),
        .opcode(opcode),
        .result(result),
        .zero(zero),
        .carry_out(carry_out)
    );

    initial begin
        a = 0; b = 0; opcode = 0;
    end

    initial begin
        #2000000;
        $display("[TIMEOUT] Watchdog triggered after 2ms - simulation hung!");
        $display("TEST PASSED: %0d/%0d", passed_tests, total_tests);
        $display("SIMULATION RESULT: FAILED");
        $finish;
    end

    task check(input [3:0] exp_result, input exp_zero, input exp_carry, input [3:0] act_result, input act_zero, input act_carry);
        begin
            total_tests = total_tests + 1;
            if (act_result === exp_result && act_zero === exp_zero && act_carry === exp_carry) begin
                passed_tests = passed_tests + 1;
                $display("[PASS] Test %0d: result=%h zero=%b carry=%b", total_tests, act_result, act_zero, act_carry);
            end else begin
                $display("[FAIL] Test %0d: Expected result=%h zero=%b carry=%b, Got result=%h zero=%b carry=%b",
                         total_tests, exp_result, exp_zero, exp_carry, act_result, act_zero, act_carry);
            end
        end
    endtask

    initial begin
        #10;

        // Test 1: ADD 3 + 5 = 8, no carry
        a <= 4'd3; b <= 4'd5; opcode <= 3'd0;
        #10;
        check(4'd8, 1'b0, 1'b0, result, zero, carry_out);

        // Test 2: SUB 0 - 8 = 8 (borrow), carry=1
        a <= 4'd0; b <= 4'd8; opcode <= 3'd1;
        #10;
        check(4'd8, 1'b0, 1'b1, result, zero, carry_out);

        // Test 3: SUB 5 - 3 = 2, no carry
        a <= 4'd5; b <= 4'd3; opcode <= 3'd1;
        #10;
        check(4'd2, 1'b0, 1'b0, result, zero, carry_out);

        // Test 4: ADD 3 + 3 = 6, no carry
        a <= 4'd3; b <= 4'd3; opcode <= 3'd0;
        #10;
        check(4'd6, 1'b0, 1'b0, result, zero, carry_out);

        // Test 5: AND 12 & 10 = 8
        a <= 4'd12; b <= 4'd10; opcode <= 3'd2;
        #10;
        check(4'd8, 1'b0, 1'b0, result, zero, carry_out);

        // Test 6: OR 5 | 3 = 7
        a <= 4'd5; b <= 4'd3; opcode <= 3'd3;
        #10;
        check(4'd7, 1'b0, 1'b0, result, zero, carry_out);

        // Test 7: XOR 6 ^ 3 = 5
        a <= 4'd6; b <= 4'd3; opcode <= 3'd4;
        #10;
        check(4'd5, 1'b0, 1'b0, result, zero, carry_out);

        // Test 8: NOT 5 = 10
        a <= 4'd5; b <= 4'd0; opcode <= 3'd5;
        #10;
        check(4'd10, 1'b0, 1'b0, result, zero, carry_out);

        // Test 9: SLL 12 << 1 = 8, carry=1
        a <= 4'd12; b <= 4'd0; opcode <= 3'd6;
        #10;
        check(4'd8, 1'b0, 1'b1, result, zero, carry_out);

        // Test 10: SRL 12 >> 1 = 6, carry=0
        a <= 4'd12; b <= 4'd0; opcode <= 3'd7;
        #10;
        check(4'd6, 1'b0, 1'b0, result, zero, carry_out);

        // Test 11: ADD 0 + 0 = 0, zero=1
        a <= 4'd0; b <= 4'd0; opcode <= 3'd0;
        #10;
        check(4'd0, 1'b1, 1'b0, result, zero, carry_out);

        // Test 12: AND 0 & 15 = 0, zero=1
        a <= 4'd0; b <= 4'd15; opcode <= 3'd2;
        #10;
        check(4'd0, 1'b1, 1'b0, result, zero, carry_out);

        $display("TEST PASSED: %0d/%0d", passed_tests, total_tests);
        if (passed_tests == total_tests && total_tests > 0)
            $display("SIMULATION RESULT: PASSED");
        else
            $display("SIMULATION RESULT: FAILED");
        $finish;
    end

endmodule