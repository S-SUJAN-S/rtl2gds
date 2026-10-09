`timescale 1ns/1ps
module counter_sync_tb;

    reg clk;
    reg rst;
    reg load;
    reg enable;
    reg up_down;
    reg [7:0] data_in;
    wire [7:0] count;
    wire terminal_count;

    integer passed_tests = 0;
    integer total_tests = 0;

    counter_sync dut (
        .clk(clk),
        .rst(rst),
        .load(load),
        .enable(enable),
        .up_down(up_down),
        .data_in(data_in),
        .count(count),
        .terminal_count(terminal_count)
    );

    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end

    initial begin
        #2000000;
        $display("[TIMEOUT] Watchdog triggered after 2ms - simulation hung!");
        $display("TEST PASSED: %0d/%0d", passed_tests, total_tests);
        $display("SIMULATION RESULT: FAILED");
        $finish;
    end

    task check;
        input [7:0] exp_count;
        input exp_tc;
        begin
            total_tests = total_tests + 1;
            if (count === exp_count && terminal_count === exp_tc) begin
                passed_tests = passed_tests + 1;
                $display("[PASS] Test %0d: count=%h tc=%b", total_tests, count, terminal_count);
            end else begin
                $display("[FAIL] Test %0d: Expected count=%h tc=%b, Got count=%h tc=%b", total_tests, exp_count, exp_tc, count, terminal_count);
            end
        end
    endtask

    initial begin
        // Initialize all stimulus regs
        rst = 0;
        load = 0;
        enable = 0;
        up_down = 0;
        data_in <= 8'd0;

        // Test 1: Reset
        rst = 1;
        @(posedge clk); #1;
        check(8'd0, 1'b0);
        rst = 0;

        // Test 2: Load value 0x10
        load = 1;
        data_in <= 8'h10;
        @(posedge clk); #1;
        check(8'h10, 1'b0);
        load = 0;

        // Test 3: Count up from 0x10
        enable = 1;
        up_down = 1;
        @(posedge clk); #1;
        check(8'h11, 1'b0);

        // Test 4: Count up again
        @(posedge clk); #1;
        check(8'h12, 1'b0);

        // Test 5: Disable counter (hold value)
        enable = 0;
        @(posedge clk); #1;
        check(8'h12, 1'b0);

        // Test 6: Count down
        enable = 1;
        up_down = 0;
        @(posedge clk); #1;
        check(8'h11, 1'b0);

        // Test 7: Count down again
        @(posedge clk); #1;
        check(8'h10, 1'b0);

        // Test 8: Load 0xFF and count up to terminal
        load = 1;
        data_in <= 8'hFE;
        @(posedge clk); #1;
        load = 0;
        enable = 1;
        up_down = 1;
        @(posedge clk); #1;
        check(8'hFF, 1'b1);

        // Test 9: Continue counting up (wrap around)
        @(posedge clk); #1;
        check(8'h00, 1'b0);

        // Test 10: Load 0x01 and count down to terminal
        load = 1;
        data_in <= 8'h01;
        @(posedge clk); #1;
        load = 0;
        enable = 1;
        up_down = 0;
        @(posedge clk); #1;
        check(8'h00, 1'b1);

        // Test 11: Continue counting down (wrap around)
        @(posedge clk); #1;
        check(8'hFF, 1'b0);

        // Test 12: Reset again
        rst = 1;
        @(posedge clk); #1;
        check(8'd0, 1'b0);
        rst = 0;

        $display("TEST PASSED: %0d/%0d", passed_tests, total_tests);
        if (passed_tests == total_tests && total_tests > 0)
            $display("SIMULATION RESULT: PASSED");
        else
            $display("SIMULATION RESULT: FAILED");
        $finish;
    end

endmodule