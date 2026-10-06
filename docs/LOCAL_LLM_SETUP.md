# Local LLM Environment — VLSI AI Engineer
**HP Victus | NVIDIA RTX 2050 4GB | 8GB RAM | Windows 11 | Ollama 0.32.7**

---

## System Overview

| Component | Detail |
|-----------|--------|
| GPU | NVIDIA GeForce RTX 2050 (4.0 GiB VRAM, CUDA 8.6) |
| RAM | 8 GB DDR4 |
| OS | Windows 11 |
| Ollama | v0.32.7 |
| API | `http://127.0.0.1:11434` |
| Models dir | `C:\Users\ssuja\.ollama\models` |
| Auto-start | `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\start_ollama.bat` |

> [!IMPORTANT]
> Always use `http://127.0.0.1:11434` (not `localhost`). On this Windows system, `localhost` resolves to IPv6 `::1` which Ollama does not bind to.

---

## Installed Models

| Model | Alias | Parameters | Disk | Primary Use |
|-------|-------|-----------|------|-------------|
| `qwen2.5-coder:3b` | - | 3B | ~2.0 GB | Fast coding, scripts, Q&A |
| `qwen2.5-coder:7b` | - | 7B | ~4.5 GB | Complex coding, architecture |
| `hf.co/mradermacher/RTLCoder-Deepseek-v1.1-GGUF:Q3_K_M` | `rtlcoder` | 6.7B | ~3.3 GB | Verilog/RTL generation |

### Resource Usage (Estimated at Runtime)

| Model | VRAM Used | RAM Used | GPU Offload |
|-------|-----------|----------|-------------|
| `qwen2.5-coder:3b` | ~2.0 GB | ~3.0 GB | Full GPU |
| `qwen2.5-coder:7b` | ~3.5 GB | ~5.5 GB | Partial GPU/CPU |
| `rtlcoder` | ~3.0 GB | ~4.5 GB | Partial GPU/CPU |

> [!NOTE]
> Only one model can be loaded in VRAM at a time on this hardware. Ollama automatically unloads the previous model when switching. Use `keep_alive: "0s"` to force unload.

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `http://127.0.0.1:11434` | GET | Health check |
| `/api/tags` | GET | List installed models |
| `/api/generate` | POST | Text generation |
| `/api/chat` | POST | Chat with history |
| `/api/pull` | POST | Pull a model |
| `/api/create` | POST | Create model from Modelfile |
| `/api/ps` | GET | Currently loaded models |
| `/api/show` | POST | Model info |

---

## Quick Start

### 1. Start the Server

```batch
:: Option A: Startup script (also auto-runs at logon)
start_ollama.bat

:: Option B: Direct binary
"C:\Users\ssuja\AppData\Local\Programs\Ollama\ollama.exe" serve
```

### 2. Verify Server

```powershell
Invoke-RestMethod http://127.0.0.1:11434
# Expected: "Ollama is running"
```

### 3. Use the Model Router (Python)

```python
from model_router import ModelRouter

router = ModelRouter()

# Auto-detect from prompt keywords
result = router.query("Generate a UART TX module in Verilog", task_type="auto")
print(result["response"])

# Explicit task types
result = router.generate_rtl("Write a 4-bit ALU in Verilog")
result = router.generate_code("Write a Python netlist parser")
result = router.analyze("Explain setup time violations")
result = router.explain_timing("What causes hold time violations?")

# Inspect results
print(f"Model used  : {result['model']}")
print(f"Task type   : {result['task_type']}")
print(f"Elapsed     : {result['elapsed_sec']}s")
print(f"Speed       : {result['tokens_per_sec']} tok/s")
```

### 4. Direct REST API (PowerShell)

```powershell
$body = @{
    model  = "qwen2.5-coder:3b"
    prompt = "Generate a D flip-flop in Verilog"
    stream = $false
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/generate" `
    -Method POST -Body $body -ContentType "application/json"
```

---

## Model Routing Logic

```
Task Type   Primary Model           Fallback
-----------------------------------------------------
general   ->  qwen2.5-coder:3b    ->  (none)
complex   ->  qwen2.5-coder:7b    ->  (none)
rtl       ->  rtlcoder            ->  qwen2.5-coder:7b
sta       ->  qwen2.5-coder:7b    ->  (none)
auto      ->  keyword detection   ->  see below
```

**Auto-routing keywords:**

| Keywords in Prompt | Task |
|-------------------|------|
| verilog, rtl, module, posedge, fifo, alu, uart, sky130, gds | `rtl` |
| explain, analyze, architecture, debug, algorithm | `complex` |
| everything else | `general` |

---

## Ollama Command Reference

```powershell
# IMPORTANT: Use the full path to ollama.exe, not the 'ollama' alias in PATH
$OLLAMA = "C:\Users\ssuja\AppData\Local\Programs\Ollama\ollama.exe"

