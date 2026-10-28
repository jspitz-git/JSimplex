from pathlib import Path
import json,hashlib,re,os,subprocess,datetime
K=Path(__file__).resolve().parent;D=K.parent;M=Path('/home/jspitz/JSimplex.jl');R=D.parents[2]
def need(x,m):
 if not x:raise RuntimeError(m)
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(n,x):
 with (K/n).open('x') as f:json.dump(x,f,indent=2,sort_keys=True);f.write('\n')
pins=read(K/'pins.json');need(len(pins['inventory'])==1311,'pin count')
for n,v in pins['inventory'].items():need(str(Path(n).resolve(strict=True))==v['resolved'] and sha(n)==v['sha256'],'pin '+n)
for tree in pins['trees']:need({str(p) for p in Path(tree).rglob('*') if p.is_file()}=={n for n in pins['inventory'] if Path(n).is_relative_to(tree)},'tree membership')
for prior in ['pins.json','pins-reviewed.json','pins-ready.json']:
 need(all(pins['inventory'].get(n)==v for n,v in read(D/prior)['inventory'].items()),'prior inventory '+prior)
for prior in ['admission.json','admission-reviewed.json','admission-ready.json','decoder-root-cause-review.json']:
 for n,v in read(D/prior)['bindings'].items():need(sha(n)==v,'prior binding '+n)
for section in read(K/'protected-before.json').values():
 for n,v in section.items():need(sha(n)==v,'protected '+n)
for name in ['entry_gate.py','guard_reviewed.py','supervisor_reviewed.py']:need((K/'guard'/name).read_bytes()==(D/'guard'/name).read_bytes(),'guard copy')
for name in ['common.py','launch.py','environment.json','protected-before.json']:need((K/name).read_bytes()==(D/name).read_bytes(),'unchanged launcher '+name)
text=(D/'extra-tests-ready.jl').read_text();old='@test precision(precise)==512;@test Rational{BigInt}(precise)==exactweight'
new='''@test precision(precise)==512
    old_decoded=Rational{BigInt}(precise)
    rounded_expected=Rational{BigInt}(1)+Rational{BigInt}(1,big(1)<<53)
    if rounding(BigFloat) in (RoundUp,RoundFromZero)
     rounded_expected+=Rational{BigInt}(1,big(1)<<(precision(BigFloat)-1))
    end
    @test old_decoded==rounded_expected
    @test old_decoded!=exactweight
    ambient=(precision(BigFloat),rounding(BigFloat))
    decoded=setprecision(BigFloat,precision(precise)) do
     Rational{BigInt}(precise)
    end
    @test decoded==exactweight
    @test ambient==(precision(BigFloat),rounding(BigFloat))'''
