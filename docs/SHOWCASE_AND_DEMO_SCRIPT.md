# SiliconFlow-AI: YouTube Video Showcase & Technical Demo Script 🎥

**Project:** `rtl-2-gds-automation-local-llm` (SiliconFlow-AI)  
**Author & Presenter:** Sujan S ([@S-SUJAN-S](https://github.com/S-SUJAN-S))  
**Title:** Independent Hardware AI & Autonomous EDA Researcher  
**Target Channel:** BlinkNBuild ([@BlinkNBuild](https://youtube.com/@BlinkNBuild))  
**Format:** 1080p 60fps Technical Walkthrough / Screen Recording + Voiceover  
**Target Runtime:** 3 Minutes (180 Seconds)  

---

## 🎯 High-CTR YouTube Title & Metadata Suggestions

### Primary Recommended Title:
> **I Built an Autonomous AI Chip Architect: English Prompt to 130nm GDSII Silicon Tapeout in 60s 🚀**

### Alternative Titles:
* *RTL to GDSII with AI: 7 Autonomous LLM Agents Tape Out 5 Real ASICs (Zero Hallucination)*
* *SiliconFlow-AI: The Autonomous EDA Engine That Writes Verilog, Fixes Regressions & Streams GDSII*
* *Watch 7 AI Agents Design, Synthesize, and Sign Off a Real Microchip in Under 60 Seconds*

### Description Template:
```text
Can AI design real, manufacturable silicon chips without human intervention?
In this video, I walk through SiliconFlow-AI — an autonomous digital ASIC physical design framework that connects Large Language Model agents with real open-source EDA engines (Verilator, Icarus Verilog, Yosys, OpenSTA, and OpenLane on SkyWater 130nm).

From a simple natural language prompt, the framework autonomously:
1. Writes synthesizable Verilog-2005 RTL
2. Self-heals syntax and simulation regressions in a closed-loop ECO cycle
3. Maps logic gates to the SkyWater 130nm PDK (sky130_fd_sc_hd)
4. Closes timing at 100 MHz with OpenSTA
5. Drives the OpenLane Docker engine through full placement, routing, DRC, and LVS
6. Streams out tapeout-ready GDSII layouts inspected in an interactive 3D WebGL viewer!

🏆 5 Benchmark ASICs Tested & Signed Off:
- 4-Bit ALU (alu4bit)
- 115200 Baud UART Transmitter (uart_tx)
- 8-bit x 16-Entry Circular FIFO (sync_fifo)
- 8-bit Synchronous Up/Down Counter (counter_sync)
- Configurable Dual-Buffer PWM (pwm_generator)

Built & Engineered by Sujan S (@S-SUJAN-S).
Independent Hardware AI & Autonomous EDA Researcher.
```

---

## ⏱️ 3-Minute Video Timeline & Script Walkthrough

```mermaid
timeline
    title 3-Minute Technical Demonstration Flow
    00:00 - 00:30 : The Hook & Silicon Bottleneck
    00:30 - 01:00 : Architecture & The 7-Agent Swarm
    01:00 - 01:45 : Live Execution & Self-Healing ECO Demo
    01:45 - 02:30 : OpenLane Tapeout, GDSII & Silicon3D WebGL
    02:30 - 03:00 : Benchmark Signoff Matrix & Conclusion
```

---

### Act 1: The Hook (0:00 – 0:30)
* **Visual:** Split screen. On the left: terminal executing `python run_pipeline.py --test-all` with high-speed token generation (450+ tok/s). On the right: a stunning 3D exploded silicon layout of `sync_fifo.gds` rotating in the WebGL Silicon3D viewer.
* **Audio / Voiceover:**  
  *"Designing a microchip traditionally takes teams of engineers months of writing RTL, debugging timing violations, and resolving design rule checks. What if you could give an AI a plain-English specification—and within sixty seconds, have a verified, timing-closed, DRC-clean GDSII silicon layout ready for tapeout?*  
  *This is SiliconFlow-AI: an autonomous hardware design framework that connects LLM reasoning models with physical EDA toolchains on the open-source SkyWater 130nm process node. No simulated toys, no hallucinations—every single gate, micron of wire, and silicon layer you're looking at was physically placed and routed."*

---

### Act 2: Architecture & The 7-Agent Swarm (0:30 – 1:00)
* **Visual:** Full-screen animated Mermaid architecture diagram highlighting the 3 major stages: Frontend Verification, Midend Synthesis & STA, and Backend Physical Implementation.
* **Audio / Voiceover:**  
  *"At the heart of SiliconFlow-AI is a closed-loop swarm of seven specialized agents.  
  First, `SpecParserAgent` extracts clock domains, reset polarities, and interface signals into a strict JSON microarchitecture contract.  
  Next, `RTLCoderAgent` writes synthesizable Verilog-2005. But instead of trusting the LLM blindly, the code is immediately passed to `Verilator` for AST static linting. If a syntax bug is caught, `LintECOAgent` diagnoses the compiler dump and fixes it on the fly.  
  Once clean, `TBGeneratorAgent` produces self-checking testbenches with assertions, which are simulated in `Icarus Verilog`. If any assertion fails, `SimECOAgent` surgically resolves the regression.  
  Only when simulation passes 100% does the design advance to Yosys logic synthesis, OpenSTA static timing closure, and containerized OpenLane place-and-route."*

---

### Act 3: Live Execution & Self-Healing ECO Demo (1:00 – 1:45)
* **Visual:** Screencast of VS Code terminal. Sujan runs:  
  `python run_pipeline.py --design counter_sync --prompt "8-bit up-down counter with synchronous reset, load, enable, and terminal count flag"`  
  Show the fast token streaming via Groq `qwen/qwen3.8-27b`, followed by Verilator linting, automated testbench generation, simulation checks with green `[PASS]` tags, Yosys gate mapping (70 logic cells), and OpenSTA slack verification (`WNS = +8.990 ns`).
* **Audio / Voiceover:**  
  *"Let's watch this live. Here, we give the pipeline a prompt: an 8-bit synchronous up-down counter with load and terminal count flags.  
  Within 300 milliseconds, the RTL coder generates the hardware. The testbench generator sets up randomized stimulus and clock edge assertions.  
  Notice our self-healing guards: testbenches enforce strict clock strobe disciplines, preventing delta-cycle race conditions. If an LLM ever introduces secondary syntax regressions during a fix, the engine detects it and rolls back to the clean baseline.  
  In under four seconds, front-end linting, simulation, Yosys gate mapping, and static timing analysis at 100 MHz are all completely clean."*

---

### Act 4: OpenLane Tapeout, GDSII Streamout & Silicon3D WebGL (1:45 – 2:30)
* **Visual:** Transition to WSL2 OpenLane physical flow. Show terminal output of `scripts/run_openlane_physical_flow.py` running in Docker:  
  - Initial Floorplan (Die 90x90 µm)  
  - Power Delivery Network (PDN Met4/Met5 straps)  
  - Global & Detailed Placement (644 cells placed)  
  - TritonCTS Clock Tree Synthesis  
  - TritonRoute Detailed Routing (2,544 µm wirelength, 700 vias)  
  - Magic DRC (0 errors) & Netgen LVS (0 errors)  
  - GDSII binary generated (`counter_sync.gds`).  
  Then switch to browser: load `tools/gds3d-viewer/index.html` with `counter_sync.gds`, drag the Z-axis exploded slider, use the cross-section slice tool, and toggle layer visibility.
* **Audio / Voiceover:**  
  *"Now for the ultimate test: physical implementation.  
  We invoke the OpenLane Docker container targeting SkyWater 130nm. The engine automatically computes core utilization, builds the power distribution network, places all standard cells, runs clock tree synthesis, and routes the interconnects with TritonRoute.  
  Zero DRC violations. Zero LVS mismatches.  
  And here is the streamed-out GDSII file opened in our native WebGL Silicon3D viewer. Because it runs directly in the browser with custom binary stream parsing, we can explode the metal stack, inspect routing congestion, and slice into the silicon core in real time."*

---

### Act 5: Benchmark Matrix & Conclusion (2:30 – 3:00)
* **Visual:** Clean full-screen graphic of the 5-Design Benchmark Matrix showing `alu4bit`, `uart_tx`, `sync_fifo`, `counter_sync`, and `pwm_generator`, all with green 🏆 TAPE-OUT READY badges, 0 DRC, and positive timing slack. Then display author card: Sujan S (@S-SUJAN-S).
* **Audio / Voiceover:**  
  *"We didn't just test one design. We ran an exhaustive regression sweep across five distinct ASIC blocks: a 4-bit ALU, a 115200 baud UART transmitter, a circular FIFO, a synchronous counter, and a dual-buffered PWM engine.  
  Every single one achieved 100% physical signoff with zero DRC defects and closed timing at 100 MHz.  
  SiliconFlow-AI proves that combining modern reasoning models with strict EDA evaluation loops can revolutionize how we design hardware.  
  Check out the GitHub repository, star the project, and subscribe to BlinkNBuild for more autonomous AI engineering. Thanks for watching!"*

---

## 📦 Video Production Asset Checklist

| Asset Description | Disk Location | Usage in Video |
|---|---|---|
| **ALU Layout Render (PNG)** | `outputs/alu4bit/images/alu4bit_layout.png` | Act 1 & 5 B-Roll / Slide |
| **UART TX Layout Render (PNG)** | `outputs/uart_tx/images/uart_tx_layout.png` | Act 5 B-Roll |
| **Sync FIFO Layout Render (PNG)** | `outputs/sync_fifo/images/sync_fifo_layout.png` | Act 1 Intro Visual |
| **Counter Sync Layout Render (PNG)**| `outputs/counter_sync/images/counter_sync_layout.png` | Act 4 Walkthrough |
| **PWM Generator Layout Render (PNG)**| `outputs/pwm_generator/images/pwm_generator_layout.png` | Act 5 Gallery |
| **Tapeout GDSII Files** | `outputs/<design>/outputs/<design>.gds` | Physical Proof & Silicon3D Demo |
| **Silicon3D WebGL Viewer** | `tools/gds3d-viewer/index.html` | Act 1 & Act 4 Interactive Demo |
| **Empirical Metrics JSON** | `docs/benchmark_results.json` | Benchmark Graphic Data Source |
| **Signoff Report** | `docs/INTERNAL_VALIDATION_REPORT.md` | Verification Reference |

---

## 🚀 Live Recording Cheatsheet (Commands to Record)

```bash
# 1. API Key Pool & Toolchain Sanity Check
python -m unittest tests/test_model_router_pool.py -v
python -m unittest tests/test_eda_toolchain.py -v

# 2. Canonical 4-Design Benchmark Suite
python run_pipeline.py --test-all

# 3. Custom Natural Language Synthesis Demo
python run_pipeline.py --design counter_sync --prompt "8-bit up-down counter with synchronous reset, load, enable, and terminal count flag"

# 4. OpenLane Physical Flow Demo (Fast Run ~37s)
python scripts/run_openlane_physical_flow.py --design alu4bit

# 5. Launch Silicon3D Viewer
start tools/gds3d-viewer/index.html
```
