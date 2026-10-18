"""Canonical closure after preserved rejected initial review. Original closure.py is UNEXECUTED draft. No Julia or old check execution."""
from pathlib import Path
import json,hashlib,subprocess,time
R=Path.cwd();E=Path(__file__).resolve().parent
SPEC='docs/superpowers/specs/2026-10-18-direct-bg-export-workspace.md';PLAN='docs/superpowers/plans/2026-10-18-direct-bg-export-workspace.md'
def rd(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
def path(n):return Path(n) if Path(n).is_absolute() else R/n
def verify(d):return all(sha(path(n))==h for n,h in d.items())
def save(p,d):
 with p.open('x') as f:json.dump(d,f,indent=2);f.write('\n')
entry=rd(E/'host.json');groups=set(entry['groups']);matches=[];unread=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  raw=(p/'stat').read_text();t=raw[raw.rfind(')')+2:].split();comm=(p/'comm').read_text().strip();exe=''
  try:exe=str((p/'exe').resolve(strict=True))
  except PermissionError:unread.append(int(p.name))
  except FileNotFoundError:pass
  if int(t[2]) in groups or int(t[3]) in groups or comm.lower().startswith('julia') or Path(exe).name.lower().startswith('julia'):
   matches.append(dict(pid=int(p.name),pgid=int(t[2]),sid=int(t[3]),start_ticks=int(t[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace'),comm=comm,exe=exe))
 except (FileNotFoundError,ProcessLookupError):pass
host=dict(time=time.time(),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),groups=sorted(groups),matches=matches,unreadable_exe_pids=unread,head=git('rev-parse','HEAD'),master=git('rev-parse','master'),remote=git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'))
save(E/'host-closure.json',host)
a=rd(E/'author-check.json');m=rd(E/'amendment-check.json');initial=rd(E/'review.json');v=rd(E/'amendment-review.json');names=rd(E/'publication-names.json')['names']
excluded={str((E/n).relative_to(R)) for n in ['closure.json','publication.json']}
actual={str(p.relative_to(R)) for p in E.rglob('*') if p.is_file()}|{SPEC,PLAN}
before={str(R/SPEC):E/'spec.before-review.md',str(R/PLAN):E/'plan.before-review.md'}
def original_verify(d):return all(sha(before.get(n,path(n)))==h for n,h in d.items())
checks=dict(amendment_pass=m['all_passed'] is True and all(m['checks'].values()) and verify(m['readtime_sha256']),initial_rejection_preserved=initial['accepted'] is False and len(initial['findings'])==2 and original_verify(initial['readtime_sha256']) and original_verify(initial['evidence_sha256']),author_pass=a['all_passed'] is True and all(a['checks'].values()),author_bindings=original_verify(a['readtime_sha256']),review_accepted=v['accepted'] is True and not v['findings'] and all(v[k]==0 for k in ['critical','important','minor']),review_bindings=verify(v['readtime_sha256']) and verify(v['evidence_sha256']),documents_bound=all(n in v['readtime_sha256'] or str(R/n) in v['readtime_sha256'] for n in [SPEC,PLAN]),fresh_host=not matches and not unread and len(groups)==246 and host['boot_id']==entry['boot_id'],refs_unchanged=host['head']==entry['head'] and host['master']==entry['master'] and host['remote']==entry['remote'] and git('branch','--show-current')=='codex/simplex-core-architecture',tracked_unchanged=not git('diff','--name-only') and not git('diff','--cached','--name-only'),no_candidate=not (R/'diagnostics/direct-bg-export-workspace').exists(),exact_names=len(names)==len(set(names)) and actual==set(names)-excluded,exact_scope=all(n in [SPEC,PLAN] or n.startswith(str(E.relative_to(R))+'/') for n in names))
record=dict(scope='Planning-only closure; no implementation or numerical admission',all_passed=all(checks.values()),checks=checks,sha256={n:sha(R/n) for n in names if n not in excluded})
save(E/'closure.json',record);print(json.dumps(dict(all_passed=record['all_passed'],checks=len(checks),bindings=len(record['sha256']),failed=[k for k,v in checks.items() if not v])))
if not record['all_passed']:raise SystemExit(1)
