import sys
from pathlib import Path
import subprocess

project_dir = Path(r"c:\Users\ssuja\OneDrive\Desktop\Learn_Antigravity_Advance\rtl-2-gds-automation-local-llm")
sys.path.append(str(project_dir))

from llm_agents import RTLFixAgent, _query

def run_cmd(cmd):
    print(f"[CMD] {cmd}")
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return res

def main():
    design_path = project_dir / "designs" / "axi4_lite_sram.v"
    verilog_code = design_path.read_text(encoding="utf-8")
    
    print("=== 1. Invoking Local LLM: RTL Fix Agent ===")
    errors = ["%Error: syntax error, unexpected end of file at line 160. The file was cut off. Close the if/else block, close the always block, and add endmodule."]
    fix_ai = RTLFixAgent()
    fix_ai.verbose = False
    
    print("Sending truncated RTL to Ollama for fixing...")
    result = fix_ai.fix(verilog_code, errors, [], "axi4_lite_sram")
    
    fixed_code = result["fixed_verilog"]
    if fixed_code:
        design_path.write_text(fixed_code, encoding="utf-8")
        print("\n[+] Local LLM fixed the Verilog and wrote it back.")
    else:
        print("[-] LLM failed to return fixed code.")
        return
        
    print("\n=== 2. Re-running Verilator ===")
    cmd = f'wsl bash -c "verilator --lint-only -Wall -Wno-fatal --timing /mnt/c/Users/ssuja/OneDrive/Desktop/Learn_Antigravity_Advance/rtl-2-gds-automation-local-llm/designs/axi4_lite_sram.v 2>&1"'
    lint_res = run_cmd(cmd)
    print(lint_res.stdout)
    if lint_res.returncode == 0 or "%Error" not in lint_res.stdout:
        print("[+] Lint Passed!")
    else:
        print("[-] Lint Failed after fix.")
        
    print("\n=== 3. Invoking Local LLM: Testbench Agent ===")
    prompt = f"""
Write a Verilog testbench for the following AXI4-Lite SRAM Controller.
Save the module as `axi4_sram_controller_tb`.
Ensure you test a write transaction followed by a read transaction.
Return ONLY the Verilog code inside ```verilog ... ```, no other text.

RTL:
{fixed_code}
"""
    print("Sending prompt to Ollama to generate Testbench...")
    res_tb = _query(prompt, task_type="rtl", stream=False)
    
    tb_text = res_tb["response"]
    if "```verilog" in tb_text:
        parts = tb_text.split("```verilog")
        if len(parts) > 1:
            tb_code = parts[1].split("```")[0].strip()
    elif "```" in tb_text:
        parts = tb_text.split("```")
        if len(parts) > 1:
            tb_code = parts[1].strip()
    else:
        tb_code = tb_text
        
    tb_path = project_dir / "designs" / "axi4_lite_sram_tb.v"
    tb_path.write_text(tb_code, encoding="utf-8")
    print(f"\n[+] Local LLM wrote testbench to {tb_path.name}")
    
if __name__ == "__main__":
    main()
