module sync_fifo (
    input clk,
    input rst,
    input wr_en,
    input rd_en,
    input [7:0] data_in,
    output [7:0] data_out,
    output full,
    output empty
);

    localparam DATA_WIDTH = 8;
    localparam FIFO_DEPTH = 16;
    localparam PTR_WIDTH = 4; // log2(16)

    reg [DATA_WIDTH-1:0] mem [0:FIFO_DEPTH-1];
    reg [PTR_WIDTH-1:0] wr_ptr;
    reg [PTR_WIDTH-1:0] rd_ptr;
    reg [DATA_WIDTH-1:0] data_out_reg;

    assign full  = ((wr_ptr + 1'b1) % FIFO_DEPTH) == rd_ptr;
    assign empty = (wr_ptr == rd_ptr);
    assign data_out = data_out_reg;

    always @(posedge clk) begin
        if (rst) begin
            wr_ptr <= 0;
            rd_ptr <= 0;
            data_out_reg <= 0;
        end else begin
            if (wr_en && !full) begin
                mem[wr_ptr] <= data_in;
                wr_ptr <= (wr_ptr + 1) % FIFO_DEPTH;
            end

            if (rd_en && !empty) begin
                data_out_reg <= mem[rd_ptr];
                rd_ptr <= (rd_ptr + 1) % FIFO_DEPTH;
            end
        end
    end

endmodule