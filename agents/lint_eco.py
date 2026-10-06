"""
agents/lint_eco.py
==================
Agent 1.3 - Lint ECO Agent
Runs Verilator --lint-only on a Verilog file and uses a local LLM to
automatically patch any syntax/latch/width errors. Retries up to MAX_RETRIES times.
"""

import sys
import time
from pathlib import Path

_HERE = Path(__file__).parent.parent.resolve()
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from agents.base_agent import BaseAgent
from wsl_tool_runner import run_verilator_lint


class LintECOAgent(BaseAgent):
    """
    Runs Verilator lint and auto-patches Verilog errors using a local LLM.
    """
    MAX_RETRIES = 3

    SYSTEM = (
        "You are an expert Verilog RTL engineer performing a targeted ECO patch. "
        "You will receive a Verilog file and a list of SPECIFIC Verilator errors/warnings. "
        "Rules:\n"
        "  1. Fix ONLY what is reported. Do not modify logic that is not mentioned.\n"
        "  2. You MUST output the ENTIRE corrected Verilog file - from 'module' to 'endmodule'.\n"
        "  3. Return ONLY the raw Verilog code. No markdown, no explanations.\n"
        "  4. The LAST LINE must be exactly: endmodule\n"
        "  5. Do NOT change port names or module names.\n"
        "  6. Fix 'Procedural assignment to wire' (PROCASSWIRE) by changing the signal declaration from 'wire' to 'reg'.\n"
        "  7. Fix latch warnings by adding default assignments at the top of case/if blocks.\n"
        "  8. Fix width mismatch warnings by explicit bit-selection or zero-extension.\n"
        "  9. Fix undriven nets by assigning them to 0 or removing unused outputs."
    )

    def __init__(self):
        super().__init__(name="LintECO", stage="Stage1", default_task_type="rtl")

    def lint_and_fix(self, verilog_path: str, verbose: bool = True) -> dict:
        """
        Run lint on a file and fix it until it passes or MAX_RETRIES is reached.
        """
        t0 = time.time()
        path = Path(verilog_path)
        design_name = path.stem
        verilog = path.read_text(encoding="utf-8")
        attempts = 0

        for attempt in range(self.MAX_RETRIES + 1):
            attempts = attempt + 1
            if verbose:
                print(f"  [LintECO] Attempt {attempts}: Running Verilator on {path.name}")
            lint = run_verilator_lint(str(path))

            if lint.passed:
                if verbose:
                    print(f"  [LintECO] [OK] LINT PASS - {lint.warning_count} warnings, 0 errors")
                self.log_action("lint_passed", {
                    "design_name": design_name,
                    "attempts": attempts,
                    "warnings_count": lint.warning_count,
                    "elapsed_sec": round(time.time() - t0, 2),
                })
                return {
                    "passed": True,
                    "verilog": verilog,
                    "lint_errors": [],
                    "lint_warnings": lint.warnings,
                    "attempts": attempts,
                    "elapsed_sec": round(time.time() - t0, 2),
                }

            if verbose:
                print(f"  [LintECO] [FAIL] {lint.error_count} errors, {lint.warning_count} warnings")
                for e in lint.errors[:5]:
                    print(f"           {e}")

            if attempt >= self.MAX_RETRIES:
                break

            # Ask LLM to fix
            all_issues = lint.errors + lint.warnings
            issues_str = "\n".join(f"  - {i}" for i in all_issues[:20])

            prompt = f"""Fix the following Verilator lint issues in the Verilog module '{design_name}'.

ISSUES TO FIX:
{issues_str}

CURRENT VERILOG (complete file):
{verilog}

Output the ENTIRE corrected Verilog file. Last line must be: endmodule"""

            if verbose:
                print(f"  [LintECO] Sending {len(all_issues)} issues to local LLM for ECO patch...")

            result = self.query(prompt, task_type="rtl", system=self.SYSTEM, verbose=verbose)
            fixed = self.extract_verilog(result.get("response", ""))

            if not fixed or len(fixed) < 20:
                if verbose:
                    print(f"  [LintECO] [WARN] LLM returned empty/tiny response. Skipping.")
                continue

            if not fixed.rstrip().endswith("endmodule"):
                fixed = fixed.rstrip() + "\nendmodule\n"

            path.write_text(fixed, encoding="utf-8")
            verilog = fixed
            if verbose:
                print(f"  [LintECO] LLM patch applied ({len(fixed.splitlines())} lines written)")

        # Final state after retries
        lint_final = run_verilator_lint(str(path))
        elapsed = round(time.time() - t0, 2)
        self.log_action("lint_result", {
            "design_name": design_name,
            "passed": lint_final.passed,
            "attempts": attempts,
            "errors_count": lint_final.error_count,
            "warnings_count": lint_final.warning_count,
            "elapsed_sec": elapsed,
        })

        return {
            "passed": lint_final.passed,
            "verilog": path.read_text(encoding="utf-8"),
            "lint_errors": lint_final.errors,
            "lint_warnings": lint_final.warnings,
            "attempts": attempts,
            "elapsed_sec": elapsed,
        }