need(text.count(old)==1 and text.replace(old,new)==(K/'extra-corrected.jl').read_text(),'sole decoder correction')
log=(D/'output/run.log').read_text();rows=[v for v in log.splitlines() if v.startswith('  ordinary whole functions ') or v.startswith('  independent boundaries ')]
need(len(rows)==38 and sum(int(v.split('|')[1].split()[-2]) for v in rows)==27957,'original correctness total')
need(log.count('Test Failed at ')==90 and log.count('Expression: Rational{BigInt}(precise) == exactweight')==90 and 'Error During Test' not in log,'root failures')
need('Some tests did not pass: 111259 passed, 90 failed, 0 errored, 0 broken.' in log,'root summary')
p=read(D/'output/process.json');sup=read(D/'supervisor.json');need(p['returncode']==1 and p['reason']=='exit1' and p['pins_unchanged'] is True and sup['accepted'] is False and not sup['soft_timeout'] and not sup['hard_timeout'],'preserved failed run')
proof=read(D/'decoder-root-cause-review.json');need(proof['root_cause_confirmed'] is True and proof['comparison_passed'] is False and proof['cost_acceptance'] is False and proof['cells']==2636 and proof['windows']==47448,'independent raw/formula proof')
contract=read(K/'contract.json');expected_command=read(D/'contract-ready.json')['command'][:-2]+[str(K/'driver.jl')]
need(contract==dict(command=expected_command,attempts=1,expected_exit=0,contexts=19,expected_assertions=28227,measured_windows=0,shared_limit_seconds=900,guard_limit_seconds=892,original_comparison_remains_failed=True),'qualification exact contract')
driver=(K/'driver.jl').read_text();need(all(x not in driver for x in ['@timed','CELLS','GRID','cell(','timed(','results.toml']),'cost measurement in qualifier')
need(driver.count('correctness(BigFloat);extra_correctness(BigFloat)')==1 and driver.count('correctness(T);extra_correctness(T)')==1,'ordinary correctness calls')
need('for bits in (64,128,256),(mode,name) in zip(MODES,("Nearest","Down","Up","ToZero","FromZero"))' in driver and 'for T in (Float32,Float64,Rational{BigInt},Rational{Int64})' in driver,'contexts')
need('include(joinpath(PARENT,"fixtures-reviewed.jl"));include(joinpath(@__DIR__,"extra-corrected.jl"))' in driver,'fixture sources')
need(not (K/'output').exists() and not (K/'reservation.json').exists(),'qualification attempt exists')
OVERRIDES=['JULIA_PROJECT','JULIA_LOAD_PATH','JULIA_BINDIR','JULIA_CPU_TARGET','JULIA_DEPOT_PATH','LD_PRELOAD','LD_LIBRARY_PATH','LD_AUDIT','BASH_ENV','ENV','PYTHONPATH','PYTHONHOME']
need(all(not os.environ.get(k) for k in OVERRIDES),'environment override')
need({k:os.environ[k] for k in OVERRIDES+['JULIA_NUM_THREADS','OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'] if k in os.environ}==read(K/'environment.json')['inherited'],'environment drift')
env=dict(os.environ,GIT_OPTIONAL_LOCKS='0')
def git(root,*args):return subprocess.check_output(['/usr/bin/git','-C',str(root),*args],env=env).decode().strip()
need(all(git(M,'rev-parse',v)=='ce5d4a74019e0dc2e656d08161641c498b159e7b' for v in ['HEAD','master','origin/master']),'master refs')
need(git(R,'rev-parse','HEAD')=='c01e9376bdbcda7cb54ba55735cf053299b9af45','diagnostic HEAD')
need(not git(M,'diff','--name-only','HEAD','--','src','test','Project.toml'),'production drift')
old=read(K/'host-seed.json');groups=set(old['groups']);parentgroups=set(read(D/'host-seed.json')['groups']);newgroups={p[k][v] for k in ['runner','child'] for v in ['pgid','sid']}
need(len(groups)==651 and groups==parentgroups|newgroups,'all historical and failed-run groups')
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();need(boot==old['boot_id'],'boot changed')
allowance=R/'diagnostics/generic-quality-local/2026-10-27/host-identity-allowance.json';need(sha(allowance)=='f0b6a5093b9c1875ec8718bca8775bc44ba4d6d6ab98a1ac23adfe52d69f2a92','fixed identity allowance')
permitted=read(allowance)['identities'];processes=[];collisions=[]
for proc in Path('/proc').glob('[0-9]*'):
 try:
  st=(proc/'stat').read_text().rsplit(')',1)[1].split();cmd=[v.decode(errors='replace') for v in (proc/'cmdline').read_bytes().split(b'\0') if v];comm=(proc/'comm').read_text().strip()
  ident=dict(pid=int(proc.name),pgid=int(st[2]),sid=int(st[3]),start_ticks=int(st[19]),command=cmd,boot_id=boot)
  need(not any(Path(v).name.lower().startswith('julia') for v in [comm]+cmd[:1]),'live Julia')
  if ident['pgid'] in groups or ident['sid'] in groups:need(ident in permitted,'historical group/session collision');collisions.append(ident)
  processes.append(ident)
 except (FileNotFoundError,ProcessLookupError):pass
