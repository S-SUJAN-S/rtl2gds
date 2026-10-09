module barrel_shifter_8bit (
    input  [7:0] data_in,
    input  [2:0] shift_amt,
    input  shift_right,
    output reg [7:0] data_out
);

    always @(*) begin
        if (shift_right) begin
            data_out = data_in >> shift_amt;
        end else begin
            data_out = data_in << shift_amt;
        end
    end

endmodule