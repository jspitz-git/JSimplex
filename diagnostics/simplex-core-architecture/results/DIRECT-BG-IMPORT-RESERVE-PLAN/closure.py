"""New planning-only closure, executed once after reviewer files are frozen."""
from pathlib import Path
import json,hashlib,subprocess,time
R=Path.cwd();E=Path(__file__).resolve().parent
SPEC='docs/superpowers/specs/2026-10-18-direct-bg-import-reserve.md';PLAN='docs/superpowers/plans/2026-10-18-direct-bg-import-reserve.md'
def rd(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
def path(n):return Path(n) if Path(n).is_absolute() else R/n
def verify(mapping):return all(sha(path(n))==h for n,h in mapping.items())
def save(p,j):
 with p.open('x') as f:json.dump(j,f,indent=2);f.write('\n')
a=rd(E/'author-check.json');v=rd(E/'review.json');entry=rd(E/'host.json');groups=entry['groups'];matches=[];unreadable=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  t=(p/'stat').read_text().rsplit(')',1)[1].split();comm=(p/'comm').read_text().strip();exe=''
  try:exe=str((p/'exe').resolve(strict=True))
  except PermissionError:unreadable.append(int(p.name))
  except FileNotFoundError:pass
  if int(t[2]) in groups or int(t[3]) in groups or comm.lower().startswith('julia') or Path(exe).name.lower().startswith('julia'):
   matches.append(dict(pid=int(p.name),pgid=int(t[2]),sid=int(t[3]),start_ticks=int(t[19]),comm=comm,exe=exe,command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except (FileNotFoundError,ProcessLookupError):pass
host=dict(time=time.time(),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),groups=groups,matches=matches,unreadable_exe_pids=unreadable,head=git('rev-parse','HEAD'),master=git('rev-parse','master'),remote_refs=git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'))
save(E/'host-closure.json',host)
names=rd(E/'publication-names.json')['names'];exclude={str((E/n).relative_to(R)) for n in ['closure.json','publication.json']};actual={str(p.relative_to(R)) for p in E.rglob('*') if p.is_file()}|{SPEC,PLAN}
checks=dict(author_pass=a['all_passed'] is True and len(a['checks'])==190,author_bindings=verify(a['readtime_sha256']),review_accepted=v['scope']=='direct BG import reserve plan' and v['accepted'] is True and not v['findings'] and all(v[k]==0 for k in ['critical','important','minor']),review_bindings=verify(v['readtime_sha256']) and verify(v['evidence_sha256']),current_documents_reviewed=all(str(R/n) in v['readtime_sha256'] or n in v['readtime_sha256'] for n in [SPEC,PLAN]),fresh_host=len(groups)==246 and not matches and host['boot_id']==entry['boot_id'],refs_unchanged=host['head']==entry['head'] and host['master']==entry['master'] and host['remote_refs']==entry['remote_refs'] and git('branch','--show-current')=='codex/simplex-core-architecture',tracked_unchanged=not git('diff','--name-only') and not git('diff','--cached','--name-only'),no_candidate=not (R/'diagnostics/direct-bg-import-reserve').exists(),exact_complete_names=len(names)==len(set(names)) and actual==set(names)-exclude,exact_scope=all(n in [SPEC,PLAN] or n.startswith(str(E.relative_to(R))+'/') for n in names))
record=dict(scope='Import reserve planning closure only; no implementation or Julia',all_passed=all(checks.values()),checks=checks,sha256={n:sha(R/n) for n in names if n not in exclude})
save(E/'closure.json',record);print(json.dumps(dict(all_passed=record['all_passed'],checks=len(checks),bindings=len(record['sha256']),failed=[k for k,x in checks.items() if not x])))
if not record['all_passed']:raise SystemExit(1)
