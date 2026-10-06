"""
fix_encoding.py - Fix all non-ASCII characters in agent files for Windows cp1252 compatibility
"""
from pathlib import Path

replacements = {
    '\u2500': '-',   # box drawing dash
    '\u2501': '-',
    '\u2502': '|',
    '\u2014': '-',   # em dash
    '\u2013': '-',   # en dash
    '\u2705': '[OK]',
    '\u274c': '[FAIL]',
    '\u26a0\ufe0f': '[WRN]',
    '\u26a0': '[WRN]',
    '\u2714': '[OK]',
    '\u2718': '[X]',
    '\U0001f50d': '[>>]',
    '\u27a1': '->',
    '\u2192': '->',
    '\U0001f916': '[ROBOT]',
    '\U0001f3c6': '[TROPHY]',
    '\U0001f527': '[WRENCH]',
    '\u2019': "'",
    '\u201c': '"',
    '\u201d': '"',
}

files_to_fix = list(Path('agents').glob('*.py')) + [Path('run_local.py')]

for filepath in files_to_fix:
    text = filepath.read_text(encoding='utf-8')
    original = text
    for old, new in replacements.items():
        text = text.replace(old, new)
    # Final sweep: replace any remaining non-cp1252 chars with '?'
    encoded = text.encode('cp1252', errors='replace')
    text_clean = encoded.decode('cp1252')
    if text_clean != original:
        filepath.write_text(text_clean, encoding='utf-8')
        print("Fixed:", filepath.name)
    else:
        print("Clean:", filepath.name)

print("Done.")
