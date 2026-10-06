# WSL Storage Optimization & Maintenance Guide 🧹

## 1. Problem Overview
WSL2 virtual disk images (`ext4.vhdx`) dynamically expand when Linux applications write data, but by default they **do not automatically shrink** when files are deleted inside Linux. 

In this digital physical design repository:
* Every OpenLane RTL-to-GDS execution generates hundreds of megabytes to gigabytes of intermediate routing iterations, DEF layers, SDF, SPEF, and timing matrices in `<design>/runs/`.
* Over multiple test runs across `simd_alu_v2`, `sdpa_accelerator`, `systolic`, and `spm`, scratch files accumulated to **~30.7 GB**.
* Formal verification runs (`/home/sujan123/simd_alu_v2/equiv`) accumulated an additional **5.9 GB**.
* On Windows, `ext4.vhdx` grew to **61.54 GB**, driving drive `C:` down to **~50 GB free**.

---

## 2. Storage Inventory Breakdown

| Component | Path | Size | Status | Action |
| :--- | :--- | :--- | :--- | :--- |
| **OpenLane Runs** | `~/rtl2gds/OpenLane/designs/*/runs` | ~30.7 GB | Scratch / Iterations | **Safe to prune** (Final artifacts are safe in Windows `outputs/`) |
| **Formal Equiv Scratch** | `~/simd_alu_v2/equiv` | 5.9 GB | Old Verification Logs | **Safe to remove** |
| **Journal Logs** | `/var/log/journal` | ~810 MB | OS System Logs | **Pruned to 50MB** |
| **APT Cache** | `/var/cache/apt` | ~570 MB | Cached `.deb` packages | **Cleaned** |
| **Pip Cache** | `~/.cache/pip` | ~150 MB | Python Wheel Cache | **Purged** |
| **Sky130 PDK** | `~/.ciel` | 2.1 GB | Silicon Technology Kit | 🔒 **KEEP - Required for ASIC flow** |
| **EDA Binaries** | `/usr/bin` (yosys, klayout, etc.) | 3.1 GB | Core Toolchain | 🔒 **KEEP - Required** |
| **Docker OpenLane** | `/var/lib/docker` | 1.62 GB | OpenROAD Container | 🔒 **KEEP - Required** |

---

## 3. How to Clean and Shrink the Disk

### Step A: Clean Inside WSL
Run the automated cleanup script:
```bash
chmod +x scripts/environment/clean_wsl_storage.sh
./scripts/environment/clean_wsl_storage.sh
```
This prunes:
* System and package download caches.
* All intermediate `<design>/runs/*` iterations.
* The obsolete `~/simd_alu_v2/equiv` scratch folder.

### Step B: Reclaim Physical Space on Windows C:
After deleting files in WSL, Windows requires a VHDX compaction. Run in **PowerShell**:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\environment\compact_wsl_disk.ps1
```
Or manually run:
```powershell
wsl --shutdown
wsl --manage Ubuntu --set-sparse true
```
This forces Windows to reclaim the deleted blocks and shrink `ext4.vhdx` back down to ~12–15 GB, immediately restoring **35–45 GB** of free space to Drive `C:`.

---

## 4. Best Practices Going Forward
1. **Always export what you need**: After completing an OpenLane run, ensure your final GDS, LEF, DEF, and reports are saved to your Windows `outputs/` folder (which `./build.sh` already does automatically).
2. **Periodically prune old runs**: After validating a tapeout run, run `./scripts/environment/clean_wsl_storage.sh` to prevent `runs/` folders from accumulating 10+ gigabytes.
3. **Sparse VHD enabled**: With `--set-sparse true` enabled, any future file deletions in WSL will immediately return storage space to Windows without requiring manual compaction.
