#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_model_router_pool.py
===============================
Verification Suite for ModelRouter Multi-Account API Key Pooling:
  1. Key Detection: Detects all 3 Groq keys, 3 OpenRouter keys, and 3 Gemini keys from .env.
  2. Round-Robin Rotation: Sequentially rotates across Key #1, #2, #3 and wraps around.
  3. HTTP 429 Simulation: Graceful auto-failover to the next key on rate limit.
  4. Live Verilog Generation: Live query to Groq (qwen/qwen3.8-27b) returning clean synthesizable Verilog.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure repo root is in python path
REPO_ROOT = Path(__file__).parent.parent.resolve()
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from model_router import ModelRouter, PROVIDER_CONFIGS


class TestModelRouterKeyPool(unittest.TestCase):
    """Test suite for multi-account key pooling and failover in ModelRouter."""

    def setUp(self):
        self.router = ModelRouter(provider="groq")

    def test_01_detect_all_keys(self):
        """Verify that 3 Groq keys, 3 OpenRouter keys, and 3 Gemini keys are detected from .env."""
        groq_keys = self.router._get_key_pool("groq")
        nvidia_keys = self.router._get_key_pool("nvidia")
        openrouter_keys = self.router._get_key_pool("openrouter")
        gemini_keys = self.router._get_key_pool("gemini")

        print(f"\n[Test 1] Detected Groq keys: {len(groq_keys)}")
        print(f"[Test 1] Detected NVIDIA NIM keys: {len(nvidia_keys)}")
        print(f"[Test 1] Detected OpenRouter keys: {len(openrouter_keys)}")
        print(f"[Test 1] Detected Gemini keys: {len(gemini_keys)}")

        self.assertGreaterEqual(len(groq_keys), 3, "Expected at least 3 Groq API keys in pool")
        self.assertGreaterEqual(len(nvidia_keys), 1, "Expected at least 1 NVIDIA NIM API key in pool")
        self.assertGreaterEqual(len(openrouter_keys), 3, "Expected at least 3 OpenRouter API keys in pool")
        self.assertGreaterEqual(len(gemini_keys), 3, "Expected at least 3 Gemini API keys in pool")

        # Ensure all keys in each pool are distinct non-empty strings
        for name, pool in [("Groq", groq_keys), ("NVIDIA", nvidia_keys), ("OpenRouter", openrouter_keys), ("Gemini", gemini_keys)]:
            self.assertEqual(len(pool), len(set(pool)), f"{name} key pool contains duplicates")
            for k in pool:
                self.assertTrue(bool(k.strip()), f"{name} contains an empty key")

    def test_02_round_robin_rotation(self):
        """Verify sequential rotation across Key #1, Key #2, and Key #3, wrapping back to Key #1."""
        router = ModelRouter(provider="groq")
        num_keys = len(router._get_key_pool("groq"))
        self.assertGreaterEqual(num_keys, 3)

        observed_key_indices = []

        # Mock the network call to observe key_index passed to _execute_http_request
        original_exec = router._execute_http_request
        def mock_exec(*args, **kwargs):
            k_idx = kwargs.get("key_index", 1)
            observed_key_indices.append(k_idx)
            return {
                "model": "qwen/qwen3.8-27b",
                "provider": "groq",
                "key_index": k_idx,
                "task_type": "rtl",
                "response": "module test(); endmodule",
                "tokens_per_sec": 450.0,
                "elapsed_sec": 0.2,
                "prompt_tokens": 10,
                "response_tokens": 10,
            }

        with patch.object(router, "_execute_http_request", side_effect=mock_exec):
            for i in range(num_keys + 1):
                res = router.query("test prompt", task_type="rtl", provider="groq")
                self.assertIn("response", res)

        print(f"[Test 2] Observed round-robin sequence: {observed_key_indices}")
        expected_sequence = list(range(1, num_keys + 1)) + [1]
        self.assertEqual(observed_key_indices, expected_sequence, "Round-robin sequence mismatch")

    def test_03_http_429_auto_failover(self):
        """Simulate HTTP 429 on Key #1 and verify auto-rotation to Key #2 without crashing."""
        router = ModelRouter(provider="groq")
        attempts_logged = []

        def mock_exec_with_429(*args, **kwargs):
            k_idx = kwargs.get("key_index", 1)
            attempts_logged.append(k_idx)
            if k_idx == 1:
                # Key 1 hits rate limit
                return {
                    "model": "qwen/qwen3.8-27b",
                    "provider": "groq",
                    "key_index": 1,
                    "task_type": "rtl",
                    "response": "[HTTP Error 429 from groq (Key #1)]: Rate limit reached",
                    "tokens_per_sec": 0.0,
                    "elapsed_sec": 0.1,
                    "prompt_tokens": 0,
                    "response_tokens": 0,
                }
            else:
                # Key 2 succeeds
                return {
                    "model": "qwen/qwen3.8-27b",
                    "provider": "groq",
                    "key_index": k_idx,
                    "task_type": "rtl",
                    "response": "module recovered_module(); endmodule",
                    "tokens_per_sec": 480.0,
                    "elapsed_sec": 0.3,
                    "prompt_tokens": 15,
                    "response_tokens": 15,
                }

        with patch.object(router, "_execute_http_request", side_effect=mock_exec_with_429):
            res = router.query("generate module", task_type="rtl", provider="groq")

        print(f"[Test 3] Attempted key indices during 429: {attempts_logged}")
        print(f"[Test 3] Final response from key #{res.get('key_index')}")

        self.assertEqual(attempts_logged[:2], [1, 2], "Did not rotate from Key 1 to Key 2 on 429")
        self.assertEqual(res.get("key_index"), 2, "Response should come from Key 2 after failover")
        self.assertIn("recovered_module", res.get("response", ""))

    def test_04_live_groq_verilog_generation(self):
        """Execute a live API call to Groq with qwen/qwen3.8-27b and verify clean synthesizable Verilog."""
        prompt = (
            "Write a 4-bit synchronous up counter with active-high synchronous reset and enable.\n"
            "Ports:\n"
            "  input clk,\n"
            "  input rst,\n"
            "  input en,\n"
            "  output reg [3:0] count\n"
            "Rules:\n"
            "- Return ONLY valid Verilog-2005.\n"
            "- Module name must be 'counter4'.\n"
            "- Non-blocking assignments inside always @(posedge clk)."
        )

        t0_start = self.router
        result = self.router.query(
            prompt=prompt,
            task_type="rtl",
            provider="groq",
            system="You are an expert Verilog engineer. Return ONLY clean Verilog code with module counter4."
        )

        response_text = result.get("response", "")
        self.assertNotIn("[HTTP Error", response_text, f"Groq request returned HTTP error: {response_text}")
        self.assertNotIn("[Request Error", response_text, f"Groq request failed: {response_text}")

        verilog_code = self.router.extract_verilog_code(response_text)
        print(f"\n[Test 4] Model: {result.get('model')}")
        print(f"[Test 4] Provider: {result.get('provider')} (Key #{result.get('key_index')})")
        print(f"[Test 4] Throughput: {result.get('tokens_per_sec')} tok/s")
        print(f"[Test 4] Latency: {result.get('elapsed_sec')} s")
        print(f"[Test 4] Generated Verilog ({len(verilog_code.splitlines())} lines):\n{verilog_code}")

        self.assertIn("module counter4", verilog_code, "Verilog missing 'module counter4'")
        self.assertIn("endmodule", verilog_code, "Verilog missing 'endmodule'")
        self.assertIn("count", verilog_code, "Verilog missing port 'count'")
        self.assertGreater(result.get("tokens_per_sec", 0), 50.0, "Expected fast throughput from Groq LPU")


if __name__ == "__main__":
    unittest.main(verbosity=2)
