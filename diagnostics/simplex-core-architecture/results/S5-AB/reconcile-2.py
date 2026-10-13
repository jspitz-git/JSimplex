"""Exclusive source/evidence reconciliation; no Julia and no frozen executables."""
from pathlib import Path
import re,json,hashlib,subprocess
R=Path.cwd();H=Path(__file__).resolve().parent;D=H.parent.parent;C=R/'.superpowers/simplex-core-architecture/S6-A/ci-inventory-1';pins={}
def read(p):
 p=Path(p);b=p.read_bytes();pins[str(p)]=hashlib.sha256(b).hexdigest();return b
def js(p):return json.loads(read(p))
def git(ref,f):return subprocess.check_output(['git','show',ref+':'+f])
def sh(b):return hashlib.sha256(b).hexdigest()
def norm(s):return re.sub(r'(?:\x1b|\^\[)\[[0-9;]*m','',s)
def block(b,name):
 t=b.decode();m=re.search(r'^([ \t]*)@testset '+re.escape(json.dumps(name))+' begin',t,re.M);assert m,name
 following=re.search(r'^'+re.escape(m[1])+r'@testset ',t[m.end():],re.M)
 return t[m.start():m.end()+following.start() if following else len(t)].encode()
files=['unscaled_cleanup_tests.jl','postsolve_cleanup_performance_tests.jl','postsolve_hint_tests.jl','postsolve_box_hint_tests.jl','postsolve_native_projection_tests.jl','legacy_phase_artificial_bound_tests.jl','simplex_phase_one_tests.jl','simplex_phase_one_state_tests.jl','simplex_phase_one_guard_tests.jl']
selected={f:re.findall(r'^\s*@testset "([^"$]+)" begin',read(R/'test'/f).decode(),re.M) for f in files}
selected['presolve_tests.jl']=['Singleton equality aggregation preserves LP and basis','Original LP resolves an inconclusive reduced numerical run','Advanced presolve reduces rows and restores solutions','Presolve removes reversible structure','Cleanup resolves the original model from a restored basis','Postsolve basis projection retains implied-bound values','Numerical cleanup failure retries the original LP','Original LP retry explains the restart and keeps cumulative iterations','Presolve handles a completely reduced LP','Optimal simplex runs retain an original-column basis']
sources=['solver.jl','transformations.jl','presolve.jl','simplex_phase_one.jl','primal_simplex.jl','simplex_driver.jl','simplex_precision.jl','simplex_precision_recovery.jl','simplex_recovery.jl','simplex_perturbation.jl','simplex_pricing.jl','dual_simplex.jl','simplex_start.jl','simplex.jl']
rows=[];cmp=[];runs=[]
for run in ['38142752357','38149970679']:
 meta=js(C/f'{run}-metadata.json');ref=meta['headSha'];runs.append(dict(run=run,ref=ref,conclusion=meta['conclusion']));raw=read(C/f'{run}-failed.log').decode().splitlines()
 for f,names in selected.items():
  p='test/'+f;old=git(ref,p);now=read(R/p);cmp.append(dict(run=run,file=p,historical=sh(old),current=sh(now),equal=old==now))
  for name in names:
   found=[(i+1,line,norm(line)) for i,line in enumerate(raw) if name+' ' in norm(line) and '|' in norm(line)]
   assert len(found)==1,(run,name,len(found));line,original,clean=found[0];tail=clean.split('|',1)[1].strip();fields=tail.split();assert len(fields)==3 and fields[0]==fields[1] and fields[0].isdigit(),(name,tail)
   rows.append(dict(run=run,file=p,name=name,line=line,raw=original,normalized=clean,passed=int(fields[0]),total=int(fields[1]),test_source_equal=old==now))
 for f in sources:
  p='src/'+f;old=git(ref,p);now=read(R/p);cmp.append(dict(run=run,file=p,historical=sh(old),current=sh(now),equal=old==now))
# Actual C focused execution: include list plus complete run summary, never pin-presence alone.
cbase=H.parent/'S5-C';cp=js(R/'.superpowers/simplex-core-architecture/S5-C/focused-1/pins.json')['inventory'];driver=read(D/'reproduce/restoration_copy_focused.jl').decode();log=read(cbase/'focused-1-run.log').decode();ca=js(cbase/'focused-1-audit.json');cfiles=re.findall(r'^FILE (.+)$',log,re.M);cmap=[]
for f in cfiles:
 p=R/'test'/f;old=cp[str(p)]['sha256'];now=read(p);equal=sh(now)==old
 # AO is an append: hash the known complete pre-AO file recovered from the pinned commit.
 oldbytes=git('e7014fb','test/'+f)
 cmap.append(dict(file='test/'+f,launch_sha256=old,current_sha256=sh(now),whole_equal=equal,historical_commit='e7014fb',historical_matches_pin=sh(oldbytes)==old,current_preserves_historical_prefix=now.startswith(oldbytes)))
