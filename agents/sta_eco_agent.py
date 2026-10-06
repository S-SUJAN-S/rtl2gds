"""
agents/sta_eco_agent.py
========================
Agent 2.2 - Timing & STA ECO Agent
Performs Static Timing Analysis (STA), extracts WNS/TNS, and drives
closed-loop Timing ECO iterations (pipeline registers, logic refactoring, cell sizing).
"""

import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

_HERE = Path(__file__).parent.parent.resolve()
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from agents.base_agent import BaseAgent
from wsl_tool_runner import run_sta_analysis, run_yosys_synth, generate_sdc_file, STAResult

SYSTEM_TIMING_ECO = (
    "You are an expert Silicon Timing Closure and STA engineer performing a Timing ECO. "
    "You will receive a Verilog module and a Static Timing Analysis report with negative slack (WNS < 0). "
    "Your objective is to achieve timing closure (Slack >= 0).\n"
    "Timing Optimization Strategies:\n"
    "  1. Insert pipeline register stages along long combinational arithmetic/multiplexer paths.\n"
    "  2. Split multi-cycle computations into separate clock cycles.\n"
    "  3. Restructure complex boolean expressions to reduce logic gate depth.\n"
    "  4. Ensure all synchronous logic meets setup time constraints.\n"
    "Rules:\n"
    "  - Preserve exact functional correctness and interface port definitions.\n"
    "  - Output the ENTIRE updated Verilog module. The LAST line must be: endmodule.\n"
    "  - Return ONLY raw Verilog code. No markdown fences, no explanations."
)


