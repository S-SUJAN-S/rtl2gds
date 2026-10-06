`timescale 1ns / 1ps
module ahb_gpio (
    input  wire        HCLK,
    input  wire        HRESETn,
    
    // AHB-Lite Slave Interface
    input  wire        HSEL,
    input  wire [31:0] HADDR,
    input  wire [ 1:0] HTRANS,
    input  wire        HWRITE,
    input  wire [ 2:0] HSIZE,
    input  wire [31:0] HWDATA,
    input  wire        HREADY,
    
    output wire        HREADYOUT,
    output reg  [31:0] HRDATA,
    output wire        HRESP,
    
    // GPIO external interface
    inout  wire [31:0] gpio
);

    // Register map
    // 0x00 : DIR (Direction: 1 = Output, 0 = Input)
    // 0x04 : DOUT (Data Out)
    // 0x08 : DIN (Data In, Read Only)

    reg [31:0] r_dir;
    reg [31:0] r_dout;
    
    // AHB bus control phases
    reg        ahb_write;
    reg        ahb_read;
    reg [31:0] ahb_addr_reg;
    
    // HTRANS phases
    localparam HTRANS_IDLE   = 2'b00;
    localparam HTRANS_NONSEQ = 2'b10;
    localparam HTRANS_SEQ    = 2'b11;

    wire valid_bus_phase = HSEL && HREADY && (HTRANS == HTRANS_NONSEQ || HTRANS == HTRANS_SEQ);
    
    always @(posedge HCLK or negedge HRESETn) begin
        if (!HRESETn) begin
            ahb_write    <= 1'b0;
            ahb_read     <= 1'b0;
            ahb_addr_reg <= 32'h0;
        end else begin
            if (valid_bus_phase) begin
                ahb_write    <=  HWRITE;
                ahb_read     <= !HWRITE;
                ahb_addr_reg <= HADDR;
            end else begin
                ahb_write    <= 1'b0;
                ahb_read     <= 1'b0;
            end
        end
    end

    // Write operation
    always @(posedge HCLK or negedge HRESETn) begin
        if (!HRESETn) begin
            r_dir  <= 32'h0000_0000;
            r_dout <= 32'h0000_0000;
        end else if (ahb_write) begin
            case (ahb_addr_reg[7:0])
                8'h00: r_dir  <= HWDATA;
                8'h04: r_dout <= HWDATA;
                default: ; // Do nothing
            endcase
        end
    end

    // Synchronize GPIO inputs (2-stage synchronizer to avoid metastability)
    reg [31:0] sync1_din;
    reg [31:0] sync2_din;
    
    always @(posedge HCLK or negedge HRESETn) begin
        if (!HRESETn) begin
            sync1_din <= 32'h0;
            sync2_din <= 32'h0;
        end else begin
            sync1_din <= gpio;
            sync2_din <= sync1_din;
        end
    end

    // Read operation
    always @(*) begin
        HRDATA = 32'h0000_0000;
        if (ahb_read) begin
            case (ahb_addr_reg[7:0])
                8'h00: HRDATA = r_dir;
                8'h04: HRDATA = r_dout;
                8'h08: HRDATA = sync2_din;
                default: HRDATA = 32'h0000_0000;
            endcase
        end
    end
    
    // AHB Responses
    assign HREADYOUT = 1'b1; // Zero wait states
    assign HRESP = 1'b0;     // OKAY response

    // Tristate GPIO Buffers
    genvar i;
    generate
        for (i = 0; i < 32; i = i + 1) begin : gpio_buf
            assign gpio[i] = (r_dir[i]) ? r_dout[i] : 1'bz;
        end
    endgenerate

endmodule
