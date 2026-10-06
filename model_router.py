"""
model_router.py
===============
Universal High-Performance Model Router for RTL-to-GDSII EDA Automation.
Supports free and high-speed cloud APIs (Groq, Google Gemini, OpenRouter, DeepSeek)
with graceful fallback to local Ollama. Zero external dependencies required.

Supported Cloud Providers (Free Tiers):
  1. Groq Cloud (GROQ_API_KEY):
     - Ultra-fast (500+ tok/s) inference. Free tier at https://console.groq.com/keys
     - Models: qwen-2.5-coder-32b, llama-3.3-70b-versatile, deepseek-r1-distill-llama-70b
  2. Google Gemini (GEMINI_API_KEY or GOOGLE_API_KEY):
     - Generous free tier (15 RPM, 1M context) at https://aistudio.google.com/app/apikey
     - Models: gemini-2.5-flash, gemini-1.5-pro, gemini-1.5-flash
  3. OpenRouter (OPENROUTER_API_KEY):
     - Aggregator with free models at https://openrouter.ai/keys
     - Models: meta-llama/llama-3.3-70b-instruct:free, qwen/qwen-2.5-coder-32b-instruct:free
  4. Local Ollama (OLLAMA_HOST):
     - Offline fallback at http://127.0.0.1:11434

Usage:
    from model_router import ModelRouter

    router = ModelRouter()
    res = router.query("Generate an AXI4-Lite arbiter in Verilog", task_type="rtl")
    print(res["response"])
"""

import os
import sys
import json
import time
import ssl
import re
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Generator

# ---------------------------------------------------------------------------
# Load .env file automatically without external packages
# ---------------------------------------------------------------------------
def _load_dotenv():
    search_dirs = [Path.cwd(), Path(__file__).parent.resolve()]
    for d in search_dirs:
        env_file = d / ".env"
        if env_file.exists():
            try:
                for line in env_file.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    if key and key not in os.environ:
                        os.environ[key] = val
            except Exception:
                pass

_load_dotenv()


# ---------------------------------------------------------------------------
# Provider Configurations & Defaults
# ---------------------------------------------------------------------------
PROVIDER_CONFIGS = {
    "groq": {
        "name": "Groq Cloud (High-Speed Free Tier)",
        "api_base": "https://api.groq.com/openai/v1/chat/completions",
        "env_key": "GROQ_API_KEY",
        "signup_url": "https://console.groq.com/keys",
        "models": {
            "rtl": "qwen-2.5-coder-32b",
            "complex": "llama-3.3-70b-versatile",
            "sta": "llama-3.3-70b-versatile",
            "general": "llama-3.3-70b-versatile",
            "reasoning": "deepseek-r1-distill-llama-70b",
        },
    },
    "gemini": {
        "name": "Google Gemini API (1M Context Free Tier)",
        "api_base": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "env_key": "GEMINI_API_KEY",
        "signup_url": "https://aistudio.google.com/app/apikey",
        "models": {
            "rtl": "gemini-2.5-flash",
            "complex": "gemini-1.5-pro",
            "sta": "gemini-2.5-flash",
            "general": "gemini-2.5-flash",
            "reasoning": "gemini-2.5-flash",
        },
    },
    "openrouter": {
        "name": "OpenRouter API",
        "api_base": "https://openrouter.ai/api/v1/chat/completions",
        "env_key": "OPENROUTER_API_KEY",
        "signup_url": "https://openrouter.ai/keys",
        "models": {
            "rtl": "qwen/qwen-2.5-coder-32b-instruct:free",
            "complex": "meta-llama/llama-3.3-70b-instruct:free",
            "sta": "meta-llama/llama-3.3-70b-instruct:free",
            "general": "meta-llama/llama-3.3-70b-instruct:free",
            "reasoning": "deepseek/deepseek-r1:free",
        },
    },
    "ollama": {
        "name": "Local Ollama Server",
        "api_base": os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434") + "/api/chat",
        "env_key": None,
        "signup_url": "https://ollama.ai",
        "models": {
            "rtl": "qwen2.5-coder:7b",
            "complex": "qwen2.5-coder:7b",
            "sta": "qwen2.5-coder:7b",
            "general": "qwen2.5-coder:3b",
            "reasoning": "qwen2.5-coder:7b",
        },
    },
}


class StreamResponse:
    """Streaming response wrapper compatible with BaseAgent and terminal outputs."""

    def __init__(self, generator: Generator[str, None, None], model: str, provider: str, task_type: str):
        self._gen = generator
        self.model = model
        self.provider = provider
        self.task_type = task_type
        self.response_text = ""
        self.start_time = time.time()
        self.metrics = {
            "model": self.model,
            "provider": self.provider,
            "task_type": self.task_type,
            "tokens_per_sec": 0.0,
            "elapsed_sec": 0.0,
            "prompt_tokens": 0,
            "response_tokens": 0,
        }

    def __iter__(self):
        for chunk in self._gen:
            self.response_text += chunk
            yield chunk
        elapsed = max(time.time() - self.start_time, 0.01)
        est_tokens = int(len(self.response_text.split()) * 1.3)
        self.metrics.update({
            "tokens_per_sec": round(est_tokens / elapsed, 1),
            "elapsed_sec": round(elapsed, 2),
            "response_tokens": est_tokens,
        })

    def get_full_response(self) -> str:
        if not self.response_text:
            for _ in self:
                pass
        return self.response_text


