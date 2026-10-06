"""
agents/rtl_coder.py
===================
Agent 1.2 - RTL Coder
Converts a structured spec.json into clean, synthesizable Verilog-2005 code.
Inherits from BaseAgent with chunked generation and truncation recovery.
"""

import re
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

_HERE = Path(__file__).parent.parent.resolve()
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from agents.base_agent import BaseAgent

# --- Protocol-aware system prompts -------------------------------------------

SYSTEM_BASE = (
    "You are an expert RTL hardware engineer. Write clean, synthesizable Verilog-2005.\n"
    "Rules you MUST follow:\n"
    "  1. Use non-blocking assignments (<=) in all clocked always blocks (@(posedge clk)).\n"
    "  2. Use blocking assignments (=) ONLY in combinational always blocks (@(*)).\n"
    "  3. Assign default values at the start of every case/if to prevent unintended latches.\n"
    "  4. Every module must start with 'module <name>' and end with 'endmodule'.\n"
    "  5. Return ONLY the raw Verilog code - no markdown, no commentary, no explanations.\n"
    "  6. Do NOT truncate. The LAST line must be exactly 'endmodule'.\n"
    "  7. CRITICAL ANSI PORT DECLARATION RULE: If an output port is updated inside an always block, declare it directly in the module port list as 'output reg ...' (e.g. 'output reg [3:0] result', 'output reg carry_out'). NEVER declare it as 'output' and then assign to it procedurally, and NEVER add duplicate signal declarations inside the module body."
)

SYSTEM_AXI = SYSTEM_BASE + (
    "\n\nAXI4-Lite Protocol Rules:\n"
    "  - AWREADY, WREADY, ARREADY: deasserted by default, pulsed high when slave accepts.\n"
    "  - Handshake occurs at posedge clk when BOTH valid AND ready are high simultaneously.\n"
    "  - BVALID stays high until master asserts BREADY. Same for RVALID/RREADY.\n"
    "  - Use separate FSMs for write channel (AW+W+B) and read channel (AR+R).\n"
    "  - States: IDLE -> AW_PHASE -> W_PHASE -> B_PHASE -> IDLE (write)\n"
    "  - States: IDLE -> AR_PHASE -> R_PHASE -> IDLE (read)"
)

SYSTEM_UART = SYSTEM_BASE + (
    "\n\nUART Protocol Rules:\n"
    "  - Bit period = CLK_FREQ / BAUD_RATE clock cycles.\n"
    "  - Frame: 1 start bit (0), 8 data bits LSB-first, 1 stop bit (1).\n"
    "  - Use a baud rate counter (bit_cnt) that counts to CLK_FREQ/BAUD_RATE-1.\n"
    "  - TX line idles HIGH (1). Start bit drives TX LOW (0).\n"
    "  - Declare 'output reg tx' and 'output reg tx_ready' in the port list."
)

SYSTEM_FIFO = SYSTEM_BASE + (
    "\n\nFIFO Design Rules:\n"
    "  - Use a circular buffer with wr_ptr and rd_ptr registers.\n"
    "  - Declare 'output reg [WIDTH-1:0] data_out', 'output full', 'output empty'.\n"
    "  - assign full  = ((wr_ptr + 1'b1) % DEPTH) == rd_ptr;\n"
    "  - assign empty = (wr_ptr == rd_ptr);\n"
    "  - Do NOT write when full, do NOT read when empty.\n"
    "  - Do NOT declare full or empty as reg or assign to them inside always blocks."
)

SYSTEM_ALU = SYSTEM_BASE + (
    "\n\nALU Design Rules:\n"
    "  - Purely combinational logic using always @(*) or continuous assign.\n"
    "  - Declare 'output reg [3:0] result' and 'output reg carry_out' directly in the module port list header.\n"
    "  - Initialize default values at top of always @(*): result = 4'b0; carry_out = 1'b0;\n"
    "  - Opcodes:\n"
    "      0: {carry_out, result} = a + b;\n"
    "      1: {carry_out, result} = {1'b0, a} - {1'b0, b};\n"
    "      2: begin result = a & b; carry_out = 0; end\n"
    "      3: begin result = a | b; carry_out = 0; end\n"
    "      4: begin result = a ^ b; carry_out = 0; end\n"
    "      5: begin result = ~a; carry_out = 0; end\n"
    "      6: begin result = a << 1; carry_out = a[3]; end\n"
    "      7: begin result = a >> 1; carry_out = a[0]; end\n"
    "  - assign zero = (result == 4'b0);\n"
    "  - Do NOT redeclare result or carry_out inside the module body."
)

PROTOCOL_SYSTEMS = {
    "AXI": SYSTEM_AXI,
    "AXI4": SYSTEM_AXI,
    "AXI4-Lite": SYSTEM_AXI,
    "UART": SYSTEM_UART,
    "FIFO": SYSTEM_FIFO,
    "ALU": SYSTEM_ALU,
    "custom": SYSTEM_BASE,
}


