module alu4bit(
    input  [3:0] a,
    input  [3:0] b,
    input  [2:0] opcode,
    output reg [3:0] result,
    output zero,
    output reg carry_out
);

    always @(*) begin
        result = 4'b0;
        carry_out = 1'b0;
        case (opcode)
            3'd0: begin
                {carry_out, result} = a + b;
            end
            3'd1: begin
                {carry_out, result} = {1'b0, a} - {1'b0, b};
            end
            3'd2: begin
                result = a & b;
                carry_out = 1'b0;
            end
            3'd3: begin
                result = a | b;
                carry_out = 1'b0;
            end
            3'd4: begin
                result = a ^ b;
                carry_out = 1'b0;
            end
            3'd5: begin
                result = ~a;
                carry_out = 1'b0;
            end
            3'd6: begin
                result = a << 1;
                carry_out = a[3];
            end
            3'd7: begin
                result = a >> 1;
                carry_out = a[0];
            end
            default: begin
                result = 4'b0;
                carry_out = 1'b0;
            end
        endcase
    end

    assign zero = (result == 4'b0);

endmodule