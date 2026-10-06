"""
agents/base_agent.py
====================
Base Agent Class for Enterprise Autonomous EDA Pipeline.
Provides standardized JSON logging, streaming support, telemetry capture,
code parsing helpers, and deterministic retry mechanics.
"""

import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

_HERE = Path(__file__).parent.parent.resolve()
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from model_router import ModelRouter, StreamResponse

_router: Optional[ModelRouter] = None

def get_shared_router() -> ModelRouter:
    global _router
    if _router is None:
        _router = ModelRouter()
    return _router


class BaseAgent:
    """
    Base class for all EDA pipeline sub-agents.
    Standardizes prompt execution, error recovery, JSON logging, and metrics.
    """

    def __init__(self, name: str, stage: str, default_task_type: str = "general"):
        self.name = name
        self.stage = stage
        self.default_task_type = default_task_type
        self.router = get_shared_router()
        self.telemetry_history: List[Dict[str, Any]] = []

    def log_action(self, action_type: str, details: Dict[str, Any]):
        """Record an action into agent telemetry history."""
        record = {
            "timestamp": datetime.now().isoformat(),
            "agent": self.name,
            "stage": self.stage,
            "action": action_type,
            **details,
        }
        self.telemetry_history.append(record)

    def query(
        self,
        prompt: str,
        task_type: Optional[str] = None,
        model: Optional[str] = None,
        stream: bool = False,
        system: Optional[str] = None,
        verbose: bool = True,
    ) -> Union[Dict[str, Any], StreamResponse]:
        """
        Query LLM router with automatic telemetry logging.
        """
        resolved_task = task_type or self.default_task_type
        t0 = time.time()

        if stream:
            stream_resp = self.router.query(
                prompt=prompt,
                task_type=resolved_task,
                model=model,
                stream=True,
                system=system,
            )
            return stream_resp

        result = self.router.query(
            prompt=prompt,
            task_type=resolved_task,
            model=model,
            stream=False,
            system=system,
        )
        elapsed = round(time.time() - t0, 2)

        self.log_action("llm_query", {
            "task_type": resolved_task,
            "model": result.get("model", "unknown"),
            "elapsed_sec": elapsed,
            "tokens_per_sec": result.get("tokens_per_sec", 0.0),
            "prompt_tokens": result.get("prompt_tokens", 0),
            "response_tokens": result.get("response_tokens", 0),
            "prompt_snippet": prompt[:120] + "..." if len(prompt) > 120 else prompt,
            "response_length": len(result.get("response", "")),
        })

        return result

    def execute_with_retry(
        self,
        task_fn: Callable[..., Any],
        validator_fn: Callable[[Any], tuple[bool, str]],
        max_retries: int = 3,
        step_name: str = "execution",
        verbose: bool = True,
    ) -> Dict[str, Any]:
        """
        Deterministic retry loop with validation and structured outcome.
        """
        t0 = time.time()
        attempts = 0
        last_error = ""
        last_result = None

        for attempt in range(1, max_retries + 1):
            attempts = attempt
            if verbose:
                print(f"  [{self.name}] Attempt {attempt}/{max_retries} for {step_name}...")
            try:
                result = task_fn(attempt=attempt, last_error=last_error)
                passed, reason = validator_fn(result)
                last_result = result
                if passed:
                    elapsed = round(time.time() - t0, 2)
                    if verbose:
                        print(f"  [{self.name}] [OK] {step_name} succeeded on attempt {attempt} ({elapsed}s)")
                    self.log_action("retry_success", {
                        "step": step_name,
                        "attempts": attempts,
                        "elapsed_sec": elapsed,
                        "reason": reason,
                    })
                    return {
                        "success": True,
                        "result": result,
                        "attempts": attempts,
                        "elapsed_sec": elapsed,
                        "reason": reason,
                    }
                else:
                    last_error = reason
                    if verbose:
                        print(f"  [{self.name}] [WARN] Attempt {attempt} validation failed: {reason}")
            except Exception as e:
                last_error = str(e)
                if verbose:
                    print(f"  [{self.name}] [ERROR] Exception on attempt {attempt}: {e}")

        elapsed = round(time.time() - t0, 2)
        self.log_action("retry_exhausted", {
            "step": step_name,
            "attempts": attempts,
            "elapsed_sec": elapsed,
            "last_error": last_error,
        })
        return {
            "success": False,
            "result": last_result,
            "attempts": attempts,
            "elapsed_sec": elapsed,
            "reason": last_error,
        }

    # ---------------------------------------------------------------------------
    # Code and Text Extraction Utilities
    # ---------------------------------------------------------------------------
    @staticmethod
    def extract_verilog(text: str) -> str:
        """Strip markdown fences and extract raw Verilog code."""
        text = text.strip()
        if "```verilog" in text:
            parts = text.split("```verilog")
            text = parts[1].split("```")[0].strip() if len(parts) > 1 else text
        elif "```systemverilog" in text:
            parts = text.split("```systemverilog")
            text = parts[1].split("```")[0].strip() if len(parts) > 1 else text
        elif "```" in text:
            parts = text.split("```")
            blocks = [p.strip() for p in parts if len(p.strip()) > 30]
            text = max(blocks, key=len) if blocks else text

        # Find where timescale or module starts, stripping any leading HTTP error headers
        if "`timescale" in text:
            ts_idx = text.find("`timescale")
            text = text[ts_idx:]
        elif "module " in text:
            idx = text.find("module ")
            header_sub = text[:idx]
            if idx > 0 and not header_sub.strip().startswith("//") and not header_sub.strip().startswith("/*"):
                text = text[idx:]

        return text.strip()

    @staticmethod
    def extract_json(text: str) -> dict:
        """Safely parse JSON response from LLM text."""
        text = text.strip()
        if "```json" in text:
            parts = text.split("```json")
            text = parts[1].split("```")[0].strip() if len(parts) > 1 else text
        elif "```" in text:
            parts = text.split("```")
            text = parts[1].strip() if len(parts) > 1 else text

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Attempt to find the first { and last }
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                return json.loads(text[start : end + 1])
            raise

    def export_telemetry(self, output_path: Union[str, Path]):
        """Save agent telemetry history as JSON."""
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self.telemetry_history, indent=2), encoding="utf-8")
