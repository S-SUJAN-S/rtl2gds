"""
rtl_local_pipeline.py
=====================
RTL-to-GDS Local LLM Automation Pipeline
=========================================
A fully standalone, locally-runnable RTL-to-GDS pipeline using:
  - Ollama local LLMs (RTLCoder, qwen2.5-coder:7b, qwen2.5-coder:3b)
  - WSL EDA tools (Verilator 5.032, iverilog 12.0, Yosys 0.52)

Usage:
    python rtl_local_pipeline.py --design alu4bit
    python rtl_local_pipeline.py --design full_adder
    python rtl_local_pipeline.py --design uart
    python rtl_local_pipeline.py --design alu4bit --stages 1     # stage 1 only
    python rtl_local_pipeline.py --design alu4bit --stages 1,2   # stage 1 + 2
    python rtl_local_pipeline.py --all                            # all 3 test designs

Architecture:
    Stage 1 (Frontend): Lint -> Simulate -> LLM Analysis -> Auto-Fix if needed
    Stage 2 (Backend):  Yosys Synthesis -> LLM Analysis -> ECO if needed
    Stage 3 (Lite):     Parse metrics, flag risks
    Stage 4 (Signoff):  Generate full markdown report
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# ─── Project root ──────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.resolve()
DESIGNS_DIR  = PROJECT_ROOT / "designs"
OUTPUTS_DIR  = PROJECT_ROOT / "outputs" / "pipeline_runs"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

# ─── Design registry ──────────────────────────────────────────────────────────
DESIGNS = {
    "full_adder": {
        "top_module": "full_adder",
        "verilog":    "designs/full_adder/full_adder.v",
        "testbench":  "designs/full_adder/full_adder_tb.v",
        "tb_top":     "full_adder_tb",
        "clock_port": None,
        "has_clock":  False,
    },
    "alu4bit": {
        "top_module": "alu4bit",
        "verilog":    "designs/alu4bit/alu4bit.v",
        "testbench":  "designs/alu4bit/alu4bit_tb.v",
        "tb_top":     "alu4bit_tb",
        "clock_port": None,
        "has_clock":  False,
    },
    "uart": {
        "top_module": "uart_top",
        "verilog":    "designs/uart/uart.v",
        "testbench":  "designs/uart/uart_tb.v",
        "tb_top":     "uart_tb",
        "clock_port": "clk",
        "has_clock":  True,
    },
}


# ─── Console helpers ──────────────────────────────────────────────────────────

CYAN  = "\033[96m"
GREEN = "\033[92m"
RED   = "\033[91m"
YELL  = "\033[93m"
BOLD  = "\033[1m"
RST   = "\033[0m"

def hdr(msg: str):
    bar = "=" * 60
    print(f"\n{CYAN}{BOLD}{bar}{RST}")
    print(f"{CYAN}{BOLD}  {msg}{RST}")
    print(f"{CYAN}{BOLD}{bar}{RST}\n")

def ok(msg: str):  print(f"  {GREEN}[OK]{RST}  {msg}")
def err(msg: str): print(f"  {RED}[FAIL]{RST} {msg}")
def info(msg: str):print(f"  {YELL}[..]{RST}  {msg}")
def step(msg: str):print(f"\n  {BOLD}>> {msg}{RST}")


# ─── Pipeline class ───────────────────────────────────────────────────────────

class RTLPipeline:
    def __init__(self, design_name: str, stages: list = None,
                 auto_fix: bool = True, verbose: bool = True, verbose_ai: bool = False):
        if design_name not in DESIGNS:
            raise ValueError(f"Unknown design '{design_name}'. Available: {list(DESIGNS.keys())}")

        self.design_name  = design_name
        self.cfg          = DESIGNS[design_name]
        self.stages       = stages or [1, 2, 3, 4]
        self.auto_fix     = auto_fix
        self.verbose      = verbose
        self.verbose_ai   = verbose_ai
        self.ts           = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_dir      = OUTPUTS_DIR / design_name / self.ts
        self.run_dir.mkdir(parents=True, exist_ok=True)

        self.verilog_path = PROJECT_ROOT / self.cfg["verilog"]
        self.tb_path      = PROJECT_ROOT / self.cfg["testbench"]

        # Stage results accumulated here
        self.results = {
            "design":    design_name,
            "timestamp": self.ts,
            "stages":    {},
        }

        # Lazy-import tool modules
        self._tools  = None
        self._agents = None

    def _get_tools(self):
        if self._tools is None:
            from wsl_tool_runner import (
                run_verilator_lint, run_iverilog_sim,
                run_yosys_synth, check_wsl_tools
            )
            self._tools = {
                "lint": run_verilator_lint,
                "sim":  run_iverilog_sim,
                "synth": run_yosys_synth,
                "check": check_wsl_tools,
            }
        return self._tools

    def _get_agents(self):
        if self._agents is None:
            from llm_agents import (
                LintAnalysisAgent, RTLFixAgent, SimAnalysisAgent,
                SynthesisAnalysisAgent, ECOAgent, SignoffAgent
            )
            self._agents = {
                "lint_ai":  LintAnalysisAgent(),
                "fix_ai":   RTLFixAgent(),
                "sim_ai":   SimAnalysisAgent(),
                "synth_ai": SynthesisAnalysisAgent(),
                "eco_ai":   ECOAgent(),
                "signoff":  SignoffAgent(),
            }
            # Inject verbose AI flag
            for agent in self._agents.values():
                agent.verbose = self.verbose_ai
        return self._agents

    def _save(self, filename: str, content: str):
        path = self.run_dir / filename
        path.write_text(content, encoding="utf-8")
        return path

    def _read_verilog(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")

    # ─── Stage 1: Frontend ────────────────────────────────────────────────────

    def run_stage1(self) -> dict:
        hdr(f"STAGE 1 — FRONTEND  |  {self.design_name}")
        tools  = self._get_tools()
        agents = self._get_agents()
        s1 = {}

        # ── 1a. Verilator Lint ────────────────────────────────────────────────
        step("1a. Verilator Lint")
        info(f"Running verilator --lint-only on {self.cfg['verilog']}")
        lint = tools["lint"](str(self.verilog_path))
        self._save("stage1_lint.txt", lint.raw_output)

        if lint.passed:
            ok(f"Lint PASS — {lint.warning_count} warnings, 0 errors")
        else:
            err(f"Lint FAIL — {lint.error_count} errors, {lint.warning_count} warnings")
            for e in lint.errors[:5]:
                print(f"       {RED}{e}{RST}")

        s1["lint_passed"]   = lint.passed
        s1["lint_errors"]   = lint.error_count
        s1["lint_warnings"] = lint.warning_count
        s1["lint_raw"]      = lint.raw_output

        # ── 1b. LLM Lint Analysis ─────────────────────────────────────────────
        step("1b. LLM Lint Analysis (RTLCoder)")
        verilog_src = self._read_verilog(self.verilog_path)
        lint_ai = agents["lint_ai"].analyze(lint.raw_output, verilog_src, self.design_name)
        self._save("stage1_llm_lint_analysis.md", lint_ai["analysis"])
        ok(f"LLM analysis done — {lint_ai['model']} @ {lint_ai['tokens_per_sec']} tok/s in {lint_ai['elapsed_sec']}s")
        s1["lint_ai"] = lint_ai

        # ── 1c. Auto-Fix if lint failed ───────────────────────────────────────
        if not lint.passed and self.auto_fix and lint.errors:
            step("1c. RTL Auto-Fix Agent")
            info(f"Attempting auto-patch for {lint.error_count} errors...")
            fix = agents["fix_ai"].fix(verilog_src, lint.errors, lint.warnings, self.design_name)
            fixed_path = self.run_dir / f"{self.design_name}_fixed.v"
            fixed_path.write_text(fix["fixed_verilog"], encoding="utf-8")
            ok(f"Fixed RTL written to {fixed_path.name}")

            # Re-lint the fixed file
            info("Re-linting fixed RTL...")
            relint = tools["lint"](str(fixed_path))
            if relint.passed:
                ok(f"Re-lint PASS after auto-fix!")
                self.verilog_path = fixed_path   # use fixed version going forward
                s1["lint_passed"] = True
                s1["auto_fixed"]  = True
            else:
                err(f"Re-lint still failing ({relint.error_count} errors). Using original.")
                s1["auto_fixed"] = False

            s1["fix_ai"] = fix

        # ── 1d. iverilog Simulation ───────────────────────────────────────────
        if self.tb_path.exists():
            step("1d. Icarus Verilog Simulation")
            info(f"Compiling + running {self.tb_path.name}")
            sim = tools["sim"](
                str(self.verilog_path),
                str(self.tb_path),
                top_module=self.cfg["tb_top"]
            )
            self._save("stage1_simulation.txt", sim.output)

            if sim.passed:
                ok(f"Simulation PASS — finish reached: {sim.finish_reached}")
            else:
                err(f"Simulation FAIL — {sim.assertions_failed} failures detected")

            # Print first 20 lines of sim output
            for line in sim.output.splitlines()[:20]:
                print(f"       {line}")

            s1["sim_passed"]       = sim.passed
            s1["sim_finish"]       = sim.finish_reached
            s1["sim_output"]       = sim.output
            s1["sim_pass_count"]   = sim.assertions_passed
            s1["sim_fail_count"]   = sim.assertions_failed

            # ── 1e. LLM Simulation Analysis ───────────────────────────────────
            step("1e. LLM Simulation Analysis")
            sim_ai = agents["sim_ai"].analyze(sim.output, self.design_name)
            self._save("stage1_llm_sim_analysis.md", sim_ai["analysis"])
            ok(f"Sim analysis done — {sim_ai['model']} in {sim_ai['elapsed_sec']}s")
            s1["sim_ai"] = sim_ai
        else:
            info(f"No testbench found at {self.tb_path}. Skipping simulation.")
            s1["sim_passed"] = None
            s1["sim_output"] = "No testbench"

        # ── Stage 1 verdict ───────────────────────────────────────────────────
        s1_pass = s1["lint_passed"] and (s1.get("sim_passed") in [True, None])
        s1["stage_verdict"] = "STAGE1_PASS" if s1_pass else "STAGE1_FAIL"
        verdict_color = GREEN if s1_pass else RED
        print(f"\n  {verdict_color}{BOLD}Stage 1 Verdict: {s1['stage_verdict']}{RST}")

        self.results["stages"]["stage1"] = s1
        return s1

    # ─── Stage 2: Backend Synthesis ───────────────────────────────────────────

    def run_stage2(self, stage1: dict = None) -> dict:
        hdr(f"STAGE 2 — BACKEND SYNTHESIS  |  {self.design_name}")
        tools  = self._get_tools()
        agents = self._get_agents()
        s2 = {}

        # ── 2a. Yosys Synthesis ───────────────────────────────────────────────
        step("2a. Yosys Logic Synthesis")
        info(f"Synthesizing {self.cfg['top_module']} with Yosys...")
        synth = tools["synth"](
            str(self.verilog_path),
            self.cfg["top_module"]
        )
        self._save("stage2_synthesis.txt", synth.raw_stats)

        if synth.success:
            ok(f"Synthesis SUCCESS — {synth.cell_count} cells, {synth.wire_count} wires")
            ok(f"Area estimate: {synth.area_estimate}")
            if synth.cell_breakdown:
                print(f"\n       Cell Breakdown:")
                for cell, cnt in list(synth.cell_breakdown.items())[:10]:
                    print(f"         {cell:<30} {cnt}")
        else:
            err("Synthesis FAILED — check stage2_synthesis.txt for details")

        s2["synth_passed"]     = synth.success
        s2["cell_count"]       = synth.cell_count
        s2["wire_count"]       = synth.wire_count
        s2["cell_breakdown"]   = synth.cell_breakdown
        s2["area_estimate"]    = synth.area_estimate
        s2["synth_raw"]        = synth.raw_stats

        # ── 2b. LLM Synthesis Analysis ────────────────────────────────────────
        step("2b. LLM Synthesis Analysis (qwen2.5-coder:7b)")
        synth_ai = agents["synth_ai"].analyze(
            synth.raw_stats, self.design_name,
            synth.cell_count, synth.wire_count
        )
        self._save("stage2_llm_synth_analysis.md", synth_ai["analysis"])
        ok(f"Synthesis analysis done — {synth_ai['model']} in {synth_ai['elapsed_sec']}s")
        s2["synth_ai"] = synth_ai

        # ── 2c. ECO if needed ─────────────────────────────────────────────────
        if not synth.success and self.auto_fix:
            step("2c. ECO Agent")
            eco = agents["eco_ai"].propose_eco(
                "Synthesis failed — check Yosys log for unresolved references",
                synth.raw_stats, self.design_name
            )
            self._save("stage2_eco_proposal.md", eco["eco_proposal"])
            ok(f"ECO proposal written to stage2_eco_proposal.md")
            s2["eco"] = eco

        # ── Stage 2 verdict ───────────────────────────────────────────────────
        s2_pass = synth.success
        s2["stage_verdict"] = "STAGE2_PASS" if s2_pass else "STAGE2_FAIL"
        verdict_color = GREEN if s2_pass else RED
        print(f"\n  {verdict_color}{BOLD}Stage 2 Verdict: {s2['stage_verdict']}{RST}")

        self.results["stages"]["stage2"] = s2
        return s2

    # ─── Stage 3: Lite Verification ───────────────────────────────────────────

    def run_stage3(self, stage1: dict, stage2: dict) -> dict:
        hdr(f"STAGE 3 — VERIFICATION METRICS  |  {self.design_name}")
        s3 = {}

        step("3a. Design Metrics Summary")
        cell_count = stage2.get("cell_count", 0)
        lint_pass  = stage1.get("lint_passed", False)
        sim_pass   = stage1.get("sim_passed", None)
        synth_pass = stage2.get("synth_passed", False)

        # Complexity estimate
        if cell_count < 50:
            complexity = "Simple"
        elif cell_count < 500:
            complexity = "Medium"
        else:
            complexity = "Complex"

        ok(f"Design complexity: {complexity} ({cell_count} cells)")
        ok(f"Lint clean: {lint_pass}")
        ok(f"Simulation: {'PASS' if sim_pass else 'FAIL' if sim_pass is False else 'N/A'}")
        ok(f"Synthesis: {synth_pass}")

        # PDK suitability check
        if cell_count > 0 and cell_count < 200000:
            ok(f"PDK fit: Suitable for sky130 (within cell budget)")
            s3["pdk_fit"] = True
        else:
            info(f"PDK fit: Review needed for large designs")
            s3["pdk_fit"] = False

        s3["complexity"]   = complexity
        s3["stage_verdict"] = "STAGE3_PASS" if (lint_pass and synth_pass) else "STAGE3_FAIL"
        print(f"\n  {GREEN if 'PASS' in s3['stage_verdict'] else RED}{BOLD}Stage 3 Verdict: {s3['stage_verdict']}{RST}")

        self.results["stages"]["stage3"] = s3
        return s3

    # ─── Stage 4: Signoff Report ──────────────────────────────────────────────

    def run_stage4(self, stage1: dict, stage2: dict, stage3: dict) -> dict:
        hdr(f"STAGE 4 — SIGNOFF REPORT  |  {self.design_name}")
        agents = self._get_agents()
        s4 = {}

        step("4a. Generating LLM Signoff Report")
        report = agents["signoff"].generate_report(self.design_name, stage1, stage2)
        self._save("stage4_signoff_report.md", report["report"])
        ok(f"Signoff report generated — {report['model']} in {report['elapsed_sec']}s")

        # Overall verdict
        all_pass = (
            stage1.get("lint_passed", False) and
            stage2.get("synth_passed", False) and
            stage1.get("sim_passed") in [True, None]
        )
        verdict = "TAPE-OUT READY" if all_pass else "NEEDS REWORK"
        verdict_color = GREEN if all_pass else RED
        print(f"\n  {verdict_color}{BOLD}Final Verdict: {verdict}{RST}")

        # Save master results JSON
        self.results["overall_verdict"] = verdict
        self.results["stages"]["stage4"] = {"report": report["report"], "verdict": verdict}
        results_json = json.dumps(self.results, indent=2, default=str)
        self._save("pipeline_results.json", results_json)

        # Print report to console
        print(f"\n{'─'*60}")
        print(report["report"][:2000])
        print(f"{'─'*60}")

        ok(f"All outputs saved to: {self.run_dir}")
        s4["verdict"] = verdict
        s4["report_path"] = str(self.run_dir / "stage4_signoff_report.md")
        return s4

    # ─── Main run ─────────────────────────────────────────────────────────────

    def run(self):
        t_total = time.time()

        print(f"\n{'='*60}")
        print(f"{BOLD}  RTL-to-GDS Local LLM Pipeline{RST}")
        print(f"  Design  : {BOLD}{self.design_name}{RST}")
        print(f"  Stages  : {self.stages}")
        print(f"  Output  : {self.run_dir}")
        print(f"{'='*60}")

        # Check Ollama is up — auto-start if needed
        step("Pre-flight: Checking Ollama server")
        import subprocess as _sp
        import urllib.request as _ur

        def _ollama_ready():
            try:
                _ur.urlopen("http://127.0.0.1:11434", timeout=2)
                return True
            except Exception:
                return False

        if not _ollama_ready():
            info("Ollama not running — auto-starting...")
            ollama_exe = r"C:\Users\ssuja\AppData\Local\Programs\Ollama\ollama.exe"
            _sp.Popen(
                [ollama_exe, "serve"],
                stdout=_sp.DEVNULL, stderr=_sp.DEVNULL,
                creationflags=_sp.CREATE_NO_WINDOW
            )
            # Wait up to 20s for it to become ready
            for i in range(20):
                time.sleep(1)
                if _ollama_ready():
                    ok(f"Ollama auto-started (waited {i+1}s)")
                    time.sleep(3)   # Allow /api/tags to warm up
                    break
            else:
                err("Ollama failed to start in 20s. Run start_ollama.bat manually.")
                sys.exit(1)

        try:
            from model_router import ModelRouter
            r = ModelRouter()
            models = r.list_models()
            ok(f"Ollama ready — {len(models)} models installed")
            for m in models:
                print(f"       {m['name']:<50} {m['size_mb']} MB")
        except Exception as e:
            err(f"Ollama not available: {e}")
            err("Start Ollama with: start_ollama.bat")
            sys.exit(1)

        # Check EDA tools
        step("Pre-flight: Checking WSL EDA tools")
        from wsl_tool_runner import check_wsl_tools
        tools = check_wsl_tools()
        all_ok = True
        for name, ver in tools.items():
            if ver:
                ok(f"{name}: {ver}")
            else:
                err(f"{name}: NOT FOUND in WSL")
                all_ok = False
        if not all_ok:
            err("Some EDA tools missing. Install with: wsl -e bash -c 'sudo apt install -y verilator iverilog yosys'")
            sys.exit(1)

        # Run stages
        stage1 = stage2 = stage3 = stage4 = {}

        if 1 in self.stages:
            stage1 = self.run_stage1()

        if 2 in self.stages:
            stage2 = self.run_stage2(stage1)

        if 3 in self.stages:
            stage3 = self.run_stage3(stage1, stage2)

        if 4 in self.stages:
            stage4 = self.run_stage4(stage1, stage2, stage3)

        elapsed = round(time.time() - t_total, 1)
        hdr(f"PIPELINE COMPLETE — {self.design_name} [{elapsed}s]")
        ok(f"Run directory: {self.run_dir}")
        ok(f"Signoff report: stage4_signoff_report.md")
        ok(f"Raw results: pipeline_results.json")
        print()

        return self.results


# ─── CLI entry point ──────────────────────────────────────────────────────────

def parse_stages(stages_str: str) -> list:
    return [int(s.strip()) for s in stages_str.split(",")]


def main():
    parser = argparse.ArgumentParser(
        description="RTL-to-GDS Local LLM Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python rtl_local_pipeline.py --design alu4bit
  python rtl_local_pipeline.py --design full_adder --stages 1
  python rtl_local_pipeline.py --design uart --stages 1,2
  python rtl_local_pipeline.py --all
        """
    )
    parser.add_argument("--design",  choices=list(DESIGNS.keys()),
                        help="Design to run")
    parser.add_argument("--stages",  default="1,2,3,4",
                        help="Comma-separated stages to run (default: 1,2,3,4)")
    parser.add_argument("--all",     action="store_true",
                        help="Run all 3 test designs sequentially")
    parser.add_argument("--no-fix",  action="store_true",
                        help="Disable auto-fix (analysis only)")

    parser.add_argument("--verbose-ai", action="store_true",
                        help="Stream AI responses live to the console")

    args = parser.parse_args()
    stages    = parse_stages(args.stages)
    auto_fix  = not args.no_fix

    if args.all:
        designs = ["full_adder", "alu4bit", "uart"]
        print(f"\n{BOLD}Running all {len(designs)} designs: {designs}{RST}\n")
        for name in designs:
            p = RTLPipeline(name, stages=stages, auto_fix=auto_fix, verbose_ai=args.verbose_ai)
            p.run()
        print(f"\n{GREEN}{BOLD}All designs complete! Check outputs/pipeline_runs/{RST}\n")
    elif args.design:
        p = RTLPipeline(args.design, stages=stages, auto_fix=auto_fix, verbose_ai=args.verbose_ai)
        p.run()
    else:
        parser.print_help()
        print(f"\nAvailable designs: {list(DESIGNS.keys())}")


if __name__ == "__main__":
    main()
