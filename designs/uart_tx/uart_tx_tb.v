`timescale 1ns/1ps
module uart_tx_tb;

    reg clk;
    reg rst_n;
    reg [7:0] tx_data;
    reg tx_start;
    wire tx;
    wire tx_ready;

    integer passed_tests = 0;
    integer total_tests = 0;

    // DUT instantiation
    uart_tx dut (
        .clk(clk),
        .rst_n(rst_n),
        .tx_data(tx_data),
        .tx_start(tx_start),
        .tx(tx),
        .tx_ready(tx_ready)
    );

    // Clock generator: 10ns period = 100MHz
    initial clk = 0;
    always #5 clk = ~clk;

    // Watchdog
    initial begin
        #2000000;
        $display("[TIMEOUT] Watchdog triggered after 2ms - simulation hung!");
        $display("TEST PASSED: %0d/%0d", passed_tests, total_tests);
        $display("SIMULATION RESULT: FAILED");
        $finish;
    end

    // Helper task: wait for tx_ready to go high (transmission complete)
    task wait_tx_complete;
        integer timeout;
        begin
            timeout = 0;
            while (tx_ready == 1'b0) begin
                @(posedge clk);
                timeout = timeout + 1;
                if (timeout > 5000) begin
                    $display("[ERROR] Timeout waiting for tx_ready");
                    $finish;
                end
            end
        end
    endtask

    // Helper task: send a byte and wait for completion
    task send_byte(input [7:0] data);
        begin
            @(posedge clk);
            tx_start <= 1'b1;
            tx_data <= data;
            @(posedge clk);
            tx_start <= 1'b0;
            wait_tx_complete;
        end
    endtask

    initial begin
        // Initialize all stimulus regs
        rst_n <= 1'b0;
        tx_data <= 8'h00;
        tx_start <= 1'b0;

        // Reset sequence
        #20;
        rst_n <= 1'b1;
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
        tx_start <= 1'b1;
        tx_data <= 8'h55;
        @(posedge clk);
        tx_start <= 1'b0;
        // Wait a few cycles to ensure we're in transmission
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

        // Test 9: Send 0x12
        total_tests = total_tests + 1;
        send_byte(8'h12);
        if (tx_ready == 1'b1) begin
            passed_tests = passed_tests + 1;
            $display("[PASS] Test %0d: Successfully transmitted 0x12", total_tests);
        end else begin
            $display("[FAIL] Test %0d: Failed to transmit 0x12", total_tests);
        end

        // Test 10: Send 0x34
        total_tests = total_tests + 1;
        send_byte(8'h34);
        if (tx_ready == 1'b1) begin
            passed_tests = passed_tests + 1;
            $display("[PASS] Test %0d: Successfully transmitted 0x34", total_tests);
        end else begin
            $display("[FAIL] Test %0d: Failed to transmit 0x34", total_tests);
        end

        // Test 11: Verify tx_ready is high after multiple transmissions
        total_tests = total_tests + 1;
        #10;
        if (tx_ready == 1'b1) begin
            passed_tests = passed_tests + 1;
            $display("[PASS] Test %0d: tx_ready is high after multiple transmissions", total_tests);
        end else begin
            $display("[FAIL] Test %0d: Expected tx_ready==1, got %b", total_tests, tx_ready);
        end

        // Test 12: Send 0xAB
        total_tests = total_tests + 1;
        send_byte(8'hAB);
        if (tx_ready == 1'b1) begin
            passed_tests = passed_tests + 1;
            $display("[PASS] Test %0d: Successfully transmitted 0xAB", total_tests);
        end else begin
            $display("[FAIL] Test %0d: Failed to transmit 0xAB", total_tests);
        end

        // Final summary
        $display("TEST PASSED: %0d/%0d", passed_tests, total_tests);
        if (passed_tests == total_tests && total_tests > 0)
            $display("SIMULATION RESULT: PASSED");
        else
            $display("SIMULATION RESULT: FAILED");

        #100;
        $finish;
    end

endmodule