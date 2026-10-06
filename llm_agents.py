"""
llm_agents.py
=============
LLM-powered analysis agents for the RTL-to-GDS pipeline.
Built on top of model_router.py — uses local Ollama models exclusively.

Agents:
  LintAnalysisAgent    — interprets Verilator output, suggests RTL fixes
  RTLFixAgent          — auto-patches Verilog RTL using RTLCoder
  SimAnalysisAgent     — reviews simulation output
  SynthesisAgent       — reads Yosys stats, flags issues
  ECOAgent             — proposes timing/area ECO fixes
  SignoffAgent         — generates final markdown signoff report
"""

import json
import time
from pathlib import Path
from model_router import ModelRouter


# ─── Shared router instance ───────────────────────────────────────────────────

_router: ModelRouter = None

def get_router() -> ModelRouter:
    global _router
    if _router is None:
        _router = ModelRouter()
    return _router


# ─── Helper ───────────────────────────────────────────────────────────────────

def _query(prompt: str, task_type: str = "rtl", system: str = None, stream: bool = False) -> dict:
    router = get_router()
    if stream:
        print("\n" + "="*40 + "\n[LLM STREAM START]\n" + "="*40)
        generator = router.query(prompt, task_type=task_type, system=system, stream=True)
        response_text = ""
        for chunk in generator:
            print(chunk, end="", flush=True)
            response_text += chunk
        print("\n" + "="*40 + "\n[LLM STREAM END]\n" + "="*40 + "\n")
        
        # Mock the return dictionary since we streamed
        return {
            "model": "streaming_model",
            "task_type": task_type,
            "response": response_text,
            "tokens_per_sec": 0.0,
            "elapsed_sec": 0.0,
            "prompt_tokens": 0,
            "response_tokens": 0,
        }
    else:
        return router.query(prompt, task_type=task_type, system=system, stream=False)


# ─── Agent 1.3: Lint Analysis Agent ──────────────────────────────────────────

class LintAnalysisAgent:
    """
    Interprets Verilator --lint-only output.
    Categorizes issues and suggests targeted RTL fixes.
    Model: RTLCoder (task_type=rtl) for domain accuracy.
    """

    SYSTEM = (
        "You are a Verilog lint expert. Analyze Verilator output strictly. "
        "For each error or warning: identify the line, explain the root cause in 1 sentence, "
        "and provide an exact Verilog fix. Be concise and precise. No hallucination."
    )

    def analyze(self, lint_raw: str, verilog_code: str, design_name: str) -> dict:
        prompt = f"""Verilator lint output for design '{design_name}':

--- LINT OUTPUT ---
{lint_raw[:3000]}

--- VERILOG SOURCE ---
{verilog_code[:2000]}

Task:
1. Identify if the output contains ERRORS (fatal) or WARNINGS (non-fatal). 
2. If there are only warnings, do NOT claim it is an error.
3. For each issue, provide a 1-sentence explanation of the root cause.
4. Final verdict: Must be exactly LINT_PASS (if 0 errors) or LINT_FAIL (if >0 errors). Warnings do not cause LINT_FAIL.
"""
        t0  = time.time()
        res = _query(prompt, task_type="rtl", system=self.SYSTEM, stream=getattr(self, 'verbose', False))
        return {
            "agent": "LintAnalysisAgent",
            "model": res["model"],
            "elapsed_sec": round(time.time() - t0, 1),
            "tokens_per_sec": res["tokens_per_sec"],
            "analysis": res["response"],
        }


# ─── Agent 1.2: RTL Fix Agent ─────────────────────────────────────────────────

