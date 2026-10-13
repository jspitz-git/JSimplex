"""Offline admission review fixes, prior sources preserved byte-exact."""
from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent
for n in ['common.py','audit.py','guard.py']:
 p=H/n
 with (H/(n+'.before-identity-fix')).open('xb') as f:f.write(p.read_bytes())
p=H/'guard.py';s=p.read_text();old="record['ended'] = time.time()"
new="""record['terminal_memory'] = memory()
            if record['reason'] == 'exit0' and pressure(record['terminal_memory']):
                record['reason'] = 'terminal_memory_guard'
            record['ended'] = time.time()"""
assert s.count(old)==1;s=s.replace(old,new);p.write_text(s)
p=H/'common.py';s=p.read_text();s+='''
RUNTIME='/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/bin/julia'
def identities_ok(p,stage):
 try:
  runner=p['runner'];child=p['child'];boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
  for obj in (runner,child):
   if not all(type(obj[k]) is int and obj[k]>0 for k in ('pid','pgid','start_ticks')):return False
   if obj['boot_id']!=boot or type(obj['command']) is not str:return False
  commands=[' '.join(command(stage))+' ',' '.join([RUNTIME,'--startup-file=no',*command(stage)[2:]])+' ']
  return runner['command']==' '.join(guard_command(stage))+' ' and child['command'] in commands and child['pid']==child['pgid'] and child['pid']!=runner['pid'] and child['start_ticks']>=runner['start_ticks']
 except (KeyError,TypeError):return False

def terminal_memory_ok(p):
 try:
  m=p['terminal_memory'];return set(m)=={'available_kib','swap_used_kib'} and type(m['available_kib']) is int and m['available_kib']>=6*1024**2 and type(m['swap_used_kib']) is int and 0<=m['swap_used_kib']<=1024**2
 except (KeyError,TypeError):return False
'''
s=s.replace("'session-fix.json'", "'session-fix.json','admission_fix.py','fix-tests.py','fix-tests.json'");p.write_text(s)
p=H/'audit.py';s=p.read_text();s=s.replace("c.update(elapsed_guard=", "c.update(process_identity=identities_ok(process,stage),terminal_memory=terminal_memory_ok(process),elapsed_guard=");p.write_text(s)
with (H/'identity-fix.json').open('x') as f:json.dump({'source_sha256':{str(H/n):hashlib.sha256((H/n).read_bytes()).hexdigest() for n in ['common.py','audit.py','guard.py']},'guard_change':'One terminal memory snapshot and failclosed exit gate, no numerical call.'},f,indent=2)
