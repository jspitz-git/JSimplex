from pathlib import Path
import json,hashlib,re,os,subprocess,datetime
P=Path(__file__).resolve().parent;D=P.parent;M=Path('/home/jspitz/JSimplex.jl');R=D.parents[2];RED=D/'RED'
def need(x,m):
 if not x:raise RuntimeError(m)
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(n,v):
 with (P/n).open('x') as f:json.dump(v,f,indent=2,sort_keys=True);f.write('\n')
pins=read(P/'pins.json');need(len(pins['inventory'])==1343,'pins')
for n,v in pins['inventory'].items():need(str(Path(n).resolve(strict=True))==v['resolved'] and sha(n)==v['sha256'],'pin '+n)
for tree in pins['trees']:need({str(p) for p in Path(tree).rglob('*') if p.is_file()}=={n for n in pins['inventory'] if Path(n).is_relative_to(tree)},'tree membership')
for n,v in read(D/'baseline-tree.json').items():need(sha(RED/n)==sha(M/n)==v,'original baseline '+n)
for tree in ['src','test']:
 expected={n for n in read(D/'baseline-tree.json') if n.startswith(tree+'/')}
 if tree=='test':expected.add('test/generic_sum_rational_growth_tests.jl')
 need({str(p.relative_to(RED)) for p in (RED/tree).rglob('*') if p.is_file()}==expected,'only new test added '+tree)
need((D/'new-test.jl').read_bytes()==(RED/'test/generic_sum_rational_growth_tests.jl').read_bytes(),'test exact copy')
for record in [read(D/'result-review.json'),read(D/'correctness-qualification/result-review.json')]:
 need(record['accepted'] is True and record['findings']==[],'accepted candidate/correctness review')
 for n,v in record['bindings'].items():need(sha(n)==v,'prior binding '+n)
for section in read(P/'protected-before.json').values():
 for n,v in section.items():need(sha(n)==v,'protected '+n)
text=(D/'new-test.jl').read_text();prefix='module GenericSumRationalGrowthTests\nusing Test,JSimplex,SparseArrays,LinearAlgebra,Statistics\n'+(D/'Reference.jl').read_text()+'\nconst SRGA=JSimplex\nconst SRGB=JSimplex\nconst SRGC=JSimplex\n'+(D/'fixtures-reviewed.jl').read_text()+'\n'+(D/'correctness-qualification/extra-corrected.jl').read_text()
need(text.startswith(prefix),'exact qualified numerical source prefix')
rest=text[len(prefix):]
need(rest.count('function allocation_gate(')==1 and rest.count('   allocation_gate(')==7,'seven fixed gates')
need('for k in 1:3,(tag,v)' in rest and 'for pair in 1:3,tag in (isodd(pair) ? (:original,arm) : (arm,:original))' in rest,'fixed warm/pair count')
need('v=tag===:original ? a : b;reset!(v);t=timed(Val(tag),v)' in rest,'reset outside timing')
need('@test t["compile_seconds"]==t["recompile_seconds"]==0' in rest,'compile zero')
gate_assert=' @test all(after[k]["events"]<before[k]["events"] for k in 1:3)&&median(x["bytes"] for x in after)<median(x["bytes"] for x in before)'
need(text.splitlines()[623]==gate_assert,'exact failure line/assertion')
gates=read(D/'test-gates.json');need(gates['accepted_variants']==['A','B','C'] and gates['expected_RED_failures']==7 and gates['failure_line']==624 and len(gates['gates'])==7,'gate manifest')
for q in gates['gates']:
 call='   allocation_gate('+q['type']+',:'+q['scope']+',:'+q['arm']+','+str(q['n'])+',:'+q['density']+',:'+q['shape']+','+str(q['below']).lower()+','+str(q['chain'])+')'
 need(rest.count(call)==1,'exact fixed gate '+q['scope'])
