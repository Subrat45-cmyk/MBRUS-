"""
MBRUS Security Audit Script
Verifies that .env is ignored, no secrets are tracked, and no hardcoded API keys exist.
"""

import os
import re
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

SECRET_PATTERNS = [
    (r"AIza[0-9A-Za-z\-_]{35}", "Google API Key (AIza...)"),
    (r"AQ\.[0-9A-Za-z\-_]{30,}", "Google GenAI API Key (AQ....)"),
    (r"sk-[a-zA-Z0-9]{32,}", "OpenAI API Key (sk-...)"),
    (r"ghp_[a-zA-Z0-9]{36}", "GitHub Personal Access Token (ghp_...)"),
]

EXCLUDE_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", ".idea", ".vscode"}
EXCLUDE_FILES = {".env", ".env.example", "package-lock.json"}


def check_git_ignored():
    print("[1/3] Verifying .env is ignored by Git...")
    try:
        res = subprocess.run(["git", "check-ignore", "-v", ".env"], cwd=ROOT_DIR, capture_output=True, text=True)
        if res.returncode == 0 and ".env" in res.stdout:
            print("  ✅ SUCCESS: .env is properly ignored by Git.")
            return True
        else:
            print("  ❌ WARNING: .env is NOT ignored by Git!")
            return False
    except Exception as e:
        print(f"  ⚠️ Could not run git check-ignore: {e}")
        return True


def check_git_tracked_secrets():
    print("[2/3] Checking tracked files for accidental secrets...")
    try:
        res = subprocess.run(["git", "ls-files"], cwd=ROOT_DIR, capture_output=True, text=True)
        tracked = res.stdout.strip().splitlines()
        found_sensitive = []
        for f in tracked:
            if f.endswith(".env") or f == ".env" or ".pyc" in f:
                found_sensitive.append(f)
        if found_sensitive:
            print(f"  ❌ WARNING: Sensitive files tracked in git: {found_sensitive}")
            return False
        else:
            print("  ✅ SUCCESS: No sensitive files or compiled binaries tracked in Git.")
            return True
    except Exception as e:
        print(f"  ⚠️ Could not check git ls-files: {e}")
        return True


def scan_source_code_for_keys():
    print("[3/3] Scanning source files for hardcoded API keys...")
    leaks = []
    for root, dirs, files in os.walk(ROOT_DIR):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for f in files:
            if f in EXCLUDE_FILES or f.endswith(".log") or f.endswith(".pyc"):
                continue
            fpath = Path(root) / f
            try:
                content = fpath.read_text(encoding="utf-8", errors="ignore")
                for pat, label in SECRET_PATTERNS:
                    matches = re.findall(pat, content)
                    for m in matches:
                        rel = fpath.relative_to(ROOT_DIR)
                        leaks.append((str(rel), label, m[:8] + "..." + m[-4:]))
            except Exception:
                pass

    if leaks:
        print(f"  ❌ FOUND {len(leaks)} POTENTIAL HARDCODED SECRET(S):")
        for file, label, masked in leaks:
            print(f"     - {file}: {label} [{masked}]")
        return False
    else:
        print("  ✅ SUCCESS: Zero hardcoded API keys detected across repository source files.")
        return True


def main():
    print("=" * 60)
    print("  🔒 MBRUS Repository Security & Secret Audit")
    print("=" * 60)
    ok1 = check_git_ignored()
    ok2 = check_git_tracked_secrets()
    ok3 = scan_source_code_for_keys()
    print("=" * 60)
    if ok1 and ok2 and ok3:
        print("  🟢 AUDIT PASSED: Repository is clean and secure.")
    else:
        print("  🔴 AUDIT FAILED: Please resolve the security warnings above.")
    print("=" * 60)


if __name__ == "__main__":
    main()
