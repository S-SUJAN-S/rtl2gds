module uart_tb;
    reg clk;
    reg rst;
    reg tx_start;
    reg [7:0] tx_data;
    wire tx_busy;
    wire [7:0] rx_data;
    wire rx_done;
    wire serial_line;

    uart_top uut (
        .clk(clk),
        .rst(rst),
        .tx_start(tx_start),
        .tx_data(tx_data),
        .tx_busy(tx_busy),
        .rx_data(rx_data),
        .rx_done(rx_done),
        .tx(serial_line),
        .rx(serial_line)
    );

    always #5 clk = ~clk; // 100MHz clock

    initial begin
        $display("Testing UART Tx/Rx Loopback");
        clk = 0;
        rst = 1;
        tx_start = 0;
        tx_data = 0;

        #20 rst = 0;
        #20;

        // Transmit 0xAB
        @(posedge clk);
        tx_data = 8'hAB;
        tx_start = 1;
        @(posedge clk);
        tx_start = 0;

        @(posedge rx_done); // Wait for the positive edge of rx_done
        #20;

        if (rx_data == 8'hAB) begin
            $display("SUCCESS: Transmitted 0xAB, Received 0x%h", rx_data);
        end else begin
            $display("ERROR: Transmitted 0xAB, Received 0x%h", rx_data);
        end

        #100; // wait some time before next transmission

        // Transmit 0x3F
        @(posedge clk);
        tx_data = 8'h3F;
        tx_start = 1;
        @(posedge clk);
        tx_start = 0;
        
        @(posedge rx_done);
        #20;

        if (rx_data == 8'h3F) begin
            $display("SUCCESS: Transmitted 0x3F, Received 0x%h", rx_data);
        end else begin
            $display("ERROR: Transmitted 0x3F, Received 0x%h", rx_data);
        end

        $display("UART Test Complete.");
        $finish;
    end
endmodule
