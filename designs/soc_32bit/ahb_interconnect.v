`timescale 1ns/1ps

module ahb_interconnect (
    input wire hclk,
    input wire hresetn,

    // Master interface
    input wire [31:0] hmaster_addr,
    input wire [1:0]  hmaster_trans,
    input wire        hmaster_write,
    input wire [2:0]  hmaster_size,
    input wire [2:0]  hmaster_burst,
    input wire [3:0]  hmaster_prot,
    input wire [31:0] hmaster_wdata,
    output wire [31:0] hmaster_rdata,
    output wire        hmaster_ready,
    output wire        hmaster_resp,

    // Slave interfaces
    // GPIO
    output wire        hsel_gpio,
    input  wire [31:0] hrdata_gpio,
    input  wire        hready_gpio,
    input  wire        hresp_gpio,

    // UART
    output wire        hsel_uart,
    input  wire [31:0] hrdata_uart,
    input  wire        hready_uart,
    input  wire        hresp_uart,

    // SPI
    output wire        hsel_spi,
    input  wire [31:0] hrdata_spi,
    input  wire        hready_spi,
    input  wire        hresp_spi,

    // I2C
    output wire        hsel_i2c,
    input  wire [31:0] hrdata_i2c,
    input  wire        hready_i2c,
    input  wire        hresp_i2c,

    // PWM
    output wire        hsel_pwm,
    input  wire [31:0] hrdata_pwm,
    input  wire        hready_pwm,
    input  wire        hresp_pwm,

    // Timer
    output wire        hsel_timer,
    input  wire [31:0] hrdata_timer,
    input  wire        hready_timer,
    input  wire        hresp_timer,

    // Watchdog
    output wire        hsel_wdt,
    input  wire [31:0] hrdata_wdt,
    input  wire        hready_wdt,
    input  wire        hresp_wdt,

    // INTC
    output wire        hsel_intc,
    input  wire [31:0] hrdata_intc,
    input  wire        hready_intc,
    input  wire        hresp_intc,

    // RSTMGR
    output wire        hsel_rstmgr,
    input  wire [31:0] hrdata_rstmgr,
    input  wire        hready_rstmgr,
    input  wire        hresp_rstmgr,

    // Shared signals for all slaves
    output wire [31:0] hslv_addr,
    output wire [1:0]  hslv_trans,
    output wire        hslv_write,
    output wire [2:0]  hslv_size,
    output wire [2:0]  hslv_burst,
    output wire [3:0]  hslv_prot,
    output wire [31:0] hslv_wdata,
    output wire        hslv_ready_in
);

    // Address decoding
    // 0x4000_0000 + 64KB offsets
    wire [31:0] addr = hmaster_addr;
    wire sel_gpio   = (addr >= 32'h4000_0000 && addr < 32'h4001_0000);
    wire sel_uart   = (addr >= 32'h4001_0000 && addr < 32'h4002_0000);
    wire sel_spi    = (addr >= 32'h4002_0000 && addr < 32'h4003_0000);
    wire sel_i2c    = (addr >= 32'h4003_0000 && addr < 32'h4004_0000);
    wire sel_pwm    = (addr >= 32'h4004_0000 && addr < 32'h4005_0000);
    wire sel_timer  = (addr >= 32'h4005_0000 && addr < 32'h4006_0000);
    wire sel_wdt    = (addr >= 32'h4006_0000 && addr < 32'h4007_0000);
    wire sel_intc   = (addr >= 32'h4007_0000 && addr < 32'h4008_0000);
    wire sel_rstmgr = (addr >= 32'h4008_0000 && addr < 32'h4009_0000);

    assign hsel_gpio   = sel_gpio;
    assign hsel_uart   = sel_uart;
    assign hsel_spi    = sel_spi;
    assign hsel_i2c    = sel_i2c;
    assign hsel_pwm    = sel_pwm;
    assign hsel_timer  = sel_timer;
    assign hsel_wdt    = sel_wdt;
    assign hsel_intc   = sel_intc;
    assign hsel_rstmgr = sel_rstmgr;

    // Shared signals to slaves
    assign hslv_addr = hmaster_addr;
    assign hslv_trans = hmaster_trans;
    assign hslv_write = hmaster_write;
    assign hslv_size = hmaster_size;
    assign hslv_burst = hmaster_burst;
    assign hslv_prot = hmaster_prot;
    assign hslv_wdata = hmaster_wdata;
    
    // AHB requires tracking which slave is selected during data phase
    reg [3:0] active_slave;
    always @(posedge hclk or negedge hresetn) begin
        if (!hresetn) begin
            active_slave <= 4'd0;
        end else if (hmaster_ready) begin
            if (sel_gpio)   active_slave <= 4'd1;
            else if (sel_uart)   active_slave <= 4'd2;
            else if (sel_spi)    active_slave <= 4'd3;
            else if (sel_i2c)    active_slave <= 4'd4;
            else if (sel_pwm)    active_slave <= 4'd5;
            else if (sel_timer)  active_slave <= 4'd6;
            else if (sel_wdt)    active_slave <= 4'd7;
            else if (sel_intc)   active_slave <= 4'd8;
            else if (sel_rstmgr) active_slave <= 4'd9;
            else                 active_slave <= 4'd0;
        end
    end

    // Mux read data and responses
    reg [31:0] mux_rdata;
    reg        mux_ready;
    reg        mux_resp;

    always @(*) begin
        case (active_slave)
            4'd1: begin mux_rdata = hrdata_gpio;   mux_ready = hready_gpio;   mux_resp = hresp_gpio; end
            4'd2: begin mux_rdata = hrdata_uart;   mux_ready = hready_uart;   mux_resp = hresp_uart; end
            4'd3: begin mux_rdata = hrdata_spi;    mux_ready = hready_spi;    mux_resp = hresp_spi; end
            4'd4: begin mux_rdata = hrdata_i2c;    mux_ready = hready_i2c;    mux_resp = hresp_i2c; end
            4'd5: begin mux_rdata = hrdata_pwm;    mux_ready = hready_pwm;    mux_resp = hresp_pwm; end
            4'd6: begin mux_rdata = hrdata_timer;  mux_ready = hready_timer;  mux_resp = hresp_timer; end
            4'd7: begin mux_rdata = hrdata_wdt;    mux_ready = hready_wdt;    mux_resp = hresp_wdt; end
            4'd8: begin mux_rdata = hrdata_intc;   mux_ready = hready_intc;   mux_resp = hresp_intc; end
            4'd9: begin mux_rdata = hrdata_rstmgr; mux_ready = hready_rstmgr; mux_resp = hresp_rstmgr; end
            default: begin mux_rdata = 32'h0;      mux_ready = 1'b1;          mux_resp = 1'b0; end // Default ready, no error
        endcase
    end

    assign hmaster_rdata = mux_rdata;
    assign hmaster_ready = mux_ready;
    assign hmaster_resp  = mux_resp;
    assign hslv_ready_in = mux_ready;

endmodule
