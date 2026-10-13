"""Exclusive synthetic absent/malformed-input checks. No Julia."""
from common import *
import subprocess,sys
root=H/'synthetic-failures';root.mkdir()
checks={}
for name,files in [('missing',{}),('malformed-process',{'process.json':'{broken'}),('malformed-raw',{'process.json':'{}','pins.json':'{}','resources.jsonl':'{}\n','report.toml':'[broken'})]:
 out=root/name;out.mkdir()
 for p,t in files.items():(out/p).write_text(t)
 dest=root/(name+'.json');p=subprocess.run([sys.executable,str(H/'audit.py'),str(out),str(dest)],capture_output=True,text=True)
 (root/(name+'.log')).write_text(p.stdout+p.stderr)
 r=read(dest);checks[name]=p.returncode==1 and r['all_passed'] is False and bool(r.get('error'))
dump(H/'failure-cases.json',dict(checks=checks,all_passed=all(checks.values())));assert all(checks.values())
