from pathlib import Path
import sys,json
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');H=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-HARNESS';D=H.with_name('DIRECT-BG-BLOCKED-UPDATE-RED')
sys.path.insert(0,str(H));import control as c
c.require(not D.exists(),'Fresh RED diagnostics path');D.mkdir();(D/'entry.py').write_bytes(Path(__file__).read_bytes())
h=c.full_host();h.update(memory=c.guard.memory(),branch=c.git('branch','--show-current'),status=c.git('status','--porcelain'))
c.save(D/'host-entry.json',h)
checks={'host':c.host_safe(h),'resources':not c.guard.pressure(h['memory']),'head':h['head']=='6900c4473a39411b074109fb6362fd8753ca10d0','branch':h['branch']=='codex/simplex-core-architecture','clean_tracked':not c.git('diff','HEAD','--name-only'),'fresh_red':not (H/'runs/red300').exists() and not (H/'outers/red300').exists()}
for name,fn in [('environment',c.validate_environment),('sources',c.validate_sources),('preparation',c.preparation)]:
 try:fn();checks[name]=True
 except Exception as e:checks[name]=False;checks[name+'_error']=repr(e)
c.save(D/'entry.json',dict(all_passed=all(v is True for k,v in checks.items() if not k.endswith('_error')),checks=checks,request='One independently admitted RED attempt, expected6 named failures,300s; no GREEN.',sha256={str(H/n):c.sha(H/n) for n in ['review.json','preparation-pins-reviewed.json','ADMISSION.md','driver.jl','control.py','guard.py','oracle.py','audit.py','outer.py','seal.py','launch.py']}))
print(json.dumps({'checks':checks,'memory':h['memory'],'matches':h['matches'],'boot':h['boot_id'],'groups':len(h['groups'])}));c.require(c.rd(D/'entry.json')['all_passed'],'Entry refusal; no launch')
