from pathlib import Path
import json,hashlib,subprocess,os,datetime,ast
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-quality-local/2026-10-27');Q=D/'comparison-2';M=Path('/home/jspitz/JSimplex.jl')
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(root,n):return json.loads((root/n).read_text())
pins=read(Q,'pins.json');original=read(D,'pins.json');admission=read(D,'admission.json');review=read(D,'result-review.json')
assert review['accepted'] is False and review['test_counts']==dict(passed=63389,failed=2,total=63391)
for n,v in pins['inventory'].items():assert str(Path(n).resolve(strict=True))==v['resolved'] and sha(n)==v['sha256'],n
for tree in pins['trees']:assert {str(p) for p in Path(tree).rglob('*') if p.is_file()}=={n for n in pins['inventory'] if Path(n).is_relative_to(tree)}
for n,v in original['inventory'].items():assert pins['inventory'][n]==v
for n,v in admission['bindings'].items():assert sha(n)==v
for n in ['Reference.jl','CandidateA.jl','CandidateB.jl','CandidateAB.jl','CandidateC.jl','common.py','launch.py','protected-before.json','environment.json']:assert (Q/n).read_bytes()==(D/n).read_bytes(),n
for n in ['entry_gate.py','guard_reviewed.py','supervisor_reviewed.py']:assert (Q/'guard'/n).read_bytes()==(D/'guard'/n).read_bytes()
old=(D/'fixtures.jl').read_text();new=(Q/'fixtures.jl').read_text();find='edge===:nonfinite&&scope===:audit&&@test z[1]===:value&&z[2]===:corrected';replacement='edge===:nonfinite&&scope===:audit&&@test z[1]===:value&&z[2]===(T<:AbstractFloat ? :corrected : :accurate)'
assert old.count(find)==new.count(replacement)==1 and old.replace(find,replacement)==new and new.replace(replacement,find)==old
old=(D/'driver.jl').read_text();new=(Q/'driver.jl').read_text();start='@testset "Local quality whole-function comparison" begin';write='open(ARGS[1],"w") do io;TOML.print(io,Dict("cells"=>CELLS,"preparation"=>PREP));end\n';assert old.replace(start,'try\n'+start).replace(write,'finally\n '+write+'end\n')==new
assert new.replace('try\n'+start,start).replace('finally\n '+write+'end\n',write)==old
contract=read(Q,'contract.json');prior=read(D,'contract.json');expected=json.loads(json.dumps(prior));expected['command']=[s.replace(str(D/'driver.jl'),str(Q/'driver.jl')).replace(str(D/'output/results.toml'),str(Q/'output/results.toml')) for s in expected['command']];assert contract==expected
assert contract['cases']==2172 and contract['measured_windows']==39096 and contract['shared_limit_seconds']==600
for f in [*Q.glob('*.py'),*(Q/'guard').glob('*.py')]:ast.parse(f.read_text())
auditor=(Q/'audit.py').read_text();assert str(Q) in auditor and "sink']==1" in auditor and "sink']==4" in auditor
for n,v in {**read(Q,'protected-before.json')['files'],**read(Q,'protected-before.json')['indexes']}.items():assert sha(n)==v,n
refs=subprocess.check_output(['/usr/bin/git','-C',str(M),'rev-parse','HEAD','master','origin/master'],env=dict(os.environ,GIT_OPTIONAL_LOCKS='0')).decode().splitlines();assert set(refs)=={'ca64312f7f74b1d7bec047718399f229674b3e1d'}
assert not any((Q/n).exists() for n in ['output','reservation.json'])
h=read(Q,'host-seed.json');groups=set(h['groups']);assert len(groups)==587;assert groups==set(read(D,'host-seed.json')['groups'])|{75010,75011};assert h['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip();procs=[]
for proc in Path('/proc').glob('[0-9]*'):
 try:
  st=(proc/'stat').read_text().rsplit(')',1)[1].split();cmd=[v.decode(errors='replace') for v in (proc/'cmdline').read_bytes().split(b'\0') if v];comm=(proc/'comm').read_text().strip();assert int(st[2]) not in groups and int(st[3]) not in groups;assert not any(Path(v).name.lower().startswith('julia') for v in [comm]+cmd[:1]);procs.append(dict(pid=int(proc.name),pgid=int(st[2]),sid=int(st[3]),start_ticks=int(st[19]),command=cmd))
 except (FileNotFoundError,ProcessLookupError):pass
mem={l.split(':')[0]:int(l.split()[1]) for l in Path('/proc/meminfo').read_text().splitlines()};assert mem['MemAvailable']>=6*1024**2 and mem['SwapTotal']-mem['SwapFree']<=1024**2
r=dict(accepted=True,findings=[],inventory_files_verified=len(pins['inventory']),original_inventory_files_frozen=len(original['inventory']),original_failed_review_frozen=True,exact_five_clones=True,fixture_one_status_exact_inverse=True,driver_finally_exact_inverse=True,no_removed_test=True,no_candidate_change=True,contexts=19,cells=2172,measured_windows=39096,limit_seconds=600,historical_groups=587,groups=sorted(groups),fresh_no_Julia=True,processes=procs,boot_id=h['boot_id'],available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree'],checked_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),checker_sha256=sha(__file__))
with Path('/tmp/local-quality-comparison2-independent-evidence.json').open('x') as f:json.dump(r,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({k:v for k,v in r.items() if k not in ['processes','groups']}))
