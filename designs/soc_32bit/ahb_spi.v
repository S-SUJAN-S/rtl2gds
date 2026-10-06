module ahb_spi (
    // AHB-Lite Interface
    input  wire        HCLK,
    input  wire        HRESETn,
    input  wire [31:0] HADDR,
    input  wire [31:0] HWDATA,
    input  wire        HWRITE,
    input  wire        HSEL,
    input  wire        HREADY,
    input  wire [1:0]  HTRANS,
    output wire [31:0] HRDATA,
    output wire        HREADYOUT,
    output wire [1:0]  HRESP,
    
    // SPI Interface
    output wire        spi_sclk,
    output wire        spi_mosi,
    input  wire        spi_miso,
    output wire        spi_cs_n
);

    // AHB-Lite Transfer Types
    localparam HTRANS_NONSEQ = 2'b10;
    localparam HTRANS_SEQ    = 2'b11;
    
    // Registers mapping
    // 0x00: CTRL (31:16 = DIV, 2 = CPOL, 1 = CPHA, 0 = START)
    // 0x04: STATUS (0 = BUSY)
    // 0x08: TXDATA
    // 0x0C: RXDATA
    
    reg [31:0] ctrl_reg;
    reg [31:0] tx_data_reg;
    reg [31:0] rx_data_reg;
    wire       busy;
    
    // AHB write phase control
    reg [31:0] addr_reg;
    reg        write_en;
    
    wire ahb_valid = HSEL && HREADY && (HTRANS == HTRANS_NONSEQ || HTRANS == HTRANS_SEQ);
    
    always @(posedge HCLK or negedge HRESETn) begin
        if (!HRESETn) begin
            addr_reg <= 32'h0;
            write_en <= 1'b0;
        end else begin
            if (ahb_valid) begin
                addr_reg <= HADDR;
                write_en <= HWRITE;
            end else begin
                write_en <= 1'b0;
            end
        end
    end
    
    wire start_pulse = write_en && (addr_reg[7:0] == 8'h00) && HWDATA[0];
    
    always @(posedge HCLK or negedge HRESETn) begin
        if (!HRESETn) begin
            ctrl_reg    <= 32'h0;
            tx_data_reg <= 32'h0;
        end else begin
            if (write_en) begin
                case (addr_reg[7:0])
                    8'h00: ctrl_reg    <= {HWDATA[31:1], 1'b0}; // Auto-clear start bit
                    8'h08: tx_data_reg <= HWDATA;
                    default: ;
                endcase
            end
        end
    end
    
    // AHB read response
    reg [31:0] hrdata_reg;
    always @(*) begin
        case (addr_reg[7:0])
            8'h00: hrdata_reg = ctrl_reg;
            8'h04: hrdata_reg = {31'h0, busy};
            8'h0C: hrdata_reg = rx_data_reg;
            default: hrdata_reg = 32'h0;
        endcase
    end
    
    assign HRDATA    = hrdata_reg;
    assign HREADYOUT = 1'b1;
    assign HRESP     = 2'b00; // OKAY
    
    // SPI Engine
    wire [15:0] clk_div = ctrl_reg[31:16];
    wire        cpol    = ctrl_reg[2];
    wire        cpha    = ctrl_reg[1];
    
    reg [15:0] clk_cnt;
    reg [3:0]  bit_cnt;
    reg        sclk_reg;
    reg        cs_n_reg;
    reg [7:0]  shift_tx;
    reg [7:0]  shift_rx;
    
    localparam IDLE = 2'b00;
    localparam PHASE1 = 2'b01;
    localparam PHASE2 = 2'b10;
    localparam DONE = 2'b11;
    
    reg [1:0] state;
    
    assign busy = (state != IDLE) || start_pulse;
    
    always @(posedge HCLK or negedge HRESETn) begin
        if (!HRESETn) begin
            state    <= IDLE;
            clk_cnt  <= 16'h0;
            bit_cnt  <= 4'h0;
            sclk_reg <= 1'b0;
            cs_n_reg <= 1'b1;
            shift_tx <= 8'h0;
            shift_rx <= 8'h0;
            rx_data_reg <= 32'h0;
        end else begin
            if (state == IDLE) begin
                sclk_reg <= cpol;
                cs_n_reg <= 1'b1;
                if (start_pulse) begin
                    state    <= PHASE1;
                    clk_cnt  <= clk_div;
                    bit_cnt  <= 4'h0;
                    cs_n_reg <= 1'b0;
                    shift_tx <= tx_data_reg[7:0];
                end
            end else begin
                if (clk_cnt != 16'h0) begin
                    clk_cnt <= clk_cnt - 1;
                end else begin
                    clk_cnt <= clk_div;
                    
                    if (state == PHASE1) begin
                        sclk_reg <= ~sclk_reg;
                        state    <= PHASE2;
                        if (cpha == 1'b0) begin
                            shift_rx <= {shift_rx[6:0], spi_miso};
                        end else begin
                            shift_tx <= {shift_tx[6:0], 1'b0};
                        end
                    end else if (state == PHASE2) begin
                        sclk_reg <= ~sclk_reg;
                        if (cpha == 1'b0) begin
                            shift_tx <= {shift_tx[6:0], 1'b0};
                        end else begin
                            shift_rx <= {shift_rx[6:0], spi_miso};
                        end
                        
                        if (bit_cnt == 4'h7) begin
                            state <= DONE;
                        end else begin
                            state   <= PHASE1;
                            bit_cnt <= bit_cnt + 1;
                        end
                    end else if (state == DONE) begin
                        state <= IDLE;
                        cs_n_reg <= 1'b1;
                        sclk_reg <= cpol;
                        rx_data_reg <= {24'h0, shift_rx};
                    end
                end
            end
        end
    end
    
    assign spi_sclk = sclk_reg;
    assign spi_cs_n = cs_n_reg;
    assign spi_mosi = (state != IDLE && cs_n_reg == 1'b0) ? shift_tx[7] : 1'b0;

endmodule
