import sys
from pathlib import Path

# Add project root to path so we can import model_router
project_dir = Path(r"c:\Users\ssuja\OneDrive\Desktop\Learn_Antigravity_Advance\rtl-2-gds-automation-local-llm")
sys.path.append(str(project_dir))

from model_router import ModelRouter

router = ModelRouter()

prompt = """
Write a highly complex and powerful Verilog RTL module. 
It should be approximately 200 lines of code. 
Design an AXI4-Lite Slave SRAM Controller.
It should properly handle all 5 AXI4-Lite channels (AW, W, B, AR, R).
Include a parameter for DATA_WIDTH and ADDR_WIDTH.
Implement strict state machines for the Write Transaction and Read Transaction to comply with the AXI4-Lite protocol handshaking.
Make sure the Verilog is synthesizable, clean, and well-commented.
Return ONLY the Verilog code inside ```verilog ... ```, no other text.
"""

print(f"Requesting local LLM to generate complex RTL...\n")

res = router.generate_rtl(prompt, stream=True)

print("\n\n--- STREAMING OUTPUT ---\n")
response_text = ""
for chunk in res:
    print(chunk, end="", flush=True)
    response_text += chunk

# Save to a file for review
out_path = project_dir / "designs" / "axi4_lite_sram.v"

# Extract code block if present
if "```verilog" in response_text:
    parts = response_text.split("```verilog")
    if len(parts) > 1:
        code = parts[1].split("```")[0].strip()
        out_path.write_text(code, encoding="utf-8")
else:
    out_path.write_text(response_text, encoding="utf-8")

print(f"\n\nDone! Saved to {out_path}")
