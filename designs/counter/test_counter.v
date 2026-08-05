module test_counter (
    input wire clk,
    input wire rst,
    output reg [7:0] count
);

    always @(posedge clk or posedge rst) begin
        if (rst) begin
            count <= 8'b0;
        end else begin
            count <= count + 1;
        end
    end

endmodule
