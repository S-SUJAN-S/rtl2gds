module full_adder (
  input a, b, cin,
  output sum, cout
);

  assign sum = a ^ b ^ cin;
  assign cout = (a & b) | (cin & (a ^ b));
  
endmodule