# Stage 1: Front-End RTL Design & Verification Guide 🚀

Welcome to the comprehensive reference guide for **Stage 1 (Front-End RTL Design & Verification)** of the digital ASIC physical design flow. 

Discovering bugs in Stage 1 is **100x cheaper** than finding them during physical layout or after silicon fabrication. This document breaks down the **10 sub-steps** required to take a hardware architecture from concept to front-end signoff readiness.

---

## 🏗️ Architecture & Workflow Sitemap

```
                             STAGE 1: FRONT-END RTL & VERIFICATION
                                              │
  ┌───────────────────────────────────────────┴───────────────────────────────────────────┐
  │                                                                                       │
  ▼                                                                                       ▼
[ RTL DESIGN PHASE ]                                                     [ VERIFICATION PHASE ]
 1.1 Micro-Arch Spec                                                      1.5 Testbench & BFM Setup
 1.2 RTL Coding (.v / .sv)                                                1.6 Directed Simulation
 1.3 Static Linting (Verilator)                                           1.7 Constrained-Random Testing
 1.4 CDC & RDC Audit                                                      1.8 Code Coverage Analysis
                                                                          1.9 Functional & SVA Coverage
                                              │                                   │
                                              └───────────────────┬───────────────┘
                                                                  ▼
                                                   1.10 Front-End Signoff Gate
```

---

## 📌 1. RTL Design Phase

### 1.1 Micro-Architecture Specification & Block Interface Definition
* **Goal:** Establish block-level hardware requirements, interfaces, and state diagrams before writing RTL code.
* **Key Tasks:**
  - Define module pinouts, bus width parameters, reset strategies (synchronous vs. asynchronous), and clock frequencies.
  - Choose interface protocols (e.g., AXI4-Lite, APB, Wishbone, or custom valid/ready handshakes).
  - Draw Finite State Machine (FSM) state transition diagrams and pipeline stage timing charts.
* **Primary Output:** Micro-Architecture Specification Document (`.md` / `.pdf`).

---

### 1.2 RTL Hardware Coding (.v / .sv)
* **Goal:** Implement hardware specifications using synthesizable Verilog / SystemVerilog constructs.
* **Key Tasks:**
  - Separate **Datapath** (ALUs, adders, multipliers, shift registers) from **Control Path** (FSMs, decoders, control logic).
  - Use non-blocking assignments (`<=`) exclusively in sequential logic (`always @(posedge clk)`).
  - Use blocking assignments (`=`) exclusively in combinational logic (`always @(*)`).
* **Code Example (Clean FSM Pattern):**
  ```verilog
  typedef enum logic [1:0] { IDLE, PROCESS, DONE } state_t;
  state_t current_state, next_state;

  // Sequential State Register
  always_ff @(posedge clk or negedge rst_n) begin
      if (!rst_n) current_state <= IDLE;
      else        current_state <= next_state;
  end

  // Combinational Next State & Output Logic
  always_comb begin
      next_state = current_state;
      case (current_state)
          IDLE:    if (start) next_state = PROCESS;
          PROCESS: if (ready) next_state = DONE;
          DONE:    next_state = IDLE;
          default: next_state = IDLE;
      endcase
  end
  ```

---

### 1.3 Static Code Linting (Verilator / SpyGlass)
* **Goal:** Detect structural, syntactic, and synthesis-invalid coding patterns without running simulation.
* **Tools:** Verilator (`verilator --lint-only -Wall`)
* **Key Checks:**
  - **`LATCH` / `UNOPTFLAT`:** Detects incomplete `if/else` or missing `default:` branches in combinational logic that infer unwanted transparent latches.
  - **`WIDTH`:** Detects implicit bit truncation or zero-padding in bus operations.
  - **`BLKANDNBLK`:** Catches dangerous mixing of blocking (`=`) and non-blocking (`<=`) assignments to the same register.
  - **`UNDRIVEN` / `UNUSED`:** Identifies floating nets or unused module outputs.

---