class RTLFixAgent:
    """
    Auto-patches Verilog RTL based on lint errors.
    Uses RTLCoder for domain-accurate hardware code generation.
    Returns the corrected Verilog source.
    """

    SYSTEM = (
        "You are an expert Verilog RTL engineer. Generate ONLY synthesizable, clean Verilog code. "
        "Fix EXACTLY the reported issues. Do not change logic unless required by the fix. "
        "You MUST output the ENTIRE file content including all modules, even if they are unmodified. "
        "Return ONLY the complete Verilog code wrapped in ```verilog ... ```, no commentary."
    )

    def fix(self, verilog_code: str, errors: list, warnings: list, design_name: str) -> dict:
        issues = "\n".join(f"- {e}" for e in errors + warnings)
        prompt = f"""Fix the following Verilog file for design '{design_name}' to resolve all reported issues.
IMPORTANT: The file may contain multiple modules. You MUST output the entire file with all modules included.

ISSUES TO FIX:
{issues}

CURRENT VERILOG:
```verilog
{verilog_code}
```

Return ONLY the corrected complete Verilog file in a ```verilog block, no commentary.
"""
        t0  = time.time()
        res = _query(prompt, task_type="rtl", system=self.SYSTEM, stream=getattr(self, 'verbose', False))
        # Extract Verilog block if wrapped in ```
        response = res["response"]
        if "```verilog" in response:
            parts = response.split("```verilog")
            if len(parts) > 1:
                response = parts[1].split("```")[0].strip()
        elif "```" in response:
            parts = response.split("```")
            if len(parts) > 1:
                response = parts[1].strip()

        return {
            "agent": "RTLFixAgent",
            "model": res["model"],
            "elapsed_sec": round(time.time() - t0, 1),
            "fixed_verilog": response,
        }


# ─── Agent 1.6: Simulation Analysis Agent ────────────────────────────────────

class SimAnalysisAgent:
    """
    Reviews iverilog simulation output.
    Identifies functional failures, assertion violations, and timing issues.
    """

    SYSTEM = (
        "You are a digital verification engineer. Analyze simulation logs critically. "
        "Identify functional failures, unexpected outputs, and missing assertions. "
        "Provide a clear PASS/FAIL verdict with evidence from the log."
    )

    def analyze(self, sim_output: str, design_name: str) -> dict:
        prompt = f"""Analyze this Icarus Verilog simulation output for '{design_name}':

--- SIMULATION OUTPUT ---
{sim_output[:3000]}

Task:
1. Verdict: SIM_PASS or SIM_FAIL
2. List any failures or unexpected outputs (with timestamps if available).
3. List what was verified successfully.
4. Confidence score: 0-100%.
"""
        t0  = time.time()
        res = _query(prompt, task_type="complex", system=self.SYSTEM, stream=getattr(self, 'verbose', False))
        return {
            "agent": "SimAnalysisAgent",
            "model": res["model"],
            "elapsed_sec": round(time.time() - t0, 1),
            "analysis": res["response"],
        }


# ─── Agent 2.1: Synthesis Analysis Agent ─────────────────────────────────────

class SynthesisAnalysisAgent:
    """
    Analyzes Yosys synthesis statistics.
    Flags area issues, checks cell library mapping, estimates timing.
    """

    SYSTEM = (
        "You are a digital ASIC synthesis engineer specializing in SkyWater 130nm (sky130). "
        "Analyze Yosys synthesis stats critically based ONLY on the provided text. "
        "Do NOT invent or suggest generic Yosys passes (like PROC_RMDEAD). "
        "Be precise and factual based on the cell breakdown provided."
    )

    def analyze(self, synth_stats: str, design_name: str,
                cell_count: int, wire_count: int) -> dict:
        prompt = f"""Analyze Yosys synthesis results for design '{design_name}':

Cell count : {cell_count}
Wire count : {wire_count}

--- YOSYS STATS OUTPUT ---
{synth_stats[:4000]}

Task:
1. Is the synthesis successful? SYNTH_PASS or SYNTH_FAIL based on the logs.
2. Analyze the specific Cell Breakdown provided in the stats. What does this design primarily consist of?
3. Area assessment: Small/Medium/Large for sky130 target.
4. Any critical warnings actually present in the stats text.
"""
        t0  = time.time()
        res = _query(prompt, task_type="rtl", system=self.SYSTEM, stream=getattr(self, 'verbose', False))
        return {
            "agent": "SynthesisAnalysisAgent",
            "model": res["model"],
            "elapsed_sec": round(time.time() - t0, 1),
            "analysis": res["response"],
        }


