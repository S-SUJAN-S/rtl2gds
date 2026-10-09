"""
agents/sim_eco.py
==================
Agent 1.5 - Simulation ECO Agent
Runs iverilog + vvp simulation, classifies failures (RTL vs Testbench),
and automatically drives closed-loop repair iterations.
"""

import json
import re
import sys
import time
from pathlib import Path
from typing import Tuple, Dict, Any, List

_HERE = Path(__file__).parent.parent.resolve()
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from agents.base_agent import BaseAgent
from wsl_tool_runner import run_iverilog_sim

SYSTEM_CLASSIFY = (
    "You are a Verilog simulation debug expert. "
    "Given a simulation failure report, classify the root cause and provide a targeted fix. "
    "Respond ONLY with this JSON:\n"
    '{"fault_location": "RTL" | "TESTBENCH", '
    '"root_cause": "<one sentence>", '
    '"fix_description": "<one sentence>", '
    '"confidence": 0-100}\n'
    "No other text."
)

SYSTEM_FIX_RTL = (
    "You are an expert RTL Verilog engineer. Fix the DUT to pass simulation. "
    "Rules:\n"
    "  1. Fix ONLY the reported bug - do not restructure unrelated logic.\n"
    "  2. Non-blocking (<=) in clocked blocks. Blocking (=) in combinational.\n"
    "  3. Output ENTIRE corrected Verilog. Last line: endmodule. No markdown."
)

SYSTEM_FIX_TB = (
    "You are an expert Verilog verification engineer. Fix the testbench to correctly test the DUT. "
    "Rules:\n"
    "  1. NEVER assign to DUT output signals (they are wires - not l-values).\n"
    "  2. All DUT inputs driven by the TB must be declared as reg.\n"
    "  3. Use non-blocking (<=) for all reg drivers.\n"
    "  4. Add timeout forks/watchdogs for all wait() calls.\n"
    "  5. In sequential/clocked designs, wait for @(posedge clk); #1; after stimulus before checking outputs.\n"
    "  6. Verilog tasks CANNOT contain 'return;' statements.\n"
    "  7. Output ENTIRE corrected testbench. Last line: endmodule. No markdown."
)


