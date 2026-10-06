import sys
from pathlib import Path
import subprocess

project_dir = Path(r"c:\Users\ssuja\OneDrive\Desktop\Learn_Antigravity_Advance\rtl-2-gds-automation-local-llm")
sys.path.append(str(project_dir))

from llm_agents import RTLFixAgent

def main():
    design_dir = project_dir / "designs"
    tb_path = design_dir / "axi4_lite_sram_tb.v"
    tb_code = tb_path.read_text(encoding="utf-8")
    
    print("=== Invoking Local LLM: TB Fix Agent ===")
    errors = [
        "axi4_lite_sram_tb.v:89: error: s_axi_awready is not a valid l-value in axi4_sram_controller_tb. (You cannot assign to an output of the instantiated module! Wait for the module to assert it.)",
        "axi4_lite_sram_tb.v:91: error: s_axi_wready is not a valid l-value in axi4_sram_controller_tb.",
        "axi4_lite_sram_tb.v:103: error: s_axi_arready is not a valid l-value in axi4_sram_controller_tb."
    ]
    
    fix_ai = RTLFixAgent()
    
    print("Sending broken testbench to Ollama for fixing...")
    result = fix_ai.fix(tb_code, errors, [], "axi4_lite_sram_tb")
    
    fixed_code = result["fixed_verilog"]
    if fixed_code:
        tb_path.write_text(fixed_code, encoding="utf-8")
        print("\n[+] Local LLM fixed the Testbench and wrote it back.")
    else:
        print("[-] LLM failed to return fixed code.")
        
if __name__ == "__main__":
    main()
