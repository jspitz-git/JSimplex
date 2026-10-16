from pathlib import Path
import sys,json,tomllib,math
E=Path(__file__).resolve().parent;D=E.parent/'DIRECT-BG-DYNAMIC-COST-PREPARATION';sys.path.insert(0,str(D))
import control_reviewed as c
from analysis_reviewed import matrix,window_ok,summarize
from evidence_reviewed import preflight_ok,probe_ok
r=D/'runs/cost1-300';o=r/'output';checks={}
def ck(n,v):
 checks[n]=bool(v)
 if not v:raise RuntimeError(n)
def tom(n):return tomllib.loads((o/n).read_text())
s=c.rd(r/'sealed.json');pins=c.rd(r/'launch-pins.json');cfg=c.config('cost1-300');a=c.rd(r/'audit.json')
ck('original_failure_preserved',a['all_passed'] is False and a['pure_timeout'] is False and a['error']=="RuntimeError('Raw schema/count/path')")
ck('original_audit_bindings',c.bindings(a))
c.validate_environment();c.validate_sources();c.preparation();c.predecessor('cost1-300');checks['sources_environment_preparation_green']=True
ck('pins',c.guard.pins_match(s) and c.guard.pins_match(pins) and c.rd(o/'pins.json')==pins)
ck('launch_membership',set(pins['files'])==set(s['files'])|{str(r/'sealed.json'),str(r/'admission.json'),str(r/'prehost.json')} and pins['trees']==s['trees'] and len(pins['files'])==1862)
c.verify_review(c.rd(r/'admission.json'),r/'sealed.json',s['files']+[str(r/'sealed.json')],'dynamic BG matched cost admission','cost1-300')
ck('config',s['config']==cfg==c.rd(r/'config.json'))
p=c.rd(o/'process.json');cur=c.rd(o/'current.json');inv=c.rd(r/'invocation.json');sup=inv['supervisor'];res=c.rd(r/'reservation.json')
ck('identity',p['runner']==cur['runner']==sup['guard_identity'] and p['child']==cur['child'])
ck('identifiers',all(p[role]['start_ticks']>0 and p[role]['command'] and p[role]['boot_id']==s['boot_id'] and p[role]['pid']==p[role]['pgid']==p[role]['sid'] for role in ['runner','child']))
ck('commands',p['command']==cur['command']==inv['command']==cfg['command'] and inv['guard_command']==c.guard_command(cfg,r/'launch-pins.json',inv['monotonic_start']) and Path(inv['python']).resolve()==Path(sys.executable).resolve())
ck('linkage',p['pins_sha256']==cur['pins_sha256']==inv['pins_sha256']==c.sha(r/'launch-pins.json') and inv['review_sha256']==c.sha(r/'admission.json') and inv['reservation_sha256']==c.sha(r/'reservation.json'))
ck('reservation',res==dict(one_attempt=True,phase='cost1-300',command=cfg['command'],pins_sha256=c.sha(r/'launch-pins.json'),review_sha256=c.sha(r/'admission.json'),max_seconds=300))
ck('exit',p['reason']=='exit0' and p['returncode']==0 and p['pins_unchanged'] is True and sup['returncode']==0 and sup['accepted'] is True and not any(sup[k] for k in ['soft_timeout','hard_timeout','child_kill','guard_term','guard_kill']) and 'cleanup_error' not in sup)
ck('time',all(type(v) in (float,int) and math.isfinite(v) and 0<=v<=300 for v in [inv['elapsed_seconds'],sup['elapsed_seconds'],p['elapsed_including_launch']]))
hosts=[c.rd(r/n) for n in ['host.json','prehost.json','posthost.json']]+[c.rd(E/'failure-posthost.json')]
ck('saved_host',all(not h['matches'] and all(h[k]==s[k] for k in ['head','master','boot_id']) for h in hosts))
ck('closure_groups',all(p[role][k] in hosts[-1]['groups'] for role in ['runner','child'] for k in ['pgid','sid']) and set(s['groups'])<=set(hosts[-1]['groups']))
h=c.full_host(hosts[-1]['groups']);ck('fresh_host',not h['matches'] and len(h['groups'])==234)
resources=[json.loads(z) for z in (o/'resources.jsonl').read_text().splitlines()]
ck('resources',bool(resources) and all(not c.guard.pressure(z) for z in resources+[p['terminal_memory']]) and p['child_maxrss_kib']>0)
log=(o/'run.log').read_text();ck('numerical_log',not any(t in log for t in ['FATAL COST:','ERROR:','Traceback','WARNING','Warning']))
expected={'pins.json','current.json','process.json','resources.jsonl','run.log','raw.toml'}|{f'{x}-{i}.toml' for i in range(1,9) for x in ['started','preflight','probe','cell']}|{f'window-{i}-{j}.toml' for i in range(1,9) for j in range(1,21)}
ck('outputs_membership',{q.name for q in o.iterdir()}==expected and all(q.is_file() and not q.is_symlink() for q in o.iterdir()))
raw=tom('raw.toml');expected_loaded=c.loaded_for(cfg);test=expected_loaded.pop('Test')
ck('only_Test_absent',raw==dict(phase='cost1-300',loaded=expected_loaded,completed=True,fatal='',cells=8,windows=160,threads=1,blas_threads=1))
ck('raw_types',raw['completed'] is True and all(type(raw[k]) is int for k in ['cells','windows','threads','blas_threads']))
source=(D/'cost.jl').read_text();ck('source_explains_difference','for m in (J,LinearAlgebra,SparseArrays,TOML,PrecompileTools)' in source and 'using Test' not in source and 'using Test' not in (D/'probe-oracles.jl').read_text())
fixtures=c.rd(D/'inputs.json')['fixtures'];cells=[];count=0
for f in fixtures:
 matrices=[(matrix(m),matrix(m,True)) for m in f['matrices']]
 for backend in ['native','markowitz']:
  i=len(cells)+1;identity=dict(fixture=f['name'],manager='BG',backend=backend,policy='threshold_one' if backend=='native' else 'default')
  ck('cell_identity_'+str(i),tom(f'started-{i}.toml')==identity and tom(f'cell-{i}.toml')==dict(identity,windows=20))
  preflight_ok(tom(f'preflight-{i}.toml'),backend);probe=tom(f'probe-{i}.toml');probe_ok(probe,f,matrices);count+=72
  rows=[]
  for j in range(1,21):
   row=tom(f'window-{i}-{j}.toml');ck('policy_'+str(i)+'_'+str(j),row['policy']==identity['policy']);window_ok(row,f,1,(j+1)//2,1+(j-1)%2,matrices);rows.append(row);count+=24
  ck('paired_'+str(i),all(rows[j]['outputs']==rows[j+1]['outputs'] and rows[j]['modes']==rows[j+1]['modes'] for j in range(0,20,2)))
  st=summarize(rows);st['probe_memory_gate']=all(10*z['graphs'][1]<=11*z['graphs'][0] for z in probe['states']);st['memory_gate'] &= st['probe_memory_gate']
  cells.append(dict(identity,statistics=st,probe=probe,preflight=tom(f'preflight-{i}.toml')))
ck('residual_count',count==4416)
proof=dict(all_passed=True,scope='Independent saved-data diagnostic review; original audit remains FALSE',checks=checks,exact_residuals=count,cells=cells,host=h,inclusive_seconds=inv['elapsed_seconds'],child_maxrss_kib=p['child_maxrss_kib'],missing_expected_key='Test',no_second_process=True,sha256={str(q):c.sha(q) for q in r.rglob('*') if q.is_file()})
c.save(E/'independent-result-proof-v1.json',proof)
print(json.dumps(dict(passed=True,checks=len(checks),exact_residuals=count,cells=[dict(fixture=z['fixture'],backend=z['backend'],ratio=z['statistics']['seconds']['paired_ratio']['median'],faster=z['statistics']['faster_pairs'],gates={k:z['statistics'][k] for k in ['time_median_gate','allocation_gate','memory_gate','probe_memory_gate']}) for z in cells])))
