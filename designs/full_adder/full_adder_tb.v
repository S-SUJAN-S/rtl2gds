module full_adder_tb;

    reg a, b, cin;
    wire sum, cout;

    integer passed_tests = 0;
    integer total_tests = 0;

    full_adder dut (
        .a(a),
        .b(b),
        .cin(cin),
        .sum(sum),
        .cout(cout)
    );

    // Watchdog
    initial begin
        #2000000;
        $display("[TIMEOUT] Watchdog triggered after 2ms - simulation hung!");
        $display("TEST PASSED: %0d/%0d", passed_tests, total_tests);
        $display("SIMULATION RESULT: FAILED");
        $finish;
    end

    task check;
        input [1:0] expected_sum_cout;
        begin
            total_tests = total_tests + 1;
            if (sum === expected_sum_cout[0] && cout === expected_sum_cout[1]) begin
                passed_tests = passed_tests + 1;
                $display("[PASS] Test %0d: a=%b b=%b cin=%b -> sum=%b cout=%b", total_tests, a, b, cin, sum, cout);
            end else begin
                $display("[FAIL] Test %0d: a=%b b=%b cin=%b -> Expected sum=%b cout=%b, Got sum=%b cout=%b", total_tests, a, b, cin, expected_sum_cout[0], expected_sum_cout[1], sum, cout);
            end
        end
    endtask

    initial begin
        // Initialize all stimulus regs to 0
        a = 0; b = 0; cin = 0;

        // Test 1: 0 + 0 + 0 = 0, carry 0
        a = 0; b = 0; cin = 0;
        #10;
        check(2'b00);

        // Test 2: 0 + 0 + 1 = 1, carry 0
        a = 0; b = 0; cin = 1;
        #10;
        check(2'b01);

        // Test 3: 0 + 1 + 0 = 1, carry 0
        a = 0; b = 1; cin = 0;
        #10;
        check(2'b01);

        // Test 4: 0 + 1 + 1 = 0, carry 1
        a = 0; b = 1; cin = 1;
        #10;
        check(2'b10);

        // Test 5: 1 + 0 + 0 = 1, carry 0
        a = 1; b = 0; cin = 0;
        #10;
        check(2'b01);

        // Test 6: 1 + 0 + 1 = 0, carry 1
        a = 1; b = 0; cin = 1;
        #10;
        check(2'b10);

        // Test 7: 1 + 1 + 0 = 0, carry 1
        a = 1; b = 1; cin = 0;
        #10;
        check(2'b10);

        // Test 8: 1 + 1 + 1 = 1, carry 1
        a = 1; b = 1; cin = 1;
        #10;
        check(2'b11);

        // Test 9: Verify 0+0+0 again (edge case re-check)
        a = 0; b = 0; cin = 0;
        #10;
        check(2'b00);

        // Test 10: Verify 1+1+1 again (max carry case)
        a = 1; b = 1; cin = 1;
        #10;
        check(2'b11);

        // Test 11: Verify 0+1+1 (carry propagation)
        a = 0; b = 1; cin = 1;
        #10;
        check(2'b10);

        // Test 12: Verify 1+0+1 (carry propagation)
        a = 1; b = 0; cin = 1;
        #10;
        check(2'b10);

        $display("TEST PASSED: %0d/%0d", passed_tests, total_tests);
        if (passed_tests == total_tests && total_tests > 0)
            $display("SIMULATION RESULT: PASSED");
        else
            $display("SIMULATION RESULT: FAILED");

        $finish;
    end

endmodule