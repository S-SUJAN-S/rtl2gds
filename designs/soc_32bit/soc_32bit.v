`timescale 1ns/1ps

module soc_32bit (
    input  wire        clk,
    input  wire        resetn,

    // GPIO
    inout  wire [31:0] gpio_pins,
    
    // UART
    output wire        uart_tx,
    input  wire        uart_rx,
    
    // SPI
    output wire        spi_sck,
    output wire        spi_mosi,
    input  wire        spi_miso,
    output wire        spi_cs_n,
    
    // I2C
    output wire        i2c_scl_o,
    output wire        i2c_scl_oen,
    input  wire        i2c_scl_i,
    output wire        i2c_sda_o,
    output wire        i2c_sda_oen,
    input  wire        i2c_sda_i,
    
    // PWM
    output wire [3:0]  pwm_out
);

    // Master Signals (Driven by dummy CPU for now)
    wire [31:0] hmaster_addr;
    wire [1:0]  hmaster_trans;
    wire        hmaster_write;
    wire [2:0]  hmaster_size;
    wire [2:0]  hmaster_burst;
    wire [3:0]  hmaster_prot;
    wire [31:0] hmaster_wdata;
    wire [31:0] hmaster_rdata;
    wire        hmaster_ready;
    wire        hmaster_resp;

    // Interconnect to Slave Signals
    wire        hsel_gpio, hsel_uart, hsel_spi, hsel_i2c, hsel_pwm;
    wire        hsel_timer, hsel_watchdog, hsel_intc, hsel_rstmgr;
    
    wire [31:0] hrdata_gpio, hrdata_uart, hrdata_spi, hrdata_i2c, hrdata_pwm;
    wire [31:0] hrdata_timer, hrdata_watchdog, hrdata_intc, hrdata_rstmgr;
    
    wire        hreadyout_gpio, hreadyout_uart, hreadyout_spi, hreadyout_i2c, hreadyout_pwm;
    wire        hreadyout_timer, hreadyout_watchdog, hreadyout_intc, hreadyout_rstmgr;
    
    wire        hresp_gpio;
    wire [1:0]  hresp_uart, hresp_spi;
    wire        hresp_i2c, hresp_pwm;
    wire        hresp_timer;
    wire [1:0]  hresp_watchdog;
    wire        hresp_intc, hresp_rstmgr;
    
    wire [31:0] hslv_addr;
    wire [1:0]  hslv_trans;
    wire        hslv_write;
    wire [2:0]  hslv_size;
    wire [2:0]  hslv_burst;
    wire [3:0]  hslv_prot;
    wire [31:0] hslv_wdata;
    wire        hslv_ready_in;

    // Peripheral-to-INTC IRQ lines
    wire        irq_uart, irq_spi, irq_timer, irq_watchdog;
    wire [7:0]  irq_bus = {4'b0000, irq_watchdog, irq_timer, irq_spi, irq_uart};
    wire        cpu_irq;

    // Reset lines
    wire [31:0] soft_rst_n;
    wire        rst_gpio     = resetn & soft_rst_n[0];
    wire        rst_uart     = resetn & soft_rst_n[1];
    wire        rst_spi      = resetn & soft_rst_n[2];
    wire        rst_i2c      = resetn & soft_rst_n[3];
    wire        rst_pwm      = resetn & soft_rst_n[4];
    wire        rst_timer    = resetn & soft_rst_n[5];
    wire        rst_watchdog = resetn; // Cannot soft reset watchdog
    wire        rst_intc     = resetn & soft_rst_n[7];
    wire        sys_rst      = resetn & (~wdg_rst); // Watchdog resets system
    wire        wdg_rst;

    // Clock gating (from rstmgr)
    wire [31:0] clk_en;
    wire        clk_gpio     = clk; // Simplified
    wire        clk_uart     = clk;
    wire        clk_spi      = clk;
    wire        clk_i2c      = clk;
    wire        clk_pwm      = clk;
    wire        clk_timer    = clk;
    wire        clk_watchdog = clk;
    wire        clk_intc     = clk;

    // Dummy CPU Master
    assign hmaster_addr  = 32'h4000_0000;
    assign hmaster_trans = 2'h0; // IDLE
    assign hmaster_write = 1'b0;
    assign hmaster_size  = 3'h2;
    assign hmaster_burst = 3'h0;
    assign hmaster_prot  = 4'h3;
    assign hmaster_wdata = 32'h0;

    // AHB-Lite Interconnect
    ahb_interconnect u_ahb_ic (
        .hclk          (clk),
        .hresetn       (sys_rst),
        
        // Master Ports
        .hmaster_addr  (hmaster_addr),
        .hmaster_trans (hmaster_trans),
        .hmaster_write (hmaster_write),
        .hmaster_size  (hmaster_size),
        .hmaster_burst (hmaster_burst),
        .hmaster_prot  (hmaster_prot),
        .hmaster_wdata (hmaster_wdata),
        .hmaster_rdata (hmaster_rdata),
        .hmaster_ready (hmaster_ready),
        .hmaster_resp  (hmaster_resp),
        
        // Slave HSEL
        .hsel_gpio     (hsel_gpio),
        .hsel_uart     (hsel_uart),
        .hsel_spi      (hsel_spi),
        .hsel_i2c      (hsel_i2c),
        .hsel_pwm      (hsel_pwm),
        .hsel_timer    (hsel_timer),
        .hsel_wdt      (hsel_watchdog),
        .hsel_intc     (hsel_intc),
        .hsel_rstmgr   (hsel_rstmgr),
        
        // Slave Read Data
        .hrdata_gpio   (hrdata_gpio),
        .hrdata_uart   (hrdata_uart),
        .hrdata_spi    (hrdata_spi),
        .hrdata_i2c    (hrdata_i2c),
        .hrdata_pwm    (hrdata_pwm),
        .hrdata_timer  (hrdata_timer),
        .hrdata_wdt    (hrdata_watchdog),
        .hrdata_intc   (hrdata_intc),
        .hrdata_rstmgr (hrdata_rstmgr),
        
        // Slave Ready
        .hready_gpio   (hreadyout_gpio),
        .hready_uart   (hreadyout_uart),
        .hready_spi    (hreadyout_spi),
        .hready_i2c    (hreadyout_i2c),
        .hready_pwm    (hreadyout_pwm),
        .hready_timer  (hreadyout_timer),
        .hready_wdt    (hreadyout_watchdog),
        .hready_intc   (hreadyout_intc),
        .hready_rstmgr (hreadyout_rstmgr),
        
        // Slave Resp
        .hresp_gpio    (hresp_gpio),
        .hresp_uart    (hresp_uart[0]),
        .hresp_spi     (hresp_spi[0]),
        .hresp_i2c     (hresp_i2c),
        .hresp_pwm     (hresp_pwm),
        .hresp_timer   (hresp_timer),
        .hresp_wdt     (hresp_watchdog[0]),
        .hresp_intc    (hresp_intc),
        .hresp_rstmgr  (hresp_rstmgr),
        
        // Shared Slave Ports
        .hslv_addr     (hslv_addr),
        .hslv_trans    (hslv_trans),
        .hslv_write    (hslv_write),
        .hslv_size     (hslv_size),
        .hslv_burst    (hslv_burst),
        .hslv_prot     (hslv_prot),
        .hslv_wdata    (hslv_wdata),
        .hslv_ready_in (hslv_ready_in)
    );

    // 0x4000_0000 : GPIO
    ahb_gpio u_gpio (
        .HCLK       (clk_gpio),
        .HRESETn    (rst_gpio),
        .HSEL       (hsel_gpio),
        .HADDR      (hslv_addr),
        .HTRANS     (hslv_trans),
        .HWRITE     (hslv_write),
        .HSIZE      (hslv_size),
        .HWDATA     (hslv_wdata),
        .HREADY     (hslv_ready_in),
        .HREADYOUT  (hreadyout_gpio),
        .HRDATA     (hrdata_gpio),
        .HRESP      (hresp_gpio),
        .gpio       (gpio_pins)
    );

    // 0x4001_0000 : UART
    ahb_uart u_uart (
        .HCLK       (clk_uart),
        .HRESETn    (rst_uart),
        .HSEL       (hsel_uart),
        .HADDR      (hslv_addr),
        .HTRANS     (hslv_trans),
        .HWRITE     (hslv_write),
        .HSIZE      (hslv_size),
        .HBURST     (hslv_burst),
        .HPROT      (hslv_prot),
        .HWDATA     (hslv_wdata),
        .HREADY     (hslv_ready_in),
        .HREADYOUT  (hreadyout_uart),
        .HRDATA     (hrdata_uart),
        .HRESP      (hresp_uart),
        .tx         (uart_tx),
        .rx         (uart_rx)
    );

    // 0x4002_0000 : SPI
    ahb_spi u_spi (
        .HCLK       (clk_spi),
        .HRESETn    (rst_spi),
        .HSEL       (hsel_spi),
        .HADDR      (hslv_addr),
        .HTRANS     (hslv_trans),
        .HWRITE     (hslv_write),
        .HWDATA     (hslv_wdata),
        .HREADY     (hslv_ready_in),
        .HREADYOUT  (hreadyout_spi),
        .HRDATA     (hrdata_spi),
        .HRESP      (hresp_spi),
        .spi_sclk   (spi_sck),
        .spi_mosi   (spi_mosi),
        .spi_miso   (spi_miso),
        .spi_cs_n   (spi_cs_n)
    );

    // 0x4003_0000 : I2C
    ahb_i2c u_i2c (
        .HCLK       (clk_i2c),
        .HRESETn    (rst_i2c),
        .HSEL       (hsel_i2c),
        .HADDR      (hslv_addr),
        .HTRANS     (hslv_trans),
        .HWRITE     (hslv_write),
        .HSIZE      (hslv_size),
        .HWDATA     (hslv_wdata),
        .HREADY     (hslv_ready_in),
        .HREADYOUT  (hreadyout_i2c),
        .HRDATA     (hrdata_i2c),
        .HRESP      (hresp_i2c),
        .scl_o      (i2c_scl_o),
        .scl_oen    (i2c_scl_oen),
        .scl_i      (i2c_scl_i),
        .sda_o      (i2c_sda_o),
        .sda_oen    (i2c_sda_oen),
        .sda_i      (i2c_sda_i)
    );

    // 0x4004_0000 : PWM
    ahb_pwm u_pwm (
        .HCLK       (clk_pwm),
        .HRESETn    (rst_pwm),
        .HSEL       (hsel_pwm),
        .HADDR      (hslv_addr),
        .HTRANS     (hslv_trans),
        .HWRITE     (hslv_write),
        .HSIZE      (hslv_size),
        .HBURST     (hslv_burst),
        .HPROT      (hslv_prot),
        .HWDATA     (hslv_wdata),
        .HREADY     (hslv_ready_in),
        .HREADYOUT  (hreadyout_pwm),
        .HRDATA     (hrdata_pwm),
        .HRESP      (hresp_pwm),
        .pwm_out    (pwm_out)
    );

    // 0x4005_0000 : Timer
    ahb_timer u_timer (
        .HCLK       (clk_timer),
        .HRESETn    (rst_timer),
        .HSEL       (hsel_timer),
        .HADDR      (hslv_addr),
        .HTRANS     (hslv_trans),
        .HWRITE     (hslv_write),
        .HSIZE      (hslv_size),
        .HWDATA     (hslv_wdata),
        .HREADY     (hslv_ready_in),
        .HREADYOUT  (hreadyout_timer),
        .HRDATA     (hrdata_timer),
        .HRESP      (hresp_timer),
        .timer_int  (irq_timer)
    );

    // 0x4006_0000 : Watchdog
    ahb_watchdog u_watchdog (
        .HCLK       (clk_watchdog),
        .HRESETn    (rst_watchdog),
        .HSEL       (hsel_watchdog),
        .HADDR      (hslv_addr),
        .HTRANS     (hslv_trans),
        .HWRITE     (hslv_write),
        .HSIZE      (hslv_size),
        .HWDATA     (hslv_wdata),
        .HREADY     (hslv_ready_in),
        .HREADYOUT  (hreadyout_watchdog),
        .HRDATA     (hrdata_watchdog),
        .HRESP      (hresp_watchdog),
        .WDG_RST    (wdg_rst)
    );

    // 0x4007_0000 : INTC
    ahb_intc u_intc (
        .HCLK       (clk_intc),
        .HRESETn    (rst_intc),
        .HSEL       (hsel_intc),
        .HADDR      (hslv_addr),
        .HTRANS     (hslv_trans),
        .HWRITE     (hslv_write),
        .HSIZE      (hslv_size),
        .HBURST     (hslv_burst),
        .HPROT      (hslv_prot),
        .HWDATA     (hslv_wdata),
        .HREADY     (hslv_ready_in),
        .HREADYOUT  (hreadyout_intc),
        .HRDATA     (hrdata_intc),
        .HRESP      (hresp_intc),
        .irq_in     (irq_bus),
        .irq_out    (cpu_irq)
    );

    // 0x4008_0000 : Reset/Clock Manager
    ahb_rstmgr u_rstmgr (
        .HCLK       (clk),
        .HRESETn    (resetn),
        .HSEL       (hsel_rstmgr),
        .HADDR      (hslv_addr),
        .HTRANS     (hslv_trans),
        .HWRITE     (hslv_write),
        .HSIZE      (hslv_size),
        .HBURST     (hslv_burst),
        .HPROT      (hslv_prot),
        .HWDATA     (hslv_wdata),
        .HREADY     (hslv_ready_in),
        .HREADYOUT  (hreadyout_rstmgr),
        .HRDATA     (hrdata_rstmgr),
        .HRESP      (hresp_rstmgr),
        .soft_rst_n (soft_rst_n),
        .clk_en     (clk_en)
    );

    assign irq_uart = 1'b0; // No UART IRQ out from generated ahb_uart.v
    assign irq_spi  = 1'b0; // No SPI IRQ out from generated ahb_spi.v
    assign irq_watchdog = 1'b0; // No Watchdog IRQ out from generated ahb_watchdog.v

endmodule
