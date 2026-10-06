`timescale 1ns / 1ps

module sdpa_tb;

    reg clk;
    reg rst_n;
    reg start;
    reg [31:0] Q_in;
    reg [31:0] K_in;
    reg [31:0] V_in;
    
    wire [31:0] Z_out;
    wire valid;

    sdpa_accelerator uut (
        .clk(clk),
        .rst_n(rst_n),
        .start(start),
        .Q_in(Q_in),
        .K_in(K_in),
        .V_in(V_in),
        .Z_out(Z_out),
        .valid(valid)
    );

    // Clock gen
    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end

    // Helper macro to pack a 2x2 matrix of 8-bit values into 32 bits
    function [31:0] pack_matrix;
        input integer v00, v01;
        input integer v10, v11;
        begin
            pack_matrix = {
                v00[7:0], v01[7:0],
                v10[7:0], v11[7:0]
            };
        end
    endfunction

    initial begin
        $dumpfile("sdpa_tb.vcd");
        $dumpvars(0, sdpa_tb);

        rst_n = 0;
        start = 0;
        Q_in = 0;
        K_in = 0;
        V_in = 0;

        #20;
        rst_n = 1;
        #10;

        // Provide 2x2 matrices
        // Q: identity-ish
        Q_in = pack_matrix(
            16,  0,
             0, 16
        );

        // K: scaled
        K_in = pack_matrix(
             4,  0,
             0,  4
        );

        // V: incrementing values
        V_in = pack_matrix(
             1,  2,
             3,  4
        );

        start = 1;
        #10;
        start = 0;

        // Wait for pipeline (3 cycles)
        wait(valid == 1);
        
        $display("========================================");
        $display("Output Z Context Matrix [Row 0]: %d, %d", 
            $signed(Z_out[31-:8]), $signed(Z_out[23-:8]));
        $display("Output Z Context Matrix [Row 1]: %d, %d", 
            $signed(Z_out[15-:8]), $signed(Z_out[7-:8]));
        $display("========================================");

        #20;
        $finish;
    end

endmodule