for f in sources:read(R/'src'/f)
# Accepted permanent integrations, tied to actual master launch pins and stored logs/audits.
specs=[('S5-I','master-1/pins.json','master-1-audit.json','master-1/run.log','simplex_precision_state_tests.jl'),('S5-O','master-1/pins.json','master-1-audit.json','master-1/run.log','adaptive_pricing_tests.jl'),('S5-U','master/pins.json','master/audit.json','master/portable/run.log','simplex_precision_tests.jl'),('S5-AA','master/pins.json','master/audit.json','master/portable/run.log','simplex_start_state_tests.jl'),('S6-AC','master-1-pins.json','master-1-audit.json','master-1-run.log','native_phase_transfer_tests.jl'),('S6-AO','master-1-pins.json','master-1-audit.json','master-1-run.log','primal_perturbation_integration_tests.jl')]
integrations=[]
for s,p,a,l,f in specs:
 b=H.parent/s;inv=js(b/p)['inventory'];audit=js(b/a);text=read(b/l).decode();current=read(R/'test'/f);matches=[v['sha256'] for k,v in inv.items() if k.endswith('/test/'+f)]
 sp=[]
 for src in sources:
  vals=[v['sha256'] for k,v in inv.items() if k.endswith('/src/'+src)]
  sp.append(dict(file=src,matched=bool(vals) and all(v==pins[str(R/'src'/src)] for v in vals)))
 integrations.append(dict(stage=s,test=f,current_sha256=sh(current),test_matches_all_launch_entries=bool(matches) and all(v==sh(current) for v in matches),source=sp,audit_all_passed=audit['all_passed'],log=text))
# S6-AA source intentionally changed by AC: bind exact unchanged reliable target, not whole old file.
aa=H.parent/'S6-AA';old=read(aa/'master-1-test.jl');cur=read(R/'test/native_phase_transfer_tests.jl');name='Reliable artificial exchanges need no reconstruction recovery';names=re.findall(r'@testset "([^"]+)"',old.decode());aa_same=block(old,name)==block(cur,name)
read(aa/'master-1-audit.json');read(aa/'master-1-run.log');
# S5 A/B/C reports and exact accepted audit outputs; accepted numerical evidence is reused.
for f in ['S5-INVENTORY-NOTES.md','S5-ENTRY.md','S5-RESTORATION.md','S5-COPIES.md','S5-ENTRY-REVIEW.md','S5-RESTORATION-REVIEW.md','S5-COPIES-REVIEW.md','S5-PRECISION-JOURNAL-INTERRUPTION-TEST-INTEGRATION.md','S5-DUAL-AUXILIARY-PENDING-OBSERVER-TEST-INTEGRATION.md','S5-BASIS-INITIALIZATION-STOP-TEST-INTEGRATION.md','S5-CRASH-FALLBACK-OBSERVER-TEST-INTEGRATION.md','S6-PHASE-RECONSTRUCTION-FIXTURE.md','S6-RELIABLE-EXCHANGE-FIXTURE.md','S6-NATIVE-CLEANUP-ENTRY-COVERAGE.md']:
 read(D/f)
checks=dict(AA_reliable_target_unchanged=aa_same,two_failed_historical_runs=all(x['conclusion']=='failure' for x in runs),all_selected_rows_pass=all(x['passed']==x['total'] for x in rows),all_selected_historical_tests_identical=all(x['equal'] for x in cmp if x['file'].startswith('test/')),C_executed_nine_files=len(cfiles)==9 and all('"'+f+'"' in driver for f in cfiles) and bool(re.search(r'1463\s+1463',log)),C_historical_pin_identity=all(x['historical_matches_pin'] for x in cmap),C_current_prefix_or_whole=all(x['current_preserves_historical_prefix'] for x in cmap),integration_current_test_identity=all(x['test_matches_all_launch_entries'] for x in integrations),integration_source_identity=all(y['matched'] for x in integrations for y in x['source']),integration_audits_pass=all(x['audit_all_passed'] for x in integrations))
result=dict(checks=checks,all_passed=all(checks.values()),runs=runs,rows=rows,comparisons=cmp,C_files=cmap,integrations=integrations,sha256=pins)
with (H/'reconciliation-2.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(dict(checks=checks,rows=len(rows),comparisons=len(cmp),pins=len(pins),different=[x for x in cmp if not x['equal']],C_files=cmap)));assert all(checks.values())