class SimECOAgent(BaseAgent):
    """
    Runs simulation and auto-fixes failures using local LLM and deterministic diagnostics.
    """
    MAX_RETRIES = 5

    def __init__(self):
        super().__init__(name="SimECO", stage="Stage1", default_task_type="rtl")

    def simulate_and_fix(self, dut_path: str, tb_path: str,
                          design_name: str, verbose: bool = True) -> dict:
        """
        Run simulation and fix failures until passing or MAX_RETRIES reached.
        """
        t0 = time.time()
        dut_path = Path(dut_path)
        tb_path  = Path(tb_path)
        attempts = 0
        fault_history = []

        for attempt in range(self.MAX_RETRIES):
            attempts = attempt + 1
            if verbose:
                print(f"\n  [SimECO] -- Attempt {attempts}/{self.MAX_RETRIES} -----------------")

            sim = run_iverilog_sim(
                str(dut_path), str(tb_path),
                top_module=f"{design_name}_tb"
            )

            # Check compilation errors
            if not sim.passed and "error" in sim.output.lower() and not sim.finish_reached:
                compile_errors = self._extract_compile_errors(sim.output)
                if verbose:
                    print(f"  [SimECO] [FAIL] Compilation errors ({len(compile_errors)}):")
                    for e in compile_errors[:5]:
                        print(f"           {e}")

                fault_type, fault_info = self._classify_and_fix(
                    dut_path.read_text(encoding="utf-8"),
                    tb_path.read_text(encoding="utf-8"),
                    sim.output,
                    design_name,
                    verbose,
                )
                fault_history.append({"attempt": attempts, "fault": fault_type, "info": fault_info})

                if fault_type == "TESTBENCH":
                    self._apply_fix(tb_path, fault_info["fixed_code"])
                else:
                    self._apply_fix(dut_path, fault_info["fixed_code"])
                continue

            # Check runtime pass
            if sim.passed and sim.finish_reached:
                output_lower = sim.output.lower()
                if "fail" in output_lower and not ("0 fail" in output_lower or "test passed: 0/0" in output_lower and "passed" in output_lower):
                    # Check if there are explicit failed test lines
                    if any(line.strip().startswith("[FAIL]") or "assertion failed" in line.lower() for line in sim.output.splitlines()):
                        if verbose:
                            print(f"  [SimECO] [FAIL] Explicit test case failures detected")
                    else:
                        if verbose:
                            print(f"  [SimECO] [OK] SIMULATION PASS - $finish reached")
                            print(f"           Output: {sim.output[:300]}")
                        self.log_action("sim_passed", {
                            "design_name": design_name,
                            "attempts": attempts,
                            "elapsed_sec": round(time.time() - t0, 2),
                        })
                        return {
                            "passed": True,
                            "sim_output": sim.output,
                            "attempts": attempts,
                            "fault_history": fault_history,
                            "elapsed_sec": round(time.time() - t0, 2),
                        }
                else:
                    if verbose:
                        print(f"  [SimECO] [OK] SIMULATION PASS - $finish reached")
                        print(f"           Output: {sim.output[:300]}")
                    self.log_action("sim_passed", {
                        "design_name": design_name,
                        "attempts": attempts,
                        "elapsed_sec": round(time.time() - t0, 2),
                    })
                    return {
                        "passed": True,
                        "sim_output": sim.output,
                        "attempts": attempts,
                        "fault_history": fault_history,
                        "elapsed_sec": round(time.time() - t0, 2),
                    }

            # Deadlock / runtime error
            sim_fail_output = sim.output
            if not sim.finish_reached:
                if verbose:
                    print(f"  [SimECO] [FAIL] DEADLOCK - simulation timed out (no $finish)")
                sim_fail_output += "\n[DEADLOCK: simulation timed out - likely a wait() that never unblocks]"

            fault_type, fault_info = self._classify_and_fix(
                dut_path.read_text(encoding="utf-8"),
                tb_path.read_text(encoding="utf-8"),
                sim_fail_output,
                design_name,
                verbose,
            )
            fault_history.append({"attempt": attempts, "fault": fault_type, "info": fault_info})

            target_path = tb_path if fault_type == "TESTBENCH" else dut_path
            backup_code = target_path.read_text(encoding="utf-8")
            self._apply_fix(target_path, fault_info["fixed_code"])

            # Safeguard: check if new patch introduced syntax compilation errors
            check_sim = run_iverilog_sim(str(dut_path), str(tb_path), top_module=f"{design_name}_tb")
            has_syntax_err = any("syntax error" in l.lower() or "error:" in l.lower() for l in check_sim.output.splitlines())
            orig_had_syntax = any("syntax error" in l.lower() or "error:" in l.lower() for l in sim_fail_output.splitlines())
            if has_syntax_err and not orig_had_syntax:
                if verbose:
                    print("  [SimECO] [WARN] Patch introduced new syntax errors. Rolling back to clean version.")
                target_path.write_text(backup_code, encoding="utf-8")

        # Final evaluation
        sim_final = run_iverilog_sim(
            str(dut_path), str(tb_path),
            top_module=f"{design_name}_tb"
        )
        passed_final = sim_final.passed and sim_final.finish_reached and not any(
            line.strip().startswith("[FAIL]") for line in sim_final.output.splitlines()
        )
        elapsed = round(time.time() - t0, 2)

        self.log_action("sim_result", {
            "design_name": design_name,
            "passed": passed_final,
            "attempts": attempts,
            "fault_history": fault_history,
            "elapsed_sec": elapsed,
        })

        return {
            "passed": passed_final,
            "sim_output": sim_final.output,
            "attempts": attempts,
            "fault_history": fault_history,
            "elapsed_sec": elapsed,
        }

    def _classify_and_fix(self, dut_code: str, tb_code: str,
                           sim_output: str, design_name: str, verbose: bool) -> Tuple[str, Dict[str, Any]]:
        """Classify root cause and generate targeted fix."""
        # Fast deterministic classification for common TB syntax issues
        if "Cannot \"return\" from tasks" in sim_output or "cannot \"return\"" in sim_output.lower():
            fault_type = "TESTBENCH"
            root_cause = "Illegal 'return' in task - Verilog tasks cannot contain return statements"
            fixed_code = re.sub(r'^\s*return\s*;', '    ; // AUTO-NEUTRALIZED return', tb_code, flags=re.MULTILINE)
            return fault_type, {
                "fixed_code": fixed_code,
                "root_cause": root_cause,
                "model": "deterministic_sanitizer",
            }
        elif "_tb.v:" in sim_output and "is not a valid l-value" in sim_output:
            fault_type = "TESTBENCH"
            root_cause = "Signals driven in testbench are declared as wire instead of reg"
        elif "_tb.v:" in sim_output and ("syntax error" in sim_output.lower() or "error:" in sim_output.lower()):
            fault_type = "TESTBENCH"
            root_cause = "Syntax error inside testbench"
        elif f"{design_name}.v:" in sim_output and ("syntax error" in sim_output.lower() or "error:" in sim_output.lower()):
            fault_type = "RTL"
            root_cause = "Syntax error inside RTL module"
        else:
            classify_prompt = f"""Simulation of '{design_name}' failed. Classify the root cause.

SIMULATION OUTPUT (failure):
{sim_output[:1500]}

DUT VERILOG (last 40 lines):
{self._last_lines(dut_code, 40)}

TESTBENCH (last 40 lines):
{self._last_lines(tb_code, 40)}

Classify: Is this an RTL bug or a TESTBENCH bug?"""

            cls_result = self.query(classify_prompt, task_type="json", system=SYSTEM_CLASSIFY, verbose=False)
            try:
                classification = self.extract_json(cls_result.get("response", ""))
                fault_type = classification.get("fault_location", "TESTBENCH").upper()
                root_cause = classification.get("root_cause", "Unknown failure")
            except Exception:
                fault_type = "TESTBENCH" if "_tb.v" in sim_output else "RTL"
                root_cause = "Heuristic classification based on failure log"

        if verbose:
            print(f"  [SimECO] [>>] Classified as: {fault_type} - {root_cause}")

        fail_lines = [l for l in sim_output.splitlines() if any(kw in l for kw in ["[FAIL]", "error:", "%Error", "Error:"])]
        compact_fail = "\n".join(fail_lines[:10]) if fail_lines else sim_output[:400]

        # Fix the targeted code
        if fault_type == "RTL":
            fix_prompt = f"""Fix the RTL Verilog for '{design_name}' to pass simulation.

BUG REPORT: {root_cause}

FAILING SIMULATION CHECKS:
{compact_fail}

CURRENT RTL:
{dut_code}

Output the ENTIRE corrected Verilog. Last line: endmodule"""
            fix_result = self.query(fix_prompt, task_type="rtl", system=SYSTEM_FIX_RTL, verbose=verbose)
        else:
            fix_prompt = f"""Fix the testbench for '{design_name}' to correctly stimulate the DUT.

BUG REPORT: {root_cause}

FAILING SIMULATION CHECKS:
{compact_fail}

DUT VERILOG (reference only - do NOT change this):
{dut_code[:1000]}

CURRENT TESTBENCH:
{tb_code}

Output the ENTIRE corrected testbench. Last line: endmodule"""
            fix_result = self.query(fix_prompt, task_type="rtl", system=SYSTEM_FIX_TB, verbose=verbose)

        fixed_code = self.extract_verilog(fix_result.get("response", ""))
        if not fixed_code.rstrip().endswith("endmodule"):
            fixed_code = fixed_code.rstrip() + "\nendmodule\n"

        return fault_type, {
            "fixed_code": fixed_code,
            "root_cause": root_cause,
            "model": fix_result.get("model", "unknown"),
        }

    def _apply_fix(self, path: Path, fixed_code: str):
        if not fixed_code or len(fixed_code) < 20:
            return
        if "[HTTP Error" in fixed_code or "[Request Error" in fixed_code or "[ModelRouter Error" in fixed_code:
            print("  [SimECO] [WARN] LLM returned error string. Skipping overwrite.")
            return
        if "module " not in fixed_code or "endmodule" not in fixed_code:
            print("  [SimECO] [WARN] Patch missing module/endmodule definition. Skipping overwrite.")
            return
        path.write_text(fixed_code, encoding="utf-8")

    def _extract_compile_errors(self, output: str) -> List[str]:
        errors = []
        for line in output.split("\n"):
            if "error:" in line.lower() or "%error" in line.lower():
                errors.append(line.strip())
        return errors

    def _last_lines(self, text: str, n: int) -> str:
        lines = text.strip().split("\n")
        return "\n".join(lines[-n:])
