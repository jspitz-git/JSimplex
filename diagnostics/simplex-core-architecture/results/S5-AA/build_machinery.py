"""One-time source generation from read-only historical templates; no old imports."""
from pathlib import Path
H=Path(__file__).resolve().parent;U=H.parent/'S5-U';Y=H.parent/'S5-Y'
def save(n,s):
 with (H/n).open('x') as f:f.write(s)
s=(U/'common_final.py').read_text().replace("import hashlib,json,time,sys","import hashlib,json,time,sys,os,math,subprocess")
s=s.replace("T=H.parent/'S5-T'","T=H.parent/'S5-Z'").replace('S5-U','S5-AA').replace("C=T/'candidate.jl'","C=T/'candidate-reviewed.jl'").replace('simplex_precision_tests.jl','simplex_start_state_tests.jl')
s=s.replace('357a976f5fc984025452ee4b259f2fc1f140885212f5b40ff71e072ebfab3684','ce256932a4bbda14bb9c55678525d6506a8e63732683442def57b22873b0415f')
import hashlib
s=s.replace('b864b39bde32ee9a1c2b85ef57fdc6efd6d69a59c3a56571cdf62d8659bf4ba5',hashlib.sha256((H/'original-test.jl').read_bytes()).hexdigest()).replace('2026-10-13-basis-initialization-stop-test-integration.md','2026-10-13-crash-fallback-observer-test-integration.md')
s=s.replace('71824,71826}', '71824,71826,75902,75907,76742,76746,84681,84689}')
for old,new in [('common_final.py','common.py'),('launcher-final.py','launcher.py'),('audit-final.py','audit.py'),('required-final-paths.json','required-paths.json'),('admission-acceptance-final.json','acceptance.json'),('admission-final-pins.json','admission-pins.json'),('admission-final-review.md','admission-review.md')]:s=s.replace(old,new)
a=s.index('def dump(');b=s.index('def root(',a);y=(Y/'common.py').read_text();s=s[:a]+y[y.index('def dump('):y.index('def absent(')]+s[b:]
a=s.index('def essentials():');b=s.index('def required(',a)
s=s[:a]+'''INITIAL_REFS={str(R):'8e5a4ad61b35cc68f852763affb5ec919533b88b',str(M):'2b546e946ddb7fdb6c0092df9cc19f566e301aa2'}
def essentials():return [C,G,W,W.parents[3]/'.superpowers/basis-chain-cost/julia.sh',PLAN,*[H/n for n in ('common.py','launcher.py','audit.py','driver.jl','schema.json','expected.toml','insertions.toml','expected-suffix.jl','admission.md','host-before.json','source-preparation.json','prepare.py','build_machinery.py','guard-source.json','entry.py','entry.json','entry-2.py','entry-2.json','original-test.jl','failure_tests.py','failure-tests.json','freeze_requirements.py','postcheck.py')]]
'''+s[b:]
s=s.replace("assert all(sha(k)==v for k,v in a['sha256'].items());return a", "assert all(sha(k)==v for k,v in a['sha256'].items())\n assert a.get('initial_refs')==INITIAL_REFS and a.get('candidate_sha256')==EXPECTED\n review=(H/'admission-review.md').read_text();assert 'Verdict: ACCEPTED' in review and 'Unresolved findings: []' in review\n return a")
s=s.replace("('audit.json','postcheck.json','review.md','pins.json')}\n return paths", "('audit.json','postcheck.json','review.md','pins.json')}|{str(H/'integration.json'),str(H/'master/admission-review.md')}\n return paths")
s=s.replace("and a.get('refs')==refs and", "and a.get('refs')==refs and (refs==INITIAL_REFS if stage=='green' else refs==read(H/'integration.json')['refs']) and a.get('command')==command(stage) and")
s=s.replace("assert 'ACCEPTED' in review", "assert 'Verdict: ACCEPTED' in review")
s=s.replace("if stage=='master':\n  evidence=green_evidence();", "if stage=='master':\n  integration=read(H/'integration.json');review=(H/'master/admission-review.md').read_text()\n  assert 'Verdict: ACCEPTED' in review and 'Unresolved findings: []' in review\n  assert integration['candidate_sha256']==EXPECTED and integration['refs']==current_refs()\n  for p in (R,M):\n   assert subprocess.check_output(['git','-C',str(p),'diff-tree','--no-commit-id','--name-only','-r','HEAD'],text=True).splitlines()==[REL]\n   assert subprocess.check_output(['git','-C',str(p),'show','HEAD:'+REL])==C.read_bytes()\n  evidence=green_evidence();")
s=s.replace("and res.get('pins_sha256')==pin_hash and log==process", "and res.get('pins_sha256')==pin_hash and res.get('output')==str(out(stage)) and res.get('launch_binding_sha256')==sha(h/'launch-binding.json') and log==process")
s+='\n'+y[y.index('def terminal_ok('):y.index('def invocation_ok(')]+ '\n'+y[y.index('def invoke('):]
s+='''
def guard_command(stage):return [sys.executable,str(G),'run',str(stage_files(stage)/'pins.json'),str(out(stage)),'--seconds','120','--',*command(stage)]
'''
save('common.py',s)
s=(U/'launcher-final.py').read_text().replace('common_final','common')
for old,new in [('admission-final-pins.json','admission-pins.json'),('admission-final-review.md','admission-review.md'),('admission-acceptance-final.json','acceptance.json'),('required-final-paths.json','required-paths.json')]:s=s.replace(old,new)
a=s.index(" assert not out(stage).exists();dump")
s=s[:a]+''' assert not out(stage).exists()
 dump(h/'attempt-reserved.json',dict(time_ns=time.time_ns(),command=command(stage),pins_sha256=sha(pins),output=str(out(stage)),launch_binding_sha256=sha(h/'launch-binding.json')))
 inv=invoke(guard_command(stage),h/'guard-output.log',h/'guard-invocation.json',root(stage),absent())
 raise SystemExit(0 if type(inv['returncode']) is int and inv['returncode']==0 and 'error' not in inv else 1)
else:raise ValueError(mode)
'''
s=s.replace("files|={str(h/'stage-acceptance.json')};stage_accepted(stage)","files|={str(h/'stage-acceptance.json')};stage_accepted(stage)\n  if stage=='master':files|={str(H/'integration.json'),str(h/'admission-review.md')}")
s=s.replace("if mode in ('freeze-admission','freeze-launch'):","if mode=='freeze-admission':assert current_refs()==INITIAL_REFS and sha(R/REL)==OLD and sha(M/REL)==OLD\nif mode in ('freeze-admission','freeze-launch'):")
save('launcher.py',s)