& $OLLAMA list               # List installed models
& $OLLAMA pull qwen2.5-coder:3b  # Pull a model
& $OLLAMA run qwen2.5-coder:3b   # Interactive chat
& $OLLAMA show qwen2.5-coder:3b  # Model details
& $OLLAMA rm model-name          # Delete a model
& $OLLAMA create mymodel -f Modelfile  # Create from Modelfile
& $OLLAMA --version              # Version check
```

> [!WARNING]
> Do NOT use bare `ollama` from PATH - it resolves to `ollama app.exe` (GUI wrapper) which fails to initialize on this system. Always use the full path to `ollama.exe`.

---

## Project Files

| File | Purpose |
|------|---------|
| `setup_llm_env.ps1` | Full setup: server + pulls + verify + benchmark |
| `start_ollama.bat` | Start/auto-start Ollama server |
| `model_router.py` | Python router with auto-routing and fallback |
| `model_router_config.yaml` | Swap models here without touching code |
| `Modelfile.rtlcoder` | RTLCoder alias with VLSI system prompt |
| `benchmark_results.json` | Auto-generated benchmark data |
| `LOCAL_LLM_SETUP.md` | This documentation |

---

## Performance Tuning for RTX 2050 + 8GB RAM

### Environment Variables (set before starting server)

```powershell
$env:OLLAMA_GPU_OVERHEAD    = "512"   # Reserve 512MB VRAM for OS
$env:OLLAMA_CONTEXT_LENGTH  = "4096"  # Match VRAM capacity
$env:OLLAMA_NUM_PARALLEL    = "1"     # Single request (RAM limited)
$env:OLLAMA_FLASH_ATTENTION = "1"     # Faster on RTX series
```

### VRAM Management

```python
# Free VRAM after heavy tasks
router.unload_model("qwen2.5-coder:7b")
```

### Recommended Context Lengths

| Model | ctx | Reason |
|-------|-----|--------|
| `qwen2.5-coder:3b` | 8192 | Fits fully in VRAM |
| `qwen2.5-coder:7b` | 4096 | Shared GPU+CPU |
| `rtlcoder` | 4096 | Shared GPU+CPU |

### RTL Generation Best Practices

- Use `temperature=0.1` for deterministic, synthesizable code
- Use `num_predict=2048` for complete module generation
- One module per prompt - do not chain multiple
- Always specify port widths and clock frequency in the prompt

---

## Expected Performance

| Model | Expected tok/s | Best For |
|-------|---------------|----------|
| `qwen2.5-coder:3b` | 30-50 tok/s | Quick scripts, Q&A |
| `qwen2.5-coder:7b` | 10-20 tok/s | Complex tasks |
| `rtlcoder` | 10-18 tok/s | Verilog generation |

---

## Future VLSI Toolchain Integration

```
ModelRouter
    |
    +-- RTL Generation  ->  rtlcoder / qwen2.5-coder:7b
    |       |
    |       v
    |   Verilator / Icarus Verilog (simulation)
    |       |
    |       v
    |   Yosys (synthesis)
    |       |
    |       v
    |   OpenSTA (static timing analysis)
    |       |
    |       v
    |   OpenROAD (place and route)
    |       |
    |       v
    |   Magic / KLayout (GDSII export)
    |
    +-- RAG (retrieval from PDK docs, STA reports, netlists)
```

---

## 5. Local LLM RTL-to-GDS Pipeline (NEW)

The previous implementation relied on the Antigravity IDE agent framework and cloud Gemini models. We have now built a **standalone, fully local Python orchestrator** that replicates the 4-stage flow using Ollama and native WSL tools.

### Features
* **100% Local AI**: Uses `RTLCoder`, `qwen2.5-coder:7b`, and `qwen2.5-coder:3b` automatically via `model_router.py`.
* **Real EDA Execution**: Uses `wsl_tool_runner.py` to seamlessly execute `verilator`, `iverilog`, and `yosys` inside your Ubuntu WSL instance.
* **Auto-Start**: The pipeline will automatically launch the Ollama server in the background if it's not running.
* **Auto-Fix Loop**: If the RTL fails Verilator linting, `RTLCoder` will attempt to automatically patch the Verilog and re-lint it.

### Usage
Run the pipeline from the project root:

```bash
# Run a specific design (e.g., full_adder, alu4bit, uart)
python rtl_local_pipeline.py --design full_adder

# Run all 3 test designs sequentially
python rtl_local_pipeline.py --all

# Run only specific stages (1=Frontend Lint/Sim, 2=Backend Synthesis, etc.)
python rtl_local_pipeline.py --design uart --stages 1,2
```

### Outputs
All outputs are saved to `outputs/pipeline_runs/<design>/<timestamp>/`:
* `stage1_lint.txt` — Verilator raw output
* `stage1_llm_lint_analysis.md` — RTLCoder analysis of the lint results
* `stage1_simulation.txt` — Icarus Verilog simulation logs
* `stage1_llm_sim_analysis.md` — Simulation analysis
* `stage2_synthesis.txt` — Yosys synthesis logs and statistics
* `stage2_llm_synth_analysis.md` — LLM area and timing review
* `stage4_signoff_report.md` — Final executive summary report
* `pipeline_results.json` — Master JSON of all metrics

---

## Troubleshooting

### Server won't start

```powershell
Get-Process -Name "ollama*" | Stop-Process -Force
& "C:\Users\ssuja\AppData\Local\Programs\Ollama\ollama.exe" serve
Get-Content "$env:LOCALAPPDATA\Ollama\server.log" -Tail 50
```

### API not responding

```powershell
Test-NetConnection -ComputerName 127.0.0.1 -Port 11434
Invoke-RestMethod http://127.0.0.1:11434
```

### Model loads slowly / out of memory

```powershell
nvidia-smi --query-gpu=memory.free,memory.total --format=csv
Invoke-RestMethod http://127.0.0.1:11434/api/ps
```

### RTLCoder alias not found

Re-run `setup_llm_env.ps1` - it recreates the alias automatically. The router falls back to `qwen2.5-coder:7b` in the meantime.

### `ollama` not found in new terminal

```powershell
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" +
            [System.Environment]::GetEnvironmentVariable("Path","User")
```

---

*Generated by Antigravity AI | 2026-08-10*
