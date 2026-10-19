"""Summarize saved failed RED2 without rerunning Julia or its auditor."""
from pathlib import Path
import sys,json,tomllib
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');H=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-RED2-HARNESS';D=H.with_name('DIRECT-BG-BLOCKED-UPDATE-RED2');sys.path.insert(0,str(H));import control as c;import oracle
run=H/'runs/red300';out=run/'output';outer=c.outer_dir('red300');checks={}
def ck(n,v):c.require(v,n);checks[n]=True
s=c.rd(run/'sealed.json');p=c.rd(out/'process.json');a=c.rd(run/'audit.json');inv=c.rd(run/'invocation.json');cl=c.rd(run/'outer-closure.json')
raw=tomllib.loads((out/'raw.toml').read_text());u=tomllib.loads((out/'unit-1.toml').read_text());counts=oracle.tree(u['tests'])
ck('seal_unchanged',c.guard.pins_match(s));ck('launch_pins_unchanged',c.guard.pins_match(c.rd(run/'launch-pins.json')))
ck('failed_audit_preserved',a['all_passed'] is False and a['pure_timeout'] is False and 'Exact exit' in a['error'] and c.bindings(a))
ck('external_closure',c.validate_result_closure('red300',cl))
ck('one_saved_unit',sorted(q.name for q in out.glob('unit-*.toml'))==['unit-1.toml'])
ck('panel_completed',u['complete'] is True and u['fatal']=='' and u['name']=='panel' and u['index']==1)
ck('full_panel_sites',u['records']['sites']==oracle.panel_counts())
ck('panel_counts',counts==[11759,1,0,0])
f=u['records']['failures'];ck('only_P011',len(f)==u['records']['failure_count']==1 and f[0]['site']=='P011' and f[0]['kind']=='fail')
ck('raw_stopped_before_aggregate',raw['complete'] is False and raw['units_completed']==0 and raw['totals']==[0,0,0,0] and 'Unexpected unit failure' in raw['fatal'])
ck('loaded_repaired_stage',raw['loaded']==c.loaded_for(c.config('red300')) and raw['threads']==raw['blas_threads']==1)
ck('non_timeout_exit2',p['returncode']==2 and p['reason']=='exit2' and p['pins_unchanged'] is True and inv['supervisor']['returncode']==1 and inv['supervisor']['soft_timeout'] is False and inv['supervisor']['hard_timeout'] is False and inv['elapsed_seconds']<=300)
log=(out/'run.log').read_text();ck('prefix_only',log.count('TEST FAILURE:')==1 and 'UNIT BEGIN 1 panel' in log and 'UNIT END 1 panel' in log and 'UNIT BEGIN 2' not in log and 'N026' not in log)
ck('no_warning',not oracle.warning_log(log+(run/'launcher.log').read_text()))
resources=[json.loads(x) for x in (out/'resources.jsonl').read_text().splitlines()]
ck('resources',resources and all(not c.guard.pressure(x) for x in resources+[p['terminal_memory']]))
ck('no_false_predecessor_or_green',not (run/'result-review.json').exists() and not (H/'runs/green300').exists())
files=[q for root in [run,outer] for q in root.rglob('*') if q.is_file()]+[H/'driver.jl',H/'panel-tests.jl',H/'recorder.jl',c.C/'panel.jl']
c.save(D/'summary.json',dict(qualification_pass=False,checks=checks,counts=counts,raw_totals=raw['totals'],raw_units_completed=0,saved_units=1,expected_N026_reached=False,failure_site='P011',allocated_bytes=None,allocated_events=None,process_seconds=p['elapsed_including_launch'],inclusive_supervisor_seconds=inv['elapsed_seconds'],resource_samples=len(resources),min_available_kib=min(x['available_kib'] for x in resources),max_swap_kib=max(x['swap_used_kib'] for x in resources),child_maxrss_kib=p['child_maxrss_kib'],groups=cl['host']['groups'],sha256={str(q):c.sha(q) for q in files},scope=__doc__))
print(json.dumps(dict(checks=len(checks),counts=counts,samples=len(resources),groups=len(cl['host']['groups']),min_available_kib=min(x['available_kib'] for x in resources),inclusive_seconds=inv['elapsed_seconds'])))