mem={v.split(':')[0]:int(v.split()[1]) for v in Path('/proc/meminfo').read_text().splitlines()};need(mem['MemAvailable']>=6*1024**2 and mem['SwapTotal']-mem['SwapFree']<=1024**2,'RAM/swap')
put('independent-host.json',dict(time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),boot_id=boot,groups=sorted(groups),processes=processes,verified_unrelated_collisions=collisions,no_Julia=True,available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree']))
report='''# Independent correctness-only qualification admission: accepted

The concrete qualification is admitted for one guarded ordinary Test run, with 19 contexts and exactly 28,227 expected assertions. The original correctness subtotal is independently counted as 27,957 across 38 recorded leaf testsets. The correction adds exactly three assertions at each of 90 decoder sites, for 270 additional checks. No timing grid, timed calls, result-window capture or cost repetition is invoked by the qualification driver.

The sole change to existing correctness logic scopes Rational{BigInt}(precise) to the stored precision of its already computed result. Candidate calls, inputs, tolerances, existing arithmetic precision contexts and exact expected rational remain unchanged. The old decoder is separately asserted equal to the independently derived rounded value and unequal to the exact target, while the corrected decoder must equal the original exact target and restore ambient precision and rounding. Installed Julia's ambient-precision ldexp in the Rational decoder explains all 90 original failures; the independent raw Fraction proof remains bound and unchanged.

All Reference/A/B/C and fixtures-reviewed sources remain byte-identical to the admitted comparison, so prior numerical and computational review applies. No additional production scan, solve, copy, numerical cache or retained buffer is introduced. Supplementary decoder construction and assertions are correctness preparation only, outside the preserved cost measurements. No speedup or allocation-saving conclusion follows from this admission.

All 1,311 pins, every earlier 1,288/1,274/1,254 inventory entry, original admissions and independent root-cause bindings passed fresh hashing. Protected user files, source/test files and Git indexes are unchanged. Root comparison remains failed with 111,259 passes, 90 failures and zero errors/broken; its complete 2,636 cells and 47,448 windows remain frozen, with no fabricated success marker. Root failed-process and supervisor records are retained.

The copied guards/common/launcher are byte-identical to previously reviewed versions. The exact command retains one Julia/BLAS thread, GC1,0, compiled-modules existing, heap2G, AS8G, availableRAM6G and swap1G, with 900 shared/892 guarded seconds and owned-process cleanup. Fresh host checks cover all 651 historical and failed-run identifiers as PGIDs AND SIDs, exact boot/start-ticks/commands, the fixed unrelated-process allowance, no Julia, refs, inherited environment, and RAM/swap. No qualification output or reservation exists.

This offline review executed no Julia, old audit, production change or Git mutation. Acceptance authorizes only this pinned supplemental correctness run. The failed comparison is not relabeled as passing, and its costs remain unaccepted until complete qualification evidence and a separately reviewed strict qualified audit establish all required conditions.
'''
with (K/'ADMISSION-REVIEW.md').open('x') as f:f.write(report)
paths=[K/n for n in ['pins.json','contract.json','driver.jl','extra-corrected.jl','oracle-correction.json','prepare.py','common.py','launch.py','guard/guard_reviewed.py','guard/supervisor_reviewed.py','guard/entry_gate.py','independent-admission.py','independent-host.json','ADMISSION-REVIEW.md']]+[D/n for n in ['pins-ready.json','admission-ready.json','decoder-root-cause-review.json','output/process.json','output/run.log','output/results.toml','Reference.jl','A.jl','B.jl','C.jl','fixtures-reviewed.jl','extra-tests-ready.jl']]
put('admission.json',dict(accepted=True,findings=[],bindings={str(p):sha(p) for p in paths},pins=1311,contexts=19,expected_assertions=28227,measured_windows=0,original_comparison_passed=False,Julia_executed=False))
print(json.dumps(dict(accepted=True,findings=0,pins=1311,expected_assertions=28227,contexts=19,measured_windows=0,host_groups_and_sessions=651,no_Julia=True)))
