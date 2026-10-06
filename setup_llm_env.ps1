Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force

$OLLAMA_EXE   = "C:\Users\ssuja\AppData\Local\Programs\Ollama\ollama.exe"
$PROJECT_ROOT = "c:\Users\ssuja\OneDrive\Desktop\Learn_Antigravity_Advance\rtl-2-gds-automation-local-llm"
$API_BASE     = "http://127.0.0.1:11434"
$RTL_MODEL    = "hf.co/mradermacher/RTLCoder-Deepseek-v1.1-GGUF:Q3_K_M"
$RTL_ALIAS    = "hf.co/mradermacher/RTLCoder-Deepseek-v1.1-GGUF:Q3_K_M"

function Write-Step([string]$msg) {
    Write-Host ""
    Write-Host "========================================"  -ForegroundColor Cyan
    Write-Host "  $msg"                                   -ForegroundColor Cyan
    Write-Host "========================================"  -ForegroundColor Cyan
    Write-Host ""
}

function Wait-OllamaReady([int]$TimeoutSec = 30) {
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        try {
            $r = Invoke-RestMethod "$API_BASE" -TimeoutSec 2 -ErrorAction Stop
            if ($r -match "running") { return $true }
        } catch {}
        Start-Sleep -Seconds 1
    }
    return $false
}

function Pull-Model([string]$ModelName) {
    Write-Host "  -> Pulling: $ModelName" -ForegroundColor Yellow
    $t0 = Get-Date
    try {
        $bodyObj = @{ name = $ModelName; stream = $false }
        $bodyJson = $bodyObj | ConvertTo-Json
        Invoke-RestMethod -Uri "$API_BASE/api/pull" -Method POST -Body $bodyJson `
            -ContentType "application/json" -TimeoutSec 7200 | Out-Null
        $secs = [int]((Get-Date) - $t0).TotalSeconds
        Write-Host "  [OK] Pulled $ModelName in ${secs}s" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "  [FAIL] $ModelName : $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Test-Model([string]$ModelName, [string]$TestPrompt) {
    Write-Host "  -> Testing: $ModelName" -ForegroundColor Yellow
    $t0 = Get-Date
    try {
        $bodyObj = @{ model = $ModelName; prompt = $TestPrompt; stream = $false }
        $bodyJson = $bodyObj | ConvertTo-Json -Depth 5
        $resp = Invoke-RestMethod -Uri "$API_BASE/api/generate" -Method POST -Body $bodyJson `
            -ContentType "application/json" -TimeoutSec 300
        $secs = [int]((Get-Date) - $t0).TotalSeconds
        $evalDurSec = [math]::Max($resp.eval_duration / 1e9, 0.01)
        $tps = [math]::Round($resp.eval_count / $evalDurSec, 1)
        $preview = $resp.response.Substring(0, [math]::Min(120, $resp.response.Length))
        Write-Host "  [OK] ${secs}s | ${tps} tok/s | $preview..." -ForegroundColor Green
        return @{ ok=$true; secs=$secs; tps=$tps; output=$resp.response }
    } catch {
        Write-Host "  [FAIL] $ModelName : $($_.Exception.Message)" -ForegroundColor Red
        return @{ ok=$false; secs=0; tps=0; output="" }
    }
}