class RTLCoderAgent(BaseAgent):
    """
    Generates synthesizable Verilog from a structured spec dict.
    Handles truncation recovery by continuing generation until 'endmodule' is detected.
    """

    MAX_CONTINUE_ATTEMPTS = 3

    def __init__(self):
        super().__init__(name="RTLCoder", stage="Stage1", default_task_type="rtl")

    def generate(self, spec: dict, verbose: bool = True) -> dict:
        """
        Generate Verilog for the given spec.
        Returns dict: {verilog, design_name, elapsed_sec, model, truncation_recovered}
        """
        design_name = spec.get("design_name", "unknown")
        protocol    = spec.get("protocol", "custom")
        system_msg  = PROTOCOL_SYSTEMS.get(protocol, SYSTEM_BASE)

        ports_str   = self._format_ports(spec.get("ports", []))
        params_str  = self._format_params(spec.get("params", {}))
        fsm_str     = self._format_fsm(spec.get("fsm_states", []))
        behaviors   = "\n".join(f"  - {b}" for b in spec.get("key_behaviors", []))

        prompt = f"""Generate a complete, synthesizable Verilog module for: {spec.get('description', design_name)}

MODULE NAME: {spec.get('top_module', design_name)}

PARAMETERS:
{params_str}

PORT LIST:
{ports_str}

FSM STATES (if applicable):
{fsm_str}

KEY BEHAVIORS:
{behaviors}

CRITICAL: Write the ENTIRE module. The LAST line must be exactly: endmodule
Start your response with: module {spec.get('top_module', design_name)}"""

        t0 = time.time()
        if verbose:
            print(f"  [RTLCoder] Generating {design_name} ({protocol} protocol)...")

        result = self.query(prompt, task_type="rtl", system=system_msg, verbose=verbose)
        raw_verilog = self.extract_verilog(result.get("response", ""))
        model = result.get("model", "unknown")

        # Truncation detection & continuation loop
        truncation_recovered = False
        for attempt in range(self.MAX_CONTINUE_ATTEMPTS):
            if self._is_complete(raw_verilog):
                break
            if verbose:
                print(f"  [RTLCoder] [WARN] Output truncated (attempt {attempt+1}/{self.MAX_CONTINUE_ATTEMPTS}). Continuing...")

            continue_prompt = (
                f"You were writing a Verilog module but got cut off. "
                f"Continue EXACTLY from where you left off. "
                f"The partial code so far (last 30 lines):\n\n"
                f"{self._last_lines(raw_verilog, 30)}\n\n"
                f"Continue the code. The last line must be: endmodule\n"
                f"Output ONLY the continuation (no repetition of what was already written):"
            )
            cont_result = self.query(continue_prompt, task_type="rtl", system=system_msg, verbose=verbose)
            continuation = self.extract_verilog(cont_result.get("response", ""))
            raw_verilog = raw_verilog.rstrip() + "\n" + continuation.lstrip()
            truncation_recovered = True

        if not self._is_complete(raw_verilog):
            if verbose:
                print(f"  [RTLCoder] [WARN] Could not auto-complete. Force-appending endmodule.")
            raw_verilog = raw_verilog.rstrip() + "\nendmodule\n"

        elapsed = round(time.time() - t0, 2)
        lines = len(raw_verilog.splitlines())

        if verbose:
            print(f"  [RTLCoder] Generated {lines} lines in {elapsed}s (truncation_recovered={truncation_recovered})")

        self.log_action("rtl_generated", {
            "design_name": design_name,
            "lines": lines,
            "elapsed_sec": elapsed,
            "truncation_recovered": truncation_recovered,
        })

        return {
            "agent": self.name,
            "design_name": design_name,
            "verilog": raw_verilog,
            "model": model,
            "elapsed_sec": elapsed,
            "truncation_recovered": truncation_recovered,
        }

    def _is_complete(self, verilog: str) -> bool:
        stripped = verilog.strip()
        last_meaningful = stripped.split("\n")[-1].strip() if stripped else ""
        return last_meaningful == "endmodule"

    def _last_lines(self, text: str, n: int) -> str:
        lines = text.strip().split("\n")
        return "\n".join(lines[-n:])

    def _format_ports(self, ports: list) -> str:
        if not ports:
            return "  (not specified)"
        lines = []
        for p in ports:
            w = p.get("width", 1)
            width_str = f"[{w-1}:0] " if w > 1 else ""
            lines.append(f"  {p['direction']:6s} {width_str}{p['name']:<20} // {p.get('description','')}")
        return "\n".join(lines)

    def _format_params(self, params: dict) -> str:
        if not params:
            return "  (none)"
        return "\n".join(f"  {k} = {v}" for k, v in params.items())

    def _format_fsm(self, states: list) -> str:
        if not states:
            return "  (none - not an FSM design)"
        return "  " + " -> ".join(states)
