import os
import sys
import subprocess
import re
import json

def run(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip(), result.returncode

def audit():
    print("=== [ARC Reactor Governance Audit] ===")
    issues = []

    # 1. Check Commit Signature
    last_commit_msg, _ = run("git log -1 --pretty=%B")
    if not re.search(r'\(by \w+\)', last_commit_msg):
        issues.append(f"Commit message missing signature '(by AgentName)'. Last msg: '{last_commit_msg}'")
    else:
        print("✅ Commit signature found.")

    # 2. Check RT Association for Modified Files
    # Check staged changes (between HEAD and Index)
    diff_files, _ = run("git diff --cached --name-only")
    files = diff_files.splitlines()
    
    code_files = [f for f in files if f.endswith(('.py', '.sh', '.yaml', '.json')) and not f.startswith('RT/')]
    if code_files:
        # Check if RT/ was also touched in this commit or recently
        rt_files = [f for f in files if f.startswith('RT/RT-')]
        if not rt_files:
            # Check recent RT hits (optional, simplified for now)
            issues.append(f"Code changes detected in {code_files} but no matching RT spec was found in this commit.")
        else:
            print(f"✅ RT association verified for {len(code_files)} files.")

    # 3. Check Wiki Integrity (No manual edits in arc-reactor-doc/wiki/ without record)
    # We check if wiki files were modified but archive-manager.py log wasn't updated
    wiki_files = [f for f in files if 'arc-reactor-doc/wiki/' in f and not f.endswith('log.md')]
    if wiki_files:
        log_updated = any('log.md' in f for f in files)
        if not log_updated:
            issues.append("Wiki files modified manually without updating the operational log.md. Use archive-manager.py!")
        else:
            print("✅ Wiki integrity check passed.")

    # 4. Final Verdict
    if issues:
        print("\n❌ Governance Violations Found:")
        for i in issues:
            print(f"  - {i}")
        return 1
    
    print("\n🌟 All systems compliant. Governance protocol followed.")
    return 0

if __name__ == "__main__":
    sys.exit(audit())