class ModelRouter:
    """
    Enterprise Unified Model Router.
    Intelligently routes prompts to free cloud APIs (Groq, Gemini, OpenRouter)
    with automatic fallbacks and zero local VRAM bottlenecks.
    """

    def __init__(self, provider: Optional[str] = None, api_key: Optional[str] = None, timeout: int = 120):
        self.timeout = timeout
        self.override_api_key = api_key
        self.active_provider = self._resolve_provider(provider)
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

    def _resolve_provider(self, requested: Optional[str]) -> str:
        if requested and requested.lower() in PROVIDER_CONFIGS:
            return requested.lower()

        # Priority 1: Groq (ultra fast 500+ tok/s free tier)
        if os.environ.get("GROQ_API_KEY") or (requested == "groq"):
            return "groq"

        # Priority 2: Google Gemini (generous 1M token context free tier)
        if os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or (requested == "gemini"):
            return "gemini"

        # Priority 3: OpenRouter
        if os.environ.get("OPENROUTER_API_KEY") or (requested == "openrouter"):
            return "openrouter"

        # Priority 4: Local Ollama if running
        if self._is_ollama_alive():
            return "ollama"

        # Default to Groq with helpful instructions
        return "groq"

    def _get_api_key(self, provider: str) -> Optional[str]:
        if self.override_api_key:
            return self.override_api_key
        cfg = PROVIDER_CONFIGS.get(provider, {})
        env_key = cfg.get("env_key")
        if not env_key:
            return None
        val = os.environ.get(env_key)
        if not val and provider == "gemini":
            val = os.environ.get("GOOGLE_API_KEY")
        return val

    def _is_ollama_alive(self) -> bool:
        try:
            host = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
            req = urllib.request.Request(f"{host}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                return resp.status == 200
        except Exception:
            return False

    def get_model_for_task(self, task_type: str, provider: Optional[str] = None) -> str:
        p = provider or self.active_provider
        cfg = PROVIDER_CONFIGS.get(p, PROVIDER_CONFIGS["groq"])
        models = cfg.get("models", {})
        return models.get(task_type, models.get("general", "llama-3.3-70b-versatile"))

    def query(
        self,
        prompt: str,
        task_type: str = "general",
        model: Optional[str] = None,
        stream: bool = False,
        system: Optional[str] = None,
        provider: Optional[str] = None,
        format: Optional[str] = None,
    ) -> Union[Dict[str, Any], StreamResponse]:
        target_provider = provider or self.active_provider
        api_key = self._get_api_key(target_provider)
        target_model = model or self.get_model_for_task(task_type, target_provider)

        # Check API key requirement
        if target_provider != "ollama" and not api_key:
            # Check if any other key is available
            for fallback_prov in ["gemini", "groq", "openrouter"]:
                fallback_key = self._get_api_key(fallback_prov)
                if fallback_key:
                    target_provider = fallback_prov
                    api_key = fallback_key
                    target_model = self.get_model_for_task(task_type, target_provider)
                    break

        if target_provider != "ollama" and not api_key:
            err_msg = (
                f"\n[ModelRouter Error] No API key detected for provider '{target_provider}'.\n"
                f"Please set a free API key to unlock online generation:\n"
                f"  - Groq (Free 500+ tok/s):   export GROQ_API_KEY=\"gsk_...\" (Sign up: https://console.groq.com/keys)\n"
                f"  - Gemini (Free 1M context): export GEMINI_API_KEY=\"AIza...\" (Sign up: https://aistudio.google.com)\n"
                f"  Or create a .env file in the project root with GROQ_API_KEY=your_key\n"
            )
            return {
                "model": target_model,
                "provider": target_provider,
                "task_type": task_type,
                "response": err_msg,
                "tokens_per_sec": 0.0,
                "elapsed_sec": 0.0,
                "prompt_tokens": 0,
                "response_tokens": 0,
            }

        if target_provider == "ollama":
            return self._query_ollama(prompt, target_model, task_type, stream, system)
        else:
            return self._query_openai_compatible(
                provider=target_provider,
                api_key=api_key,
                model=target_model,
                prompt=prompt,
                task_type=task_type,
                stream=stream,
                system=system,
                format=format,
            )

    def _query_openai_compatible(
        self,
        provider: str,
        api_key: str,
        model: str,
        prompt: str,
        task_type: str,
        stream: bool,
        system: Optional[str],
        format: Optional[str],
    ) -> Union[Dict[str, Any], StreamResponse]:
        cfg = PROVIDER_CONFIGS[provider]
        endpoint = cfg["api_base"]

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.1 if task_type in ["rtl", "sta"] else 0.2,
            "stream": stream,
        }
        if format == "json":
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "RTL2GDS-Autonomous-EDA/1.0",
        }
        if provider == "openrouter":
            headers["HTTP-Referer"] = "https://github.com/S-SUJAN-S/rtl2gds"
            headers["X-Title"] = "RTL-to-GDSII AI Automation"

        t0 = time.time()
        req_data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(endpoint, data=req_data, headers=headers, method="POST")

        if stream:
            def _stream_gen():
                try:
                    with urllib.request.urlopen(req, timeout=self.timeout, context=self.ssl_context) as resp:
                        for line in resp:
                            line_str = line.decode("utf-8", errors="ignore").strip()
                            if not line_str or line_str == "data: [DONE]":
                                continue
                            if line_str.startswith("data: "):
                                try:
                                    chunk_json = json.loads(line_str[6:])
                                    delta = chunk_json.get("choices", [{}])[0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        yield content
                                except Exception:
                                    pass
                except Exception as e:
                    yield f"\n[Streaming Error: {e}]"

            return StreamResponse(_stream_gen(), model=model, provider=provider, task_type=task_type)

        try:
            with urllib.request.urlopen(req, timeout=self.timeout, context=self.ssl_context) as resp:
                resp_json = json.loads(resp.read().decode("utf-8"))
            elapsed = round(time.time() - t0, 2)
            content = resp_json.get("choices", [{}])[0].get("message", {}).get("content", "")
            usage = resp_json.get("usage", {})
            prompt_toks = usage.get("prompt_tokens", 0)
            resp_toks = usage.get("completion_tokens", 0)
            tps = round(resp_toks / max(elapsed, 0.01), 1) if resp_toks > 0 else round(len(content.split()) * 1.3 / max(elapsed, 0.01), 1)

            return {
                "model": model,
                "provider": provider,
                "task_type": task_type,
                "response": content,
                "tokens_per_sec": tps,
                "elapsed_sec": elapsed,
                "prompt_tokens": prompt_toks,
                "response_tokens": resp_toks,
            }
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            return {
                "model": model,
                "provider": provider,
                "task_type": task_type,
                "response": f"[HTTP Error {e.code} from {provider}]: {err_body}",
                "tokens_per_sec": 0.0,
                "elapsed_sec": round(time.time() - t0, 2),
                "prompt_tokens": 0,
                "response_tokens": 0,
            }
        except Exception as e:
            return {
                "model": model,
                "provider": provider,
                "task_type": task_type,
                "response": f"[Request Error from {provider}]: {str(e)}",
                "tokens_per_sec": 0.0,
                "elapsed_sec": round(time.time() - t0, 2),
                "prompt_tokens": 0,
                "response_tokens": 0,
            }

    def _query_ollama(
        self,
        prompt: str,
        model: str,
        task_type: str,
        stream: bool,
        system: Optional[str],
    ) -> Union[Dict[str, Any], StreamResponse]:
        host = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
        endpoint = f"{host}/api/chat"
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {"model": model, "messages": messages, "stream": stream}
        req_data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(endpoint, data=req_data, headers={"Content-Type": "application/json"}, method="POST")

        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                resp_json = json.loads(resp.read().decode("utf-8"))
            elapsed = round(time.time() - t0, 2)
            content = resp_json.get("message", {}).get("content", "")
            return {
                "model": model,
                "provider": "ollama",
                "task_type": task_type,
                "response": content,
                "tokens_per_sec": 0.0,
                "elapsed_sec": elapsed,
                "prompt_tokens": 0,
                "response_tokens": 0,
            }
        except Exception as e:
            return {
                "model": model,
                "provider": "ollama",
                "task_type": task_type,
                "response": f"[Ollama Error]: {str(e)}",
                "tokens_per_sec": 0.0,
                "elapsed_sec": round(time.time() - t0, 2),
                "prompt_tokens": 0,
                "response_tokens": 0,
            }

    def list_models(self) -> List[Dict[str, Any]]:
        models_list = []
        for p, cfg in PROVIDER_CONFIGS.items():
            for t_type, m_name in cfg.get("models", {}).items():
                models_list.append({
                    "name": m_name,
                    "provider": p,
                    "task_type": t_type,
                    "size_mb": "Cloud (0 VRAM)",
                    "active": (p == self.active_provider),
                })
        return models_list

    def is_model_available(self, model_name: str) -> bool:
        return True


if __name__ == "__main__":
    print("=== Testing ModelRouter Cloud Providers ===")
    r = ModelRouter()
    print(f"Active Provider: {r.active_provider} ({PROVIDER_CONFIGS[r.active_provider]['name']})")
    res = r.query("What is the difference between blocking and non-blocking in Verilog?", task_type="rtl")
    print(f"Response snippet:\n{res['response'][:300]}...")
