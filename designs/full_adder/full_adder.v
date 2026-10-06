module full_adder (
    input  a,
    input  b,
    input  cin,
    output sum,
    output cout
);

    wire ab_xor;

    assign ab_xor = a ^ b;
    assign sum    = ab_xor ^ cin;
    assign cout   = (a & b) | (cin & ab_xor);

endmodule