class STAECOAgent(BaseAgent):
    """
    Closed-loop Static Timing Analysis (STA) and Timing ECO agent.
    Drives timing convergence and generates standard timing reports.
    """
    MAX_ECO_RETRIES = 3

    def __init__(self):
        super().__init__(name="STAECOAgent", stage="Stage2", default_task_type="sta")

    def analyze_and_close_timing(
        self,
        dut_path: str,
        top_module: str,
        clock_period_ns: float = 10.0,
        clock_port: str = "clk",
        sdc_path: Optional[str] = None,
        output_dir: Optional[str] = None,
        verbose: bool = True,
    ) -> Dict[str, Any]:
        """
        Run STA on the design, and if timing is violated (WNS < 0),
        autonomously apply timing ECO patches and re-synthesize until timing is met.
        """
        t0 = time.time()
        path = Path(dut_path)
        out_dir = Path(output_dir or path.parent)
        out_dir.mkdir(parents=True, exist_ok=True)

        if not sdc_path or not Path(sdc_path).exists():
            sdc_path = str(out_dir / f"{top_module}.sdc")
            generate_sdc_file(
                output_path=sdc_path,
                clock_port=clock_port,
                clock_period_ns=clock_period_ns,
            )

        attempts = 0
        current_verilog = path.read_text(encoding="utf-8")
        sta_res: Optional[STAResult] = None

        for attempt in range(1, self.MAX_ECO_RETRIES + 1):
            attempts = attempt
            if verbose:
                print(f"  [STAECO] Iteration {attempt}/{self.MAX_ECO_RETRIES}: Running STA for {top_module} @ {1000.0/clock_period_ns:.1f} MHz (T={clock_period_ns:.2f}ns)...")

            # 1. Run STA Analysis
            sta_res = run_sta_analysis(
                verilog_file=str(path),
                top_module=top_module,
                clock_period_ns=clock_period_ns,
                clock_port=clock_port,
                sdc_file=sdc_path,
                output_rpt_dir=str(out_dir),
            )

            if sta_res.timing_met:
                elapsed = round(time.time() - t0, 2)
                if verbose:
                    print(f"  [STAECO] [OK] TIMING MET: WNS = {sta_res.wns:+.3f} ns | Critical Path = {sta_res.critical_path_delay:.3f} ns")

                self.log_action("timing_closed", {
                    "top_module": top_module,
                    "clock_period_ns": clock_period_ns,
                    "target_freq_mhz": sta_res.target_freq_mhz,
                    "wns": sta_res.wns,
                    "tns": sta_res.tns,
                    "critical_path_delay": sta_res.critical_path_delay,
                    "attempts": attempts,
                    "elapsed_sec": elapsed,
                })

                return {
                    "timing_met": True,
                    "wns": sta_res.wns,
                    "tns": sta_res.tns,
                    "target_freq_mhz": sta_res.target_freq_mhz,
                    "critical_path_delay": sta_res.critical_path_delay,
                    "startpoint": sta_res.startpoint,
                    "endpoint": sta_res.endpoint,
                    "report_path": sta_res.report_path,
                    "report_text": sta_res.report_text,
                    "attempts": attempts,
                    "elapsed_sec": elapsed,
                }

            # Timing Violated (WNS < 0)
            if verbose:
                print(f"  [STAECO] [WARN] TIMING VIOLATION: WNS = {sta_res.wns:+.3f} ns (TNS = {sta_res.tns:+.3f} ns)")
                for v in sta_res.violations[:3]:
                    print(f"           {v}")

            if attempt >= self.MAX_ECO_RETRIES:
                break

            # 2. Invoke LLM Timing ECO
            if verbose:
                print(f"  [STAECO] Generating Timing ECO patch (reducing logic depth / pipeline balancing)...")

            prompt = f"""Perform a Timing ECO on module '{top_module}' to fix the negative slack.

TIMING REPORT:
{sta_res.report_text[:1200]}

VIOLATION SUMMARY:
- Worst Negative Slack (WNS): {sta_res.wns:+.3f} ns
- Target Clock Period: {clock_period_ns:.3f} ns ({sta_res.target_freq_mhz:.1f} MHz)
- Critical Path Start: {sta_res.startpoint}
- Critical Path End:   {sta_res.endpoint}

CURRENT VERILOG:
{current_verilog}

Output the complete, timing-optimized Verilog module. The last line must be: endmodule"""

            result = self.query(prompt, task_type="sta", system=SYSTEM_TIMING_ECO, verbose=verbose)
            patched_code = self.extract_verilog(result.get("response", ""))

            if not patched_code or len(patched_code) < 30:
                if verbose:
                    print(f"  [STAECO] [WARN] LLM returned empty ECO patch. Retrying...")
                continue

            if not patched_code.rstrip().endswith("endmodule"):
                patched_code = patched_code.rstrip() + "\nendmodule\n"

            # Apply patch
            path.write_text(patched_code, encoding="utf-8")
            current_verilog = patched_code

            # Re-synthesize to verify netlist is still valid
            synth_chk = run_yosys_synth(str(path), top_module)
            if not synth_chk.success:
                if verbose:
                    print(f"  [STAECO] [WARN] ECO patch broke synthesis. Reverting.")
                continue

        elapsed = round(time.time() - t0, 2)
        self.log_action("timing_result", {
            "top_module": top_module,
            "timing_met": sta_res.timing_met if sta_res else False,
            "wns": sta_res.wns if sta_res else 0.0,
            "attempts": attempts,
            "elapsed_sec": elapsed,
        })

        return {
            "timing_met": sta_res.timing_met if sta_res else False,
            "wns": sta_res.wns if sta_res else 0.0,
            "tns": sta_res.tns if sta_res else 0.0,
            "target_freq_mhz": sta_res.target_freq_mhz if sta_res else round(1000.0/clock_period_ns, 2),
            "critical_path_delay": sta_res.critical_path_delay if sta_res else clock_period_ns,
            "startpoint": sta_res.startpoint if sta_res else "in",
            "endpoint": sta_res.endpoint if sta_res else "out",
            "report_path": sta_res.report_path if sta_res else "",
            "report_text": sta_res.report_text if sta_res else "",
            "attempts": attempts,
            "elapsed_sec": elapsed,
        }
