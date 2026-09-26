"""Scan staged text without printing possible secret values."""
import re, subprocess, sys
patterns = [r'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----', r'gh[pousr]_[A-Za-z0-9]{30,}', r'github_pat_[A-Za-z0-9_]{30,}', r'AKIA[A-Z0-9]{16}', r'(?:sk_live_|sk_test_)[A-Za-z0-9]{16,}', r'(?i)(?:password|api_secret|vercel_token|github_token)\s*[:=]\s*[\"\x27][^\"\x27\s]{12,}']
files=subprocess.check_output(['git','diff','--cached','--name-only','--diff-filter=ACM','-z']).decode().split('\0')
issues=[]
for name in filter(None,files):
    raw=subprocess.check_output(['git','show',':'+name])
    if b'\0' in raw: continue
    text=raw.decode(errors='replace')
    if any(re.search(p,text) for p in patterns): issues.append(name)
print('Secret scan: '+('FAIL in '+', '.join(issues) if issues else 'PASS (no matching secrets)'))
sys.exit(bool(issues))
