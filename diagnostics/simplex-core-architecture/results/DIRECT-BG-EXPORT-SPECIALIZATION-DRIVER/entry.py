from pathlib import Path
import importlib.util,sys,json
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');E=R/'diagnostics/simplex-core-architecture/results';P=E/'DIRECT-BG-EXPORT-WORKSPACE-ALLOCATION-PROVENANCE-REVIEWED';T=E/'DIRECT-BG-EXPORT-SPECIALIZATION-TASK1';D=E/'DIRECT-BG-EXPORT-SPECIALIZATION-DRIVER'
sys.path.insert(0,str(P));s=importlib.util.spec_from_file_location('entry_control',P/'control.py');c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
h=c.full_host(c.rd(T/'host-closure.json')['groups']);h['remote']=c.git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture');h['status']=c.git('status','--porcelain');h['branch']=c.git('branch','--show-current')
c.require(c.host_safe(h),'unsafe host');c.require(h['head']=='b504ea4fbf3bc40a9fa87cfc0b9a7dd69cc821cd' and h['master']==c.MASTER,'refs');c.require(h['branch']=='codex/simplex-core-architecture','branch');c.require(h['head']+'\trefs/heads/codex/simplex-core-architecture' in h['remote'] and c.MASTER+'\trefs/heads/master' in h['remote'],'remote');c.require(not c.git('diff','--name-only') and not c.git('diff','--cached','--name-only'),'tracked dirty')
v=c.rd(T/'review.json');c.require(v['accepted'] is True and v['findings']==[] and c.bindings(v),'Task1 review');c.require(c.bindings(c.rd(T/'publication.json')),'Task1 publication')
D.mkdir();c.save(D/'host.json',h);(D/'entry.py').write_bytes(Path(__file__).read_bytes());print(json.dumps({'head':h['head'],'boot':h['boot_id'],'groups':len(h['groups']),'safe':c.host_safe(h),'created':str(D)}))