# 28227 qualified tests, 47 whole-function validation assertions, 42 compile checks, 7 allocation gates.
expected_total=28227+(8+6+6+6+7+7+7)+7*6+7
need(expected_total==28323,'derived total')
c=read(P/'contract.json');need(c['arm']=='RED' and c['attempts']==1 and c['expected_exit']==1 and c['expected_failures']==7 and c['expected_failure_locations']==[[str(RED/'test/generic_sum_rational_growth_tests.jl'),624]]*7,'RED outcome')
need(c['source_root']==str(RED) and c['files']==['generic_sum_rational_growth_tests.jl'] and c['shared_limit_seconds']==3000 and c['guard_limit_seconds']==2992,'exact phase scope')
need(c['expected_total'] in [None,expected_total],'compatible expected total')
command=read(D/'contract-ready.json')['command'][:-2]+[str(P/'tests.jl')];command=[x.replace('--project='+str(M),'--project='+str(RED)) for x in command];need(c['command']==command,'exact command')
driver=(P/'tests.jl').read_text();need('const ROOT="'+str(RED)+'"' in driver and 'realpath(pathof(JSimplex))==realpath(joinpath(ROOT,"src/JSimplex.jl"))' in driver and 'Base.active_project()==joinpath(ROOT,"Project.toml")' in driver and 'for file in ["generic_sum_rational_growth_tests.jl"]' in driver,'actual source/whole-file driver')
for n in ['entry_gate.py','guard_reviewed.py','supervisor_reviewed.py']:need((P/'guard'/n).read_bytes()==(D/'guard'/n).read_bytes(),'same guard')
need((P/'common.py').read_bytes()==(D/'common.py').read_bytes(),'same common')
need((P/'launch.py').read_text()==(D/'launch.py').read_text().replace('892','2992').replace('900','3000'),'only phase deadline launcher change')
need(not (P/'output').exists() and not (P/'reservation.json').exists(),'unreserved attempt')
OVERRIDES=['JULIA_PROJECT','JULIA_LOAD_PATH','JULIA_BINDIR','JULIA_CPU_TARGET','JULIA_DEPOT_PATH','LD_PRELOAD','LD_LIBRARY_PATH','LD_AUDIT','BASH_ENV','ENV','PYTHONPATH','PYTHONHOME']
need(all(not os.environ.get(k) for k in OVERRIDES),'environment override');need({k:os.environ[k] for k in OVERRIDES+['JULIA_NUM_THREADS','OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'] if k in os.environ}==read(P/'environment.json')['inherited'],'environment')
env=dict(os.environ,GIT_OPTIONAL_LOCKS='0')
def git(root,*args):return subprocess.check_output(['/usr/bin/git','-C',str(root),*args],env=env).decode().strip()
need(all(git(M,'rev-parse',v)=='ce5d4a74019e0dc2e656d08161641c498b159e7b' for v in ['HEAD','master','origin/master']),'master refs')
need(git(R,'rev-parse','HEAD')=='c01e9376bdbcda7cb54ba55735cf053299b9af45','diagnostic HEAD');need(not git(M,'diff','--name-only','HEAD','--','src','test','Project.toml'),'production drift')
seed=read(P/'host-seed.json');groups=set(seed['groups']);historical=set(read(D/'host-seed.json')['groups'])
for n in ['output/process.json','correctness-qualification/output/process.json']:
 q=read(D/n);historical.update(q[k][v] for k in ['runner','child'] for v in ['pgid','sid'])
need(groups==historical and len(groups)==653,'historical completeness')
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();need(boot==seed['boot_id'],'boot');allowance=R/'diagnostics/generic-quality-local/2026-10-27/host-identity-allowance.json';need(sha(allowance)=='f0b6a5093b9c1875ec8718bca8775bc44ba4d6d6ab98a1ac23adfe52d69f2a92','fixed allowance');allowed=read(allowance)['identities'];processes=[];collisions=[]
for proc in Path('/proc').glob('[0-9]*'):
 try:
  fields=(proc/'stat').read_text().rsplit(')',1)[1].split();cmd=[x.decode(errors='replace') for x in (proc/'cmdline').read_bytes().split(b'\0') if x];comm=(proc/'comm').read_text().strip();identity=dict(pid=int(proc.name),pgid=int(fields[2]),sid=int(fields[3]),start_ticks=int(fields[19]),command=cmd,boot_id=boot)
  need(not any(Path(x).name.lower().startswith('julia') for x in [comm]+cmd[:1]),'live Julia')
  if identity['pgid'] in groups or identity['sid'] in groups:need(identity in allowed,'historical group/session collision');collisions.append(identity)
  processes.append(identity)
 except (FileNotFoundError,ProcessLookupError):pass
