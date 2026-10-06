module alu4bit(
  input [3:0] a,
  input [3:0] b,
  input [2:0] opcode,
  output reg [3:0] result,
  output zero,
  output carry_out
);

  wire [3:0] sum;
  wire [4:0] shift_result;
  
  assign {carry_out, sum} = a + b;
  assign shift_result = $signed(b) >>> opcode[1:0];
  
  always @* begin
    case (opcode[2:0])
      3'b000: result = a & b; // AND operation
      3'b001: result = a | b; // OR operation
      3'b010: result = ~a; // NOT operation on first operand
      3'b011: result = ~(a ^ b); // XNOR operation
      3'b100: result = sum[4]; // ADD operation
      3'b101: result = $signed(sum) < 0; // SUBTRACT operation
      3'b110: result = shift_result[3:0]; // SHIFT LEFT operation
      3'b111: result = {shift_result[4], shift_result[3:0]}; // SHIFT RIGHT operation
      default: result = 4'bxxxx; // Invalid opcode
    endcase
  end
  
  assign zero = (result == 4'b0);
  
endmodule