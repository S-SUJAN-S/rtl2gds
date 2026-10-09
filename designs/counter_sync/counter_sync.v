module counter_sync (
    input clk,
    input rst,
    input load,
    input enable,
    input up_down,
    input [7:0] data_in,
    output reg [7:0] count,
    output reg terminal_count
);

    always @(posedge clk) begin
        if (rst) begin
            count <= 8'd0;
            terminal_count <= 1'b0;
        end else if (load) begin
            count <= data_in;
            terminal_count <= 1'b0;
        end else if (enable) begin
            if (up_down) begin
                count <= count + 8'd1;
                terminal_count <= ((count + 8'd1) == 8'hFF);
            end else begin
                count <= count - 8'd1;
                terminal_count <= ((count - 8'd1) == 8'h00);
            end
        end else begin
            count <= count;
            terminal_count <= 1'b0;
        end
    end

endmodule