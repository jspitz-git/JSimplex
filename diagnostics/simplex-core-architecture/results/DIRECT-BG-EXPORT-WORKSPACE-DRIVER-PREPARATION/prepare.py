from pathlib import Path
import json,hashlib,subprocess,sys,os,time
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');C=R/'diagnostics/direct-bg-export-workspace/reproduce';D=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-EXPORT-WORKSPACE-DRIVER-PREPARATION';O=D.with_name('DIRECT-BG-SPLIT-DRIVER-PREPARATION');T=D.with_name('DIRECT-BG-EXPORT-WORKSPACE-TASK2');W=Path('/home/jspitz/.codex/worktrees/native-pivot-production-integration/JSimplex.jl')
def need(v,m):
 if not v:raise RuntimeError(m)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def rd(p):return json.loads(Path(p).read_text())
def put(n,s):
 with (D/n).open('x') as f:f.write(s)
def save(n,v):put(n,json.dumps(v,indent=2)+'\n')
def git(*a,cwd=R):return subprocess.check_output(['git',*a],cwd=cwd,text=True).strip()
groups=rd(T/'host-closure.json')['groups'];matches=[];unread=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  text=(p/'stat').read_text();v=text[text.rfind(')')+2:].split();comm=(p/'comm').read_text().strip();cmd=(p/'cmdline').read_bytes().split(b'\0')[0].decode(errors='replace')
  if int(v[2]) in groups or int(v[3]) in groups or any('julia' in Path(s).name.lower() for s in (comm,cmd)):matches.append(dict(pid=int(p.name),pgid=int(v[2]),sid=int(v[3]),start_ticks=int(v[19]),comm=comm,command=cmd))
 except (FileNotFoundError,ProcessLookupError):pass
 except PermissionError:unread.append(int(p.name))
h=dict(time=time.time(),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),groups=groups,matches=matches,unread=unread,head=git('rev-parse','HEAD'),master=git('rev-parse','master'),branch=git('branch','--show-current'),remote=git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'),status=git('status','--porcelain'),scope='Fresh offline stat/comm/argv0 full246groups ANDsessions; no universal executable visibility proof')
need(not matches and not unread,'Host busy/unreadable');need(h['head']=='8bd2e14cdf0210363747f86b716e70569cf7b9b2' and h['master']=='26e2291745999f485a74f643298ca997d65c7205','Refs drift')
D.mkdir();put('prepare.py',Path(__file__).read_text());save('host.json',h)
lineage={}
for n in ('guard.py','supervisor.py','recorder.jl'):
 put(n,(O/n).read_text());lineage[n]=dict(source=str(O/n),source_sha256=sha(O/n),sha256=sha(D/n),byte_identical=True)
for n in ('control.py','seal.py','launch.py','audit.py','oracle.py'):
 s=(O/n).read_text().replace('direct-bg-split-upper','direct-bg-export-workspace').replace('split BG','BG export workspace').replace('Split BG correctness','BG export workspace correctness').replace('73216b71debb99c7515b3d265702e0d68afe7064',h['head'])
 if n=='audit.py':s=s.replace("(10 if cfg['mode']=='red' else 0)","(6 if cfg['mode']=='red' else 0)")
 put(n,s);lineage[n]=dict(source=str(O/n),source_sha256=sha(O/n),initial_sha256=sha(D/n),scope='New copy; scope/reference/path and RED6 changes; prospective host refinements below')
save('control-lineage.json',lineage)
m=rd(C/'overlay-manifest.json');src=Path(m['stage']);original={str(Path(p).relative_to(src)):v for p,v in m['original_readtime_sha256'].items() if Path(p).is_relative_to(src)}
need(len(original)==75,'Stage count');need(all(sha(src/n)==v for n,v in original.items()),'Original drift')
L=R/'.superpowers/sdd/2026-10-18-direct-bg-export-workspace/task3-driver-stages';stages={}
for mode in ('red','green'):
 out=L/mode;out.mkdir(parents=True,exist_ok=False)
 for n,v in original.items():
  dest=out/n;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((src/n).read_bytes())
 if mode=='green':
  additions=[]
  for row in m['root_additions']:
   need(sha(row['source'])==row['source_sha256'],'Candidate drift');(out/row['staged_relative']).write_bytes(Path(row['source']).read_bytes());additions.append(row['include_literal'])
  root=out/'src/JSimplex.jl';s=root.read_text();need(s.endswith('\nend\n'),'Root boundary');root.write_text(s[:-5]+'\n'+'\n'.join(additions)+'\nend\n')
 stages[mode]=dict(path=str(out),source=str(src),master=h['master'],sha256={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()},baseline_sha256=original)
save('stages.json',stages)
# New copied guard definitions only. No old script import or launcher invoked.
sys.dont_write_bytecode=True;sys.path.insert(0,str(D));import guard
prior=rd(O/'runtime-inputs-complete.json')['inventory'];current=guard.inventory(list(prior)+[sys.executable,str(Path(sys.executable).resolve())],[])
need(all(current[p]==v for p,v in prior.items()),'Runtime drift')
save('runtime-inputs-complete.json',dict(scope='Fresh runtime/script dependency readtime bindings, not actual launch or loaded closure',inventory=current,source=str(O/'runtime-inputs-complete.json')))
loaded=rd(O/'loaded-paths.json');need(all(p in current for p in loaded.values()),'Loaded membership');save('loaded-paths.json',loaded)
save('environment.json',{k:os.environ.get(k) for k in rd(O/'environment.json')})
baseline={}
for label,root in [('diagnostic',R),('production',W)]:baseline[label]={n:sha(root/n) for n in git('ls-files','src','test','.github','Project.toml',cwd=root).splitlines()}
save('baseline.json',baseline)
paths=[R/'AGENTS.md',R/'docs/superpowers/plans/2026-10-18-direct-bg-export-workspace.md',R/'docs/superpowers/specs/2026-10-18-direct-bg-export-workspace.md']
for task in ('TASK1','TASK2'):
 e=D.with_name('DIRECT-BG-EXPORT-WORKSPACE-'+task);paths += [e/n for n in ('FINAL.md','final-review.md','final-review.json','closure.json','publication.json')]
paths += list(C.iterdir());save('entry.json',dict(sha256={str(p):sha(p) for p in paths if p.is_file()}))
save('authorization.json',dict(scope='User requests Task3 OFFLINE RED/GREEN driver and admission preparation plus independent review only',numerical_allowance=False,no_seal_no_launch=True,master_unchanged=True))
print(json.dumps(dict(host='PASS',stages={k:len(v['sha256']) for k,v in stages.items()},runtime=len(current))))
