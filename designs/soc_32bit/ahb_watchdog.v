module ahb_watchdog (
    input  wire        HCLK,
    input  wire        HRESETn,
    
    // AHB-Lite interface
    input  wire        HSEL,
    input  wire [31:0] HADDR,
    input  wire [1:0]  HTRANS,
    input  wire        HWRITE,
    input  wire [2:0]  HSIZE,
    input  wire [31:0] HWDATA,
    input  wire        HREADY,
    
    output wire        HREADYOUT,
    output wire [1:0]  HRESP,
    output wire [31:0] HRDATA,
    
    // Watchdog reset output
    output reg         WDG_RST
);

    // AHB-Lite constants
    localparam HTRANS_NONSEQ = 2'b10;
    localparam HTRANS_SEQ    = 2'b11;
    
    // Register map offsets
    localparam REG_LOAD   = 8'h00; // R/W: Load value
    localparam REG_VALUE  = 8'h04; // R/O: Current value
    localparam REG_CTRL   = 8'h08; // R/W: Control register
    localparam REG_INTCLR = 8'h0C; // W/O: Interrupt clear / Kick
    localparam REG_RIS    = 8'h10; // R/O: Raw interrupt status
    localparam REG_MIS    = 8'h14; // R/O: Masked interrupt status
    localparam REG_LOCK   = 8'hC0; // R/W: Lock register

    // Lock unlock value
    localparam UNLOCK_VAL = 32'h1ACCE551;
    
    // Registers
    reg [31:0] load_reg;
    reg [31:0] value_reg;
    reg        ctrl_resen; // Reset enable
    reg        ctrl_inten; // Interrupt enable
    reg        locked;     // 1 = locked (writes ignored), 0 = unlocked
    reg        int_stat;   // Interrupt status

    // AHB address phase sampling
    reg        ahb_write_phase;
    reg [7:0]  ahb_addr_phase;
    reg        ahb_sel_phase;
    
    always @(posedge HCLK or negedge HRESETn) begin
        if (!HRESETn) begin
            ahb_write_phase <= 1'b0;
            ahb_addr_phase  <= 8'h00;
            ahb_sel_phase   <= 1'b0;
        end else if (HREADY) begin
            ahb_sel_phase   <= HSEL && (HTRANS == HTRANS_NONSEQ || HTRANS == HTRANS_SEQ);
            ahb_write_phase <= HWRITE;
            if (HSEL && (HTRANS == HTRANS_NONSEQ || HTRANS == HTRANS_SEQ)) begin
                ahb_addr_phase <= HADDR[7:0];
            end
        end
    end

    // AHB Write Phase and Watchdog Core Logic
    always @(posedge HCLK or negedge HRESETn) begin
        if (!HRESETn) begin
            load_reg   <= 32'hFFFFFFFF;
            value_reg  <= 32'hFFFFFFFF;
            ctrl_resen <= 1'b0;
            ctrl_inten <= 1'b0;
            locked     <= 1'b1;
            int_stat   <= 1'b0;
            WDG_RST    <= 1'b0;
        end else begin
            WDG_RST <= 1'b0; // Default pulse low
            
            // Watchdog decrement logic
            if (ctrl_inten) begin
                if (value_reg == 32'd0) begin
                    if (ctrl_resen && int_stat) begin
                        // Second timeout and reset enabled -> Trigger Reset
                        WDG_RST <= 1'b1;
                        value_reg <= load_reg; // Reload
                    end else begin
                        // First timeout -> Trigger interrupt
                        int_stat <= 1'b1;
                        value_reg <= load_reg;
                    end
                end else begin
                    value_reg <= value_reg - 1'b1;
                end
            end
            
            // AHB Write Processing
            if (ahb_sel_phase && ahb_write_phase) begin
                case (ahb_addr_phase)
                    REG_LOAD: begin
                        if (!locked) begin
                            load_reg <= HWDATA;
                            value_reg <= HWDATA;
                        end
                    end
                    REG_CTRL: begin
                        if (!locked) begin
                            ctrl_inten <= HWDATA[0];
                            ctrl_resen <= HWDATA[1];
                        end
                    end
                    REG_INTCLR: begin
                        if (!locked) begin
                            int_stat <= 1'b0;
                            // Kick the watchdog by reloading
                            value_reg <= load_reg; 
                        end
                    end
                    REG_LOCK: begin
                        if (HWDATA == UNLOCK_VAL)
                            locked <= 1'b0;
                        else
                            locked <= 1'b1;
                    end
                    default: ; // Do nothing for other addresses
                endcase
            end
        end
    end

    // AHB Read Phase
    reg [31:0] rdata;
    always @(*) begin
        rdata = 32'h0;
        if (ahb_sel_phase && !ahb_write_phase) begin
            case (ahb_addr_phase)
                REG_LOAD:   rdata = load_reg;
                REG_VALUE:  rdata = value_reg;
                REG_CTRL:   rdata = {30'h0, ctrl_resen, ctrl_inten};
                REG_RIS:    rdata = {31'h0, int_stat};
                REG_MIS:    rdata = {31'h0, int_stat & ctrl_inten};
                REG_LOCK:   rdata = {31'h0, locked};
                default:    rdata = 32'h0;
            endcase
        end
    end

    assign HRDATA    = rdata;
    assign HREADYOUT = 1'b1; // Zero wait states
    assign HRESP     = 2'b00; // OKAY

endmodule
