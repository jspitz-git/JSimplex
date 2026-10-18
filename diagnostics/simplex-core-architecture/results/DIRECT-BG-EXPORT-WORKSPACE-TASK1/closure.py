"""New Task1 offline closure. No Julia, old checker or numerical admission."""
from pathlib import Path
import json,hashlib,subprocess,time
R=Path.cwd();E=Path(__file__).resolve().parent;C=R/'diagnostics/direct-bg-export-workspace/reproduce'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def rd(n):return json.loads((E/n).read_text())
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
def path(n):return Path(n) if Path(n).is_absolute() else R/n
def save(n,x):
 with (E/n).open('x') as f:json.dump(x,f,indent=2);f.write('\n')
entry=rd('host.json');groups=set(entry['groups']);matches=[];unread=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  raw=(p/'stat').read_text();t=raw[raw.rfind(')')+2:].split();comm=(p/'comm').read_text().strip();args=(p/'cmdline').read_bytes().split(b'\0');argv0=args[0].decode(errors='replace')
  if int(t[2]) in groups or int(t[3]) in groups or any(Path(s).name.lower().startswith('julia') for s in [comm,argv0]):matches.append(dict(pid=int(p.name),pgid=int(t[2]),sid=int(t[3]),start_ticks=int(t[19]),comm=comm,command=b' '.join(args).decode(errors='replace')))
 except (FileNotFoundError,ProcessLookupError):pass
 except PermissionError:unread.append(int(p.name))
host=dict(time=time.time(),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),groups=sorted(groups),matches=matches,unreadable_stat_or_command=unread,head=git('rev-parse','HEAD'),master=git('rev-parse','master'),remote=git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'),scope='Offline candidate publication only; comm/argv0 and full246 groups/sessions survey, NOT universal executable identity or numerical admission.')
save('host-closure.json',host)
a=rd('source-check.json');v=rd('final-review.json');lineage=rd('lineage.json');names=rd('publication-names.json')['names']
def verify(d,mapping=None):return all(sha(path((mapping or {}).get(n,n)))==h for n,h in d.items())
excluded={str((E/n).relative_to(R)) for n in ['closure.json','publication.json']}
actual={str(p.relative_to(R)) for base in [C,E] for p in base.rglob('*') if p.is_file()}
checks=dict(author_pass=a['all_passed'] is True and all(a['checks'].values()),original_bindings=verify(a['readtime_sha256'],lineage['before_mapping']),lineage_bindings=verify(lineage['sha256']),review_accepted=v['accepted'] is True and not v['findings'] and all(v[k]==0 for k in ['critical','important','minor']),review_bindings=verify(v['readtime_sha256']) and verify(v['evidence_sha256']),all_candidate_bound=all(str(p) in v['readtime_sha256'] for p in C.iterdir() if p.is_file()),fresh_host=not matches and not unread and len(groups)==246 and host['boot_id']==entry['boot_id'],refs_unchanged=host['head']==entry['head'] and host['master']==entry['master'] and host['remote']==entry['remote'] and git('branch','--show-current')==entry['branch'],tracked_unchanged=not git('diff','--name-only') and not git('diff','--cached','--name-only'),task1_only=not (C/'factor.jl').exists() and not (C/'driver.jl').exists(),exact_names=len(names)==len(set(names)) and actual==set(names)-excluded,exact_scope=all(n.startswith(str(C.relative_to(R))+'/') or n.startswith(str(E.relative_to(R))+'/') for n in names))
out=dict(all_passed=all(checks.values()),checks=checks,scope=host['scope'],sha256={n:sha(R/n) for n in names if n not in excluded})
save('closure.json',out);print(json.dumps(dict(all_passed=out['all_passed'],checks=len(checks),bindings=len(out['sha256']),failed=[k for k,v in checks.items() if not v])))
if not out['all_passed']:raise SystemExit(1)
