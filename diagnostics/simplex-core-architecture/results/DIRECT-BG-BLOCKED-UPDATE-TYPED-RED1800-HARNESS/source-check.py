"""New offline source/integrity check; definitions only, no numerical entrypoint."""
from pathlib import Path
import sys,json,re,ast,hashlib
D=Path(__file__).resolve().parent;R=D.parents[3];P=D.with_name('DIRECT-BG-BLOCKED-UPDATE-TYPED-HARNESS');sys.path.insert(0,str(D));import control as c
checks={};bound={}
def ck(k,v):
 checks[k]=bool(v)
 if not v:raise RuntimeError(k)
def bind(p):bound[str(p)]=c.sha(p)
c.validate_environment();ck('environment',True)
c.validate_sources();ck('current_master_stage_runtime_sources',True)
c.validate_probe();c.validate_typed();c.validate_qualification();c.validate_timeout_record();ck('frozen_qualified_sources_and_unaccepted_timeout',True)
cp=c.rd(D/'copied-files.json');ck('22_copies_exact',len(cp)==22 and all(c.sha(D/n)==v['sha256']==c.sha(v['source']) for n,v in cp.items()))
for n,v in c.rd(D/'control-transform.json').items():
 s=(D/n).read_text();ck(n+'_current_hash',c.sha(D/n)==v['prepared_sha256'])
 if 'append' in v:
  ck(n+'_append_exact',s.endswith(v['append']));s=s[:-len(v['append'])]
 for e in reversed(v['edits']):
  ck(n+'_inverse_'+str(len(checks)),s.count(e['new'])==e['count']);s=s.replace(e['new'],e['old'])
 ck(n+'_whole_source_inverse',s.encode()==Path(v['source']).read_bytes() and c.sha(v['source'])==v['source_sha256'])
ck('oracle_only_time_bound',(D/'oracle.py').read_text().replace('0<=v[k]<=1800','0<=v[k]<=300')==(P/'oracle.py').read_text())
cfg=c.config('red1800');ck('new_phase_same_driver_semantic',cfg['phase']=='red1800' and cfg['command'][-1]=='red300' and cfg['command'][-4]==str(D/'driver.jl') and cfg['seconds']==1800 and cfg['expected_exit']==1)
for p in ['red300','green300','green1800',None]:
 try:c.config(p)
 except RuntimeError:ck('refuses_'+str(p),True)
 else:raise RuntimeError('Accepted unpreparedphase')
cmd=c.guard_command(cfg,Path('/tmp/not-created-pins'),100.);ck('1792_guard_deadline',cmd[cmd.index('--seconds')+1]=='1792' and cmd[cmd.index('--deadline')+1]=='1892.0')
ck('new_paths',cfg['run']==str(D/'runs/red1800') and cfg['payload']==str(D/'runs/red1800/payload'))
pf,pg=c.predecessor('red1800');ck('81_previous289groups',len(pf)==81 and len(pg)==289)
ck('no_launch_state',not (D/'runs').exists() and not (D/'outers').exists())
sites=set()
for n in ['panel-tests.jl','lifecycle-tests.jl','numerical-tests.jl']:sites|=set(re.findall(r'@check(?:throws)? "([PLN][0-9]{3})"',(D/n).read_text()))
ck('168_actual_sites',len(sites)==168 and {f'P{i:03d}' for i in range(1,103)}<=sites)
sch=c.rd(D/'schedule.json');ck('28units_sixN026',len(sch['units'])==28 and len(sch['expected_red_units'])==6)
ck('driver_exact_unchanged',c.sha(D/'driver.jl')==c.sha(P/'driver.jl'))
ck('numeric_assertions_exact_unchanged',all(c.sha(D/n)==c.sha(P/n) for n in ['panel-tests.jl','lifecycle-tests.jl','numerical-tests.jl','panel.jl','panel-fault.jl','factor.jl','factor-fault.jl']))
j=c.rd(D/'tests.json');ck('new_synthetic2378',j['all_passed'] is True and j['count']==2378 and c.bindings(j))
for p in D.glob('*.py'):ast.parse(p.read_text());bind(p)
ck('Python_AST_only',True)
ck('entry_refs',c.git('rev-parse','HEAD')=='67533adf18a5ba4929e77cafa73472c29d3dd5d0' and c.git('rev-parse','master')==c.MASTER)
ck('tracked_clean',c.git('diff','--name-only')==c.git('diff','--cached','--name-only')=='')
for p in D.iterdir():
 if p.is_file():bind(p)
c.save(D/'source-check.json',dict(all_passed=True,checks=checks,sha256=bound,scope='Offline Python source/schema/hash checks only; no Julia, launch, numerical test, or old checker execution'))
print(json.dumps(dict(all_passed=True,checks=len(checks),bindings=len(bound))))
