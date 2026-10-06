module axi4_sram_controller_tb;

// Parameters for the SRAM Controller
parameter DATA_WIDTH = 32;
parameter ADDR_WIDTH = 16;

// Clock and reset signals
reg clk, rstn;

// AXI4-Lite Slave Interface Signals
reg [ADDR_WIDTH-1:0] s_axi_awaddr;
reg [2:0] s_axi_awprot;
reg s_axi_awvalid;
wire s_axi_awready;
reg [DATA_WIDTH-1:0] s_axi_wdata;
reg [(DATA_WIDTH/8)-1:0] s_axi_wstrb;
reg s_axi_wvalid;
wire s_axi_wready;
wire [1:0] s_axi_bresp;
wire s_axi_bvalid;
reg s_axi_bready;
reg [ADDR_WIDTH-1:0] s_axi_araddr;
reg [2:0] s_axi_arprot;
reg s_axi_arvalid;
wire s_axi_arready;
wire [DATA_WIDTH-1:0] s_axi_rdata;
wire [1:0] s_axi_rresp;
wire s_axi_rvalid;
reg s_axi_rready;

// SRAM Interface Signals
wire [ADDR_WIDTH-1:0] sram_addr;
inout [DATA_WIDTH-1:0] sram_data;
wire sram_we;
wire sram_oe;
wire sram_ce;

// Instantiate the SRAM Controller and connect its signals to the testbench
axi4_lite_sram #(.DATA_WIDTH(DATA_WIDTH), .ADDR_WIDTH(ADDR_WIDTH)) dut (
    .clk(clk),
    .rstn(rstn),
    .s_axi_awaddr(s_axi_awaddr),
    .s_axi_awprot(s_axi_awprot),
    .s_axi_awvalid(s_axi_awvalid),
    .s_axi_awready(s_axi_awready),
    .s_axi_wdata(s_axi_wdata),
    .s_axi_wstrb(s_axi_wstrb),
    .s_axi_wvalid(s_axi_wvalid),
    .s_axi_wready(s_axi_wready),
    .s_axi_bresp(s_axi_bresp),
    .s_axi_bvalid(s_axi_bvalid),
    .s_axi_bready(s_axi_bready),
    .s_axi_araddr(s_axi_araddr),
    .s_axi_arprot(s_axi_arprot),
    .s_axi_arvalid(s_axi_arvalid),
    .s_axi_arready(s_axi_arready),
    .s_axi_rdata(s_axi_rdata),
    .s_axi_rresp(s_axi_rresp),
    .s_axi_rvalid(s_axi_rvalid),
    .s_axi_rready(s_axi_rready),
    .sram_addr(sram_addr),
    .sram_data(sram_data),
    .sram_we(sram_we),
    .sram_oe(sram_oe),
    .sram_ce(sram_ce)
);

// Clock generation
initial begin
    clk = 0;
    forever #5 clk = ~clk;
end

// Reset generation
initial begin
    rstn = 1'b0;
    #10 rstn = 1'b1;
end

initial begin
    $monitor("[%0t] wr_state=%b awv=%b awr=%b wv=%b wr=%b bv=%b br=%b | rd_state=%b arv=%b arr=%b rv=%b rr=%b", 
             $time, dut.wr_state, s_axi_awvalid, s_axi_awready, s_axi_wvalid, s_axi_wready, s_axi_bvalid, s_axi_bready,
             dut.rd_state, s_axi_arvalid, s_axi_arready, s_axi_rvalid, s_axi_rready);
end

// Write transaction testbench code
initial begin
    // Initialize signals
    s_axi_awvalid <= 1'b0;
    s_axi_wvalid <= 1'b0;
    s_axi_bready <= 1'b0;
    s_axi_arvalid <= 1'b0;
    s_axi_rready <= 1'b0;
    
    // Wait for reset to deassert
    @(posedge rstn);
    @(posedge clk);
    
    // ---------------------------------------------------------
    // WRITE TRANSACTION
    // ---------------------------------------------------------
    $display("[%0t] Starting Write Transaction", $time);
    s_axi_awaddr <= 16'h0000;
    s_axi_awvalid <= 1'b1;
    s_axi_wdata <= 32'hdeadbeef;
    s_axi_wstrb <= {(DATA_WIDTH/8){1'b1}};
    s_axi_wvalid <= 1'b1;
    s_axi_bready <= 1'b1;
    
    // Wait for AWREADY
    wait(s_axi_awready == 1'b1);
    @(posedge clk);
    s_axi_awvalid <= 1'b0;
    
    // Wait for WREADY
    wait(s_axi_wready == 1'b1);
    @(posedge clk);
    s_axi_wvalid <= 1'b0;
    
    // Wait for BVALID (Write Response)
    wait(s_axi_bvalid == 1'b1);
    @(posedge clk);
    s_axi_bready <= 1'b0;
    $display("[%0t] Write Transaction Completed. BRESP: %b", $time, s_axi_bresp);
    
    repeat(4) @(posedge clk); // Idle gap synced to clock
    
    // ---------------------------------------------------------
    // READ TRANSACTION
    // ---------------------------------------------------------
    $display("[%0t] Starting Read Transaction", $time);
    s_axi_araddr <= 16'h0000;
    s_axi_arvalid <= 1'b1;
    s_axi_rready <= 1'b1;
    
    // Wait for ARREADY
    wait(s_axi_arready == 1'b1);
    @(posedge clk);
    s_axi_arvalid <= 1'b0;
    
    // Wait for RVALID (Read Data)
    wait(s_axi_rvalid == 1'b1);
    $display("[%0t] Read Transaction Completed. RDATA: %h, RRESP: %b", $time, s_axi_rdata, s_axi_rresp);
    @(posedge clk);
    s_axi_rready <= 1'b0;
end

// End of simulation
initial begin
    #1000 $finish;
end

endmodule