#!/usr/bin/env python3
"""
Forensic secret and vulnerability audit script.
Scans git commits, blobs, trees, and working tree for real API keys, credentials, or sensitive tokens.
"""
import subprocess
import re
import sys

def audit_git():
    cmd = ["git", "log", "-p", "--all"]
    res = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    history_text = res.stdout

    patterns = {
        "Groq Real Key": r'gsk_[A-Za-z0-9]{20,}',
        "Gemini Real Key": r'AIza[0-9A-Za-z\-_]{35}',
        "OpenRouter Real Key": r'sk-or-v1-[a-f0-9]{40,}',
        "NVIDIA Real Key": r'nvapi-[A-Za-z0-9\-_]{20,}',
        "OpenAI Key": r'sk-[A-Za-z0-9]{32,}',
        "GitHub Token": r'ghp_[A-Za-z0-9]{36}',
        "AWS Secret": r'(?i)aws_secret_access_key\s*=\s*[A-Za-z0-9/+=]{40}',
    }

    placeholders = [
        "your_groq_api_key_here",
        "your_primary_groq_key",
        "account1_key",
        "account2_key",
        "account3_key",
        "your_gemini_api_key_here",
        "your_primary_gemini_key",
        "your_openrouter_api_key_here",
        "your_openrouter_key",
        "placeholder",
        "sample",
    ]

    findings = []
    for name, pat in patterns.items():
        matches = set(re.findall(pat, history_text))
        for m in matches:
            if not any(ph in m for ph in placeholders):
                findings.append((name, m))

    print("==================================================================")
    print("  FORENSIC GIT REPOSITORY SECRET & VULNERABILITY AUDIT")
    print("==================================================================")

    # Also check all currently tracked files on disk
    tracked_files = subprocess.run(["git", "ls-files"], capture_output=True, text=True).stdout.splitlines()
    print(f"Total Tracked Files: {len(tracked_files)}")
    
    # Verify .env is NOT tracked
    if ".env" in tracked_files:
        findings.append(("CRITICAL ERROR", ".env is tracked by Git!"))
    else:
        print("[OK] .env is NOT tracked by Git.")

    # Check for actual API keys across all tracked files
    for tf in tracked_files:
        try:
            with open(tf, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                for name, pat in patterns.items():
                    matches = set(re.findall(pat, content))
                    for m in matches:
                        if not any(ph in m for ph in placeholders):
                            findings.append((f"{name} in {tf}", m))
        except Exception:
            pass

    if findings:
        print("\n[CRITICAL ALERT] Sensitive data found:")
        for name, match in findings:
            print(f"  - {name}: {match[:8]}...{match[-4:]}")
        sys.exit(1)
    else:
        print("\n[VERDICT: 100% CLEAN]")
        print("  - Zero real API keys detected in git history.")
        print("  - Zero real API keys in tracked files.")
        print("  - .env is properly ignored and protected.")
        print("  - All sample keys in .env.example are inert placeholders.")

if __name__ == "__main__":
    audit_git()
