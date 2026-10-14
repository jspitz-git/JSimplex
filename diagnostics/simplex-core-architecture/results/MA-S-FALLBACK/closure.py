from pathlib import Path
import json,hashlib,subprocess,ast
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-S-FALLBACK';S=D.with_name('MA-S-2')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def rd(p):return json.loads(Path(p).read_text())
def bound(o):return all(sha(p)==s for p,s in o['sha256'].items())
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
h=rd(D/'host.json');a=rd(D/'analysis.json');rev=rd(D/'review.json');entry=rd(D/'entry.json');maps=rd(D/'continuation-map.json')['old_bindings']
def mapped(name):
 src=S/name;m={x['path']:x['preserved'] for x in maps if x['source']==str(src)}
 return all(sha(m.get(p,p))==s for p,s in rd(src)['sha256'].items())
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  f=(p/'stat').read_text().rsplit(')',1)[1].split()
  if int(f[2]) in h['groups'] or int(f[3]) in h['groups'] or (p/'exe').resolve().name.startswith('julia'):matches.append(dict(pid=int(p.name),pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace'),boot_id=boot))
 except (FileNotFoundError,ProcessLookupError):pass
checks={'review_accepted':rev['accepted'] is True and rev['findings']==[] and bound(rev),'entry13':entry['all_passed'] is True and len(entry['checks'])==13 and bound(entry),'analysis21':a['all_passed'] is True and len(a['checks'])==21 and bound(a),'readtime24':len(a['sha256'])==24 and all(sha(p)==v['sha256'] and str(Path(p).resolve())==v['resolved'] for p,v in a['readtime_pins'].items()),'paired336':len(a['paired_rows'])==336,'six_before_maps':len(maps)==6 and all(sha(x['preserved'])==x['sha256']==rd(x['source'])['sha256'][x['path']] for x in maps),'old_review_closure_publication':all(mapped(n) for n in ['result-review.json','execution-closure.json','execution-publication.json']),'old_cost_gate_false':rd(S/'aggregate.json')['accepted'] is False,'source514':len(h['master_identity'])==514 and all(sha(R/p)==s for p,s in h['master_identity'].items()),'protected6':len(h['protected'])==6 and all(sha(p)==s for p,s in h['protected'].items()),'host166_noJulia':len(h['groups'])==166 and not matches and boot==h['boot_id'],'refs':git('rev-parse','HEAD')==h['refs']['head'] and git('rev-parse','master')==h['refs']['master'],'tracked_scope':set(git('diff','--name-only','HEAD').splitlines())=={'diagnostics/simplex-core-architecture/STATUS.md','docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'},'no_stage':not git('diff','--cached','--name-only'),'diff_clean':subprocess.run(['git','diff','--check'],capture_output=True).returncode==0}
module=ast.parse((D/'publication.py').read_text());names=ast.literal_eval(next(n.value for n in module.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='NAMES' for t in n.targets)))
paths=[R/n for n in names if n not in {str((D/'closure.json').relative_to(R)),str((D/'publication.json').relative_to(R))}]
o=dict(all_passed=all(checks.values()),no_new_numerics=True,qualification_accepted=False,checks=checks,host=dict(boot_id=boot,groups=h['groups'],matches=matches),sha256={str(p):sha(p) for p in paths},scope='Bounded source/stored-evidence analysis closure. Attribution limitations preserved; no candidate or numerical admission.')
with (D/'closure.json').open('x') as f:json.dump(o,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=o['all_passed'],checks=checks,bindings=len(paths))))
if not o['all_passed']:raise SystemExit(1)
