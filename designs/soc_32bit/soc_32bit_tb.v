`timescale 1ns/1ps

module soc_32bit_tb;

    logic clk;
    logic resetn;

    // Peripheral IOs
    wire [31:0] gpio_pins;
    wire uart_tx;
    logic uart_rx;
    wire spi_sck;
    wire spi_mosi;
    logic spi_miso;
    wire spi_cs_n;
    wire i2c_scl_o;
    wire i2c_scl_oen;
    logic i2c_scl_i;
    wire i2c_sda_o;
    wire i2c_sda_oen;
    logic i2c_sda_i;
    wire [3:0] pwm_out;

    // Instantiate DUT
    soc_32bit dut (
        .clk(clk),
        .resetn(resetn),
        .gpio_pins(gpio_pins),
        .uart_tx(uart_tx),
        .uart_rx(uart_rx),
        .spi_sck(spi_sck),
        .spi_mosi(spi_mosi),
        .spi_miso(spi_miso),
        .spi_cs_n(spi_cs_n),
        .i2c_scl_o(i2c_scl_o),
        .i2c_scl_oen(i2c_scl_oen),
        .i2c_scl_i(i2c_scl_i),
        .i2c_sda_o(i2c_sda_o),
        .i2c_sda_oen(i2c_sda_oen),
        .i2c_sda_i(i2c_sda_i),
        .pwm_out(pwm_out)
    );

    // Clock generation
    initial begin
        clk = 0;
        forever #5 clk = ~clk; // 100MHz clock
    end

    // Test sequence
    initial begin
        $dumpfile("dump.vcd");
        $dumpvars(0, soc_32bit_tb);
        
        // Initialize inputs
        resetn = 0;
        uart_rx = 1;
        spi_miso = 0;
        i2c_scl_i = 1;
        i2c_sda_i = 1;

        // Apply reset
        #20 resetn = 1;

        // Wait for dummy CPU to attempt a read/write (it's hardcoded to 0x4000_0000)
        #100;
        
        $display("Simulation complete. VCD generated.");
        $finish;
    end

endmodule
