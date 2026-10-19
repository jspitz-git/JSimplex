"""Supplemental saved-output summary only; not part of launch inventory, never a rerun of the auditor."""
from pathlib import Path
import sys,json,tomllib
D=Path(__file__).resolve().parent;H=D.with_name('DIRECT-BG-BLOCKED-UPDATE-HARNESS');sys.path.insert(0,str(H));import control as c
run=H/'runs/red300';out=run/'output';outer=H/'outers/red300'
c.require((outer/'outer-outcome.json').is_file(),'Wait for outer completion')
def optional(p,decoder=json.loads):return decoder(p.read_text()) if p.is_file() else None
def total(t):
 a=[t[k] for k in ['pass','fail','error','broken']]
 for ch in t['children']:a=[x+y for x,y in zip(a,total(ch))]
 return a
units=[]
for p in sorted(out.glob('unit-*.toml'),key=lambda p:int(p.stem.split('-')[1])) if out.exists() else []:
 u=tomllib.loads(p.read_text());units.append(dict(index=u['index'],name=u['name'],complete=u['complete'],fatal=u['fatal'],totals=total(u['tests']),records=u['records'],observations=u['observations']))
resources=[json.loads(s) for s in (out/'resources.jsonl').read_text().splitlines()] if (out/'resources.jsonl').exists() else []
p=optional(out/'process.json');inv=optional(run/'invocation.json');audit=optional(run/'audit.json');raw=optional(out/'raw.toml',tomllib.loads)
summary=dict(scope=__doc__,qualification_pass=audit is not None and audit.get('all_passed') is True,expected_RED_failures=6,observed_failures=sum(u['totals'][1] for u in units),observed_errors=sum(u['totals'][2] for u in units),units_saved=len(units),units=units,raw=raw,process=p,invocation=inv,outer=optional(outer/'outer-outcome.json'),audit=audit,resources=dict(samples=len(resources),min_available_kib=min((x['available_kib'] for x in resources),default=None),max_swap_used_kib=max((x['swap_used_kib'] for x in resources),default=None)),timing_scope='Inclusive guarded-process elapsed is not a performance benchmark')
files=[p for root in [run,outer] for p in root.rglob('*') if p.is_file()];summary['sha256']={str(p):c.sha(p) for p in files}
c.save(D/'summary.json',summary)
print(json.dumps({k:summary[k] for k in ['qualification_pass','observed_failures','observed_errors','units_saved','resources']}))
if p:print('Process',p.get('returncode'),p.get('reason'))
