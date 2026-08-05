module alu4bit_tb;
    reg [3:0] a;
    reg [3:0] b;
    reg [2:0] op;
    wire [3:0] result;
    wire zero;

    alu4bit uut (
        .a(a),
        .b(b),
        .op(op),
        .result(result),
        .zero(zero)
    );

    initial begin
        $display("Testing 4-bit ALU");
        $monitor("Time=%0t | a=%b b=%b op=%b | result=%b zero=%b", $time, a, b, op, result, zero);

        a = 4'b0011; b = 4'b0001; // a=3, b=1
        
        op = 3'b000; #10; // ADD (3+1 = 4 -> 0100)
        op = 3'b001; #10; // SUB (3-1 = 2 -> 0010)
        op = 3'b010; #10; // AND (0011 & 0001 = 0001)
        op = 3'b011; #10; // OR  (0011 | 0001 = 0011)
        op = 3'b100; #10; // XOR (0011 ^ 0001 = 0010)
        op = 3'b101; #10; // NOT a (~0011 = 1100)
        op = 3'b110; #10; // SLL a (0011 << 1 = 0110)
        op = 3'b111; #10; // SRL a (0011 >> 1 = 0001)

        // Test Zero flag
        a = 4'b1010; b = 4'b1010;
        op = 3'b001; #10; // SUB (1010 - 1010 = 0000, zero=1)

        $display("ALU Test Complete.");
        $finish;
    end
endmodule
