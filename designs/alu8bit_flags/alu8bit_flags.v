module alu8bit_flags (
    input  [7:0] a,
    input  [7:0] b,
    input  [3:0] op,
    output reg [7:0] result,
    output zero,
    output reg carry,
    output reg overflow,
    output negative
);

    wire [8:0] add_ext = {1'b0, a} + {1'b0, b};
    wire [8:0] sub_ext = {1'b0, a} - {1'b0, b};
    wire [15:0] mul_ext = a * b;

    always @(*) begin
        result   = 8'd0;
        carry    = 1'b0;
        overflow = 1'b0;

        case (op)
            4'd0: begin // ADD
                result   = add_ext[7:0];
                carry    = add_ext[8];
                overflow = (a[7] == b[7]) && (a[7] != result[7]);
            end
            4'd1: begin // SUB
                result   = sub_ext[7:0];
                carry    = sub_ext[8]; // borrow
                overflow = (a[7] != b[7]) && (a[7] != result[7]);
            end
            4'd2: begin // MUL_LOW
                result   = mul_ext[7:0];
                carry    = (mul_ext[15:8] != 8'd0);
                overflow = (mul_ext[15:8] != 8'd0);
            end
            4'd3: begin // AND
                result = a & b;
            end
            4'd4: begin // OR
                result = a | b;
            end
            4'd5: begin // XOR
                result = a ^ b;
            end
            4'd6: begin // SHL
                result = a << 1;
                carry  = a[7];
            end
            4'd7: begin // SHR
                result = a >> 1;
                carry  = a[0];
            end
            default: begin
                result = 8'd0;
            end
        endcase
    end

    assign zero     = (result == 8'd0);
    assign negative = result[7];

endmodule