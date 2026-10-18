"""New Task2 offline closure. Never executes Julia or an earlier checker."""
from pathlib import Path
import hashlib,json,subprocess,time
R=Path.cwd();E=Path(__file__).resolve().parent;C=R/'diagnostics/direct-bg-export-workspace/reproduce';E1=E.with_name('DIRECT-BG-EXPORT-WORKSPACE-TASK1')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def rd(n):return json.loads((E/n).read_text())
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
def save(n,x):
 with (E/n).open('x') as f:json.dump(x,f,indent=2);f.write('\n')
def verify(d,mapping=None):return all(sha((mapping or {}).get(p,p))==h for p,h in d.items())
entry=rd('host.json');groups=set(entry['groups']);matches=[];unread=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  raw=(p/'stat').read_text();v=raw[raw.rfind(')')+2:].split();comm=(p/'comm').read_text().strip();args=(p/'cmdline').read_bytes().split(b'\0');argv0=args[0].decode(errors='replace')
  if int(v[2]) in groups or int(v[3]) in groups or any('julia' in Path(s).name.lower() for s in (comm,argv0)):matches.append(dict(pid=int(p.name),pgid=int(v[2]),sid=int(v[3]),start_ticks=int(v[19]),comm=comm,command=b' '.join(args).decode(errors='replace')))
 except (FileNotFoundError,ProcessLookupError):pass
 except PermissionError:unread.append(int(p.name))
host=dict(time=time.time(),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),groups=sorted(groups),matches=matches,unreadable_stat_command=unread,head=git('rev-parse','HEAD'),master=git('rev-parse','master'),branch=git('branch','--show-current'),remote=git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'),scope='Fresh offline survey stat/comm/argv0 and full246groups ANDsessions; not universal executable visibility or numerical admission')
save('host-closure.json',host)
a=rd('source-check.json');v=rd('final-review.json');initial=rd('review.json');fix=rd('review-fix.json');supp=rd('amendment-check.json');lin=rd('lineage.json');names=rd('publication-names.json')['names']
parent=json.loads((E1/'publication.json').read_text());parent_paths=parent['names']
parent_blobs={p:git('hash-object',str(R/p)) for p in parent_paths}
expected_parent={p:git('rev-parse',entry['head']+':'+p) for p in parent_paths}
future={str((E/n).relative_to(R)) for n in ('closure.json','publication.json')}
newc={str((C/n).relative_to(R)) for n in ('factor.jl','lifecycle-tests.jl','composition-ledger.md','overlay-manifest.json')}
actual=newc|{str(p.relative_to(R)) for p in E.rglob('*') if p.is_file()}
checks=dict(
 initial_author_record_pass=a['all_passed'] and all(a['checks'].values()),
 initial_author_and_reviewer_bytes_preserved=verify(a['readtime_sha256'],lin['before_mapping']) and verify(initial['readtime_sha256'],lin['before_mapping']),
 amendment_actual_hash_proof=supp['all_passed'] and all(supp['checks'].values()) and verify(supp['readtime_sha256']),
 amendment_source_checks=fix['all_passed'] and all(fix['red'].values()) and all(value for key,value in fix['green'].items() if key!='all_original_bytes_preserved') and verify(fix['sha256']) and verify(lin['sha256']),
 final_review_accepted=v['accepted'] is True and not v['findings'] and all(v[k]==0 for k in ('critical','important','minor')),
 final_review_bindings=verify(v['readtime_sha256']) and verify(v.get('evidence_sha256',{})),
 all_four_candidate_bound=all(str(C/n) in v['readtime_sha256'] for n in ('factor.jl','lifecycle-tests.jl','composition-ledger.md','overlay-manifest.json')),
 complete_Task1_publication_frozen=parent_blobs==expected_parent and all(parent_blobs[p]==h for p,h in parent['staged_blobs'].items()),
 fresh_host=len(groups)==246 and not matches and not unread and host['boot_id']==entry['boot_id'],
 refs_unchanged=all(host[k]==entry[k] for k in ('head','master','branch','remote')),
 no_tracked_or_staged_edits=not git('diff','--name-only','HEAD') and not git('diff','--cached','--name-only'),
 user_untracked_preserved=all(line in git('status','--porcelain').splitlines() for line in entry['status'].splitlines()),
 exact_complete_names=len(names)==len(set(names)) and actual==set(names)-future,
 narrow_scope=all(n in newc or n.startswith(str(E.relative_to(R))+'/') for n in names) and not (C/'driver.jl').exists())
out=dict(all_passed=all(checks.values()),checks=checks,scope='Task2 offline preparation only; original vacuous preservation gate excluded, actual supplement required',sha256={n:sha(R/n) for n in names if n not in future})
save('closure.json',out);print(json.dumps(dict(all_passed=out['all_passed'],checks=len(checks),bindings=len(out['sha256']),failed=[k for k,v in checks.items() if not v])))
if not out['all_passed']:raise SystemExit(1)
