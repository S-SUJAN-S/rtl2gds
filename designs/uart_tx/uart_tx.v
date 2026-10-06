module uart_tx (
    input clk,
    input rst,
    input [7:0] tx_data,
    input tx_valid,
    output reg tx_ready,
    output reg tx
);

    parameter CLK_FREQ = 50000000;
    parameter BAUD_RATE = 115200;
    localparam BIT_PERIOD = CLK_FREQ / BAUD_RATE;
    localparam BIT_CNT_MAX = BIT_PERIOD - 1;

    // FSM states
    localparam [1:0] IDLE  = 2'd0;
    localparam [1:0] START = 2'd1;
    localparam [1:0] DATA  = 2'd2;
    localparam [1:0] STOP  = 2'd3;

    reg [1:0] state, next_state;
    reg [7:0] shift_reg;
    reg [3:0] bit_idx;
    reg [15:0] bit_cnt;

    // Next state logic
    always @(*) begin
        next_state = state;
        case (state)
            IDLE: begin
                if (tx_valid)
                    next_state = START;
            end
            START: begin
                if (bit_cnt == BIT_CNT_MAX)
                    next_state = DATA;
            end
            DATA: begin
                if (bit_cnt == BIT_CNT_MAX) begin
                    if (bit_idx == 4'd7)
                        next_state = STOP;
                    else
                        next_state = DATA;
                end
            end
            STOP: begin
                if (bit_cnt == BIT_CNT_MAX)
                    next_state = IDLE;
            end
            default: next_state = IDLE;
        endcase
    end

    // State register and sequential logic
    always @(posedge clk) begin
        if (rst) begin
            state <= IDLE;
            tx <= 1'b1;
            tx_ready <= 1'b1;
            shift_reg <= 8'd0;
            bit_idx <= 4'd0;
            bit_cnt <= 16'd0;
        end else begin
            state <= next_state;

            case (state)
                IDLE: begin
                    tx <= 1'b1;
                    tx_ready <= 1'b1;
                    bit_cnt <= 16'd0;
                    bit_idx <= 4'd0;
                    if (tx_valid) begin
                        shift_reg <= tx_data;
                        tx_ready <= 1'b0;
                    end
                end

                START: begin
                    tx <= 1'b0;
                    if (bit_cnt == BIT_CNT_MAX) begin
                        bit_cnt <= 16'd0;
                        bit_idx <= 4'd0;
                        tx <= shift_reg[0];
                    end else begin
                        bit_cnt <= bit_cnt + 16'd1;
                    end
                end

                DATA: begin
                    if (bit_cnt == BIT_CNT_MAX) begin
                        bit_cnt <= 16'd0;
                        if (bit_idx == 4'd7) begin
                            tx <= 1'b1;
                        end else begin
                            tx <= shift_reg[bit_idx + 4'd1];
                            bit_idx <= bit_idx + 4'd1;
                        end
                    end else begin
                        bit_cnt <= bit_cnt + 16'd1;
                    end
                end

                STOP: begin
                    tx <= 1'b1;
                    if (bit_cnt == BIT_CNT_MAX) begin
                        bit_cnt <= 16'd0;
                        tx_ready <= 1'b1;
                    end else begin
                        bit_cnt <= bit_cnt + 16'd1;
                    end
                end

                default: begin
                    tx <= 1'b1;
                    tx_ready <= 1'b1;
                    bit_cnt <= 16'd0;
                    bit_idx <= 4'd0;
                end
            endcase
        end
    end

endmodule