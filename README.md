# SiliconFlow-AI: Autonomous RTL-to-GDSII EDA Pipeline 🚀

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![PDK: SkyWater 130nm](https://img.shields.io/badge/PDK-SkyWater%20130nm-orange.svg)](https://github.com/google/skywater-pdk)
[![EDA: OpenLane & Yosys](https://img.shields.io/badge/EDA-OpenLane%20%7C%20Yosys%20%7C%20OpenROAD-green.svg)](https://github.com/The-OpenROAD-Project)
[![AI Engine: Groq & Gemini](https://img.shields.io/badge/AI%20Engine-Groq%20%7C%20Gemini%20%7C%20OpenRouter-purple.svg)](https://console.groq.com)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)

**SiliconFlow-AI** is an enterprise-grade autonomous physical design platform that bridges generative AI with production Electronic Design Automation (EDA) toolchains. It automatically takes natural language specifications or Verilog RTL, performs closed-loop lint and simulation repair, drives logic synthesis on the **SkyWater 130nm (sky130)** PDK, enforces static timing closure, and outputs manufacturable GDSII silicon masks.

---

## 🏛️ Autonomous Multi-Agent Architecture

SiliconFlow-AI organizes the digital ASIC design cycle into **7 specialized AI agents** operating in a closed-loop Evaluator-Optimizer structure:

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   SILICONFLOW-AI PIPELINE FLOW                                   │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                  │
                                                  ▼
                                      ┌───────────────────────┐
                                      │   Natural Language /  │
                                      │   Micro-Arch Prompt   │
                                      └───────────┬───────────┘
                                                  │
                                                  ▼
                                      ┌───────────────────────┐
                                      │ 1. Spec Parser Agent  │
                                      └───────────┬───────────┘
                                                  │
                                                  ▼
                                      ┌───────────────────────┐
                                      │  2. RTL Coder Agent   │ <───────┐ (Closed-Loop
                                      └───────────┬───────────┘         │  Lint Repair)
                                                  │                     │
                                                  ▼                     │
                                      ┌───────────────────────┐         │
                                      │  3. Lint ECO Agent    │ ────────┘
                                      │  (Verilator AST Linter)
                                      └───────────┬───────────┘
                                                  │
                                                  ▼
                                      ┌───────────────────────┐
                                      │ 4. TB Generator Agent │ <───────┐ (Closed-Loop
                                      └───────────┬───────────┘         │  Sim Repair)
                                                  │                     │
                                                  ▼                     │
                                      ┌───────────────────────┐         │
                                      │  5. Sim ECO Agent     │ ────────┘
                                      │  (Icarus Verilog Sim) │
                                      └───────────┬───────────┘
                                                  │
                                                  ▼
                                      ┌───────────────────────┐
                                      │ 6. Synthesis Agent    │
                                      │ (Yosys + sky130 PDK)  │
                                      └───────────┬───────────┘
                                                  │
                                                  ▼
                                      ┌───────────────────────┐
                                      │ 7. STA & Signoff Agent│
                                      │ (OpenSTA + OpenROAD)  │
                                      └───────────┬───────────┘
                                                  │
                                                  ▼
                                      ┌───────────────────────┐
                                      │ Manufacturable GDSII  │
                                      │ + HTML Dark Dashboard │
                                      └───────────────────────┘
```

---

## ⚡ The 7 Autonomous Agents in Action

| # | Agent Name | Core Responsibilities & Oracles |
| :- | :--- | :--- |
| **1** | **SpecParserAgent** | Ingests hardware requirements and compiles structured JSON microarchitecture specifications (clock domains, reset polarities, port bitwidths). |
| **2** | **RTLCoderAgent** | Generates synthesizable Verilog-2005 hardware description conforming to strict ASIC guidelines (no latches, non-blocking clocked logic). |
| **3** | **LintECOAgent** | Runs **Verilator (`--lint-only`)**, captures syntax and semantic errors, and performs autonomous AST repairs until 0 errors remain. |
| **4** | **TBGeneratorAgent**| Generates self-checking testbenches with constrained random stimulus and SystemVerilog Assertions (SVA). |
| **5** | **SimECOAgent** | Executes **Icarus Verilog (`iverilog` / `vvp`)**, monitors assertions and waveform strobes, and fixes functional regressions. |
| **6** | **SynthAgent** | Drives **Yosys** logic synthesis targeting `sky130_fd_sc_hd` standard cells, generating gate-level netlists and area breakdowns. |
| **7** | **STAECOAgent** | Evaluates setup and hold slacks with **OpenSTA**, flags critical path bottlenecks, proposes buffer insertion ECOs, and generates dark-mode analytics dashboards. |

---

## 💎 Silicon-Proven Featured Accelerators

This repository contains verified hardware blocks compiled through the complete physical flow:

1. **8x8 Systolic Array Matrix Multiplication Engine**
   - **Architecture:** 64 Processing Elements (PEs) with signed multiply-accumulators (MACs) and weight-stationary dataflow.
   - **Metrics:** 50 MHz Target | 2.9ns Critical Path | 0.9 mm² Die Area | 140,546 Physical Standard Cells.
   - **Status:** Timing Clean, Zero DRC/LVS Violations.
2. **100MHz Configurable UART Transceiver**
   - **Architecture:** Complete TX/RX sub-blocks with internal baud rate generator and circular FIFO buffers.
   - **Status:** Timing Clean, Zero DRC/LVS Violations.
3. **4-Bit Arithmetic Logic Unit (ALU)**
   - **Architecture:** Combinational ALU supporting 8 arithmetic and bitwise logic operations.
   - **Status:** Formally Verified, Full Tapeout Mask Exported.
4. **Synchronous FIFO & AXI4-Lite SRAM Controller**
   - Standard industrial memory and interface IPs for on-chip interconnects.

---

## 🚀 Quickstart & Setup

SiliconFlow-AI runs completely on **free, high-speed cloud AI APIs** (Groq, Gemini, OpenRouter), requiring zero local GPU memory or heavy local model downloads.

### 1. Clone & Setup Environment
```bash
git clone https://github.com/S-SUJAN-S/rtl2gds.git
cd rtl2gds
cp .env.example .env
```

### 2. Configure a Free API Key (Choose Either):
Edit `.env` or export in your terminal:
* **Option A: Groq Cloud (Recommended: 500+ tokens/sec)**  
  Get a free key at [console.groq.com/keys](https://console.groq.com/keys):
  ```bash
  export GROQ_API_KEY="gsk_..."
  ```
* **Option B: Google Gemini (1M token context free tier)**  
  Get a free key at [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey):
  ```bash
  export GEMINI_API_KEY="AIza..."
  ```

### 3. Run the Autonomous Pipeline
Synthesize any pre-configured design:
```bash
# Run ALU through lint, simulation, synthesis, and STA signoff
python run_pipeline.py --design alu4bit --provider groq

# Run UART Transceiver targeting 100MHz
python run_pipeline.py --design uart_tx --provider gemini

# Execute full 4-design canonical benchmark suite
python run_pipeline.py --test-all
```

### 4. Synthesize from Natural Language Prompt
```bash
python run_pipeline.py --design custom_counter --prompt "8-bit up-down counter with synchronous reset, enable, and overflow flag"
```

---

## 📊 Outputs & Artifacts

After each run, inspection artifacts are exported directly to `outputs/pipeline_runs/<design>/<timestamp>/`:
* `<design>.v` — Clean synthesizable Verilog RTL
* `<design>_tb.v` — Self-checking verification testbench
* `<design>_netlist.v` — Mapped gate-level netlist
* `<design>.sdc` — Synopsys/Cadence timing constraints
* `<design>_sta.rpt` — Full path slack report
* `dashboard.html` — Interactive dark-mode silicon health dashboard
* `signoff_report.md` — Formal tapeout readiness summary

---

## 🛠️ Toolchain Prerequisites (Physical Execution)

* **Python:** 3.10+ (Standard library only; zero mandatory third-party packages)
* **EDA Tools (via WSL or Native Linux):**
  - **Verilator** (`verilator --lint-only`)
  - **Icarus Verilog** (`iverilog`, `vvp`)
  - **Yosys** (Open-source synthesis)
  - **OpenSTA / OpenROAD** (Timing and physical design)
  - **KLayout** (GDSII layout inspection)

---

## 👨‍💻 Author & Attribution

Developed by **Sujan S**  
Independent Hardware AI & Autonomous EDA Researcher  
- **GitHub:** [@S-SUJAN-S](https://github.com/S-SUJAN-S)  
- **Portfolio Repository:** [rtl2gds](https://github.com/S-SUJAN-S/rtl2gds)

---

## 📜 License
This project is licensed under the [MIT License](LICENSE).
