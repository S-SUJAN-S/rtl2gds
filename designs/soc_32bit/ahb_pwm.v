module ahb_pwm (
    input wire HCLK,
    input wire HRESETn,
    input wire HSEL,
    input wire [31:0] HADDR,
    input wire [1:0] HTRANS,
    input wire HWRITE,
    input wire [2:0] HSIZE,
    input wire [2:0] HBURST,
    input wire [3:0] HPROT,
    input wire [31:0] HWDATA,
    input wire HREADY,

    output wire HREADYOUT,
    output wire HRESP,
    output wire [31:0] HRDATA,

    output wire [3:0] pwm_out
);

    // AHB-Lite FSM and signals
    reg [31:0] haddr_reg;
    reg hwrite_reg;
    reg hsel_reg;
    wire ahb_write_en;

    // AHB phase control
    always @(posedge HCLK or negedge HRESETn) begin
        if (!HRESETn) begin
            haddr_reg <= 32'd0;
            hwrite_reg <= 1'b0;
            hsel_reg <= 1'b0;
        end else if (HREADY) begin
            haddr_reg <= HADDR;
            hwrite_reg <= HWRITE;
            hsel_reg <= HSEL && (HTRANS[1]); // NONSEQ or SEQ
        end
    end

    assign ahb_write_en = hsel_reg & hwrite_reg;

    // Registers
    reg [31:0] ctrl;
    reg [31:0] ch0_period, ch0_duty;
    reg [31:0] ch1_period, ch1_duty;
    reg [31:0] ch2_period, ch2_duty;
    reg [31:0] ch3_period, ch3_duty;

    // Write logic
    always @(posedge HCLK or negedge HRESETn) begin
        if (!HRESETn) begin
            ctrl <= 32'd0;
            ch0_period <= 32'd0; ch0_duty <= 32'd0;
            ch1_period <= 32'd0; ch1_duty <= 32'd0;
            ch2_period <= 32'd0; ch2_duty <= 32'd0;
            ch3_period <= 32'd0; ch3_duty <= 32'd0;
        end else if (ahb_write_en) begin
            case (haddr_reg[7:0])
                8'h00: ctrl <= HWDATA;
                8'h10: ch0_period <= HWDATA;
                8'h14: ch0_duty <= HWDATA;
                8'h20: ch1_period <= HWDATA;
                8'h24: ch1_duty <= HWDATA;
                8'h30: ch2_period <= HWDATA;
                8'h34: ch2_duty <= HWDATA;
                8'h40: ch3_period <= HWDATA;
                8'h44: ch3_duty <= HWDATA;
                default: ;
            endcase
        end
    end

    // Read logic
    reg [31:0] hrdata_reg;
    always @(*) begin
        hrdata_reg = 32'd0;
        if (hsel_reg && !hwrite_reg) begin
            case (haddr_reg[7:0])
                8'h00: hrdata_reg = ctrl;
                8'h10: hrdata_reg = ch0_period;
                8'h14: hrdata_reg = ch0_duty;
                8'h20: hrdata_reg = ch1_period;
                8'h24: hrdata_reg = ch1_duty;
                8'h30: hrdata_reg = ch2_period;
                8'h34: hrdata_reg = ch2_duty;
                8'h40: hrdata_reg = ch3_period;
                8'h44: hrdata_reg = ch3_duty;
                default: hrdata_reg = 32'd0;
            endcase
        end
    end

    assign HRDATA = hrdata_reg;
    assign HREADYOUT = 1'b1; // Zero wait state for simple slave
    assign HRESP = 1'b0;     // OKAY

    // PWM Logic
    reg [31:0] count0, count1, count2, count3;
    reg pwm0_r, pwm1_r, pwm2_r, pwm3_r;

    wire [3:0] en = ctrl[3:0];

    // Channel 0
    always @(posedge HCLK or negedge HRESETn) begin
        if (!HRESETn) begin
            count0 <= 32'd0;
            pwm0_r <= 1'b0;
        end else if (en[0]) begin
            if (count0 >= ch0_period - 1)
                count0 <= 32'd0;
            else
                count0 <= count0 + 1'b1;

            pwm0_r <= (count0 < ch0_duty) ? 1'b1 : 1'b0;
        end else begin
            count0 <= 32'd0;
            pwm0_r <= 1'b0;
        end
    end

    // Channel 1
    always @(posedge HCLK or negedge HRESETn) begin
        if (!HRESETn) begin
            count1 <= 32'd0;
            pwm1_r <= 1'b0;
        end else if (en[1]) begin
            if (count1 >= ch1_period - 1)
                count1 <= 32'd0;
            else
                count1 <= count1 + 1'b1;

            pwm1_r <= (count1 < ch1_duty) ? 1'b1 : 1'b0;
        end else begin
            count1 <= 32'd0;
            pwm1_r <= 1'b0;
        end
    end

    // Channel 2
    always @(posedge HCLK or negedge HRESETn) begin
        if (!HRESETn) begin
            count2 <= 32'd0;
            pwm2_r <= 1'b0;
        end else if (en[2]) begin
            if (count2 >= ch2_period - 1)
                count2 <= 32'd0;
            else
                count2 <= count2 + 1'b1;

            pwm2_r <= (count2 < ch2_duty) ? 1'b1 : 1'b0;
        end else begin
            count2 <= 32'd0;
            pwm2_r <= 1'b0;
        end
    end

    // Channel 3
    always @(posedge HCLK or negedge HRESETn) begin
        if (!HRESETn) begin
            count3 <= 32'd0;
            pwm3_r <= 1'b0;
        end else if (en[3]) begin
            if (count3 >= ch3_period - 1)
                count3 <= 32'd0;
            else
                count3 <= count3 + 1'b1;

            pwm3_r <= (count3 < ch3_duty) ? 1'b1 : 1'b0;
        end else begin
            count3 <= 32'd0;
            pwm3_r <= 1'b0;
        end
    end

    assign pwm_out = {pwm3_r, pwm2_r, pwm1_r, pwm0_r};

endmodule
