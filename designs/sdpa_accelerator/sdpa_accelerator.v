`timescale 1ns / 1ps

module sdpa_accelerator (
    input wire clk,
    input wire rst_n,
    input wire start,
    input wire [31:0] Q_in, // 2x2 matrix, 8-bit elements.
    input wire [31:0] K_in,
    input wire [31:0] V_in,
    
    output reg [31:0] Z_out,
    output reg valid
);

    // Unpack inputs into 2D arrays
    wire signed [7:0] Q [0:1][0:1];
    wire signed [7:0] K [0:1][0:1];
    wire signed [7:0] V [0:1][0:1];

    genvar i, j;
    generate
        for (i = 0; i < 2; i = i + 1) begin : unpack_row
            for (j = 0; j < 2; j = j + 1) begin : unpack_col
                assign Q[i][j] = Q_in[((1-i)*2 + (1-j))*8 +: 8];
                assign K[i][j] = K_in[((1-i)*2 + (1-j))*8 +: 8];
                assign V[i][j] = V_in[((1-i)*2 + (1-j))*8 +: 8];
            end
        end
    endgenerate

    // ==========================================
    // STAGE 1: Score Matrix S = Q * K^T
    // ==========================================
    reg signed [15:0] S_reg [0:1][0:1];
    reg s1_valid;
    reg [31:0] V_pipe_s1;

    integer r1, c1;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s1_valid <= 1'b0;
            for (r1 = 0; r1 < 2; r1 = r1 + 1) begin
                for (c1 = 0; c1 < 2; c1 = c1 + 1) begin
                    S_reg[r1][c1] <= 16'd0;
                end
            end
            V_pipe_s1 <= 32'd0;
        end else begin
            s1_valid <= start;
            V_pipe_s1 <= V_in;
            if (start) begin
                for (r1 = 0; r1 < 2; r1 = r1 + 1) begin
                    for (c1 = 0; c1 < 2; c1 = c1 + 1) begin
                        S_reg[r1][c1] <= Q[r1][0]*K[c1][0] + 
                                         Q[r1][1]*K[c1][1];
                    end
                end
            end
        end
    end

    // ==========================================
    // STAGE 2: Max & Softmax Base-2 Approximation
    // ==========================================
    reg [7:0] P_reg [0:1][0:1];
    reg s2_valid;
    reg [31:0] V_pipe_s2;

    wire signed [15:0] S_scale [0:1][0:1];
    wire signed [15:0] S_max [0:1];
    
    generate
        for (i = 0; i < 2; i = i + 1) begin : s2_math
            for (j = 0; j < 2; j = j + 1) begin : s2_scale
                assign S_scale[i][j] = S_reg[i][j] >>> 2; // scale factor
            end
            assign S_max[i] = (S_scale[i][0] > S_scale[i][1]) ? S_scale[i][0] : S_scale[i][1];
        end
    endgenerate

    integer r2, c2;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s2_valid <= 1'b0;
            for (r2 = 0; r2 < 2; r2 = r2 + 1) begin
                for (c2 = 0; c2 < 2; c2 = c2 + 1) begin
                    P_reg[r2][c2] <= 8'd0;
                end
            end
            V_pipe_s2 <= 32'd0;
        end else begin
            s2_valid <= s1_valid;
            V_pipe_s2 <= V_pipe_s1;
            
            if (s1_valid) begin
                for (r2 = 0; r2 < 2; r2 = r2 + 1) begin
                    for (c2 = 0; c2 < 2; c2 = c2 + 1) begin
                        if ((S_max[r2] - S_scale[r2][c2]) > 7) begin
                            P_reg[r2][c2] <= 8'd0;
                        end else begin
                            P_reg[r2][c2] <= 8'd127 >> (S_max[r2] - S_scale[r2][c2]);
                        end
                    end
                end
            end
        end
    end

    // ==========================================
    // STAGE 3: Context Matrix Z = P * V
    // ==========================================
    wire signed [7:0] V_stage3 [0:1][0:1];
    generate
        for (i = 0; i < 2; i = i + 1) begin : unpack_v_s3
            for (j = 0; j < 2; j = j + 1) begin : unpack_vc_s3
                assign V_stage3[i][j] = V_pipe_s2[((1-i)*2 + (1-j))*8 +: 8];
            end
        end
    endgenerate

    integer r3, c3;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            valid <= 1'b0;
            Z_out <= 32'd0;
        end else begin
            valid <= s2_valid;
            if (s2_valid) begin
                for (r3 = 0; r3 < 2; r3 = r3 + 1) begin
                    for (c3 = 0; c3 < 2; c3 = c3 + 1) begin
                        Z_out[((1-r3)*2 + (1-c3))*8 +: 8] <= (
                            $signed({1'b0, P_reg[r3][0]}) * V_stage3[0][c3] +
                            $signed({1'b0, P_reg[r3][1]}) * V_stage3[1][c3]
                        ) >> 7;
                    end
                end
            end
        end
    end

endmodule
