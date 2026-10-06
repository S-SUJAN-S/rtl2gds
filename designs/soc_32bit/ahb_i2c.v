`timescale 1ns / 1ps
module ahb_i2c (
    input  wire        HCLK,
    input  wire        HRESETn,
    input  wire        HSEL,
    input  wire [31:0] HADDR,
    input  wire [1:0]  HTRANS,
    input  wire        HWRITE,
    input  wire [2:0]  HSIZE,
    input  wire [31:0] HWDATA,
    input  wire        HREADY,
    output wire        HREADYOUT,
    output wire [31:0] HRDATA,
    output wire        HRESP,
    
    // I2C Pins
    output wire        scl_o,
    output wire        scl_oen,
    input  wire        scl_i,
    output wire        sda_o,
    output wire        sda_oen,
    input  wire        sda_i
);

    // AHB Address Phase Registration
    reg [31:0] haddr_reg;
    reg        hwrite_reg;
    reg        hsel_reg;
    
    wire ahb_write = hsel_reg && hwrite_reg;
    wire ahb_read  = HSEL && !HWRITE && (HTRANS[1]);
    
    always @(posedge HCLK or negedge HRESETn) begin
        if (!HRESETn) begin
            haddr_reg  <= 32'h0;
            hwrite_reg <= 1'b0;
            hsel_reg   <= 1'b0;
        end else if (HREADY) begin
            haddr_reg  <= HADDR;
            hwrite_reg <= HWRITE;
            hsel_reg   <= HSEL && (HTRANS[1]);
        end
    end

    // Registers
    reg [15:0] prescale;
    reg [7:0]  tx_reg;
    reg [7:0]  rx_reg;
    reg        cmd_start;
    reg        cmd_stop;
    reg        cmd_read;
    reg        cmd_write;
    reg        cmd_ack;
    
    reg        stat_rxack;
    reg        stat_busy;
    reg        stat_al;
    reg        stat_tip;
    
    // AHB Write
    always @(posedge HCLK or negedge HRESETn) begin
        if (!HRESETn) begin
            prescale  <= 16'hffff;
            tx_reg    <= 8'h00;
            cmd_start <= 1'b0;
            cmd_stop  <= 1'b0;
            cmd_read  <= 1'b0;
            cmd_write <= 1'b0;
            cmd_ack   <= 1'b0;
        end else begin
            // self clear commands once transfer starts/ends
            if (stat_tip == 1'b0 && cmd_start == 1'b1) begin
                // wait for state machine to clear it, simple model self-clears eagerly
                // cmd_start <= 1'b0;
            end
            
            if (stat_tip == 1'b0 && (cmd_start || cmd_stop || cmd_read || cmd_write)) begin
                cmd_start <= 1'b0;
                cmd_stop  <= 1'b0;
                cmd_read  <= 1'b0;
                cmd_write <= 1'b0;
                cmd_ack   <= 1'b0;
            end

            if (ahb_write) begin
                case (haddr_reg[7:0])
                    8'h00: prescale[7:0]  <= HWDATA[7:0];
                    8'h04: prescale[15:8] <= HWDATA[7:0];
                    8'h08: tx_reg         <= HWDATA[7:0];
                    8'h0C: begin
                        cmd_start <= HWDATA[7];
                        cmd_stop  <= HWDATA[6];
                        cmd_read  <= HWDATA[5];
                        cmd_write <= HWDATA[4];
                        cmd_ack   <= HWDATA[3];
                    end
                    default: ;
                endcase
            end
        end
    end

    // AHB Read
    reg [31:0] hrdata_reg;
    always @(*) begin
        hrdata_reg = 32'h0;
        if (ahb_read) begin
            case (HADDR[7:0])
                8'h00: hrdata_reg = {24'h0, prescale[7:0]};
                8'h04: hrdata_reg = {24'h0, prescale[15:8]};
                8'h08: hrdata_reg = {24'h0, rx_reg};
                8'h0C: hrdata_reg = {24'h0, stat_rxack, stat_busy, stat_al, 4'h0, stat_tip};
                default: hrdata_reg = 32'h0;
            endcase
        end
    end
    assign HRDATA = hrdata_reg;
    assign HREADYOUT = 1'b1;
    assign HRESP = 1'b0;

    // I2C State Machine
    reg [2:0] bit_cnt;
    reg [4:0] state;
    
    reg sda_o_reg, scl_o_reg;
    reg sda_oen_reg, scl_oen_reg;
    
    assign sda_o = sda_o_reg;
    assign sda_oen = sda_oen_reg;
    assign scl_o = scl_o_reg;
    assign scl_oen = scl_oen_reg;

    reg [15:0] timer;
    
    always @(posedge HCLK or negedge HRESETn) begin
        if (!HRESETn) begin
            state <= 0;
            stat_tip <= 0;
            timer <= 0;
            sda_o_reg <= 1;
            sda_oen_reg <= 1;
            scl_o_reg <= 1;
            scl_oen_reg <= 1;
            bit_cnt <= 7;
            rx_reg <= 0;
            stat_rxack <= 0;
            stat_busy <= 0;
            stat_al <= 0;
        end else begin
            if (timer != 0) begin
                timer <= timer - 1;
            end else begin
                case (state)
                    0: begin // IDLE
                        stat_tip <= 0;
                        if (cmd_start) begin
                            state <= 1; // START
                            stat_tip <= 1;
                            timer <= prescale;
                            stat_busy <= 1;
                        end else if (cmd_write || cmd_read) begin
                            state <= 4; // DATA
                            stat_tip <= 1;
                            timer <= prescale;
                            bit_cnt <= 7;
                        end else if (cmd_stop) begin
                            state <= 10; // STOP
                            stat_tip <= 1;
                            timer <= prescale;
                        end
                    end
                    // START condition
                    1: begin sda_o_reg<=0; sda_oen_reg<=0; scl_oen_reg<=1; timer<=prescale; state<=2; end
                    2: begin scl_o_reg<=0; scl_oen_reg<=0; timer<=prescale; state<=0; end
                    
                    // DATA Transfer
                    4: begin // SCL Low, set SDA
                        scl_o_reg <= 0; scl_oen_reg <= 0;
                        if (cmd_write) begin
                            sda_o_reg <= tx_reg[bit_cnt];
                            sda_oen_reg <= 0;
                        end else begin
                            sda_oen_reg <= 1; // Release for read
                        end
                        timer <= prescale; state <= 5;
                    end
                    5: begin // SCL High
                        scl_oen_reg <= 1; timer <= prescale; state <= 6;
                    end
                    6: begin // Sample data
                        if (cmd_read) rx_reg[bit_cnt] <= sda_i;
                        timer <= prescale; state <= 7;
                    end
                    7: begin // SCL Low
                        scl_o_reg <= 0; scl_oen_reg <= 0;
                        if (bit_cnt == 0) begin
                            state <= 8; // ACK phase
                        end else begin
                            bit_cnt <= bit_cnt - 1;
                            state <= 4;
                        end
                        timer <= prescale;
                    end
                    
                    // ACK Phase
                    8: begin
                        scl_o_reg <= 0; scl_oen_reg <= 0;
                        if (cmd_write) begin
                            sda_oen_reg <= 1; // Release SDA to read ACK
                        end else begin
                            sda_o_reg <= cmd_ack; // Write ACK
                            sda_oen_reg <= 0;
                        end
                        timer <= prescale; state <= 9;
                    end
                    9: begin // SCL High, Sample ACK
                        scl_oen_reg <= 1;
                        if (cmd_write) stat_rxack <= sda_i;
                        timer <= prescale; state <= 0;
                    end
                    
                    // STOP condition
                    10: begin sda_o_reg<=0; sda_oen_reg<=0; scl_o_reg<=0; scl_oen_reg<=0; timer<=prescale; state<=11; end
                    11: begin scl_o_reg<=1; scl_oen_reg<=1; timer<=prescale; state<=12; end
                    12: begin sda_o_reg<=1; sda_oen_reg<=1; stat_busy<=0; timer<=prescale; state<=0; end
                    
                    default: state <= 0;
                endcase
            end
        end
    end

endmodule