mem={v.split(':')[0]:int(v.split()[1]) for v in Path('/proc/meminfo').read_text().splitlines()};need(mem['MemAvailable']>=6*1024**2 and mem['SwapTotal']-mem['SwapFree']<=1024**2,'RAM/swap')
put('independent-host.json',dict(time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),boot_id=boot,groups=sorted(groups),processes=processes,collisions=collisions,no_Julia=True,available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree']))
report='''# Independent original-code RED admission: accepted

The concrete single whole-file RED run is admitted against the original source snapshot, before production edits. All RED source and previous tests exactly match actual master ce5d4a74019e0dc2e656d08161641c498b159e7b and the frozen baseline. The only added file is generic_sum_rational_growth_tests.jl, identical to new-test.jl. The actual project and loaded JSimplex source path are asserted by the driver; stale worktree src is not used.

The permanent file contains exactly the previously reviewed original Reference, qualified fixtures and corrected numerical tests. A/B/C test aliases target live JSimplex methods. The existing 28,227 numerical assertions retain exact enclosures, input values/owners, empty/tie/NaN/Inf, Rational exceptions and fixed-width overflow, recovery precision/restoration, state/storage and reason/cache/age controls. Imports do not collide with owned private reference definitions. The old-decoder characterization is intentionally specific to the pinned Julia1.13 runtime; a future corrected Julia decoder may require updating that diagnostic assertion, not weakening production numerical expectations.

Seven allocation gates cover complete A rows/original feasibility, B certificates in both orientations, and C growth/forced refresh/scheduled reason with real active chain8. Each constructs independent fixtures, validates equality/inputs/state, warms three times, resets state outside typed whole-call timing, then collects exactly three alternating pairs. Each gate requires fewer allocation events in every pair and lower median bytes, with compile/recompile-zero assertions. No elapsed-time assertion or threshold tuning is introduced. Raw result capture remains outside whole-call timing. With original code on both sides, strict allocation reduction is expected to fail at line624 exactly seven times; every numerical and compile assertion must pass.

The independent expected root total is28,323:28,227 numerical assertions plus47 checkpair assertions in the seven gates,42 compile-zero checks and7 allocation assertions. Expected outcome is28,316 passes,7 failures,0 errors/broken, exit1. Although the current contract leaves expected_total null for first-run discovery, this admission binds28,323 and independent post-exit review must require that exact total before staging. The current phase-audit template retains ordinary summary/expected-location/source/resource/identity checks; its minimum-total check alone is insufficient to establish this independently frozen assertion count.

No production computation or memory behavior changed. The seven extra tests add only bounded test preparation and whole-call allocation observations, using small dense fixtures and owned state; no new production scan, solve, persistent cache or retained buffer is introduced. Existing safeguards, tolerances and precision contexts remain unchanged. These gates establish regression evidence and are not another performance comparison or broad speed claim.

All1,343 pins, source/test membership, prior accepted result bindings, protected user files/indexes and refs passed review. Fresh actual-host checks cover all653 historical groups AND sessions with exact boot/start-ticks/commands and only the fixed unrelated-process allowance; no Julia is active. One Julia/BLAS thread, GC1,0, heap2G, AS8G, RAM6G/swap1G, compiled-modules existing and owned-process guards are unchanged. Shared/guarded deadlines are3000/2992 seconds. No prior RED reservation/output exists.

This offline admission authorizes one concrete RED execution only. No Julia, old audit, production change or Git mutation was executed by the reviewer. Actual accepted RED evidence is still required before candidate production staging.
'''
with (P/'ADMISSION-REVIEW.md').open('x') as f:f.write(report)
paths=[P/n for n in ['pins.json','contract.json','tests.jl','common.py','launch.py','guard/guard_reviewed.py','guard/supervisor_reviewed.py','guard/entry_gate.py','independent-admission.py','independent-host.json','ADMISSION-REVIEW.md']]+[D/n for n in ['new-test.jl','test-gates.json','test-prepare.py','phase-audit.py','result-review.json']]+[RED/'test/generic_sum_rational_growth_tests.jl']
put('admission.json',dict(accepted=True,findings=[],bindings={str(p):sha(p) for p in paths},expected_total=28323,expected_passes=28316,expected_failures=7,expected_failure_line=624,expected_exit=1,source='original baseline',pins=1343,Julia_executed=False))
print(json.dumps(dict(accepted=True,findings=0,pins=1343,expected_total=28323,expected_passes=28316,expected_failures=7,fresh_groups_and_sessions=653)))
