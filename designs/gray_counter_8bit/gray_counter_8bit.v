module gray_counter_8bit (
    input clk,
    input rst,
    input enable,
    output reg [7:0] gray_count
);

    reg [7:0] bin_count;

    always @(posedge clk) begin
        if (rst) begin
            bin_count <= 8'd0;
            gray_count <= 8'd0;
        end else if (enable) begin
            bin_count <= bin_count + 8'd1;
            gray_count <= (bin_count + 8'd1) ^ ((bin_count + 8'd1) >> 1);
        end
    end

endmodule