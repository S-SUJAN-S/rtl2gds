/* verilator lint_off UNUSEDSIGNAL */
/* verilator lint_off UNUSEDPARAM */
/* verilator lint_off UNDRIVEN */
/* verilator lint_off DECLFILENAME */

module axi4_lite_sram #(parameter DATA_WIDTH = 32, parameter ADDR_WIDTH = 16) (
    input clk,
    input rstn,
    
    // AXI4-Lite Slave Interface
    input [ADDR_WIDTH-1:0] s_axi_awaddr,
    input [2:0] s_axi_awprot,
    input s_axi_awvalid,
    output reg s_axi_awready,
    
    input [DATA_WIDTH-1:0] s_axi_wdata,
    input [(DATA_WIDTH/8)-1:0] s_axi_wstrb,
    input s_axi_wvalid,
    output reg s_axi_wready,
    
    output reg [1:0] s_axi_bresp,
    output reg s_axi_bvalid,
    input s_axi_bready,
    
    input [ADDR_WIDTH-1:0] s_axi_araddr,
    input [2:0] s_axi_arprot,
    input s_axi_arvalid,
    output reg s_axi_arready,
    
    output reg [DATA_WIDTH-1:0] s_axi_rdata,
    output reg [1:0] s_axi_rresp,
    output reg s_axi_rvalid,
    input s_axi_rready,
    
    // SRAM Interface
    output reg [ADDR_WIDTH-1:0] sram_addr,
    inout [DATA_WIDTH-1:0] sram_data,
    output reg sram_we,
    output reg sram_oe,
    output reg sram_ce
);

// Tristate buffer for SRAM data
reg [DATA_WIDTH-1:0] sram_data_out;
reg sram_data_dir;
assign sram_data = sram_data_dir ? sram_data_out : {DATA_WIDTH{1'bz}};

// Define states for the write transaction state machine
localparam IDLE = 2'b00;
localparam ADDR_PHASE = 2'b01;
localparam DATA_PHASE = 2'b10;
reg [1:0] wr_state = IDLE;

// Define states for the read transaction state machine
localparam RIDLE = 2'b00;
localparam RADDR_PHASE = 2'b01;
localparam RDATA_PHASE = 2'b10;
reg [1:0] rd_state = RIDLE;

// Define constants for the AXI4-Lite protocol handshaking
localparam OKAY = 2'b00;
localparam EXOKAY = 2'b01;
localparam SLVERROR = 2'b10;
localparam DECERR = 2'b11;

// Define constants for the SRAM interface
localparam WRITE_OP = 1'b0;
localparam READ_OP = 1'b1;

always @(posedge clk) begin
    if (!rstn) begin
        s_axi_awready <= 1'b0;
        s_axi_wready <= 1'b0;
        s_axi_bresp <= OKAY;
        s_axi_bvalid <= 1'b0;
        s_axi_arready <= 1'b0;
        s_axi_rdata <= 32'h0;
        s_axi_rresp <= OKAY;
        s_axi_rvalid <= 1'b0;
        sram_we <= 1'b0;
        sram_oe <= 1'b0;
        sram_ce <= 1'b0;
        sram_data_dir <= 1'b0;
    end else begin
        // Default SRAM signals
        sram_we <= 1'b0;
        sram_oe <= 1'b0;
        sram_ce <= 1'b1;
        sram_data_dir <= 1'b0;
        
        // AXI4-Lite Slave Write Transaction State Machine
        case (wr_state)
            IDLE: begin
                s_axi_awready <= 1'b1;
                s_axi_wready <= 1'b0;
                s_axi_bvalid <= 1'b0;
                if (s_axi_awvalid && s_axi_awready) begin
                    s_axi_awready <= 1'b0;
                    sram_addr <= s_axi_awaddr;
                    wr_state <= DATA_PHASE;
                end
            end
            
            DATA_PHASE: begin
                s_axi_wready <= 1'b1;
                if (s_axi_wvalid && s_axi_wready) begin
                    s_axi_wready <= 1'b0;
                    sram_data_out <= s_axi_wdata;
                    sram_data_dir <= 1'b1;
                    sram_we <= 1'b1;
                    s_axi_bresp <= OKAY;
                    s_axi_bvalid <= 1'b1;
                    wr_state <= 2'b11; // B_PHASE
                end
            end
            
            2'b11: begin // B_PHASE
                sram_we <= 1'b0;
                if (s_axi_bready && s_axi_bvalid) begin
                    s_axi_bvalid <= 1'b0;
                    wr_state <= IDLE;
                end
            end
            
            default: wr_state <= IDLE;
        endcase
        
        // AXI4-Lite Slave Read Transaction State Machine
        case (rd_state)
            RIDLE: begin
                s_axi_arready <= 1'b1;
                s_axi_rvalid <= 1'b0;
                if (s_axi_arvalid && s_axi_arready) begin
                    s_axi_arready <= 1'b0;
                    sram_addr <= s_axi_araddr;
                    rd_state <= RADDR_PHASE;
                end
            end
            
            RADDR_PHASE: begin
                // Drive SRAM OE to read data
                sram_oe <= 1'b1;
                // Dummy cycle for SRAM read latency
                rd_state <= RDATA_PHASE;
            end
            
            RDATA_PHASE: begin
                sram_oe <= 1'b1;
                s_axi_rdata <= sram_data;
                s_axi_rresp <= OKAY;
                s_axi_rvalid <= 1'b1;
                if (s_axi_rready && s_axi_rvalid) begin
                    s_axi_rvalid <= 1'b0;
                    sram_oe <= 1'b0;
                    rd_state <= RIDLE;
                end
            end
            
            default: rd_state <= RIDLE;
        endcase
    end
end

endmodule