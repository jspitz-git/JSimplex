"""One-shot offline GREEN-only controls/overlay; no Julia or old script execution."""
from pathlib import Path
import hashlib,json,shutil
R=Path(__file__).resolve().parents[4];D=Path(__file__).resolve().parent
A=D.parent/'DIRECT-LU-ADMISSION';P=D.parent/'DIRECT-LU-TEST-REPAIR'
W=R/'.superpowers/direct-lu-markowitz-green-2/candidate'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def req(x,s):
 if not x:raise ValueError(s)
def put(p,s):
 with p.open('x') as f:f.write(s)
def save(p,v):put(p,json.dumps(v,indent=2)+'\n')
def replace(s,a,b):
 req(s.count(a)==1,'Nonunique replacement: '+a);return s.replace(a,b)
req(json.loads((D/'host.json').read_text())['matches']==[],'Host not clear')
m=[]
for n,out in [('diagnostics/simplex-core-architecture/STATUS.md','STATUS.md.before-green-admission'),('docs/superpowers/plans/2026-10-11-simplex-core-architecture.md','roadmap.md.before-green-admission')]:
 (D/out).write_bytes((R/n).read_bytes())
 for rec in ('closure.json','publication.json'):
  req(json.loads((P/rec).read_text())['sha256'][n]==sha(R/n),'Continuation mismatch')
  m.append(dict(record=str((P/rec).relative_to(R)),key=n,preserved_path=str((D/out).relative_to(R)),sha256=sha(R/n)))
save(D/'continuation.json',dict(mappings=m,older_mappings='Unchanged'))
oldroot=R/'.superpowers/direct-lu-markowitz-admission/candidate'
req(not W.exists(),'Overlay exists');shutil.copytree(oldroot,W)
(W/'correctness.jl').write_bytes((P/'correctness.jl').read_bytes())
# RED source retained as immutable input only; there is no admitted RED command.
for n in ('guard.py','supervisor.py'):(D/n).write_bytes((A/n).read_bytes())
(D/'driver.jl').write_bytes((P/'driver.jl').read_bytes());shutil.copytree(A/'focused',D/'focused')
cfg=json.loads((A/'config.json').read_text())['phases']['green'];oldproject=cfg['project'];oldout=cfg['output']
cfg['project']=str(W);cfg['output']=str(D/'green-run');cfg['groups'][0]['counts'][0]=130
cfg['command']=[x.replace(oldproject,str(W)).replace(oldout,cfg['output']).replace(str(A/'driver.jl'),str(D/'driver.jl')) for x in cfg['command']]
save(D/'config.json',dict(phases=dict(green=cfg),scope='UNEXECUTED GREEN-only, one <=90s attempt after independent exact admission; RED never rerun'))
save(D/'staging.json',dict(root=str(W),original_root=str(oldroot),changed_paths=['correctness.jl'],original_sha256={str(p.relative_to(oldroot)):sha(p) for p in sorted(oldroot.rglob('*')) if p.is_file()},correctness_sha256=sha(P/'correctness.jl'),driver_sha256=sha(P/'driver.jl'),focused=json.loads((A/'staging.json').read_text())['focused']))
control=(A/'control_reviewed.py').read_text();start=control.index('def phase_config(');end=control.index('def validate_review(',start)
new='''def phase_config(phase):
    req(phase=='green','Only corrected GREEN is admitted; RED/retry forbidden')
    package=rd(D/'config.json');req(set(package['phases'])=={'green'},'Unexpected phase')
    c=package['phases'][phase]
    req(c['seconds']==90 and c['expected_exit']==0,'Time/exit contract changed')
    project=str(R/'.superpowers/direct-lu-markowitz-green-2/candidate')
    req(c['project']==project and c['output']==str(D/'green-run'),'Project/output path changed')
    expected=[('exports',130),('rejections',66),('orientation',12),('normalization',200),('lifecycles',18272),('fallback',288),('markowitz-sparse.jl',62),('markowitz-fill.jl',8),('markowitz-triangular.jl',144),('prepared.jl',195),('lifecycle.jl',96),('stability.jl',84)]
    req(c['groups']==[dict(name=n,counts=[v,0,0,0]) for n,v in expected],'Group schedule changed')
    wrapper='/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh'
    command=['/bin/bash',wrapper,'--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--project='+project,str(D/'driver.jl'),'green',str(D/'green-run'),project]
    req(c['command']==command,'Command changed')
    return c
'''
put(D/'control.py',control[:start]+new+control[end:])
prior=replace(control,'D=Path(__file__).resolve().parent;R=D.parents[3]',"R=Path(__file__).resolve().parents[4];D=R/'diagnostics/simplex-core-architecture/results/DIRECT-LU-ADMISSION'")
put(D/'prior_control.py',prior)
put(D/'prior_evidence.py',(A/'evidence_reviewed.py').read_text().replace('from control_reviewed import *','from prior_control import *'))
e=(A/'evidence_reviewed.py').read_text().split('\ndef validate_predecessor():')[0].replace('from control_reviewed import *','from control import *')
e+='''
def validate_predecessor():
    # New read-only validator of old exact RED records, not an old auditor rerun.
    import prior_evidence
    paths=prior_evidence.validate_predecessor()
    repair=D.parent/'DIRECT-LU-TEST-REPAIR'
    review=rd(repair/'review.json')
    req(review.get('accepted') is True and review.get('findings')==[],'Repair not accepted')
    expected=rd(D/'repair-bindings.json')
    req(sha(repair/'review.json')==expected['review_sha256'],'Repair review changed')
    req(review['sha256']==expected['sha256'],'Repair review membership changed')
    req(all(sha(Path(n) if Path(n).is_absolute() else R/n)==h for n,h in review['sha256'].items()),'Repair binding changed')
    return paths+[repair/'review.json',repair/'review.md']
'''
put(D/'evidence.py',e)
r=json.loads((P/'review.json').read_text());save(D/'repair-bindings.json',dict(review_sha256=sha(P/'review.json'),sha256=r['sha256']))
for src,dest in [('seal-reviewed.py','seal.py'),('launch-reviewed.py','launch.py'),('audit_reviewed.py','audit.py')]:
 s=(A/src).read_text().replace('control_reviewed','control').replace('evidence_reviewed','evidence').replace('audit_reviewed','audit').replace('preparation-pins-reviewed.json','preparation-pins.json').replace('required-reviewed.json','required.json').replace('preparation-review-final.json','preparation-review.json')
 if dest=='seal.py':
  s=replace(s,"    groups=rd(D/'host.json')['groups'];extra=[]\n    if phase=='green':\n        extra=validate_predecessor()\n        groups+=rd(D/'red-posthost.json')['groups']","    groups=rd(D/'host.json')['groups'];extra=validate_predecessor()")
 if dest=='launch.py':s=replace(s,"    if phase=='green':validate_predecessor()","    phase_config(phase);validate_predecessor()")
 put(D/dest,s)
save(D/'source-lineage.json',dict(unchanged={n:sha(A/n) for n in ('guard.py','supervisor.py')},prior_control_original=sha(A/'control_reviewed.py'),prior_evidence_original=sha(A/'evidence_reviewed.py'),old_controls={n:sha(A/n) for n in ('seal-reviewed.py','launch-reviewed.py','audit_reviewed.py')},repair_test=sha(P/'correctness.jl'),repair_driver=sha(P/'driver.jl')))
print(json.dumps(dict(overlay=str(W),expected=19557,groups=12,phases=['green'],continuation_mappings=len(m))))
