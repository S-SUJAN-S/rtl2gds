module pe (
    input wire clk,
    input wire rst_n,
    
    input wire signed [7:0] act_in,
    input wire signed [31:0] psum_in,
    
    input wire weight_load_en,
    input wire signed [7:0] weight_in,
    
    output reg signed [7:0] act_out,
    output reg signed [31:0] psum_out
);

    reg signed [7:0] weight_reg;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            weight_reg <= 8'd0;
            act_out <= 8'd0;
            psum_out <= 32'd0;
        end else begin
            if (weight_load_en) begin
                weight_reg <= weight_in;
            end
            act_out <= act_in;
            psum_out <= psum_in + (act_in * weight_reg);
        end
    end
endmodule

module systolic_mm_accel (
    input wire clk,
    input wire rst_n,
    
    input wire weight_load_en,
    input wire [7:0] weight_data,
    input wire [5:0] weight_addr,
    
    input wire act_valid,
    input wire [63:0] act_data,
    output reg act_ready,
    
    output reg result_valid,
    output reg [255:0] result_data,
    input wire result_ready
);

    // FSM States
    localparam IDLE = 3'd0;
    localparam LOAD_WEIGHTS = 3'd1;
    localparam COMPUTE = 3'd2;
    localparam DRAIN = 3'd3;
    localparam DONE = 3'd4;
    
    reg [2:0] state, next_state;
    reg [4:0] counter, next_counter;
    
    // PE Array Wires
    wire signed [7:0] act_wires [0:8][0:8];   
    wire signed [31:0] psum_wires [0:8][0:8]; 
    
    // Input Skewing Registers
    reg signed [7:0] skew_in [0:7][0:7];
    
    integer r1, d1;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (r1 = 0; r1 < 8; r1 = r1 + 1) begin
                for (d1 = 0; d1 < 8; d1 = d1 + 1) begin
                    skew_in[r1][d1] <= 8'd0;
                end
            end
        end else begin
            if (act_valid && act_ready) begin
                for (r1 = 0; r1 < 8; r1 = r1 + 1) begin
                    skew_in[r1][0] <= act_data[(r1*8)+7 -: 8];
                    for (d1 = 1; d1 <= r1; d1 = d1 + 1) begin
                        skew_in[r1][d1] <= skew_in[r1][d1-1];
                    end
                end
            end else begin
                // Shift 0s when not feeding valid data
                for (r1 = 0; r1 < 8; r1 = r1 + 1) begin
                    skew_in[r1][0] <= 8'd0;
                    for (d1 = 1; d1 <= r1; d1 = d1 + 1) begin
                        skew_in[r1][d1] <= skew_in[r1][d1-1];
                    end
                end
            end
        end
    end
    
    // Output Deskewing Registers
    reg signed [31:0] deskew_out [0:7][0:7];
    
    integer r2, d2;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (r2 = 0; r2 < 8; r2 = r2 + 1) begin
                for (d2 = 0; d2 < 8; d2 = d2 + 1) begin
                    deskew_out[r2][d2] <= 32'd0;
                end
            end
        end else begin
            for (r2 = 0; r2 < 8; r2 = r2 + 1) begin
                deskew_out[r2][0] <= psum_wires[8][r2];
                for (d2 = 1; d2 <= (7-r2); d2 = d2 + 1) begin
                    deskew_out[r2][d2] <= deskew_out[r2][d2-1];
                end
            end
        end
    end
    
    genvar i, j;
    generate
        for (i = 0; i < 8; i = i + 1) begin : row_inputs
            assign act_wires[i][0] = skew_in[i][i]; 
        end
        for (j = 0; j < 8; j = j + 1) begin : col_inputs
            assign psum_wires[0][j] = 32'd0;
        end
    endgenerate
    
    // Instantiate 8x8 PE Grid
    generate
        for (i = 0; i < 8; i = i + 1) begin : row_pe
            for (j = 0; j < 8; j = j + 1) begin : col_pe
                
                wire pe_weight_load = weight_load_en && (weight_addr == (i*8 + j));
                
                pe pe_inst (
                    .clk(clk),
                    .rst_n(rst_n),
                    .act_in(act_wires[i][j]),
                    .psum_in(psum_wires[i][j]),
                    .weight_load_en(pe_weight_load),
                    .weight_in(weight_data),
                    .act_out(act_wires[i][j+1]),
                    .psum_out(psum_wires[i+1][j])
                );
            end
        end
    endgenerate

    // FSM Logic
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            counter <= 5'd0;
            result_data <= 256'd0;
        end else begin
            state <= next_state;
            counter <= next_counter;
            
            // Capture aligned deskewed results at the end of DRAIN
            if (state == DRAIN && counter == 5'd15) begin
                result_data[ 31:  0] <= deskew_out[0][7];
                result_data[ 63: 32] <= deskew_out[1][6];
                result_data[ 95: 64] <= deskew_out[2][5];
                result_data[127: 96] <= deskew_out[3][4];
                result_data[159:128] <= deskew_out[4][3];
                result_data[191:160] <= deskew_out[5][2];
                result_data[223:192] <= deskew_out[6][1];
                result_data[255:224] <= deskew_out[7][0];
            end
        end
    end
    
    always @(*) begin
        next_state = state;
        next_counter = counter;
        act_ready = 1'b0;
        result_valid = 1'b0;
        
        case (state)
            IDLE: begin
                if (weight_load_en) begin
                    next_state = LOAD_WEIGHTS;
                end else if (act_valid) begin
                    next_state = COMPUTE;
                    next_counter = 5'd1;
                    act_ready = 1'b1;
                end
            end
            LOAD_WEIGHTS: begin
                if (!weight_load_en) begin
                    next_state = IDLE;
                end
            end
            COMPUTE: begin
                if (counter < 5'd8) begin
                    next_counter = counter + 1'b1;
                    act_ready = 1'b1;
                end else begin
                    next_state = DRAIN;
                    next_counter = 5'd0;
                end
            end
            DRAIN: begin
                if (counter < 5'd16) begin
                    next_counter = counter + 1'b1;
                end else begin
                    next_state = DONE;
                end
            end
            DONE: begin
                result_valid = 1'b1;
                if (result_ready) begin
                    next_state = IDLE;
                end
            end
            default: next_state = IDLE;
        endcase
    end

endmodule
