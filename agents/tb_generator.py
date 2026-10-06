"""
agents/tb_generator.py
=======================
Agent 1.4 - Enterprise Testbench Generator
Generates self-checking, assertion-rich Verilog/SystemVerilog testbenches
with strict pass/fail counter tracking, timeout watchdogs, and DUT input/output validation.
"""

import re
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple

_HERE = Path(__file__).parent.parent.resolve()
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from agents.base_agent import BaseAgent

# --- Protocol-specific Self-Checking TB System Prompts ------------------------

SYSTEM_BASE = """You are an expert Verilog/SystemVerilog verification engineer writing a self-checking testbench.

CRITICAL RULES (VIOLATING ANY WILL CAUSE SIMULATION FAILURE):

1. NEVER declare DUT INPUTS as wire if you assign them in initial/always blocks.
   - All signals driven by the testbench to DUT inputs MUST be declared as 'reg' (or logic).
   - All signals driven BY the DUT (outputs) MUST be declared as 'wire' and NEVER assigned in the testbench.

2. SELF-CHECKING PASS/FAIL TRACKING (MANDATORY):
   - Declare integer passed_tests = 0; integer total_tests = 0;
   - For every test case, increment total_tests.
   - If condition matches expected: passed_tests = passed_tests + 1; $display("[PASS] Test %0d: <description>", total_tests);
   - Else: $display("[FAIL] Test %0d: Expected %h, Got %h", total_tests, expected, actual);
   - At end of testbench, output:
     $display("TEST PASSED: %0d/%0d", passed_tests, total_tests);
     if (passed_tests == total_tests && total_tests > 0) $display("SIMULATION RESULT: PASSED");
     else $display("SIMULATION RESULT: FAILED");

3. TIMEOUT WATCHDOG (MANDATORY):
   - Add a hardware watchdog to prevent infinite hangs:
     initial begin
         #2000000;
         $display("[TIMEOUT] Watchdog triggered after 2ms - simulation hung!");
         $display("TEST PASSED: %0d/%0d", passed_tests, total_tests);
         $display("SIMULATION RESULT: FAILED");
         $finish;
     end

4. USE NON-BLOCKING ASSIGNMENTS (<=) for all reg stimulus in clocked initial/always blocks.
5. Initialize ALL stimulus regs to 0 at time 0.
6. Do NOT use SystemVerilog '$sformatf' or string variables. Use direct string literals inside $display.
7. Return ONLY the raw Verilog testbench code. No markdown fences, no commentary."""

SYSTEM_AXI = SYSTEM_BASE + """

AXI4-LITE TESTBENCH PATTERN:
- Write transaction: assert AWVALID and WVALID, wait for AWREADY and WREADY, assert BREADY, wait for BVALID.
- Read transaction: assert ARVALID, wait for ARREADY, assert RREADY, wait for RVALID, check RDATA.
- Use explicit timeout loops around every wait() call."""

SYSTEM_UART = SYSTEM_BASE + """

UART TESTBENCH PATTERN:
- Declare all DUT inputs as reg: reg clk, rst, tx_valid; reg [7:0] tx_data;
- Declare all DUT outputs as wire: wire tx_ready, tx;
- Clock generator: always #5 clk = ~clk; (10ns period = 100MHz).
- Reset sequence: rst = 1; #20; rst = 0; #20;
- Transmit test: wait for tx_ready==1; @(posedge clk); tx_valid <= 1; tx_data <= 8'h55; @(posedge clk); tx_valid <= 0;
- Wait until tx_ready rises high again (transmission complete). Increment passed_tests and total_tests.
- Test 2-3 bytes total (e.g. 8'h55, 8'hAA, 8'hF0)."""

SYSTEM_FIFO = SYSTEM_BASE + """

FIFO TESTBENCH PATTERN:
- Declare all DUT inputs as reg: reg clk, rst, wr_en, rd_en; reg [7:0] data_in;
- Declare all DUT outputs as wire: wire [7:0] data_out; wire full, empty;
- Clock generator: always #5 clk = ~clk;
- Reset sequence: rst = 1; wr_en = 0; rd_en = 0; data_in = 0; #20; rst = 0; #10;
- Verify initial reset: if (empty == 1 && full == 0) passed_tests = passed_tests + 1; total_tests = total_tests + 1;
- Write test: write 4 bytes: repeat(4) begin @(posedge clk); wr_en <= 1; data_in <= data_in + 1; end @(posedge clk); wr_en <= 0;
- Check empty == 0;
- Read test: read 4 bytes. For each byte: @(posedge clk); rd_en <= 1; @(posedge clk); rd_en <= 0; #1; check data_out matches written data.
- Check empty == 1;"""