### 1.4 Clock Domain Crossing (CDC) & Reset Domain Crossing (RDC) Audit
* **Goal:** Eliminate metastability hazards when signals cross between different clock domains.
* **Key Tasks:**
  - Audit multi-clock interfaces for proper synchronization techniques (e.g., 2-stage flip-flop synchronizers for single-bit signals, Asynchronous FIFOs with Gray Code pointers for multi-bit data buses).
  - Verify Reset Domain Crossing (RDC) to prevent reset assertion/de-assertion glitches across clock domains.

---

## 🧪 2. Verification Phase

### 1.5 Testbench & Bus Functional Model (BFM) Setup
* **Goal:** Build an automated environment to drive inputs and verify block outputs against expected behavior.
* **Tools:** SystemVerilog, UVM (Universal Verification Methodology), Verilator C++ Wrappers.
* **Key Components:**
  - **Generator / Sequence:** Creates transaction stimulus.
  - **Driver & BFM:** Translates high-level transactions into pin-level signal toggles.
  - **Monitor:** Captures pin transitions and converts them into output transactions.
  - **Scoreboard:** Compares actual output against golden reference models (e.g., Python/C++ models).

---

### 1.6 Directed Functional Simulation
* **Goal:** Verify happy-path behavior, basic functionality, and boundary test cases.
* **Tools:** Icarus Verilog (`iverilog`), VVP, GTKWave.
* **Workflow:**
  1. Compile RTL + Testbench: `iverilog -g2012 -o build/sim.out top.v top_tb.v`
  2. Run Simulation: `vvp build/sim.out`
  3. Inspect VCD Waveforms: `gtkwave dump.vcd`
  4. Verify expected output responses using `$display` and `$fatal`.

---

### 1.7 Constrained-Random Testing (CRV)
* **Goal:** Uncover complex, unanticipated corner-case bugs that human directed tests miss.
* **Key Tasks:**
  - Generate randomized input values (packet lengths, random delays, random addresses) constrained to legal operating ranges.
  - Stress-test backpressure stalls, buffer overflows, and state machine deadlocks.

---

### 1.8 Code Coverage Analysis
* **Goal:** Quantify how much of the written RTL code was actually exercised by the testsuite.
* **4 Coverage Metrics Tracked:**
  1. **Line / Statement Coverage:** Did every line of code execute at least once?
  2. **Branch Coverage:** Were both `true` and `false` paths of every `if/else` and `case` branch taken?
  3. **Toggle Coverage:** Did every net and register toggle from $0 \rightarrow 1$ and $1 \rightarrow 0$?
  4. **FSM Coverage:** Was every state visited, and was every state transition arc traversed?

---

### 1.9 Functional Coverage & Assertion-Based Verification (ABV)
* **Goal:** Verify that all high-level specification features were tested and internal invariants hold.
* **Key Mechanisms:**
  - **Functional Coverage (Covergroups & Coverpoints):** Tracks whether target protocol conditions occurred (e.g., "Buffer Full while Read and Write occur simultaneously").
  - **SystemVerilog Assertions (SVA):** Embedded inline property checks that continuously monitor internal protocol rules.
  ```verilog
  // SVA Example: Request must be followed by Grant within 1 to 3 cycles
  property p_req_gnt;
      @(posedge clk) disable iff (!rst_n)
      req |-> ##[1:3] gnt;
  endproperty
  assert property (p_req_gnt) else $error("Protocol Violation: Grant timed out!");
  ```

---

## 🚪 1.10 Front-End Signoff & Freeze Gate

Before code is locked and cleared for **Stage 2: Logic Synthesis (Yosys)**, it must pass all 4 signoff criteria:

| Metric | Target | Status |
| :--- | :--- | :---: |
| **Directed & Random Test Suite** | 100% Pass (0 Errors) | ✅ |
| **Line & Branch Code Coverage** | 100% Target Met | ✅ |
| **Functional Coverage** | >95% Target Met | ✅ |
| **Verilator Static Lint Audit** | 0 Warnings / 0 Errors | ✅ |

---

*File generated and saved in repository under [`docs/stage_1_rtl_and_verification_guide.md`](file:///c:/Users/ssuja/OneDrive/Desktop/Learn_Antigravity_Advance/rtl-2-gds-automation/docs/stage_1_rtl_and_verification_guide.md)*.
