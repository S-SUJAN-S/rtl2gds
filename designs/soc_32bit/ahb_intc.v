`timescale 1ns/1ps

module ahb_intc (
    // AHB-Lite Slave Interface
    input  wire        HCLK,
    input  wire        HRESETn,
    input  wire        HSEL,
    input  wire [31:0] HADDR,
    input  wire [1:0]  HTRANS,
    input  wire        HWRITE,
    input  wire [2:0]  HSIZE,
    input  wire [2:0]  HBURST,
    input  wire [3:0]  HPROT,
    input  wire [31:0] HWDATA,
    input  wire        HREADY,
    
    output wire        HREADYOUT,
    output wire [31:0] HRDATA,
    output wire        HRESP,
    
    // Interrupt Inputs
    input  wire [7:0]  irq_in,
    
    // CPU Interrupt Output
    output wire        irq_out
);

    // Internal Registers
    reg [7:0] int_en;    // Interrupt Enable Register (Offset 0x00)
    reg [7:0] int_raw;   // Interrupt Raw Status Register (Offset 0x04)
    reg [7:0] int_mask;  // Interrupt Masked Status Register (Offset 0x08)
    
    // AHB Address Phase sampling
    reg [31:0] addr_reg;
    reg        write_en_reg;
    reg        read_en_reg;
    
    // HTRANS types
    localparam HTRANS_IDLE   = 2'b00;
    localparam HTRANS_BUSY   = 2'b01;
    localparam HTRANS_NONSEQ = 2'b10;
    localparam HTRANS_SEQ    = 2'b11;
    
    wire ahb_valid = HSEL && HREADY && (HTRANS == HTRANS_NONSEQ || HTRANS == HTRANS_SEQ);
    
    always @(posedge HCLK or negedge HRESETn) begin
        if (!HRESETn) begin
            addr_reg     <= 32'h0;
            write_en_reg <= 1'b0;
            read_en_reg  <= 1'b0;
        end else begin
            if (ahb_valid) begin
                addr_reg     <= HADDR;
                write_en_reg <= HWRITE;
                read_en_reg  <= ~HWRITE;
            end else begin
                write_en_reg <= 1'b0;
                read_en_reg  <= 1'b0;
            end
        end
    end

    // Write Logic
    always @(posedge HCLK or negedge HRESETn) begin
        if (!HRESETn) begin
            int_en <= 8'h0;
        end else begin
            if (write_en_reg) begin
                case (addr_reg[7:0])
                    8'h00: int_en <= HWDATA[7:0]; // Write to Enable Register
                    default: ; 
                endcase
            end
        end
    end

    // Raw and Masked status updates
    always @(posedge HCLK or negedge HRESETn) begin
        if (!HRESETn) begin
            int_raw  <= 8'h0;
            int_mask <= 8'h0;
        end else begin
            int_raw  <= irq_in;
            int_mask <= irq_in & int_en;
        end
    end

    // Read Logic
    reg [31:0] hrdata_reg;
    always @(posedge HCLK or negedge HRESETn) begin
        if (!HRESETn) begin
            hrdata_reg <= 32'h0;
        end else begin
            if (read_en_reg) begin
                case (addr_reg[7:0])
                    8'h00: hrdata_reg <= {24'h0, int_en};
                    8'h04: hrdata_reg <= {24'h0, int_raw};
                    8'h08: hrdata_reg <= {24'h0, int_mask};
                    default: hrdata_reg <= 32'h0;
                endcase
            end
        end
    end

    // Outputs
    assign HREADYOUT = 1'b1;
    assign HRESP     = 1'b0; // OKAY response
    assign HRDATA    = hrdata_reg;
    assign irq_out   = |int_mask; // Assert CPU IRQ if any masked interrupt is active

endmodule