function Unload-Model([string]$ModelName) {
    try {
        $bodyObj = @{ model = $ModelName; keep_alive = "0s" }
        $bodyJson = $bodyObj | ConvertTo-Json
        Invoke-RestMethod -Uri "$API_BASE/api/generate" -Method POST -Body $bodyJson `
            -ContentType "application/json" -TimeoutSec 15 | Out-Null
    } catch {}
    Start-Sleep -Seconds 2
}

function Get-GpuMemMB {
    try {
        $smi = & nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits 2>$null
        return [int]$smi.Trim()
    } catch { return 0 }
}

function Get-RamUsedMB {
    $os = Get-CimInstance Win32_OperatingSystem
    return [int](($os.TotalVisibleMemorySize - $os.FreePhysicalMemory) / 1024)
}

# ============================================================
# STEP 1: Start server
# ============================================================
Write-Step "STEP 1: Start Ollama Server"

Get-Process -Name "ollama*" -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

$serverJob = Start-Job -ScriptBlock {
    param($exe)
    & $exe serve 2>&1
} -ArgumentList $OLLAMA_EXE

Write-Host "Server job started (Id=$($serverJob.Id)) - waiting for GPU discovery..."
Start-Sleep -Seconds 8

if (Wait-OllamaReady -TimeoutSec 30) {
    Write-Host "[OK] API ready at $API_BASE" -ForegroundColor Green
} else {
    Write-Host "[FAIL] Server did not start in 20s" -ForegroundColor Red
    Receive-Job $serverJob | ForEach-Object { Write-Host $_ }
    exit 1
}

# ============================================================
# STEP 2: Pull models
# ============================================================
Write-Step "STEP 2: Pull Models"

$pull3b   = Pull-Model "qwen2.5-coder:3b"
$pull7b   = Pull-Model "qwen2.5-coder:7b"
$pullRTL  = Pull-Model $RTL_MODEL

# ============================================================
# STEP 3: Create RTLCoder alias
# ============================================================
Write-Step "STEP 3: Create RTLCoder Alias"

$sysPrompt = "You are RTLCoder, an expert Verilog and SystemVerilog RTL hardware engineer. Generate clean, synthesizable, well-commented HDL code with proper reset handling, clock domain management, FSM encoding, and timing-safe designs."
$mfPath = Join-Path $PROJECT_ROOT "Modelfile.rtlcoder"
$mfLines = @(
    "FROM $RTL_MODEL",
    "SYSTEM `"$sysPrompt`"",
    "PARAMETER temperature 0.1",
    "PARAMETER top_p 0.9",
    "PARAMETER num_predict 2048"
)
[System.IO.File]::WriteAllLines($mfPath, $mfLines, [System.Text.Encoding]::UTF8)
Write-Host "Modelfile: $mfPath"

try {
    $mfContent = [System.IO.File]::ReadAllText($mfPath)
    $bodyObj = @{ name = $RTL_ALIAS; modelfile = $mfContent }
    $bodyJson = $bodyObj | ConvertTo-Json -Depth 5
    Invoke-RestMethod -Uri "$API_BASE/api/create" -Method POST -Body $bodyJson `
        -ContentType "application/json" -TimeoutSec 120 | Out-Null
    Write-Host "[OK] Alias '$RTL_ALIAS' created" -ForegroundColor Green
} catch {
    Write-Host "[WARN] Alias failed: $($_.Exception.Message) -- using full HF path" -ForegroundColor Yellow
    $RTL_ALIAS = $RTL_MODEL
}

# ============================================================
# STEP 4: List models
# ============================================================
Write-Step "STEP 4: Installed Models"

$tags = Invoke-RestMethod -Uri "$API_BASE/api/tags"
$tags.models | ForEach-Object {
    $mb = [math]::Round($_.size / 1MB, 0)
    Write-Host ("  {0,-48} {1,6} MB" -f $_.name, $mb) -ForegroundColor White
}

# ============================================================
# STEP 5: Verify models
# ============================================================
Write-Step "STEP 5: Model Verification"

$modelList = @("qwen2.5-coder:3b", "qwen2.5-coder:7b", $RTL_ALIAS)
$verifyResults = @{}
foreach ($m in $modelList) {
    $ram0 = Get-RamUsedMB
    $gpu0 = Get-GpuMemMB
    $res  = Test-Model $m "Reply with exactly one word: VERIFIED"
    $verifyResults[$m] = @{
        ok       = $res.ok
        secs     = $res.secs
        tps      = $res.tps
        ramDelta = (Get-RamUsedMB) - $ram0
        gpuDelta = (Get-GpuMemMB) - $gpu0
        output   = $res.output
    }
    Unload-Model $m
}

# ============================================================
# STEP 6: Benchmark
# ============================================================
Write-Step "STEP 6: VLSI Benchmark"

$benchmarks = @(
    @{ id="alu";  prompt="Generate a complete 4-bit ALU in Verilog with ADD, SUB, AND, OR, XOR and carry-out. Show full code." },
    @{ id="fifo"; prompt="Generate a 16-entry synchronous FIFO in Verilog with full and empty flags. Show full code." },
    @{ id="uart"; prompt="Generate a UART TX module in Verilog at 9600 baud, 8N1. Show full code." },
    @{ id="py";   prompt="Write a Python script to parse a Yosys JSON netlist file and print statistics of each cell type used." },
    @{ id="sta";  prompt="Explain what a setup-time violation is in digital design, why it happens, and 3 ways to fix it." }
)

$benchResults = @{}
foreach ($b in $benchmarks) {
    Write-Host "`n  Benchmark [$($b.id)]:" -ForegroundColor Magenta
    $benchResults[$b.id] = @{}
    foreach ($m in $modelList) {
        $res = Test-Model $m $b.prompt
        $benchResults[$b.id][$m] = $res
        Unload-Model $m
    }
}

# ============================================================
# STEP 7: Save results
# ============================================================
Write-Step "STEP 7: Save Results"

$report = @{
    timestamp    = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    system       = @{ gpu="RTX 2050 4GB"; ram="8GB"; os="Windows 11"; ollama="0.32.7" }
    models       = @($tags.models | ForEach-Object { @{ name=$_.name; sizeMB=[math]::Round($_.size/1MB,0) } })
    verification = $verifyResults
    benchmarks   = $benchResults
}

$jsonOut  = $report | ConvertTo-Json -Depth 10
$jsonPath = Join-Path $PROJECT_ROOT "benchmark_results.json"
[System.IO.File]::WriteAllText($jsonPath, $jsonOut, [System.Text.Encoding]::UTF8)
Write-Host "Saved: $jsonPath" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  SETUP COMPLETE" -ForegroundColor Green
Write-Host "  API:    $API_BASE" -ForegroundColor Green
Write-Host "  Models: qwen2.5-coder:3b, qwen2.5-coder:7b, $RTL_ALIAS" -ForegroundColor Green
Write-Host "  Report: $jsonPath" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
