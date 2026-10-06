module fifo_16x32_deep (
    input clk,
    input rst,
    input wr_en,
    input [15:0] wr_data,
    input rd_en,
    output reg [15:0] rd_data,
    output almost_full,
    output almost_empty,
    output full,
    output empty
);

    parameter DATA_WIDTH = 16;
    parameter DEPTH = 32;
    parameter ALMOST_FULL_THRESHOLD = 28;
    parameter ALMOST_EMPTY_THRESHOLD = 4;
    localparam PTR_WIDTH = 5;

    reg [DATA_WIDTH-1:0] mem [0:DEPTH-1];
    reg [PTR_WIDTH-1:0] wr_ptr;
    reg [PTR_WIDTH-1:0] rd_ptr;
    reg [PTR_WIDTH:0] count;

    assign full = (count == DEPTH);
    assign empty = (count == 0);
    assign almost_full = (count >= ALMOST_FULL_THRESHOLD);
    assign almost_empty = (count <= ALMOST_EMPTY_THRESHOLD);

    always @(posedge clk) begin
        if (rst) begin
            wr_ptr  <= {PTR_WIDTH{1'b0}};
            rd_ptr  <= {PTR_WIDTH{1'b0}};
            count   <= {(PTR_WIDTH+1){1'b0}};
            rd_data <= {DATA_WIDTH{1'b0}};
        end else begin
            case ({wr_en && !full, rd_en && !empty})
                2'b10: begin
                    mem[wr_ptr] <= wr_data;
                    wr_ptr <= wr_ptr + 1'b1;
                    count  <= count + 1'b1;
                end
                2'b01: begin
                    rd_data <= mem[rd_ptr];
                    rd_ptr  <= rd_ptr + 1'b1;
                    count   <= count - 1'b1;
                end
                2'b11: begin
                    mem[wr_ptr] <= wr_data;
                    wr_ptr  <= wr_ptr + 1'b1;
                    rd_data <= mem[rd_ptr];
                    rd_ptr  <= rd_ptr + 1'b1;
                end
                default: ;
            endcase
        end
    end

endmodule