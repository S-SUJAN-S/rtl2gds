module ahb_timer (
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
    output wire        HRESP,
    output wire [31:0] HRDATA,
    
    // Interrupt output
    output wire        timer_int
);

    // Memory-mapped registers
    localparam ADDR_CTRL   = 8'h00;
    localparam ADDR_RELOAD = 8'h04;
    localparam ADDR_VAL    = 8'h08;
    localparam ADDR_INTCLR = 8'h0C;

    reg [2:0]  ctrl_reg;
    reg [31:0] reload_reg;
    reg [31:0] val_reg;
    reg        int_status;

    reg        ahb_write_en;
    reg [7:0]  ahb_write_addr;
    reg [7:0]  read_addr_reg;

    wire ahb_write_phase = HSEL && HTRANS[1] && HWRITE && HREADY;
    wire ahb_read_phase  = HSEL && HTRANS[1] && !HWRITE && HREADY;

    // AHB interface registers
    always @(posedge HCLK or negedge HRESETn) begin
        if (!HRESETn) begin
            ahb_write_en   <= 1'b0;
            ahb_write_addr <= 8'h00;
            read_addr_reg  <= 8'h00;
        end else begin
            if (HREADY) begin
                ahb_write_en <= ahb_write_phase;
                if (ahb_write_phase)
                    ahb_write_addr <= HADDR[7:0];
                if (ahb_read_phase)
                    read_addr_reg  <= HADDR[7:0];
            end else begin
                ahb_write_en <= 1'b0;
            end
        end
    end

    wire timer_en   = ctrl_reg[0];
    wire int_en     = ctrl_reg[1];
    wire auto_rel   = ctrl_reg[2];

    wire write_val_reg = (ahb_write_en && ahb_write_addr == ADDR_VAL);
    wire write_ctrl    = (ahb_write_en && ahb_write_addr == ADDR_CTRL);
    wire write_reload  = (ahb_write_en && ahb_write_addr == ADDR_RELOAD);
    wire write_intclr  = (ahb_write_en && ahb_write_addr == ADDR_INTCLR);

    // Main timer logic
    always @(posedge HCLK or negedge HRESETn) begin
        if (!HRESETn) begin
            ctrl_reg   <= 3'b000;
            reload_reg <= 32'h00000000;
            val_reg    <= 32'h00000000;
            int_status <= 1'b0;
        end else begin
            // CTRL Register
            if (write_ctrl) begin
                ctrl_reg <= HWDATA[2:0];
            end
            
            // RELOAD Register
            if (write_reload) begin
                reload_reg <= HWDATA;
            end

            // VAL Register and Counter
            if (write_val_reg) begin
                val_reg <= HWDATA;
            end else if (timer_en) begin
                if (val_reg != 32'h00000000) begin
                    val_reg <= val_reg - 1'b1;
                end else if (auto_rel) begin
                    val_reg <= reload_reg;
                end
            end

            // Interrupt Status
            if (write_intclr) begin
                int_status <= 1'b0;
            end else if (timer_en && val_reg == 32'h00000001) begin
                int_status <= 1'b1;
            end
        end
    end

    // AHB read response logic
    reg [31:0] read_data_reg;
    always @(*) begin
        case (read_addr_reg)
            ADDR_CTRL:   read_data_reg = {29'h0, ctrl_reg};
            ADDR_RELOAD: read_data_reg = reload_reg;
            ADDR_VAL:    read_data_reg = val_reg;
            ADDR_INTCLR: read_data_reg = {31'h0, int_status};
            default:     read_data_reg = 32'h00000000;
        endcase
    end

    assign HRDATA    = read_data_reg;
    assign HREADYOUT = 1'b1; // Always ready (0 wait states)
    assign HRESP     = 1'b0; // OKAY response
    
    assign timer_int = int_status & int_en;

endmodule
