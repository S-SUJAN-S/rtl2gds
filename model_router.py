"""
model_router.py
===============
Universal High-Performance Model Router for RTL-to-GDSII EDA Automation.
Supports free and high-speed cloud APIs (Cerebras, Groq, Google Gemini, DeepSeek, OpenRouter)
with multi-account key pooling (round-robin + auto-failover on 429) and graceful fallback
to local Ollama. Zero external dependencies required.

Supported Cloud Providers (Free Tiers & High Quotas):
  1. Cerebras Cloud (CEREBRAS_API_KEY):
     - 1 Million Free Tokens/Day forever (no credit card). 2,000+ tok/s on Wafer-Scale Engine.
     - Signup: https://cloud.cerebras.ai
     - Models: llama3.3-70b, llama3.1-8b
  2. Groq Cloud (GROQ_API_KEY):
     - 14,400 Requests/Day on 8B, 1,000 Requests/Day on 70B (500+ tok/s on LPU).
     - Signup: https://console.groq.com/keys
     - Models: llama-3.3-70b-versatile, qwen-2.5-coder-32b, deepseek-r1-distill-llama-70b
  3. DeepSeek Platform (DEEPSEEK_API_KEY):
     - Specialized reasoning and coding (deepseek-chat V3, deepseek-reasoner R1).
     - Signup: https://platform.deepseek.com
  4. Google Gemini (GEMINI_API_KEY or GOOGLE_API_KEY):
     - 1M token context window for large netlist analysis.
     - Signup: https://aistudio.google.com/app/apikey
     - Models: gemini-2.5-flash, gemini-1.5-pro, gemini-1.5-flash
  5. OpenRouter (OPENROUTER_API_KEY):
     - Access to free community endpoints (:free).
     - Signup: https://openrouter.ai/keys
  6. Local Ollama (OLLAMA_HOST):
     - Offline fallback at http://127.0.0.1:11434

Multi-Account Key Pooling:
  Configure multiple keys in .env from multiple accounts to multiply your rate limits:
    GROQ_API_KEY_1=gsk_...
    GROQ_API_KEY_2=gsk_...
    GROQ_API_KEY_3=gsk_...
  The router automatically round-robins across all keys and instantly fails over on HTTP 429.
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

PROVIDER_CONFIGS = {
    "cerebras": {
        "name": "Cerebras Cloud (1M Free Tokens/Day | 2,000 tok/s)",
        "api_base": "https://api.cerebras.ai/v1/chat/completions",
        "env_prefix": "CEREBRAS_API_KEY",
        "signup_url": "https://cloud.cerebras.ai",
        "models": {
            "rtl": "llama3.3-70b",
            "complex": "llama3.3-70b",
            "sta": "llama3.3-70b",
            "general": "llama3.1-8b",
            "reasoning": "llama3.3-70b",
        },
    },
    "groq": {
        "name": "Groq Cloud (14.4k Requests/Day Free Tier | 500+ tok/s)",
        "api_base": "https://api.groq.com/openai/v1/chat/completions",
        "env_prefix": "GROQ_API_KEY",
        "signup_url": "https://console.groq.com/keys",
        "models": {
            "rtl": "qwen/qwen3.8-27b",
            "complex": "qwen/qwen3.8-27b",
            "sta": "qwen/qwen3.8-27b",
            "general": "qwen/qwen3.8-27b",
            "reasoning": "qwen/qwen3.8-27b",
        },
    },
    "deepseek": {
        "name": "DeepSeek Platform (Frontier Reasoning & Coding)",
        "api_base": "https://api.deepseek.com/chat/completions",
        "env_prefix": "DEEPSEEK_API_KEY",
        "signup_url": "https://platform.deepseek.com",
        "models": {
            "rtl": "deepseek-chat",
            "complex": "deepseek-chat",
            "sta": "deepseek-reasoner",
            "general": "deepseek-chat",
            "reasoning": "deepseek-reasoner",
        },
    },
    "gemini": {
        "name": "Google Gemini API (1M Context Window)",
        "api_base": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "env_prefix": "GEMINI_API_KEY",
        "signup_url": "https://aistudio.google.com/app/apikey",
        "models": {
            "rtl": "gemini-2.5-flash",
            "complex": "gemini-1.5-pro",
            "sta": "gemini-2.5-flash",
            "general": "gemini-2.5-flash",
            "reasoning": "gemini-2.5-flash",
        },
    },
    "nvidia": {
        "name": "NVIDIA NIM Cloud (1,000 Free Credits | H100 DGX Clusters)",
        "api_base": "https://integrate.api.nvidia.com/v1/chat/completions",
        "env_prefix": "NVIDIA_API_KEY",
        "signup_url": "https://build.nvidia.com",
        "models": {
            "rtl": "mistralai/codestral-22b-instruct-v0.1",
            "complex": "nvidia/llama-3.1-nemotron-70b-instruct",
            "sta": "nvidia/llama-3.1-nemotron-70b-instruct",
            "general": "nvidia/llama-3.1-nemotron-70b-instruct",
            "reasoning": "deepseek-ai/deepseek-v4.1-flash",
        },
    },
    "openrouter": {
        "name": "OpenRouter (Free Community Endpoints)",
        "api_base": "https://openrouter.ai/api/v1/chat/completions",
        "env_prefix": "OPENROUTER_API_KEY",
        "signup_url": "https://openrouter.ai/keys",
        "models": {
            "rtl": "nvidia/nemotron-3.5-lightning:free",
            "complex": "nvidia/nemotron-3-ultra-550b-a55b:free",
            "sta": "nvidia/nemotron-3-ultra-550b-a55b:free",
            "general": "google/gemma-4-31b-it:free",
            "reasoning": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
        },
    },
    "ollama": {
        "name": "Local Ollama Server",
        "api_base": os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434") + "/api/chat",
        "env_prefix": None,
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
    def __init__(self, provider: Optional[str] = None, api_key: Optional[str] = None, timeout: int = 120):
        self.timeout = timeout
        self.override_api_key = api_key
        self._key_indices: Dict[str, int] = {}
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        self.active_provider = self._resolve_provider(provider)

    def _get_api_key(self, provider: str) -> Optional[str]:
        pool = self._get_key_pool(provider)
        return pool[0] if pool else None

    def _get_key_pool(self, provider: str) -> List[str]:
        if self.override_api_key:
            return [self.override_api_key]
        cfg = PROVIDER_CONFIGS.get(provider, {})
        prefix = cfg.get("env_prefix")
        if not prefix:
            return []

        keys = []
        base_val = os.environ.get(prefix)
        if base_val:
            for k in base_val.split(","):
                k = k.strip()
                if k and k not in keys:
                    keys.append(k)

        if provider == "gemini":
            g_val = os.environ.get("GOOGLE_API_KEY")
            if g_val:
                for k in g_val.split(","):
                    k = k.strip()
                    if k and k not in keys:
                        keys.append(k)

        for i in range(1, 11):
            val = os.environ.get(f"{prefix}_{i}")
            if val:
                val = val.strip()
                if val and val not in keys:
                    keys.append(val)
            if provider == "gemini":
                val_g = os.environ.get(f"GOOGLE_API_KEY_{i}")
                if val_g:
                    val_g = val_g.strip()
                    if val_g and val_g not in keys:
                        keys.append(val_g)

        return keys

    def _resolve_provider(self, requested: Optional[str]) -> str:
        if requested and requested.lower() in PROVIDER_CONFIGS:
            return requested.lower()

        if self._get_key_pool("cerebras"):
            return "cerebras"
        if self._get_key_pool("groq"):
            return "groq"
        if self._get_key_pool("deepseek"):
            return "deepseek"
        if self._get_key_pool("gemini"):
            return "gemini"
        if self._get_key_pool("openrouter"):
            return "openrouter"
        if self._is_ollama_alive():
            return "ollama"

        return "cerebras"

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
        cfg = PROVIDER_CONFIGS.get(p, PROVIDER_CONFIGS["cerebras"])
        models = cfg.get("models", {})
        return models.get(task_type, models.get("general", "llama3.3-70b"))

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
        keys = self._get_key_pool(target_provider)

        if target_provider != "ollama" and not keys:
            for fallback_prov in ["cerebras", "groq", "deepseek", "gemini", "openrouter"]:
                f_keys = self._get_key_pool(fallback_prov)
                if f_keys:
                    target_provider = fallback_prov
                    keys = f_keys
                    break

        if target_provider != "ollama" and not keys:
            err_msg = (
                f"\n[ModelRouter Error] No API key detected for provider '{target_provider}'.\n"
                "Please configure free API keys in your .env file to run the pipeline:\n"
                "  - Cerebras (1M Free Tokens/day | 2,000 tok/s): CEREBRAS_API_KEY=\"csk-...\" (https://cloud.cerebras.ai)\n"
                "  - Groq (14.4k Requests/day | 500 tok/s):       GROQ_API_KEY=\"gsk_...\"     (https://console.groq.com/keys)\n"
                "  - DeepSeek (15M Free Tokens Trial):          DEEPSEEK_API_KEY=\"sk-...\"    (https://platform.deepseek.com)\n"
                "  - Gemini (1M Context Window):                 GEMINI_API_KEY=\"AIza...\"    (https://aistudio.google.com)\n"
                "  Tip: Add _1, _2, _3 suffixes for multi-account round-robin key pooling!\n"
            )
            return {
                "model": model or "unspecified",
                "provider": target_provider,
                "task_type": task_type,
                "response": err_msg,
                "tokens_per_sec": 0.0,
                "elapsed_sec": 0.0,
                "prompt_tokens": 0,
                "response_tokens": 0,
            }

        target_model = model or self.get_model_for_task(task_type, target_provider)

        if target_provider == "ollama":
            return self._query_ollama(prompt, target_model, task_type, stream, system)
        else:
            return self._query_cloud_with_pool(
                provider=target_provider,
                keys=keys,
                model=target_model,
                prompt=prompt,
                task_type=task_type,
                stream=stream,
                system=system,
                format=format,
            )

    def _query_cloud_with_pool(
        self,
        provider: str,
        keys: List[str],
        model: str,
        prompt: str,
        task_type: str,
        stream: bool,
        system: Optional[str],
        format: Optional[str],
    ) -> Union[Dict[str, Any], StreamResponse]:
        cfg = PROVIDER_CONFIGS[provider]
        endpoint = cfg["api_base"]

        cur_idx = self._key_indices.get(provider, 0)
        num_keys = len(keys)

        last_error = None
        for attempt in range(num_keys):
            active_idx = (cur_idx + attempt) % num_keys
            api_key = keys[active_idx]

            self._key_indices[provider] = (active_idx + 1) % num_keys

            result = self._execute_http_request(
                provider=provider,
                endpoint=endpoint,
                api_key=api_key,
                key_index=active_idx + 1,
                model=model,
                prompt=prompt,
                task_type=task_type,
                stream=stream,
                system=system,
                format=format,
            )

            if isinstance(result, dict) and "[HTTP Error 429" in result.get("response", ""):
                last_error = result
                if num_keys > 1:
                    print(f"[*] [ModelRouter] Account key #{active_idx + 1} for '{provider}' hit rate limit (429). Rotating to next account key...")
                    continue
                else:
                    break

            return result

        fallback_providers = [p for p in ["cerebras", "groq", "deepseek", "gemini", "openrouter"] if p != provider]
        for fb_prov in fallback_providers:
            fb_keys = self._get_key_pool(fb_prov)
            if fb_keys:
                print(f"[!] [ModelRouter] All keys for '{provider}' exhausted. Cascading failover to '{fb_prov}'...")
                fb_model = self.get_model_for_task(task_type, fb_prov)
                return self._query_cloud_with_pool(
                    provider=fb_prov,
                    keys=fb_keys,
                    model=fb_model,
                    prompt=prompt,
                    task_type=task_type,
                    stream=stream,
                    system=system,
                    format=format,
                )

        return last_error or {
            "model": model,
            "provider": provider,
            "task_type": task_type,
            "response": "[ModelRouter Error]: All available keys and providers hit rate limits.",
            "tokens_per_sec": 0.0,
            "elapsed_sec": 0.0,
            "prompt_tokens": 0,
            "response_tokens": 0,
        }

    def _execute_http_request(
        self,
        provider: str,
        endpoint: str,
        api_key: str,
        key_index: int,
        model: str,
        prompt: str,
        task_type: str,
        stream: bool,
        system: Optional[str],
        format: Optional[str],
    ) -> Union[Dict[str, Any], StreamResponse]:
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
                "key_index": key_index,
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
                "key_index": key_index,
                "task_type": task_type,
                "response": f"[HTTP Error {e.code} from {provider} (Key #{key_index})]: {err_body}",
                "tokens_per_sec": 0.0,
                "elapsed_sec": round(time.time() - t0, 2),
                "prompt_tokens": 0,
                "response_tokens": 0,
            }
        except Exception as e:
            return {
                "model": model,
                "provider": provider,
                "key_index": key_index,
                "task_type": task_type,
                "response": f"[Request Error from {provider} (Key #{key_index})]: {str(e)}",
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
            eval_count = resp_json.get("eval_count", 0)
            eval_dur = resp_json.get("eval_duration", 1)
            tps = round(eval_count / (eval_dur / 1e9), 1) if eval_dur > 0 else 0.0

            return {
                "model": model,
                "provider": "ollama",
                "task_type": task_type,
                "response": content,
                "tokens_per_sec": tps,
                "elapsed_sec": elapsed,
                "prompt_tokens": resp_json.get("prompt_eval_count", 0),
                "response_tokens": eval_count,
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

    def extract_verilog_code(self, response_text: str) -> str:
        match = re.search(r"```(?:verilog|systemverilog)?\s*\n(.*?)```", response_text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        mod_match = re.search(r"(module\s+\w+.*?endmodule)", response_text, re.DOTALL)
        if mod_match:
            return mod_match.group(1).strip()
        return response_text.strip()
