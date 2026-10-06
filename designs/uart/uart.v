module uart_tx (
    input clk,
    input rst,
    input tx_start,
    input [7:0] tx_data,
    output reg tx,
    output reg tx_busy
);
    parameter [15:0] CLKS_PER_BIT = 10; 
    
    localparam IDLE = 3'd0;
    localparam START = 3'd1;
    localparam DATA = 3'd2;
    localparam STOP = 3'd3;
    
    reg [2:0] state;
    reg [15:0] clk_count;
    reg [2:0] bit_index;
    reg [7:0] data_reg;
    
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            state <= IDLE;
            tx <= 1'b1;
            tx_busy <= 1'b0;
            clk_count <= 16'd0;
            bit_index <= 3'd0;
            data_reg <= 8'd0;
        end else begin
            case (state)
                IDLE: begin
                    tx <= 1'b1;
                    tx_busy <= 1'b0;
                    clk_count <= 16'd0;
                    bit_index <= 3'd0;
                    if (tx_start) begin
                        data_reg <= tx_data;
                        state <= START;
                        tx_busy <= 1'b1;
                    end
                end
                START: begin
                    tx <= 1'b0;
                    if (clk_count < CLKS_PER_BIT - 1) begin
                        clk_count <= clk_count + 16'd1;
                    end else begin
                        clk_count <= 16'd0;
                        state <= DATA;
                    end
                end
                DATA: begin
                    tx <= data_reg[bit_index];
                    if (clk_count < CLKS_PER_BIT - 1) begin
                        clk_count <= clk_count + 16'd1;
                    end else begin
                        clk_count <= 16'd0;
                        if (bit_index < 7) begin
                            bit_index <= bit_index + 3'd1;
                        end else begin
                            state <= STOP;
                        end
                    end
                end
                STOP: begin
                    tx <= 1'b1;
                    if (clk_count < CLKS_PER_BIT - 1) begin
                        clk_count <= clk_count + 16'd1;
                    end else begin
                        clk_count <= 16'd0;
                        state <= IDLE;
                    end
                end
                default: state <= IDLE;
            endcase
        end
    end
endmodule

module uart_rx (
    input clk,
    input rst,
    input rx,
    output reg [7:0] rx_data,
    output reg rx_done
);
    parameter [15:0] CLKS_PER_BIT = 10;
    
    localparam IDLE = 3'd0;
    localparam START = 3'd1;
    localparam DATA = 3'd2;
    localparam STOP = 3'd3;
    
    reg [2:0] state;
    reg [15:0] clk_count;
    reg [2:0] bit_index;
    
    // 2-Stage Synchronizer for rx input
    reg rx_sync_1;
    reg rx_sync_2;
    
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            rx_sync_1 <= 1'b1;
            rx_sync_2 <= 1'b1;
            state <= IDLE;
            rx_data <= 8'd0;
            rx_done <= 1'b0;
            clk_count <= 16'd0;
            bit_index <= 3'd0;
        end else begin
            rx_sync_1 <= rx;
            rx_sync_2 <= rx_sync_1;
            
            case (state)
                IDLE: begin
                    rx_done <= 1'b0;
                    clk_count <= 16'd0;
                    bit_index <= 3'd0;
                    if (rx_sync_2 == 1'b0) begin
                        state <= START;
                    end
                end
                START: begin
                    if (clk_count == (CLKS_PER_BIT / 2)) begin
                        if (rx_sync_2 == 1'b0) begin
                            // Good start bit
                            clk_count <= 16'd0;
                            state <= DATA;
                        end else begin
                            state <= IDLE;
                        end
                    end else begin
                        clk_count <= clk_count + 16'd1;
                    end
                end
                DATA: begin
                    if (clk_count < CLKS_PER_BIT - 1) begin
                        clk_count <= clk_count + 16'd1;
                    end else begin
                        clk_count <= 16'd0;
                        rx_data[bit_index] <= rx_sync_2;
                        if (bit_index < 7) begin
                            bit_index <= bit_index + 3'd1;
                        end else begin
                            state <= STOP;
                        end
                    end
                end
                STOP: begin
                    if (clk_count < CLKS_PER_BIT - 1) begin
                        clk_count <= clk_count + 16'd1;
                    end else begin
                        rx_done <= 1'b1;
                        clk_count <= 16'd0;
                        state <= IDLE;
                    end
                end
                default: state <= IDLE;
            endcase
        end
    end
endmodule

module uart_top (
    input clk,
    input rst,
    input tx_start,
    input [7:0] tx_data,
    output tx_busy,
    output [7:0] rx_data,
    output rx_done,
    output tx,
    input rx
);
    // Reset synchronizer for physical safety (CDC)
    reg rst_sync_1, rst_sync_2;
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            rst_sync_1 <= 1'b1;
            rst_sync_2 <= 1'b1;
        end else begin
            rst_sync_1 <= 1'b0;
            rst_sync_2 <= rst_sync_1;
        end
    end
    wire sync_rst = rst_sync_2;

    uart_tx tx_inst (
        .clk(clk),
        .rst(sync_rst),
        .tx_start(tx_start),
        .tx_data(tx_data),
        .tx(tx),
        .tx_busy(tx_busy)
    );

    uart_rx rx_inst (
        .clk(clk),
        .rst(sync_rst),
        .rx(rx),
        .rx_data(rx_data),
        .rx_done(rx_done)
    );
endmodule
