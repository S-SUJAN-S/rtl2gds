module sync_fifo(
    input clk, // System clock
    input rst, // Active-high reset
    input wr_en, // Write enable signal
    input rd_en, // Read enable signal
    input [7:0] data_in, // Data to be written into the FIFO
    output [7:0] data_out, // Data read from the FIFO
    output wire full, // Indicates if the FIFO is full
    output wire empty // Indicates if the Fifo is empty
);

parameter WIDTH = 8;
parameter DEPTH = 16;

reg [WIDTH-1:0] mem [0:DEPTH-1];
reg [3:0] wr_ptr, rd_ptr;
wire full = (wr_ptr == ((rd_ptr + 1) % DEPTH)) ? 1'b1 : 1'b0;
wire empty = (wr_ptr == rd_ptr) ? 1'b1 : 1'b0;
reg [7:0] data_out_reg;

always @(posedge clk, posedge rst) begin
    if (rst) begin
        wr_ptr <= 4'h0;
        rd_ptr <= 4'h0;
        full <= 1'b0;
        empty <= 1'b1;
    end else begin
        case({wr_en, rd_en})
            2'b01: // Reading from FIFO
                if (!empty) begin
                    data_out_reg <= mem[rd_ptr];
                    rd_ptr <= (rd_ptr + 1) % DEPTH;
                    empty <= ((wr_ptr == ((rd_ptr + 1) % DEPTH)) ? 1'b1 : 1'b0);
                end
            2'b10: // Writing to FIFO
                if (!full) begin
                    mem[wr_ptr] <= data_in;
                    wr_ptr <= (wr_ptr + 1) % DEPTH;
                    full <= ((wr_ptr == ((rd_ptr + 1) % DEPTH)) ? 1'b1 : 1'b0);
                end
            2'b11: // Reading and Writing to FIFO
                if (!empty && !full) begin
                    data_out_reg <= mem[rd_ptr];
                    rd_ptr <= (rd_ptr + 1) % DEPTH;
                    empty <= ((wr_ptr == ((rd_ptr + 1) % DEPTH)) ? 1'b1 : 1'b0);
                end
            default: ; // Do nothing
        endcase
    end
end

assign data_out = (empty) ? 'hx : data_out_reg;

endmodule