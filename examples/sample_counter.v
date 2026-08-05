// Sample Synthesizable Verilog Module: Up-Down Counter with Asynchronous Reset
module sample_counter #(
    parameter WIDTH = 8
)(
    input  wire             clk,
    input  wire             rst_n,
    input  wire             enable,
    input  wire             up_down, // 1: Up, 0: Down
    output reg  [WIDTH-1:0] count
);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count <= {WIDTH{1'b0}};
        end else if (enable) begin
            if (up_down) begin
                count <= count + 1'b1;
            end else begin
                count <= count - 1'b1;
            end
        end
    end

endmodule
