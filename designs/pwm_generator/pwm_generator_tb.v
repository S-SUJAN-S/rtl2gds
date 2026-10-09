`timescale 1ns/1ps
module pwm_generator_tb;

    reg clk;
    reg rst;
    reg [7:0] duty;
    reg [7:0] period;
    wire pwm_out;

    integer passed_tests = 0;
    integer total_tests = 0;

    pwm_generator dut (
        .clk(clk),
        .rst(rst),
        .duty(duty),
        .period(period),
        .pwm_out(pwm_out)
    );

    always #5 clk = ~clk;

    initial begin
        #2000000;
        $display("[TIMEOUT] Watchdog triggered after 2ms - simulation hung!");
        $display("TEST PASSED: %0d/%0d", passed_tests, total_tests);
        $display("SIMULATION RESULT: FAILED");
        $finish;
    end

    task check_duty;
        input [7:0] t_duty;
        input [7:0] t_period;
        integer i, high_count;
        integer expected_high;
        begin
            duty <= t_duty;
            period <= t_period;
            repeat(2 * t_period + 4) @(posedge clk);
            high_count = 0;
            for (i = 0; i < t_period; i = i + 1) begin
                @(posedge clk);
                #1;
                if (pwm_out) high_count = high_count + 1;
            end
            total_tests = total_tests + 1;
            // Calculate expected high count: min(duty, period)
            if (t_duty > t_period)
                expected_high = t_period;
            else
                expected_high = t_duty;
            
            if (high_count == expected_high) begin
                passed_tests = passed_tests + 1;
                $display("[PASS] Test %0d: duty=%0d period=%0d high_count=%0d", total_tests, t_duty, t_period, high_count);
            end else begin
                $display("[FAIL] Test %0d: duty=%0d period=%0d Expected=%0d Got=%0d", total_tests, t_duty, t_period, expected_high, high_count);
            end
        end
    endtask

    initial begin
        clk = 0;
        rst = 1;
        duty = 0;
        period = 0;

        #20;
        rst = 0;
        #10;

        // Test 1: 50% duty cycle
        check_duty(8'd5, 8'd10);

        // Test 2: 20% duty cycle
        check_duty(8'd2, 8'd10);

        // Test 3: 0% duty cycle (always low)
        check_duty(8'd0, 8'd10);

        // Test 4: 100% duty cycle (always high)
        check_duty(8'd10, 8'd10);

        // Test 5: 80% duty cycle
        check_duty(8'd8, 8'd10);

        // Test 6: Different period - 50% duty
        check_duty(8'd5, 8'd20);

        // Test 7: Different period - 25% duty
        check_duty(8'd5, 8'd20);

        // Test 8: Small period - 50% duty
        check_duty(8'd2, 8'd4);

        // Test 9: Small period - 75% duty
        check_duty(8'd3, 8'd4);

        // Test 10: Duty > period (should be 100%)
        check_duty(8'd15, 8'd10);

        // Test 11: Period = 1, duty = 1 (100%)
        check_duty(8'd1, 8'd1);

        // Test 12: Period = 1, duty = 0 (0%)
        check_duty(8'd0, 8'd1);

        $display("TEST PASSED: %0d/%0d", passed_tests, total_tests);
        if (passed_tests == total_tests && total_tests > 0)
            $display("SIMULATION RESULT: PASSED");
        else
            $display("SIMULATION RESULT: FAILED");
        $finish;
    end

endmodule