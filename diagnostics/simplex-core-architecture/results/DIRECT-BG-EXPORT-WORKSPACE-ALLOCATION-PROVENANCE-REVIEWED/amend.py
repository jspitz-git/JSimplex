from pathlib import Path
import sys,json,hashlib,subprocess
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');P=R/'diagnostics/simplex-core-architecture/results';A=P/'DIRECT-BG-EXPORT-WORKSPACE-ALLOCATION-PROVENANCE';D=P/'DIRECT-BG-EXPORT-WORKSPACE-ALLOCATION-PROVENANCE-REVIEWED'
sys.path.insert(0,str(A));import control as c
def put(n,s):(D/n).open('x').write(s)
def save(n,j):put(n,json.dumps(j,indent=2)+'\n')
c.require(not (A/'runs/profile300/reservation.json').exists(),'Initial numerical attempt must not exist')
c.require(any('reject' in p.name for p in A.glob('*review*.json')) or any('reject' in p.read_text().lower() for p in A.glob('*review*.md')),'Rejected review required')
h=c.full_host();h.update(memory=c.guard.memory(),remote=c.git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'),status=c.git('status','--porcelain'));c.require(c.host_safe(h) and not c.guard.pressure(h['memory']),'Host refusal')
D.mkdir(exist_ok=False);save('host.json',h)
copied=['guard.py','supervisor.py','analysis.py','inputs.json','inputs.toml','baseline.json','runtime-inputs-complete.json','environment.json','control.py','evidence.py','helpers.jl','helper-inverse.json','stages.json','loaded-paths.json','seal.py','launch.py','audit.py','authorization.json']
for n in copied:put(n,(A/n).read_text())
old=(A/'driver.jl').read_text();c.require(old.count('summary(')==3,'Exact naming occurrences')
new=old.replace('summary(','bg_alloc_summary(');put('driver.jl',new)
put('ADMISSION.md',(A/'ADMISSION.md').read_text()+'\nInitial offline review rejected the unexecuted driver name summary, exported by Base. This separate corrected package changes only its definition and two call sites to bg_alloc_summary. Initial driver/seal/rejection are preserved. No initial Julia process/reservation existed. This is the first numerical attempt if separately admitted.\n')
checks={'exact_three_name_inverse':new.replace('bg_alloc_summary(','summary(')==old,'old_attempt_absent':not (A/'runs/profile300/reservation.json').exists(),'all_copied_bytes':all((D/n).read_bytes()==(A/n).read_bytes() for n in copied),'unchanged_helpers':(D/'helpers.jl').read_bytes()==(A/'helpers.jl').read_bytes(),'no_candidate_change':c.guard.pins_match(c.rd(A/'runs/profile300/sealed.json'))}
for p in D.glob('*.py'):compile(p.read_text(),str(p),'exec')
checks['Python_only_syntax']=True;save('source-check.json',dict(all_passed=all(checks.values()),checks=checks,sha256={str(A/'driver.jl'):c.sha(A/'driver.jl'),str(D/'driver.jl'):c.sha(D/'driver.jl')},scope='Only three naming occurrences changed; no Julia or old auditor rerun'));c.require(all(checks.values()),'Amendment failed')
put('amend.py',Path(__file__).read_text())
files=set(c.rd(A/'required-paths.json')['paths'])|{str(p) for p in A.rglob('*') if p.is_file()}|{str(p) for p in D.iterdir() if p.is_file()}|{str(D/'required-paths.json')}
save('required-paths.json',dict(paths=sorted(files)));save('preparation-pins.json',dict(sha256={p:c.sha(p) for p in sorted(files)}))
print(json.dumps(dict(checks=len(checks),pins=len(files))))
subprocess.run(['/usr/bin/python3','-B',str(D/'seal.py'),'profile300'],cwd=R,check=True)
