module ahb_uart (
    input wire HCLK,
    input wire HRESETn,
    
    // AHB-Lite Slave Interface
    input wire [31:0] HADDR,
    input wire [1:0] HTRANS,
    input wire HWRITE,
    input wire [2:0] HSIZE,
    input wire [2:0] HBURST,
    input wire [3:0] HPROT,
    input wire [31:0] HWDATA,
    input wire HSEL,
    input wire HREADY,
    
    output reg [31:0] HRDATA,
    output wire HREADYOUT,
    output wire [1:0] HRESP,
    
    // UART External Signals
    input wire rx,
    output wire tx
);

    // AHB-Lite response
    assign HREADYOUT = 1'b1; // Always ready
    assign HRESP = 2'b00; // OKAY

    // Register map:
    // 0x00: TX/RX Data (Read/Write) - Write to transmit, read to receive
    // 0x04: Status (Read only) - [1] TX_FULL, [0] RX_EMPTY
    // 0x08: Baud rate divisor (Read/Write)

    // Internal state
    reg [31:0] baud_div;
    reg [7:0] tx_data;
    reg tx_valid;
    wire tx_ready;
    
    wire [7:0] rx_data;
    wire rx_valid;
    reg rx_ready;
    
    // AHB address decoding
    reg ahb_write_en;
    reg [31:0] ahb_addr_reg;
    
    always @(posedge HCLK or negedge HRESETn) begin
        if (!HRESETn) begin
            ahb_write_en <= 1'b0;
            ahb_addr_reg <= 32'h0;
        end else begin
            if (HSEL && HREADY && (HTRANS == 2'b10 || HTRANS == 2'b11)) begin
                ahb_write_en <= HWRITE;
                ahb_addr_reg <= HADDR;
            end else begin
                ahb_write_en <= 1'b0;
            end
        end
    end

    // Status flags
    reg rx_empty;
    reg tx_full;
    
    // AHB Write
    always @(posedge HCLK or negedge HRESETn) begin
        if (!HRESETn) begin
            baud_div <= 32'd434; // Default for 115200 at 50MHz
            tx_valid <= 1'b0;
            tx_data <= 8'h0;
            rx_ready <= 1'b0;
        end else begin
            tx_valid <= 1'b0;
            rx_ready <= 1'b0;
            
            if (ahb_write_en) begin
                case (ahb_addr_reg[3:0])
                    4'h0: begin // Write to TX Data
                        tx_data <= HWDATA[7:0];
                        tx_valid <= 1'b1;
                    end
                    4'h8: begin // Write to Baud Divisor
                        baud_div <= HWDATA;
                    end
                    default: ;
                endcase
            end else if (HSEL && HREADY && !HWRITE && (HTRANS == 2'b10 || HTRANS == 2'b11) && HADDR[3:0] == 4'h0) begin
                // Reading data
                rx_ready <= 1'b1;
            end
        end
    end

    // AHB Read
    always @(*) begin
        HRDATA = 32'h0;
        if (HSEL && HREADY && !HWRITE && (HTRANS == 2'b10 || HTRANS == 2'b11)) begin
            case (HADDR[3:0])
                4'h0: HRDATA = {24'h0, rx_data_reg}; // Reading RX data
                4'h4: HRDATA = {30'h0, tx_full, rx_empty}; // Reading Status
                4'h8: HRDATA = baud_div; // Reading Baud Divisor
                default: HRDATA = 32'h0;
            endcase
        end
    end
    
    // UART RX FIFO/Register
    reg [7:0] rx_data_reg;
    always @(posedge HCLK or negedge HRESETn) begin
        if (!HRESETn) begin
            rx_empty <= 1'b1;
            rx_data_reg <= 8'h0;
        end else begin
            if (rx_valid) begin
                rx_data_reg <= rx_data;
                rx_empty <= 1'b0;
            end else if (rx_ready) begin
                rx_empty <= 1'b1;
            end
        end
    end
    
    always @(posedge HCLK or negedge HRESETn) begin
        if (!HRESETn) begin
            tx_full <= 1'b0;
        end else begin
            if (tx_valid) begin
                tx_full <= 1'b1;
            end else if (tx_ready) begin
                tx_full <= 1'b0;
            end
        end
    end

    // UART TX Logic
    reg [31:0] tx_baud_counter;
    reg [3:0] tx_state; // 0: idle, 1: start, 2-9: data, 10: stop
    reg [7:0] tx_shift_reg;
    reg tx_reg;
    
    assign tx = tx_reg;
    assign tx_ready = (tx_state == 0) && tx_full;
    
    always @(posedge HCLK or negedge HRESETn) begin
        if (!HRESETn) begin
            tx_baud_counter <= 32'h0;
            tx_state <= 4'h0;
            tx_reg <= 1'b1;
            tx_shift_reg <= 8'h0;
        end else begin
            if (tx_state == 0) begin
                tx_reg <= 1'b1;
                if (tx_full) begin
                    tx_shift_reg <= tx_data;
                    tx_state <= 4'h1;
                    tx_baud_counter <= baud_div;
                end
            end else begin
                if (tx_baud_counter == 32'h0) begin
                    tx_baud_counter <= baud_div;
                    case (tx_state)
                        4'h1: begin // Start bit
                            tx_reg <= 1'b0;
                            tx_state <= 4'h2;
                        end
                        4'h2, 4'h3, 4'h4, 4'h5, 4'h6, 4'h7, 4'h8, 4'h9: begin // Data bits
                            tx_reg <= tx_shift_reg[0];
                            tx_shift_reg <= {1'b0, tx_shift_reg[7:1]};
                            tx_state <= tx_state + 1'b1;
                        end
                        4'hA: begin // Stop bit
                            tx_reg <= 1'b1;
                            tx_state <= 4'h0;
                        end
                        default: tx_state <= 4'h0;
                    endcase
                end else begin
                    tx_baud_counter <= tx_baud_counter - 1'b1;
                end
            end
        end
    end

    // UART RX Logic
    reg [31:0] rx_baud_counter;
    reg [3:0] rx_state; // 0: idle, 1: start wait, 2: start mid, 3-10: data, 11: stop
    reg [7:0] rx_shift_reg;
    reg rx_reg_1, rx_reg_2;
    
    assign rx_data = rx_shift_reg;
    assign rx_valid = (rx_state == 4'hB) && (rx_baud_counter == 32'h0);
    
    always @(posedge HCLK or negedge HRESETn) begin
        if (!HRESETn) begin
            rx_reg_1 <= 1'b1;
            rx_reg_2 <= 1'b1;
        end else begin
            rx_reg_1 <= rx;
            rx_reg_2 <= rx_reg_1;
        end
    end
    
    always @(posedge HCLK or negedge HRESETn) begin
        if (!HRESETn) begin
            rx_baud_counter <= 32'h0;
            rx_state <= 4'h0;
            rx_shift_reg <= 8'h0;
        end else begin
            case (rx_state)
                4'h0: begin // Idle
                    if (rx_reg_2 == 1'b0) begin
                        rx_state <= 4'h1;
                        rx_baud_counter <= {1'b0, baud_div[31:1]}; // Half baud period
                    end
                end
                4'h1: begin // Start mid
                    if (rx_baud_counter == 32'h0) begin
                        if (rx_reg_2 == 1'b0) begin
                            rx_state <= 4'h3;
                            rx_baud_counter <= baud_div;
                        end else begin
                            rx_state <= 4'h0; // False start
                        end
                    end else begin
                        rx_baud_counter <= rx_baud_counter - 1'b1;
                    end
                end
                4'h3, 4'h4, 4'h5, 4'h6, 4'h7, 4'h8, 4'h9, 4'hA: begin // Data bits
                    if (rx_baud_counter == 32'h0) begin
                        rx_shift_reg <= {rx_reg_2, rx_shift_reg[7:1]};
                        rx_state <= rx_state + 1'b1;
                        rx_baud_counter <= baud_div;
                    end else begin
                        rx_baud_counter <= rx_baud_counter - 1'b1;
                    end
                end
                4'hB: begin // Stop bit wait
                    if (rx_baud_counter == 32'h0) begin
                        rx_state <= 4'h0;
                    end else begin
                        rx_baud_counter <= rx_baud_counter - 1'b1;
                    end
                end
                default: rx_state <= 4'h0;
            endcase
        end
    end

endmodule
