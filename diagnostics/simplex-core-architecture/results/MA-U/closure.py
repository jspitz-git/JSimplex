from pathlib import Path
import json,hashlib,subprocess,ast
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-U';T=D.with_name('MA-T')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rd(p):return json.loads(Path(p).read_text())
def bound(o):return all(sha(p)==v for p,v in o['sha256'].items())
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
h=rd(D/'host.json');e=rd(D/'entry.json');s=rd(D/'source-green.json');r=rd(D/'review.json');maps=rd(D/'continuation-map.json')['old_bindings'];a=rd(D/'author-fix.json')
def oldbound(n):
 m={x['path']:x['preserved'] for x in maps if x['source']==str(T/n)}
 return all(sha(m.get(p,p))==v for p,v in rd(T/n)['sha256'].items())
def redbound():
 m={x['path']:x['preserved'] for x in a['old_bindings']}
 return all(sha(m.get(p,p))==v for p,v in rd(D/'source-red.json')['sha256'].items())
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  f=(p/'stat').read_text().rsplit(')',1)[1].split()
  if int(f[2]) in h['groups'] or int(f[3]) in h['groups'] or (p/'exe').resolve().name.startswith('julia'):
   matches.append(dict(pid=int(p.name),pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace'),boot_id=boot))
 except (FileNotFoundError,ProcessLookupError):pass
w=rd(D/'whitespace.json')
checks=dict(verbatim_whitespace=w['all_passed'] is True and bound(w),review_accepted=r['accepted'] is True and r['findings']==[] and bound(r),entry15=e['all_passed'] is True and len(e['checks'])==15 and bound(e),source19=s['all_passed'] is True and len(s['checks'])==19 and len(s['sha256'])==34 and bound(s),author_fix4=a['all_passed'] is True and len(a['checks'])==4 and bound(a),source_red_preserved=redbound(),eight_maps=len(maps)==8 and all(sha(x['preserved'])==x['sha256']==rd(x['source'])['sha256'][x['path']] for x in maps),prior_bindings=all(oldbound(n) for n in ['review-final.json','review-fix.json','closure.json','publication.json']),source514=len(h['master_identity'])==514 and all(sha(R/p)==v for p,v in h['master_identity'].items()),protected6=len(h['protected'])==6 and all(sha(p)==v for p,v in h['protected'].items()),host166_noJulia=len(h['groups'])==166 and not matches and boot==h['boot_id'],refs=git('rev-parse','HEAD')==h['refs']['head'] and git('rev-parse','master')==h['refs']['master'],tracked_scope=set(git('diff','--name-only','HEAD').splitlines())=={'diagnostics/simplex-core-architecture/STATUS.md','docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'},no_stage=not git('diff','--cached','--name-only'),diff_clean=subprocess.run(['git','diff','--check'],capture_output=True).returncode==0,old_rejection=rd(D.with_name('MA-S-2')/'aggregate.json')['accepted'] is False)
module=ast.parse((D/'publication.py').read_text());names=ast.literal_eval(next(n.value for n in module.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='NAMES' for t in n.targets)))
paths=[R/n for n in names if n not in {str((D/'closure.json').relative_to(R)),str((D/'publication.json').relative_to(R))}]
o=dict(all_passed=all(checks.values()),checks=checks,no_new_numerics=True,qualification_accepted=False,host=dict(boot_id=boot,groups=h['groups'],matches=matches),sha256={str(p):sha(p) for p in paths})
with (D/'closure.json').open('x') as f:json.dump(o,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=o['all_passed'],checks=checks,bindings=len(paths))))
if not o['all_passed']:raise SystemExit(1)
