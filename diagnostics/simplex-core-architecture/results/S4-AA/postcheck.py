"""One-use supplementary post-exit analysis; NOT a numerical launch input."""
from pathlib import Path
import sys,json,subprocess,shutil,tomllib
R=Path.cwd();A=R/'diagnostics/simplex-core-architecture/results/S4-AA';Z=A.parent/'S4-Z';sys.path.insert(0,str(Z))
from common import read,dump,sha,require,manifest_ok,absent,OUT,refs
p=read(OUT/'process.json');pins=read(Z/'launch-pins.json');audit=read(Z/'audit.json');inv=read(Z/'invocation.json')
checks={}
def check(n,c):checks[n]=c is True
check('all711launchpins_unchanged',manifest_ok(pins,read(Z/'required-paths.json')) and len(pins['inventory'])==711)
check('audit_accepted',audit['all_passed'] is True and all(v is True for v in audit['checks'].values()))
check('process_exit0_pins',p.get('reason')=='exit0' and p.get('returncode')==0 and p.get('pins_unchanged') is True)
check('launcher_exit0',inv.get('returncode')==0 and 'error' not in inv)
check('refs_unchanged',refs()==pins['refs'])
h=absent([p[k]['pgid'] for k in ('runner','child') if k in p]);check('full30groups_ANDsessions_noJulia',not h['matches'] and len(h['groups'])==30)
check('production_test_CI_unchanged',not subprocess.check_output(['git','diff','master','--','src','test','.github']))
# Raw is copied verbatim even on failed numerical/audit outcome.
portable=A/'qualification-1';portable.mkdir(exist_ok=False)
for q in OUT.iterdir():
 require(q.is_file() and not q.is_symlink(),'unexpected output object')
 with (portable/q.name).open('xb') as f:f.write(q.read_bytes())
check('portable_byteidentical',all(sha(q)==sha(OUT/q.name) for q in portable.iterdir()))
raw=tomllib.loads((OUT/'retention.toml').read_text()) if (OUT/'retention.toml').is_file() else {}
resources=[json.loads(s) for s in (OUT/'resources.jsonl').read_text().splitlines()]
summaries=[]
for c in raw.get('cases',[]):
 summaries.append({'kind':c.get('kind'),'true_predicates':sum(v is True for v in c.get('checks',{}).values()),'predicate_count':len(c.get('checks',{})),'snapshots':c.get('snapshots',[])})
files=[p for p in portable.iterdir()]+[Z/n for n in ('allowance.json','numerical-review.md','launch-pins.json','attempt-reserved.json','launcher.log','invocation.json','audit.json')]+[A/'postcheck.py']
dump(A/'postcheck.json',{'checks':checks,'all_passed':all(checks.values()),'sha256':{str(q):sha(q) for q in files},'host':h,'raw_errors':raw.get('errors'),'case_summary':summaries,'resources':{'samples':len(resources),'minimum_available_kib':min((s['available_kib'] for s in resources),default=None),'maximum_swap_kib':max((s['swap_used_kib'] for s in resources),default=None),'terminal_memory':p.get('terminal_memory'),'elapsed_including_launch':p.get('elapsed_including_launch')},'scope':'Supplementary post-exit script, not launch-pinned. Raw source-derived schedule is not instrumented complete backend/import work. Inclusive duration is not a benchmark.'})
print(json.dumps({'checks':checks,'all_passed':all(checks.values()),'summary':summaries,'resources':read(A/'postcheck.json')['resources']}))
