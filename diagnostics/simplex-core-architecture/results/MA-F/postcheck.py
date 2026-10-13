"""New failure-provenance checks. Never execute historical auditors or Julia."""
from pathlib import Path
import hashlib,json,subprocess,time,tomllib,shutil
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-F';E=D.parent/'MA-E';O=R/'.superpowers/simplex-core-architecture/MA-F/attempt-1'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
def save(n,x):
 with (D/n).open('x') as f:json.dump(x,f,indent=2);f.write('\n')
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
pre=read(D/'preflight.json');proc=read(O/'red/process.json');inv=read(O/'invocation.json');seal=read(E/'execution-seal.json');res=read(E/'attempt-reserved.json');pins=read(E/'admission-pins-reviewed.json');raw=tomllib.loads((O/'red/raw.toml').read_text());checks={}
groups=sorted(set(pre['groups']+[proc[k][t] for k in ('runner','child') for t in ('pgid','sid')]))
matches=[];boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
for p in Path('/proc').glob('[0-9]*'):
 try:
  s=(p/'stat').read_text();f=s[s.rfind(')')+2:].split()
  if int(f[2]) in groups or int(f[3]) in groups or (p/'comm').read_text().strip().lower().startswith('julia'):
   matches.append(dict(pid=int(p.name),pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),boot_id=boot,command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except (FileNotFoundError,ProcessLookupError):pass
checks['full46groups_ANDsessions_noJulia']=len(groups)==46 and not matches and boot==pre['boot_id']==proc['runner']['boot_id']==proc['child']['boot_id']
checks['expected_driver_error_preserved']=len(raw['errors'])==1 and 'UndefVarError: `push_testset` not defined in `Test`' in raw['errors'][0] and 'driver.jl:53' in raw['errors'][0]
checks['RED_not_test_failures']=raw['stage']=='red' and raw['side']=='reference' and raw['records']==[] and not any(k in raw for k in ('tests','counts','compare_metrics','full_metrics'))
checks['process_failure_preserved']=proc['returncode']==1 and proc['reason']=='exit1' and proc['pins_unchanged'] is True and inv['all_passed'] is False and inv['stages']==[] and inv['errors']==["ValueError('terminal guard failure')"]
expected={'invocation.json','red.guard.log','red/current.json','red/pins.json','red/process.json','red/raw.toml','red/resources.jsonl','red/run.log'}
checks['only_red_launched_no_audits_qualification_cost']={str(p.relative_to(O)) for p in O.rglob('*') if p.is_file()}==expected
checks['seal_reservation_command_link']=proc['command']==seal['commands'][0]==res['commands'][0] and res['commands']==seal['commands'] and len(seal['commands'])==22 and res['seal_sha256']==inv['seal_sha256']==sha(E/'execution-seal.json') and inv['reservation_sha256']==sha(E/'attempt-reserved.json') and proc['pins_sha256']==inv['pin_sha256']==res['pin_sha256']==seal['pin_sha256']==sha(E/'admission-pins-reviewed.json')
checks['all1761_launch_pins_unchanged']=len(pins['inventory'])==1761 and all(sha(p)==v['sha256'] and str(Path(p).resolve())==v['resolved'] for p,v in pins['inventory'].items())
checks['raw_pin_copy_exact']=sha(O/'red/pins.json')==sha(E/'admission-pins-reviewed.json')
checks['loaded_reference_source']=raw['source']==str(E/'overlays/reference/src/JSimplex.jl') and raw['version']=='1.13.0' and raw['ambient_ok'] is True
checks['protected_unchanged']=all(sha(p)==v for p,v in pre['protected_sha256'].items())
refs={k:git('rev-parse',v) for k,v in [('head','HEAD'),('master','master')]};refs['primary']=subprocess.check_output(['git','-C','/home/jspitz/JSimplex.jl','rev-parse','HEAD'],text=True).strip();refs['remote']=git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture')
checks['all_refs_unchanged']=all(refs[k]==pre['refs'][k] for k in refs)
checks['actual_src_test_Project_CI_unchanged']=not git('diff','HEAD','--','src','test','Project.toml','.github')
samples=[json.loads(s) for s in (O/'red/resources.jsonl').read_text().splitlines()]
checks['resource_caps']=len(samples)==4 and all(s['available_kib']>=6*1024**2 and s['swap_used_kib']<=1024**2 for s in samples+[proc['terminal_memory']]) and proc['elapsed_including_launch']<30 and inv['elapsed']<750
T=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia/stdlib/v1.13/Test/src/Test.jl');src=T.read_text();driver=(E/'driver.jl').read_text()
checks['source_localizes_pre_include_error']='push_testset' not in src and 'pop_testset' not in src and 'macro with_testset(ts, expr)' in src and 'const CURRENT_TESTSET = ScopedValue' in src and driver.index('Test.push_testset(ts)')<driver.index('Base.include(Main,joinpath(@__DIR__,"tests-instrumented.jl"))')
# New read-time binding is not a retroactive launch pin.
start=src.index('const CURRENT_TESTSET =');end=src.index('\n"""\nPrint testset entry',start)
with (D/'installed-Test-context.txt').open('x') as f:f.write(src[start:end].rstrip()+'\n')
shutil.copytree(O,D/'attempt-1')
checks['all8_portable_files_byteidentical']=all(sha(O/n)==sha(D/'attempt-1'/n) for n in expected)
inputs=[D/'preflight.py',D/'preflight.json',D/'seal-check.json',D/'postcheck.py',D/'installed-Test-context.txt',E/'execution-seal.json',E/'attempt-reserved.json',E/'driver.jl',E/'test-collector.jl',T]+[D/'attempt-1'/n for n in sorted(expected)]
save('postcheck.json',dict(all_passed=all(checks.values()),checks=checks,host=dict(time=time.time(),boot_id=boot,groups=groups,matches=matches,refs=refs),resources=dict(samples=len(samples),minimum_available_kib=min(s['available_kib'] for s in samples),maximum_swap_kib=max(s['swap_used_kib'] for s in samples),terminal=proc['terminal_memory'],inclusive_guard_seconds=proc['elapsed_including_launch'],inclusive_launcher_seconds=inv['elapsed']),sha256={str(p):sha(p) for p in inputs},scope='Failure provenance PASS only. RED/qualification/cost are NOT accepted. No Julia or original auditor rerun. Test.jl is a new read-time binding, not a launch pin.'))
print(json.dumps(checks,indent=2))
if not all(checks.values()):raise SystemExit('postcheck failed')
