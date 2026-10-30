from pathlib import Path
import ast,hashlib,json,subprocess
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');P=W/'diagnostics/dual-recovery-devex-cost-admission/2026-10-30';O=W/'diagnostics/dual-recovery-devex-task4/2026-10-30';R=W/'.superpowers/dual-recovery-devex-task4/cost-1';T=Path('/tmp/devex-candidate-cost-run-20261030');checks={};bindings={}
def text(p):
 p=Path(p);b=p.read_bytes();bindings[str(p)]=hashlib.sha256(b).hexdigest();return b.decode()
def read(p):return json.loads(text(p))
def ck(k,v):
 assert type(v) is bool;checks[k]=v
 if not v:raise AssertionError(k)
def git(*a):return subprocess.check_output(['git','-C',str(W),*a],text=True).strip()
main=read('/tmp/devex-candidate-cost-result-independent.json');ck('main accepted',main['accepted'] is True and len(main['checks'])==5731 and all(v is True for v in main['checks'].values()))
green=W/'diagnostics/dual-recovery-devex-green-fixture-preparation/2026-10-30/prepared/overlays/candidate';files=sorted(p for p in (O/'overlays/candidate').rglob('*') if p.is_file());ck('GREEN2 membership74',{p.relative_to(green) for p in green.rglob('*') if p.is_file()}=={p.relative_to(O/'overlays/candidate') for p in files})
for p in files:ck('candidate GREEN2 '+str(p.relative_to(O/'overlays/candidate')),text(p)==text(green/p.relative_to(O/'overlays/candidate')))
tree={row.split('\t',1)[1]:row.split()[2] for row in git('ls-tree','-r','master','--','src').splitlines()};refsrc=list((O/'overlays/reference/src').rglob('*.jl'));ck('reference71src',len(refsrc)==71)
for p in refsrc:
 b=text(p).encode();ck('master src '+str(p.relative_to(O/'overlays/reference')),hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==tree[str(p.relative_to(O/'overlays/reference'))])
diffs=[str(p.relative_to(O/'overlays/candidate')) for p in files if text(p)!=text(O/'overlays/reference'/p.relative_to(O/'overlays/candidate'))];ck('only three source changes',set(diffs)=={'src/simplex_numerics.jl','src/simplex_recovery.jl','src/simplex_pivot.jl'})
pubpaths={str(W/n) for folder in [O,*[W/('diagnostics/'+n+'/2026-10-30') for n in ('dual-recovery-devex-task4-red','dual-recovery-devex-task4-green','dual-recovery-devex-green-fixture-preparation','dual-recovery-devex-green2-admission','dual-recovery-devex-green2-result')],P] for n in read(folder/'publication.json')['expected_names']}
seal=read(R/'reference-cost/seal.json');j=Path(seal['command'][0]);rt=j.parents[1];required=pubpaths|{seal['guard_python'],str(j),str(rt/'lib/libjulia.so.1.13.0'),str(rt/'lib/julia/sys.so'),str(rt/'lib/julia/libjulia-internal.so.1.13.0'),str(rt/'share/julia/base/timing.jl')};ck('exact566 canonical required paths',set(read(R/'reference-cost/pins.json')['inventory'])==required)
for phase in ('reference-cost','candidate-cost'):
 done=read(R/phase/'completion.json');seal=read(R/phase/'seal.json');sup=read(R/phase/'supervisor.json');ck(phase+'typed complete clock',done['supervisor_accepted'] is True and type(done['limit_seconds']) is int and done['limit_seconds']==1800 and done['total_inclusive_seconds']==seal['used_seconds']+done['elapsed_inclusive_seconds']<=1800 and 0<sup['elapsed_seconds']<=done['elapsed_inclusive_seconds'])
for n in ('preflight.json','prelaunch-full-host.json'):
 a=read(T/n);h=a['host'] if n=='preflight.json' else a;ck('prelaunch739 '+n,len(h['checked_groups'])==739 and h['conflicts']==[] and h['still_active_current_launcher']==[] and h['refs']['HEAD']=='14720147d8850525c0603921064dfe3ba83d3fcb')
a=read('/tmp/devex-candidate-cost-numerical-admission-source-check-v2-result.json');ck('preserved15 source checks',len(a['checks'])==15 and all(type(v) is bool and v for v in a['checks'].values()))
old=text('/tmp/devex-candidate-cost-numerical-admission-source-check.py');new=text('/tmp/devex-candidate-cost-numerical-admission-source-check-v2.py');ck('only extractor and output path correction',new==old.replace("removesuffix('end')","removesuffix('end # module')").replace('source-check-result.json','source-check-v2-result.json'));ck('original failure preserved','AssertionError: legacy_kernel_exact_qualification_only' in text('/tmp/devex-candidate-cost-numerical-admission-source-check.log'))
close=text(T/'close-publish.py');ast.parse(close)
ck('closure original reportwriters preserved',"for src,digest in read(D/'report-writer-fix.json')['bindings'].items():" in close and "need(sha(src)==sha(dst)==digest,'report writer copy')" in close)
ck('closure complete review copy verification',"for src,v in table.items():" in close and "need(sha(src)==v,'review original binding '+src)" in close and "all(sha(n)==sha(maps.get(n,n))==v for n,v in table.items())" in close)
ck('closure review scope flags',"review['scope']=='candidate_cost_result_only'" in close and "review['production_admission'] is False" in close and "all(type(v) is bool and v for v in review['checks'].values())" in close)
ck('closure full host and refs',"len(h['checked_groups'])==742" in close and "set(h['checked_groups'])==C.expected_groups('candidate-cost',h['boot_id'],True)" in close and "not h['still_active_current_launcher']" in close and "C.validate_closed('reference-cost')" in close and "C.validate_closed('candidate-cost')" in close)
ck('closure exact staged names and blobs',"need(git('diff','--cached','--name-only').splitlines()==names,'exact staged names')" in close and "need(all(git('hash-object',str(W/n))==v for n,v in blobs.items()),'exact staged blobs')" in close)
ck('closure no writer execution',"write-report" not in close and 'subprocess.run([\'git\'' in close)
text(__file__)
with Path('/tmp/devex-candidate-cost-result-supplement.json').open('x') as f:json.dump(dict(accepted=True,checks=checks,bindings=bindings),f,indent=2);f.write('\n')
print(json.dumps(dict(accepted=True,checks=len(checks),bindings=len(bindings))))
