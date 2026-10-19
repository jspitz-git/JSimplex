from pathlib import Path
import json
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');H=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-HARNESS';G=H.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-GC-DRIVER')
def write(n,s):
 with (H/n).open('x') as f:f.write(s)
write('finish.py',Path(__file__).read_text())
for p in Path('/tmp/bg-harness-text').iterdir():write(p.name,p.read_text())
# New unreviewed clones amended before first source check; generator additions separately bound.
p=H/'numerical-tests.jl';s=p.read_text();a='    elseif event===:panel_reject\n';b=a+'        t.checkpoint===nothing && HarnessRecords.tick("declined_before_gather")\n';assert s.count(a)==1;s=s.replace(a,b);p.write_text(s)
p=H/'lifecycle-tests.jl';s=p.read_text()
for sid,key in [('L025','catch_overflow'),('L030','catch_nonfinite')]:
 a='@check "'+sid+'"';assert s.count(a)==1;s=s.replace(a,'HarnessRecords.tick("'+key+'");'+a)
p.write_text(s)
# Exact added instrumentation inverse is recorded, not an edit of frozen tests.
p=H/'test-transform.json';m=json.loads(p.read_text());import hashlib
m['numerical-tests.jl']['changes'].append({'old':a if False else '    elseif event===:panel_reject\n','new':'    elseif event===:panel_reject\n        t.checkpoint===nothing && HarnessRecords.tick("declined_before_gather")\n','count':1})
for sid,key in [('L025','catch_overflow'),('L030','catch_nonfinite')]:m['lifecycle-tests.jl']['changes'].append({'old':'@check "'+sid+'"','new':'HarnessRecords.tick("'+key+'");@check "'+sid+'"','count':1})
for n,v in m.items():v['clone_sha256']=hashlib.sha256((H/n).read_bytes()).hexdigest()
p.write_text(json.dumps(m,indent=2)+'\n')
s=(G/'audit.py').read_text().replace('BG specialization GC','BG blocked U').replace('BG specialization','BG blocked U')
s=s.replace('from oracle import test_results,timeout_only,warning_log','from oracle import test_results,prefix,warning_log')
a=s.index(' preps=');b=s.index(" sp=run/'sealed.json'",a)
s=s[:a]+''' units={f'unit-{i}.toml' for i in range(1,29)}
 require(base<=names<=base|{'raw.toml'}|units and all(p.is_file() and not p.is_symlink() for p in out.iterdir()),'Output membership')
'''+s[b:]
a=s.index(' from allocation_oracle');b=s.index('def audit(phase):',a)
s=s[:a]+''' saved_units={n:tomllib.loads((out/n).read_text()) for n in names & units}
 schedule=rd(D/'schedule.json')
 require(not warning_log(log),'Warning/world-age outcome rejected')
 # Conservative classification only: no failed, errored or interrupted saved unit.
 prefix(saved_units,schedule,phase)
 pure=(p['reason']=='wall_timeout' and p['returncode'] in [-15,-9] and sup['returncode']==1 and sup.get('hard_timeout') is False
       and sup.get('accepted') is False and not any(s in log for s in ['TEST FAILURE:','FATAL DRIVER:','GROUP/COUNT MISMATCH'])
       and 'BEGIN BG blocked U driver '+phase in log and raw is None)
 if pure:return dict(all_passed=False,pure_timeout=True,result={},error='Incomplete pure timeout; separate reviewed longer admission required')
 require(p['returncode']==cfg['expected_exit'] and p['reason']=='exit'+str(cfg['expected_exit']) and sup['returncode']==0 and sup['accepted'] is True,'Exact exit')
 require(raw is not None and names==base|{'raw.toml'}|units,'Missing raw/units')
 result=test_results(raw,saved_units,schedule,loaded_for(cfg),phase)
 require(not any(s in log for s in ['BROKEN TEST:','FATAL DRIVER:','GROUP/COUNT MISMATCH']),'Failure log')
 require(log.count('TEST FAILURE:')==(6 if cfg['mode']=='red' else 0),'Exact failure log count')
 require([line for line in log.splitlines() if line.startswith('UNIT BEGIN ')]==[f'UNIT BEGIN {i} {n}' for i,n in enumerate(schedule['units'],1)],'Unit start order')
 require([line for line in log.splitlines() if line.startswith('UNIT END ')]==[f'UNIT END {i} {n}' for i,n in enumerate(schedule['units'],1)],'Unit completion order')
 return dict(all_passed=True,pure_timeout=False,result=result,process_elapsed_seconds=inv['elapsed_seconds'],scope_note='Correctness only; cold exact oracles and compilation included; no performance acceptance',error='')
'''+s[b:];write('audit.py',s)
print('Driver, recorder and full auditor prepared OFFLINE')
