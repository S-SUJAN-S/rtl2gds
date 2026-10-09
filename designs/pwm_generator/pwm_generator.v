module pwm_generator (
    input clk,
    input rst,
    input [7:0] duty,
    input [7:0] period,
    output reg pwm_out
);

    reg [7:0] counter;
    reg [7:0] duty_reg;
    reg [7:0] period_reg;

    always @(posedge clk) begin
        if (rst) begin
            counter <= 8'd0;
            duty_reg <= 8'd0;
            period_reg <= 8'd0;
            pwm_out <= 1'b0;
        end else begin
            // Update double-buffered registers on period rollover or when period_reg is 0
            if (counter + 1 >= period_reg || period_reg == 8'd0) begin
                duty_reg <= duty;
                period_reg <= period;
            end

            // Counter logic
            if (counter + 1 >= period_reg || period_reg == 8'd0) begin
                counter <= 8'd0;
            end else begin
                counter <= counter + 1;
            end

            // PWM output logic
            if (duty_reg > 8'd0 && (counter < duty_reg || duty_reg >= period_reg)) begin
                pwm_out <= 1'b1;
            end else begin
                pwm_out <= 1'b0;
            end
        end
    end

endmodule