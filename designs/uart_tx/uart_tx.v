module uart_tx(
    input clk,
    input rst_n,
    input [7:0] tx_data,
    input tx_start,
    output reg tx,
    output reg tx_ready
);

    // Parameter for baud rate generation
    // Assuming a clock frequency and baud rate that results in a divisor of 100
    // For example: 100 MHz clock, 115200 baud -> ~867 cycles. 
    // Let's use a generic parameter for the bit period.
    parameter BIT_PERIOD = 100;

    localparam IDLE = 2'd0;
    localparam START = 2'd1;
    localparam DATA = 2'd2;
    localparam STOP = 2'd3;

    reg [1:0] state;
    reg [2:0] bit_idx;
    reg [7:0] shift_reg;
    reg [7:0] bit_cnt;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            tx <= 1'b1;
            tx_ready <= 1'b1;
            bit_idx <= 3'd0;
            shift_reg <= 8'd0;
            bit_cnt <= 8'd0;
        end else begin
            case (state)
                IDLE: begin
                    tx <= 1'b1;
                    tx_ready <= 1'b1;
                    if (tx_start) begin
                        state <= START;
                        tx_ready <= 1'b0;
                        shift_reg <= tx_data;
                        bit_idx <= 3'd0;
                        bit_cnt <= 8'd0;
                    end
                end
                START: begin
                    tx <= 1'b0;
                    if (bit_cnt == BIT_PERIOD - 1) begin
                        state <= DATA;
                        bit_cnt <= 8'd0;
                    end else begin
                        bit_cnt <= bit_cnt + 1'b1;
                    end
                end
                DATA: begin
                    tx <= shift_reg[0];
                    if (bit_cnt == BIT_PERIOD - 1) begin
                        bit_cnt <= 8'd0;
                        if (bit_idx == 3'd7) begin
                            state <= STOP;
                        end else begin
                            bit_idx <= bit_idx + 1'b1;
                            shift_reg <= {1'b0, shift_reg[7:1]};
                        end
                    end else begin
                        bit_cnt <= bit_cnt + 1'b1;
                    end
                end
                STOP: begin
                    tx <= 1'b1;
                    if (bit_cnt == BIT_PERIOD - 1) begin
                        state <= IDLE;
                        tx_ready <= 1'b1;
                    end else begin
                        bit_cnt <= bit_cnt + 1'b1;
                    end
                end
                default: begin
                    state <= IDLE;
                    tx <= 1'b1;
                    tx_ready <= 1'b1;
                end
            endcase
        end
    end

endmodule