# ─── Agent 2.6: ECO Agent ────────────────────────────────────────────────────

class ECOAgent:
    """
    Proposes Engineering Change Orders (ECOs) for timing/area issues.
    Generates actionable Tcl commands for OpenROAD/OpenSTA.
    """

    SYSTEM = (
        "You are an ASIC ECO engineer for sky130 PDK. "
        "Generate precise, correct Tcl ECO commands. "
        "Reference only real sky130_fd_sc_hd cells. No hallucination."
    )

    def propose_eco(self, issue: str, synth_stats: str, design_name: str) -> dict:
        prompt = f"""Design '{design_name}' has the following issue:

ISSUE: {issue}

SYNTHESIS CONTEXT:
{synth_stats[:2000]}

Generate a specific ECO fix:
1. Identify root cause
2. Provide exact Tcl commands for OpenROAD/OpenSTA to fix it
3. Predict improvement (e.g., "-0.3ns setup slack improvement")
4. Risk assessment: Low/Medium/High
"""
        t0  = time.time()
        res = _query(prompt, task_type="rtl", system=self.SYSTEM, stream=getattr(self, 'verbose', False))
        return {
            "agent": "ECOAgent",
            "model": res["model"],
            "elapsed_sec": round(time.time() - t0, 1),
            "eco_proposal": res["response"],
        }


# ─── Agent 4: Signoff Report Agent ───────────────────────────────────────────

class SignoffAgent:
    """
    Generates the final signoff report combining all stage results.
    Uses qwen2.5-coder:3b for speed (report writing, not hardware reasoning).
    """

    SYSTEM = (
        "You are a senior ASIC design manager writing a silicon readiness report. "
        "Be concise, professional, and factual. Use the provided data only."
    )

    def generate_report(self, design_name: str, stage1: dict, stage2: dict) -> dict:
        summary = f"""
Design: {design_name}

STAGE 1 - FRONTEND:
  Lint:        {'PASS' if stage1.get('lint_passed') else 'FAIL'} ({stage1.get('lint_errors',0)} errors, {stage1.get('lint_warnings',0)} warnings)
  Simulation:  {'PASS' if stage1.get('sim_passed') else 'FAIL'}
  Sim Output:  {stage1.get('sim_output','')[:500]}

STAGE 2 - BACKEND:
  Synthesis:   {'PASS' if stage2.get('synth_passed') else 'FAIL'}
  Cells:       {stage2.get('cell_count', 0)}
  Wires:       {stage2.get('wire_count', 0)}
  Area Est.:   {stage2.get('area_estimate', 'N/A')}
  Top Cells:   {json.dumps(dict(list(stage2.get('cell_breakdown',{}).items())[:8]), indent=2)}
"""
        prompt = f"""Write a concise RTL-to-GDS signoff report for this design:

{summary}

Format the report as:
## Executive Summary
## Stage 1 Frontend Signoff
## Stage 2 Backend Signoff
## Overall Verdict (TAPE-OUT READY / NEEDS REWORK)
## Recommended Next Steps
"""
        t0  = time.time()
        res = _query(prompt, task_type="general", system=self.SYSTEM, stream=getattr(self, 'verbose', False))
        return {
            "agent": "SignoffAgent",
            "model": res["model"],
            "elapsed_sec": round(time.time() - t0, 1),
            "report": res["response"],
        }

    def executive_summary(self, design_name: str, verdict: str, key_metrics: dict) -> str:
        """Single-sentence LLM summary for console output."""
        prompt = (
            f"In ONE sentence, summarize the RTL-to-GDS result for '{design_name}': "
            f"verdict={verdict}, metrics={json.dumps(key_metrics)}."
        )
        res = _query(prompt, task_type="general")
        return res["response"].strip()


# ─── Quick smoke test ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n=== LLM Agents — Smoke Test ===\n")
    router = get_router()
    print("Router connected. Installed models:")
    for m in router.list_models():
        print(f"  {m['name']:<50} {m['size_mb']} MB")
    print("\nAll agents initialized successfully.")
