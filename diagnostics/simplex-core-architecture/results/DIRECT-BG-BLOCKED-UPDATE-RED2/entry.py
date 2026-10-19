"""Fresh host/source entry for one reviewed RED2 attempt; no numerical launch."""
from pathlib import Path
import sys,json
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');H=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-RED2-HARNESS';D=H.with_name('DIRECT-BG-BLOCKED-UPDATE-RED2');sys.path.insert(0,str(H));import control as c
h=c.full_host();h.update(memory=c.guard.memory(),branch=c.git('branch','--show-current'),status=c.git('status','--porcelain'))
c.save(D/'host-entry.json',h)
checks={'host':c.host_safe(h),'resources':not c.guard.pressure(h['memory']),'head':h['head']=='b6c37d08e94fc3e6c6b28a967a8f995549929e94','branch':h['branch']=='codex/simplex-core-architecture','clean_tracked':not c.git('diff','HEAD','--name-only'),'fresh_red2':not (H/'runs/red300').exists() and not (H/'outers/red300').exists()}
for name,fn in [('environment',c.validate_environment),('sources',c.validate_sources),('preparation',c.preparation)]:
 try:fn();checks[name]=True
 except Exception as e:checks[name]=False;checks[name+'_error']=repr(e)
checks['published_preparation']=c.bindings(c.rd(H/'publication.json'))
c.save(D/'entry.json',dict(all_passed=all(v is True for k,v in checks.items() if not k.endswith('_error')),checks=checks,request='One independently admitted RED2 attempt in repaired master stage; exactly six N026 failures,300s. No GREEN.',sha256={str(H/n):c.sha(H/n) for n in ['review.json','preparation-pins.json','ADMISSION.md','driver.jl','control.py','guard.py','oracle.py','audit.py','outer.py','seal.py','launch.py','publication.json']}))
print(json.dumps(dict(checks=checks,memory=h['memory'],matches=h['matches'],groups=len(h['groups']),boot=h['boot_id'])));c.require(c.rd(D/'entry.json')['all_passed'],'Entry refusal')