SYSTEM_ALU = SYSTEM_BASE + """

ALU TESTBENCH PATTERN:
- Declare DUT inputs as reg: reg [3:0] a, b; reg [2:0] opcode;
- Declare DUT outputs as wire: wire [3:0] result; wire zero; wire carry_out;
- NEVER assign to 'result', 'zero', or 'carry_out' in initial blocks (they are wires driven by the DUT).
- Test opcodes 0 through 7 (ADD, SUB, AND, OR, XOR, NOT, SLL, SRL) with 1-2 representative vectors each.
- Use #10 delay between tests to let combinational logic settle before checking.
- Increment passed_tests and total_tests for each test case."""

PROTOCOL_SYSTEMS = {
    "AXI": SYSTEM_AXI,
    "AXI4": SYSTEM_AXI,
    "AXI4-Lite": SYSTEM_AXI,
    "UART": SYSTEM_UART,
    "FIFO": SYSTEM_FIFO,
    "ALU": SYSTEM_ALU,
    "custom": SYSTEM_BASE,
}


class TBGeneratorAgent(BaseAgent):
    """
    Generates self-checking, assertion-rich Verilog testbenches with
    automatic input/output signal sanitization and watchdog timers.
    """

    def __init__(self):
        super().__init__(name="TBGenerator", stage="Stage1", default_task_type="rtl")

    def generate(self, spec: dict, dut_path: str, verbose: bool = True) -> dict:
        """
        Generate and write a self-checking testbench for the given DUT.
        """
        t0 = time.time()
        design_name = spec.get("design_name", "unknown")
        protocol    = spec.get("protocol", "custom")
        system_msg  = PROTOCOL_SYSTEMS.get(protocol, SYSTEM_BASE)
        dut_verilog = Path(dut_path).read_text(encoding="utf-8")

        dut_outputs = self._extract_outputs(dut_verilog)
        dut_inputs  = self._extract_inputs(dut_verilog)
        output_list_str = ", ".join(dut_outputs) if dut_outputs else "(none)"
        input_list_str  = ", ".join(dut_inputs) if dut_inputs else "(none)"

        ports_str = self._format_ports(spec.get("ports", []))
        tb_module_name = f"{design_name}_tb"
        dut_module_name = spec.get("top_module", design_name)

        prompt = f"""Write a comprehensive, self-checking Verilog testbench for module '{dut_module_name}'.

DUT SPECIFICATION:
- Protocol: {protocol}
- Description: {spec.get('description', '')}

DUT INPUTS (Must be declared as 'reg' in TB):
  {input_list_str}

DUT OUTPUTS (Must be declared as 'wire' in TB - NEVER assign to them):
  {output_list_str}

DUT PORT LIST:
{ports_str}

DUT SOURCE (for reference):
{dut_verilog[:2000]}

TESTBENCH MODULE NAME: {tb_module_name}

REQUIREMENTS:
1. Instantiate '{dut_module_name}' as 'dut'.
2. Provide clock generator (10ns period) if design is sequential.
3. Provide synchronous/asynchronous reset pulse.
4. Write 8 to 12 targeted, essential tests covering opcodes/states/edge cases.
   Keep testbench concise (around 80-100 lines) so it completes fully without hitting token limits.
5. Track 'passed_tests' and 'total_tests' counters and print:
   $display("TEST PASSED: %0d/%0d", passed_tests, total_tests);
   if (passed_tests == total_tests && total_tests > 0) $display("SIMULATION RESULT: PASSED");
6. Include watchdog timer (#2000000 $finish;) to prevent hangs.
7. Call $finish at end of tests. The LAST line must be: endmodule

Output ONLY the Verilog testbench code."""

        if verbose:
            print(f"  [TBGenerator] Generating self-checking {protocol} testbench for {design_name}...")

        result = self.query(prompt, task_type="rtl", system=system_msg, verbose=verbose)
        tb_raw = self.extract_verilog(result.get("response", ""))

        if not ("module " in tb_raw):
            if verbose:
                print(f"  [TBGenerator] [WARN] Initial testbench generation incomplete or malformed. Re-attempting clean generation...")
            result = self.query(prompt, task_type="rtl", system=system_msg, verbose=verbose)
            tb_raw = self.extract_verilog(result.get("response", ""))

        # Truncation recovery loop
        for attempt in range(3):
            if tb_raw.rstrip().endswith("endmodule"):
                break
            if verbose:
                print(f"  [TBGenerator] [WARN] Testbench output truncated (attempt {attempt+1}/3). Continuing...")

            last_lines = "\n".join(tb_raw.strip().split("\n")[-25:])
            continue_prompt = (
                f"You were writing a Verilog testbench for '{dut_module_name}' but got cut off.\n"
                f"The partial code so far (last 25 lines):\n\n"
                f"{last_lines}\n\n"
                f"Continue the testbench to completion. Wrap up remaining tests, display summary, call $finish, and end with 'endmodule'.\n"
                f"Output ONLY the continuation code (do not repeat already written code):"
            )
            cont_result = self.query(continue_prompt, task_type="rtl", system=system_msg, verbose=verbose)
            continuation = self.extract_verilog(cont_result.get("response", ""))
            if continuation and not continuation.startswith("[") and "error" not in continuation.lower()[:30]:
                tb_raw = tb_raw.rstrip() + "\n" + continuation.lstrip()
            else:
                break

        if not tb_raw.rstrip().endswith("endmodule"):
            if verbose:
                print("  [TBGenerator] [WARN] Testbench unclosed after attempts. Cleanly closing testbench block.")
            tb_raw = (
                tb_raw.rstrip()
                + "\n        $display(\"TEST PASSED: %0d/%0d\", passed_tests, total_tests);\n"
                + "        if (passed_tests == total_tests && total_tests > 0) $display(\"SIMULATION RESULT: PASSED\");\n"
                + "        $finish;\n"
                + "    end\n"
                + "endmodule\n"
            )

        warnings = []
        # Post-processing passes
        tb_fixed, post_warn = self._post_process(tb_raw, dut_outputs)
        warnings.extend(post_warn)

        tb_fixed, input_warn = self._fix_input_declarations(tb_fixed, dut_verilog)
        warnings.extend(input_warn)

        tb_fixed = self._ensure_watchdog(tb_fixed)

        # Write testbench file
        dut_dir = Path(dut_path).parent
        tb_path = dut_dir / f"{design_name}_tb.v"
        tb_path.write_text(tb_fixed, encoding="utf-8")

        elapsed = round(time.time() - t0, 2)
        lines = len(tb_fixed.splitlines())

        if verbose:
            print(f"  [TBGenerator] [OK] Testbench written: {tb_path} ({lines} lines, {elapsed}s)")
            for w in warnings:
                print(f"  [TBGenerator] [AUTO-FIX] {w}")

        self.log_action("tb_generated", {
            "design_name": design_name,
            "tb_path": str(tb_path),
            "lines": lines,
            "warnings": warnings,
            "elapsed_sec": elapsed,
        })

        return {
            "tb_path": str(tb_path),
            "tb_verilog": tb_fixed,
            "design_name": design_name,
            "elapsed_sec": elapsed,
            "model": result.get("model", "unknown"),
            "warnings": warnings,
        }

    # ---------------------------------------------------------------------------
    # Sanitization & Robustness Helpers
    # ---------------------------------------------------------------------------
    def _post_process(self, tb: str, dut_outputs: list) -> Tuple[str, List[str]]:
        warnings = []
        lines = tb.split("\n")
        fixed_lines = []

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Prevent illegal assignment to DUT outputs (l-values only)
            # Do NOT strip equality comparisons like (sum == 0), if (out == 1), or assert(out == 1)
            if not re.search(r'\b(if|assert|while|\$display|case|function|task)\b', stripped):
                for out_port in dut_outputs:
                    # Match assignment: "out_port = ..." or "out_port <= ..." but NOT "== ..."
                    if re.search(rf'(?:^|[;,\s])\b{re.escape(out_port)}\s*(?:<=|=(?!=))', stripped):
                        if not re.match(r'^\s*(wire|reg|assign|input|output|task|function|parameter|localparam|integer)', line):
                            line = "    ; // AUTO-NEUTRALIZED illegal write to output: " + line.strip()
                            warnings.append(f"Line {i+1}: Illegal l-value assignment to DUT output '{out_port}' neutralized")
                            break

            # Convert simple blocking literal assignments to non-blocking in initial blocks
            if re.search(r'\b\w+\s*=\s*\d+\'[bBhHdD]', stripped):
                if not re.match(r'^\s*(wire|reg|assign|parameter|localparam|integer|if|assert|while)', line):
                    line = re.sub(r'(\w+)\s*=\s*(\d+\'[bBhHdD])', r'\1 <= \2', line)

            fixed_lines.append(line)

        return "\n".join(fixed_lines), warnings

    def _fix_input_declarations(self, tb: str, dut_verilog: str) -> Tuple[str, List[str]]:
        """Ensure all DUT input signals are declared as 'reg' in testbench."""
        warnings = []
        dut_inputs = self._extract_inputs(dut_verilog)
        if not dut_inputs:
            return tb, warnings

        lines = tb.split("\n")
        fixed_lines = []

        for line in lines:
            if re.match(r'^\s*wire\s+', line) and not re.match(r'^\s*wire\s+\[', line):
                decl_match = re.match(r'^(\s*)wire\s+(.*);', line)
                if decl_match:
                    indent = decl_match.group(1)
                    ports_str = decl_match.group(2)
                    ports = [p.strip() for p in ports_str.split(',') if p.strip()]
                    input_ports  = [p for p in ports if p in dut_inputs]
                    output_ports = [p for p in ports if p not in dut_inputs]
                    new_lines = []
                    if output_ports:
                        new_lines.append(f"{indent}wire {', '.join(output_ports)};")
                    if input_ports:
                        new_lines.append(f"{indent}reg  {', '.join(input_ports)};  // AUTO-FIXED: DUT input")
                        warnings.append(f"Converted 'wire {', '.join(input_ports)}' -> 'reg'")
                    fixed_lines.extend(new_lines if new_lines else [line])
                    continue
            elif re.match(r'^\s*wire\s+\[', line):
                decl_match = re.match(r'^(\s*)wire(\s+\[\S+\]\s+)(.*);', line)
                if decl_match:
                    indent    = decl_match.group(1)
                    width_str = decl_match.group(2)
                    ports_str = decl_match.group(3)
                    ports = [p.strip() for p in ports_str.split(',') if p.strip()]
                    input_ports  = [p for p in ports if p in dut_inputs]
                    output_ports = [p for p in ports if p not in dut_inputs]
                    new_lines = []
                    if output_ports:
                        new_lines.append(f"{indent}wire{width_str}{', '.join(output_ports)};")
                    if input_ports:
                        new_lines.append(f"{indent}reg {width_str}{', '.join(input_ports)};  // AUTO-FIXED")
                        warnings.append(f"Converted 'wire[] {', '.join(input_ports)}' -> 'reg[]'")
                    fixed_lines.extend(new_lines if new_lines else [line])
                    continue

            fixed_lines.append(line)

        return "\n".join(fixed_lines), warnings

    def _ensure_watchdog(self, tb: str) -> str:
        """Inject watchdog timer if missing."""
        if "$finish" not in tb:
            tb = tb.rstrip() + "\n\ninitial begin #1000000; $finish; end\n"
        elif "Watchdog" not in tb and "#" in tb:
            # Check if there is already a timeout block
            if "2000000" not in tb and "1000000" not in tb:
                # Insert watchdog before endmodule
                idx = tb.rfind("endmodule")
                if idx != -1:
                    watchdog_code = (
                        "\n  // Hardware Watchdog Timer\n"
                        "  initial begin\n"
                        "    #2000000;\n"
                        "    $display(\"[TIMEOUT] Watchdog triggered after 2ms!\");\n"
                        "    $finish;\n"
                        "  end\n\n"
                    )
                    tb = tb[:idx] + watchdog_code + tb[idx:]
        return tb

    def _extract_outputs(self, dut_verilog: str) -> List[str]:
        pattern = re.compile(
            r'^\s*output\s+(?:reg\s+)?(?:wire\s+)?(?:signed\s+)?(?:\[\S+\]\s+)?(\w+)',
            re.MULTILINE
        )
        return [m.group(1) for m in pattern.finditer(dut_verilog)]

    def _extract_inputs(self, dut_verilog: str) -> List[str]:
        pattern = re.compile(
            r'^\s*input\s+(?:reg\s+)?(?:wire\s+)?(?:signed\s+)?(?:\[\S+\]\s+)?(\w+)',
            re.MULTILINE
        )
        return [m.group(1) for m in pattern.finditer(dut_verilog)]

    def _format_ports(self, ports: list) -> str:
        lines = []
        for p in ports:
            w = p.get("width", 1)
            width_str = f"[{w-1}:0] " if w > 1 else ""
            lines.append(f"  {p['direction']:6s} {width_str}{p['name']:<20} // {p.get('description','')}")
        return "\n".join(lines)
