`timescale 1ns/1ps
module uart_tx_tb;

    reg clk;
    reg rst;
    reg [7:0] tx_data;
    reg tx_valid;
    wire tx;
    wire tx_ready;

    integer passed_tests = 0;
    integer total_tests = 0;

    // DUT instantiation
    uart_tx dut (
        .clk(clk),
        .rst(rst),
        .tx_data(tx_data),
        .tx_valid(tx_valid),
        .tx(tx),
        .tx_ready(tx_ready)
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

    // Helper task: wait for tx_ready to return to high
    task wait_tx_complete;
        integer timeout;
        begin
            timeout = 0;
            @(posedge clk);
            while (tx_ready == 1'b0 && timeout < 20000) begin
                @(posedge clk);
                timeout = timeout + 1;
            end
            if (timeout >= 20000) begin
                $display("[ERROR] Timeout waiting for tx_ready");
                $finish;
            end
            @(posedge clk);
        end
    endtask

    // Helper task: send a byte and wait for completion
    task send_byte(input [7:0] data);
        begin
            @(posedge clk);
            tx_valid <= 1'b1;
            tx_data  <= data;
            @(posedge clk);
            tx_valid <= 1'b0;
            wait_tx_complete;
        end
    endtask

    initial begin
        // Initialize all stimulus regs
        rst      <= 1'b1;
        tx_data  <= 8'h00;
        tx_valid <= 1'b0;

        // Reset sequence
        #20;
        @(posedge clk);
        rst <= 1'b0;
        #20;

        // Test 1: After reset, tx_ready should be high and tx should be high (idle)
        total_tests = total_tests + 1;
        if (tx_ready == 1'b1 && tx == 1'b1) begin
            passed_tests = passed_tests + 1;
            $display("[PASS] Test %0d: After reset, tx_ready is 1 and tx is 1 (idle)", total_tests);
        end else begin
            $display("[FAIL] Test %0d: Expected tx_ready==1, tx==1. Got tx_ready=%b, tx=%b", total_tests, tx_ready, tx);
        end

        // Test 2: Send 0x55, verify tx_ready goes low during transmission
        total_tests = total_tests + 1;
        @(posedge clk);
        tx_valid <= 1'b1;
        tx_data  <= 8'h55;
        @(posedge clk);
        tx_valid <= 1'b0;
        #10;
        if (tx_ready == 1'b0) begin
            passed_tests = passed_tests + 1;
            $display("[PASS] Test %0d: tx_ready goes low during transmission", total_tests);
        end else begin
            $display("[FAIL] Test %0d: Expected tx_ready==0 during transmission, got %b", total_tests, tx_ready);
        end
        wait_tx_complete;

        // Test 3: After transmission, tx_ready should be high again
        total_tests = total_tests + 1;
        if (tx_ready == 1'b1) begin
            passed_tests = passed_tests + 1;
            $display("[PASS] Test %0d: tx_ready returns to 1 after transmission", total_tests);
        end else begin
            $display("[FAIL] Test %0d: Expected tx_ready==1 after transmission, got %b", total_tests, tx_ready);
        end

        // Test 4: Send 0xAA
        total_tests = total_tests + 1;
        send_byte(8'hAA);
        if (tx_ready == 1'b1) begin
            passed_tests = passed_tests + 1;
            $display("[PASS] Test %0d: Successfully transmitted 0xAA", total_tests);
        end else begin
            $display("[FAIL] Test %0d: Failed to transmit 0xAA", total_tests);
        end

        // Test 5: Send 0xF0
        total_tests = total_tests + 1;
        send_byte(8'hF0);
        if (tx_ready == 1'b1) begin
            passed_tests = passed_tests + 1;
            $display("[PASS] Test %0d: Successfully transmitted 0xF0", total_tests);
        end else begin
            $display("[FAIL] Test %0d: Failed to transmit 0xF0", total_tests);
        end

        // Test 6: Send 0x00
        total_tests = total_tests + 1;
        send_byte(8'h00);
        if (tx_ready == 1'b1) begin
            passed_tests = passed_tests + 1;
            $display("[PASS] Test %0d: Successfully transmitted 0x00", total_tests);
        end else begin
            $display("[FAIL] Test %0d: Failed to transmit 0x00", total_tests);
        end

        // Test 7: Send 0xFF
        total_tests = total_tests + 1;
        send_byte(8'hFF);
        if (tx_ready == 1'b1) begin
            passed_tests = passed_tests + 1;
            $display("[PASS] Test %0d: Successfully transmitted 0xFF", total_tests);
        end else begin
            $display("[FAIL] Test %0d: Failed to transmit 0xFF", total_tests);
        end

        // Test 8: Verify tx is high (idle) when not transmitting
        total_tests = total_tests + 1;
        #10;
        if (tx == 1'b1) begin
            passed_tests = passed_tests + 1;
            $display("[PASS] Test %0d: tx is high (idle) when not transmitting", total_tests);
        end else begin
            $display("[FAIL] Test %0d: Expected tx==1 (idle), got %b", total_tests, tx);
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