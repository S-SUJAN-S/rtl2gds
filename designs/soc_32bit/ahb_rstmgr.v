module ahb_rstmgr (
    input  wire        HCLK,
    input  wire        HRESETn,
    
    // AHB-Lite Slave Interface
    input  wire        HSEL,
    input  wire [31:0] HADDR,
    input  wire [1:0]  HTRANS,
    input  wire        HWRITE,
    input  wire [2:0]  HSIZE,
    input  wire [2:0]  HBURST,
    input  wire [3:0]  HPROT,
    input  wire [31:0] HWDATA,
    input  wire        HREADY,
    
    output wire [31:0] HRDATA,
    output wire        HREADYOUT,
    output wire        HRESP,

    // Reset and Clock Management Outputs
    output wire [31:0] soft_rst_n, // Soft reset, active low (0 = reset, 1 = normal)
    output wire [31:0] clk_en      // Clock enable (1 = clock enabled, 0 = clock gated)
);

    // AHB-Lite HTRANS constants
    localparam HTRANS_IDLE   = 2'b00;
    localparam HTRANS_NONSEQ = 2'b10;
    
    // Register offset map
    localparam REG_RSTCTRL = 8'h00; // Reset Control Register
    localparam REG_CLKGATE = 8'h04; // Clock Gate Control Register

    // Internal Register State
    reg [31:0] rst_ctrl_q;
    reg [31:0] clkgate_ctrl_q;

    // AHB write tracking
    reg        ahb_write_q;
    reg [7:0]  ahb_waddr_q;
    
    // Address phase decoding (only valid if HREADY is high and selected)
    wire addr_phase_valid = HSEL && HREADY && (HTRANS == HTRANS_NONSEQ);
    wire ahb_write_en     = addr_phase_valid && HWRITE;
    wire ahb_read_en      = addr_phase_valid && !HWRITE;

    // Track write address and enable into the data phase
    always @(posedge HCLK or negedge HRESETn) begin
        if (!HRESETn) begin
            ahb_write_q <= 1'b0;
            ahb_waddr_q <= 8'h0;
        end else begin
            ahb_write_q <= ahb_write_en;
            if (ahb_write_en) begin
                ahb_waddr_q <= HADDR[7:0];
            end
        end
    end

    // Write Logic - Update registers during data phase
    always @(posedge HCLK or negedge HRESETn) begin
        if (!HRESETn) begin
            rst_ctrl_q     <= 32'h0;        // Default: no soft resets active
            clkgate_ctrl_q <= 32'hFFFFFFFF; // Default: all clocks enabled
        end else if (ahb_write_q) begin
            case (ahb_waddr_q)
                REG_RSTCTRL: rst_ctrl_q     <= HWDATA;
                REG_CLKGATE: clkgate_ctrl_q <= HWDATA;
                default: ;
            endcase
        end
    end

    // Read Logic - Decode address phase for read operations
    reg [31:0] rdata_comb;
    always @(*) begin
        rdata_comb = 32'h0;
        if (ahb_read_en) begin
            case (HADDR[7:0])
                REG_RSTCTRL: rdata_comb = rst_ctrl_q;
                REG_CLKGATE: rdata_comb = clkgate_ctrl_q;
                default:     rdata_comb = 32'h0;
            endcase
        end
    end

    // Register read data to output in the data phase
    reg [31:0] rdata_q;
    always @(posedge HCLK or negedge HRESETn) begin
        if (!HRESETn) begin
            rdata_q <= 32'h0;
        end else begin
            // We sample rdata_comb when a read is initiated, or just pass it through
            // If the slave takes 1 cycle, this works fine since HREADYOUT is 1
            if (ahb_read_en) begin
                rdata_q <= rdata_comb;
            end
        end
    end

    // AHB Output Assignments
    assign HRDATA    = rdata_q;
    assign HREADYOUT = 1'b1; // Zero wait-state slave
    assign HRESP     = 1'b0; // OKAY response

    // Subsystem Output Assignments
    // Note: rst_ctrl_q bit = 1 implies reset active, so soft_rst_n is the bitwise negation
    assign soft_rst_n = ~rst_ctrl_q;
    assign clk_en     = clkgate_ctrl_q;

endmodule
