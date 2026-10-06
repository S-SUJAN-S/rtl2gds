"""
agents/synth_agent.py
======================
Agent 2.1 - Synthesis Agent
Drives Yosys logic synthesis, cell mapping, gate-level netlist generation,
and handles automated synthesis ECO retries.
"""

import sys
import time
from pathlib import Path
from typing import Dict, Any, List

_HERE = Path(__file__).parent.parent.resolve()
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from agents.base_agent import BaseAgent
from wsl_tool_runner import run_yosys_synth

SYSTEM_SYNTH_FIX = (
    "You are an expert RTL-to-GDSII engineer. Fix the Verilog to be synthesizable with Yosys.\n"
    "Common synthesis issues to fix:\n"
    "  - Remove 'initial' blocks (not synthesizable - move initialization to reset logic)\n"
    "  - Replace '$pow' or floating-point math with integer shift operations or lookup tables\n"
    "  - Remove 'inout' ports from top-level synthesis modules (split into in and out)\n"
    "  - Replace unsupported non-constant index operations with multiplexers\n"
    "  - Ensure all sequential always blocks use proper sensitivity list (@(posedge clk))\n"
    "Output ONLY the corrected, clean Verilog. Last line: endmodule. No markdown."
)


class SynthAgent(BaseAgent):
    """
    Drives Yosys synthesis with automatic RTL patching for synthesis failures.
    """
    MAX_RETRIES = 3

    def __init__(self):
        super().__init__(name="SynthAgent", stage="Stage2", default_task_type="rtl")

    def synthesize(self, dut_path: str, top_module: str,
                    design_name: str, verbose: bool = True) -> dict:
        """
        Run Yosys synthesis with automatic ECO retry loop.
        """
        t0 = time.time()
        dut_path = Path(dut_path)
        attempts = 0

        for attempt in range(self.MAX_RETRIES):
            attempts = attempt + 1
            if verbose:
                print(f"  [SynthAgent] Attempt {attempts}: Synthesizing {top_module} with Yosys...")

            synth = run_yosys_synth(str(dut_path), top_module)

            if synth.success:
                elapsed = round(time.time() - t0, 2)
                if verbose:
                    print(f"  [SynthAgent] [OK] SYNTHESIS PASS - {synth.cell_count} cells, {synth.wire_count} wires")

                self.log_action("synthesis_passed", {
                    "design_name": design_name,
                    "top_module": top_module,
                    "cell_count": synth.cell_count,
                    "wire_count": synth.wire_count,
                    "cell_breakdown": synth.cell_breakdown,
                    "area_estimate": synth.area_estimate,
                    "attempts": attempts,
                    "elapsed_sec": elapsed,
                })

                return {
                    "passed": True,
                    "cell_count": synth.cell_count,
                    "wire_count": synth.wire_count,
                    "cell_breakdown": synth.cell_breakdown,
                    "area_estimate": synth.area_estimate,
                    "netlist_path": getattr(synth, "netlist_path", ""),
                    "raw_stats": synth.raw_stats,
                    "attempts": attempts,
                    "elapsed_sec": elapsed,
                }

            if verbose:
                print(f"  [SynthAgent] [FAIL] Synthesis FAILED. Analyzing errors...")

            errors = self._extract_errors(synth.raw_stats)
            if verbose:
                for e in errors[:5]:
                    print(f"           {e}")

            if attempt >= self.MAX_RETRIES - 1:
                break

            verilog = dut_path.read_text(encoding="utf-8")
            errors_str = "\n".join(f"  - {e}" for e in errors[:10])

            prompt = f"""Fix the Verilog module '{design_name}' to be synthesizable by Yosys.

YOSYS ERRORS:
{errors_str}

YOSYS LOG (relevant portion):
{synth.raw_stats[:1500]}

CURRENT VERILOG:
{verilog}

Output the ENTIRE corrected, synthesizable Verilog. Last line: endmodule"""

            result = self.query(prompt, task_type="rtl", system=SYSTEM_SYNTH_FIX, verbose=verbose)
            fixed = self.extract_verilog(result.get("response", ""))

            if fixed and len(fixed) > 20:
                if not fixed.rstrip().endswith("endmodule"):
                    fixed = fixed.rstrip() + "\nendmodule\n"
                dut_path.write_text(fixed, encoding="utf-8")
                if verbose:
                    print(f"  [SynthAgent] LLM synthesis patch applied ({len(fixed.splitlines())} lines)")

        elapsed = round(time.time() - t0, 2)
        self.log_action("synthesis_failed", {
            "design_name": design_name,
            "attempts": attempts,
            "elapsed_sec": elapsed,
        })

        return {
            "passed": False,
            "cell_count": 0,
            "wire_count": 0,
            "cell_breakdown": {},
            "area_estimate": "N/A",
            "netlist_path": "",
            "raw_stats": synth.raw_stats if 'synth' in dir() else "",
            "attempts": attempts,
            "elapsed_sec": elapsed,
        }

    def _extract_errors(self, yosys_log: str) -> List[str]:
        errors = []
        for line in yosys_log.split("\n"):
            if "error" in line.lower() or "ERROR" in line:
                errors.append(line.strip())
        return errors
