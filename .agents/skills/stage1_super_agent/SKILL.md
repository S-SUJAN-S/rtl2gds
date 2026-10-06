---
name: stage1_super_agent
description: Stage 1 Front-End RTL Design & Verification Super-Agent Orchestrator driving 11 specialized sub-agents with the Gemini Pro reasoning model tier and strict zero-hallucination web-search verification policy.
---

# Stage 1 Front-End RTL & Verification Super-Agent

This skill defines the **Stage 1 Super-Agent** and its **11 specialized sub-agents** for digital ASIC front-end engineering in Antigravity. Every agent uses the high-reasoning **`pro`** model tier.

## 🛡️ Strict Zero-Hallucination & Web Search Policy
1. **Fact Checking & Verification:** No sub-agent is permitted to guess or hallucinate hardware specifications, Verilator warning flags, or SDC constraint rules.
2. **Dynamic Web Search Fallback:** If an agent encounters unknown PDK specifications or undocumented EDA tool errors, it must perform a web search (`search_web`) or inspect authoritative documentation.
3. **Independent Verification Sub-Agent:** Sub-agent `1.10_verifier` independently audits all stage deliverables for physical correctness before signoff.

## 🤖 Sub-Agent Roster

1. **`subagent_1_1_microarch` (Micro-Architecture Spec Agent)**: Defines hardware registers, FSM state diagrams, and pinouts.
2. **`subagent_1_2_rtl_coder` (RTL Hardware Coder Agent)**: Writes clean synthesizable Verilog/SystemVerilog (`.v`, `.sv`).
3. **`subagent_1_3_static_linter` (Static Lint & Auto-Patch Agent)**: Runs Verilator linting and patches latches, width truncations, and un-driven nets.
4. **`subagent_1_4_cdc_auditor` (CDC & RDC Auditor Agent)**: Verifies multi-clock 2-stage flip-flop synchronizers and async FIFOs.
5. **`subagent_1_5_tb_bfm_setup` (Testbench Architecture Agent)**: Builds SystemVerilog testbenches, BFMs, and reference models.
6. **`subagent_1_6_directed_sim` (Directed Simulation Agent)**: Executes Icarus Verilog (`iverilog`/`vvp`) simulation and checks assertions.
7. **`subagent_1_7_random_testing` (Constrained-Random Stimulus Agent)**: Injects randomized inputs to discover corner-case bugs.
8. **`subagent_1_8_code_coverage` (Code Coverage Agent)**: Analyzes Line, Branch, Toggle, and FSM Coverage targets.
9. **`subagent_1_9_functional_sva` (Functional Coverage & SVA Agent)**: Evaluates Covergroups and SystemVerilog Assertions.
10. **`subagent_1_10_verifier` (Output Verification & Fact-Checking Agent)**: Independently audits all outputs for correctness and zero hallucination.
11. **`subagent_1_11_signoff_gate` (Signoff Review Gatekeeper)**: Enforces Stage 1 signoff readiness criteria.
