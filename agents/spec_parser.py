"""
agents/spec_parser.py
=====================
Agent 1.1 - Spec Parser
Converts a free-text user prompt into a structured JSON specification with micro-architecture,
ports, parameters, FSM states, and timing budgets.
"""

import json
import sys
import time
from pathlib import Path
from typing import Optional

_HERE = Path(__file__).parent.parent.resolve()
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from agents.base_agent import BaseAgent


class SpecParserAgent(BaseAgent):
    """
    Converts a free-text design prompt into a structured JSON spec.
    Enforces strict JSON output with clocking and timing budget metadata.
    """

    SYSTEM = (
        "You are a hardware micro-architecture specification expert. "
        "Your job is to convert a natural language hardware description into a precise JSON object. "
        "You MUST respond ONLY with a valid JSON object - no markdown, no commentary, no code blocks. "
        "If a field is unknown, use a reasonable default."
    )

    SCHEMA_EXAMPLE = """{
  "design_name": "uart_tx",
  "top_module": "uart_tx",
  "description": "UART transmitter, 8N1 format, 115200 baud, active-high reset",
  "protocol": "UART",
  "has_clock": true,
  "clock_port": "clk",
  "clock_period_ns": 10.0,
  "target_freq_mhz": 100.0,
  "reset_active": "high",
  "params": {
    "CLK_FREQ": 50000000,
    "BAUD_RATE": 115200
  },
  "ports": [
    {"name": "clk",      "direction": "input",  "width": 1,  "description": "System clock"},
    {"name": "rst",      "direction": "input",  "width": 1,  "description": "Active-high reset"},
    {"name": "tx_data",  "direction": "input",  "width": 8,  "description": "Byte to transmit"},
    {"name": "tx_valid", "direction": "input",  "width": 1,  "description": "Data valid strobe"},
    {"name": "tx_ready", "direction": "output", "width": 1,  "description": "Ready for new byte"},
    {"name": "tx",       "direction": "output", "width": 1,  "description": "Serial TX line"}
  ],
  "fsm_states": ["IDLE", "START", "DATA", "STOP"],
  "key_behaviors": [
    "Assert tx_ready=1 in IDLE state",
    "On tx_valid rising edge in IDLE, latch data and enter START state",
    "Drive tx=0 for one bit period in START",
    "Shift out 8 data bits LSB-first",
    "Drive tx=1 for one bit period in STOP",
    "Return to IDLE"
  ]
}"""

    def __init__(self):
        super().__init__(name="SpecParser", stage="Stage1", default_task_type="json")

    def parse(self, user_prompt: str, design_name: Optional[str] = None) -> dict:
        """
        Parse a natural language prompt into a structured spec dict.
        """
        name_hint = f"\nThe design_name should be: '{design_name}'" if design_name else ""
        prompt = f"""Convert this hardware description into a JSON specification object.{name_hint}

HARDWARE DESCRIPTION:
{user_prompt}

RESPOND WITH ONLY A JSON OBJECT following this schema (adapt fields to the actual design):
{self.SCHEMA_EXAMPLE}

Your JSON:"""

        t0 = time.time()
        try:
            result = self.query(prompt, task_type="json", system=self.SYSTEM)
        except Exception:
            result = self.query(prompt, task_type="complex", system=self.SYSTEM)

        raw = result.get("response", "").strip()

        try:
            spec = self.extract_json(raw)
        except Exception as e:
            print(f"  [SpecParser] [WARN] LLM returned invalid JSON: {e}")
            spec = self._fallback_spec(user_prompt, design_name)

        # Inject timing defaults if missing
        if "clock_period_ns" not in spec:
            spec["clock_period_ns"] = 10.0
        if "target_freq_mhz" not in spec:
            spec["target_freq_mhz"] = round(1000.0 / spec["clock_period_ns"], 2)

        # Inject metadata
        spec["_agent"] = self.name
        spec["_elapsed_sec"] = round(time.time() - t0, 2)
        spec["_model"] = result.get("model", "unknown")
        spec["_raw_prompt"] = user_prompt

        if design_name:
            spec["design_name"] = design_name
            spec["top_module"] = design_name

        self.log_action("spec_parsed", {
            "design_name": spec.get("design_name"),
            "protocol": spec.get("protocol"),
            "ports_count": len(spec.get("ports", [])),
            "clock_period_ns": spec.get("clock_period_ns"),
        })

        return spec

    def _fallback_spec(self, prompt: str, design_name: Optional[str]) -> dict:
        """Emergency fallback if LLM cannot produce valid JSON."""
        name = design_name or "unknown_design"
        return {
            "design_name": name,
            "top_module": name,
            "description": prompt[:200],
            "protocol": "custom",
            "has_clock": True,
            "clock_port": "clk",
            "clock_period_ns": 10.0,
            "target_freq_mhz": 100.0,
            "reset_active": "high",
            "params": {},
            "ports": [
                {"name": "clk", "direction": "input", "width": 1, "description": "Clock"},
                {"name": "rst", "direction": "input", "width": 1, "description": "Reset"},
            ],
            "fsm_states": [],
            "key_behaviors": [prompt[:200]],
        }
