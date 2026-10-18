"""Fresh independent readonly admission checker. No old scripts/imports or Julia."""
from pathlib import Path
import json, hashlib, os, subprocess, time, tomllib
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
D=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCK-DRIVER-PREPARATION'
E=D.parent/'DIRECT-BG-BLOCK-GREEN'; C=R/'diagnostics/direct-bg-block-upper/reproduce'
W=Path('/home/jspitz/.codex/worktrees/native-pivot-production-integration/JSimplex.jl')
run=D/'runs/green300'; red=D/'runs/red300'; checks=[]
def rd(p):return json.loads(Path(p).read_text())
def h(p):
 a=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):a.update(b)
 return a.hexdigest()
def check(name,ok):
 checks.append(dict(name=name,passed=bool(ok)))
 if not ok:raise RuntimeError(name)
def binds(j):return all(h(Path(n) if Path(n).is_absolute() else R/n)==v for n,v in j.items())
def git(*args,root=R):return subprocess.check_output(['git',*args],cwd=root,text=True).strip()
def inv(j):
 paths=set(j['files'])
 for t in j['trees']:
  root=Path(t);check('tree nonsymlink '+t,not root.is_symlink() and not any(p.is_symlink() for p in root.rglob('*')))
  paths.update(str(p) for p in root.rglob('*') if p.is_file())
 return {n:dict(resolved=str(Path(n).resolve(strict=True)),sha256=h(n)) for n in sorted(paths)}
s=rd(run/'sealed.json');cfg=rd(run/'config.json');prep=rd(D/'preparation-pins.json');st=rd(D/'stages.json');runtime=rd(D/'runtime-inputs-complete.json')
check('phase/config',s['phase']=='green300' and s['config']==cfg and cfg['seconds']==300 and cfg['expected_exit']==0)
check('not previously reserved/launched',set(p.name for p in run.iterdir())=={'sealed.json','host.json','config.json'})
check('preparation1865',len(prep['sha256'])==1865 and binds(prep['sha256']) and set(prep['sha256'])==set(rd(D/'required-paths.json')['paths']))
v=rd(D/'review.json');check('preparation review binding',v['accepted'] and v['findings']==[] and v['scope']=='block BG driver preparation' and v['pins_sha256']==h(D/'preparation-pins.json') and set(v['sha256'])==set(prep['sha256'])|{str(D/'preparation-pins.json')} and binds(v['sha256']))
check('runtime609',len(runtime['inventory'])==609 and all(str(Path(n).resolve())==v['resolved'] and h(n)==v['sha256'] for n,v in runtime['inventory'].items()))
for mode,num in [('red',75),('green',81)]:
 m=st[mode];root=Path(m['path']);src=Path(m['source']);names={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}
 check(mode+' exact stage',len(names)==num and names==set(m['sha256']) and not any(p.is_symlink() for p in root.rglob('*')) and all(h(root/n)==v for n,v in m['sha256'].items()))
 check(mode+' accepted source equality',names=={str(p.relative_to(src)) for p in src.rglob('*') if p.is_file()} and m['sha256']==m['baseline_sha256'] and all(h(src/n)==v for n,v in m['sha256'].items()))
 for n in ['Manifest.toml','LocalPreferences.toml']:check(mode+' environment '+n,(root/n).read_bytes()==(W/n).read_bytes())
green=Path(st['green']['path']);ref=Path(st['red']['path'])
for n in ['block-bg-tests.jl','block-upper-tests.jl','block-oracles.jl','fixtures.jl']:
 check('frozen test '+n,(green/'test'/n).read_bytes()==(C/n).read_bytes())
for n in ['block-upper.jl','block-bg.jl']:check('frozen candidate '+n,(green/'src'/n).read_bytes()==(C/n).read_bytes())
t=(green/'src/JSimplex.jl').read_text()
for name in ['block-bg.jl','block-upper.jl']:t=t.replace('\ninclude("'+name+'")\nend\n','\nend\n')
check('stage root inverse',t==(ref/'src/JSimplex.jl').read_text())
a=rd(D.parent/'DIRECT-BG-BLOCK-ADAPTER-PREPARATION/adapter-inverse-reviewed.json');t=(C/'block-bg.jl').read_text()
for edit in reversed(a['edits']):t=t.replace(edit['after'],edit['before'])
for before,after in reversed(a['renames']):t=t.replace(after,before)
check('whole adapter inverse',t==Path(a['reference']).read_text() and h(a['reference'])==a['reference_sha256'] and h(C/'block-bg.jl')==a['candidate_sha256'])
for label,root in [('diagnostic',R),('production',W)]:
 b=rd(D/'baseline.json')[label];check(label+' tracked baseline',set(git('ls-files','src','test','.github','Project.toml',root=root).splitlines())==set(b) and all(h(root/n)==v for n,v in b.items()))
 check(label+' tracked clean',not git('diff','--name-only',root=root) and not git('diff','--cached','--name-only',root=root))
master='26e2291745999f485a74f643298ca997d65c7205';head='60396400ca4a73c813bcec05cb3a602b743f82b9'
check('local production remote refs',git('rev-parse','HEAD')==s['head']==head and git('rev-parse','master')==s['master']==master and git('rev-parse','HEAD',root=W)==master and git('ls-remote','origin','refs/heads/master')==master+'\trefs/heads/master')
check('accepted history ancestor',subprocess.run(['git','merge-base','--is-ancestor','8faca92005efbb65ad7212222b17844a248d208a','HEAD'],cwd=R).returncode==0)
env=rd(D/'environment.json');check('environment unchanged',all(os.environ.get(k)==v for k,v in env.items()))
v=rd(red/'result-review.json');files={str(p) for p in red.rglob('*') if p.is_file() and p.name!='result-review.json'}
check('accepted unique RED exact binding',not (D/'runs/red600/result-review.json').exists() and v['accepted'] and v['findings']==[] and v['phase']=='red300' and v['scope']=='block BG RED result' and set(v['sha256'])==files and binds(v['sha256']))
check('RED audit',rd(red/'audit.json')['all_passed'] is True and rd(red/'audit.json')['pure_timeout'] is False and rd(red/'audit.json')['result']['assertions']==8)
check('RED frozen seal',inv(rd(red/'sealed.json'))==rd(red/'sealed.json')['inventory'])
raw=tomllib.loads((red/'output/raw.toml').read_text());root=raw['tests'];leaf=root['children'][0]
check('RED raw8 no errors',raw['complete'] and not raw['fatal'] and len(root['children'])==1 and leaf['pass']==0 and leaf['fail']==8 and leaf['error']==leaf['broken']==0)
expected=set(prep['sha256'])|{str(D/'preparation-pins.json'),str(D/'review.json')}|set(runtime['inventory'])|files|{str(red/'result-review.json'),str(run/'host.json'),str(run/'config.json')}
for label,root in [('diagnostic',R),('production',W)]:expected.update(str(root/n) for n in rd(D/'baseline.json')[label])
expected.update(str(green/n) for n in st['green']['sha256'])
check('sealed1887 exact membership',len(s['files'])==1887 and set(s['files'])==expected and s['trees']==[str(green),str(C)] and s['inputs']==[])
check('sealed all hashes/resolution/tree',inv(s)==s['inventory'])
wrapper='/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh'
command=['/bin/bash',wrapper,'--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--history-file=no','--project='+str(green),str(D/'driver.jl'),str(run/'output'),str(green),'green300']
check('exact command',cfg['command']==command and cfg['stage']==str(green) and cfg['output']==str(run/'output'))
groups=set(rd(D/'host.json')['groups'])|set(rd(red/'posthost.json')['groups']);check('236 groups and sessions',len(groups)==236 and groups==set(s['groups'])==set(rd(run/'host.json')['groups']))
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[];unreadable=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  a=(p/'stat').read_text().rsplit(')',1)[1].split();comm=(p/'comm').read_text().strip();exe=''
  try:exe=str((p/'exe').resolve(strict=True))
  except PermissionError:unreadable.append(int(p.name))
  except FileNotFoundError:pass
  if int(a[2]) in groups or int(a[3]) in groups or comm.lower().startswith('julia') or Path(exe).name.lower().startswith('julia'):matches.append(dict(pid=int(p.name),pgid=int(a[2]),sid=int(a[3]),start_ticks=int(a[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace'),boot_id=boot))
 except (FileNotFoundError,ProcessLookupError):pass
check('fresh host no matches same boot',not matches and boot==s['boot_id']==rd(run/'host.json')['boot_id'] and rd(run/'host.json')['matches']==[])
m={l.split(':')[0]:int(l.split()[1]) for l in Path('/proc/meminfo').read_text().splitlines()};memory=dict(available_kib=m['MemAvailable'],swap_used_kib=m['SwapTotal']-m['SwapFree'])
check('fresh resources',memory['available_kib']>=6*1024**2 and memory['swap_used_kib']<=1024**2)
e=rd(D/'expected-tests.json')['green'];counts=[21,21,12,6,30,9,18,85,313,17,4,351,3242,215,7634,115,461,239,1042,1248,10]
check('exact15093/21 expectations',e['assertions']==sum(counts)==15093 and len(e['groups'])==21 and [r[1] for r in e['groups']]==counts and all(r[2:]==[0,0,0] for r in e['groups']))
tom=tomllib.loads((D/'expected-tests.toml').read_text())['green']['groups'];check('TOML exact expectation',[[r[k] for k in ['name','pass','fail','error','broken']] for r in tom]==e['groups'])
driver=(D/'driver.jl').read_text();check('top-level includes before main',driver.rfind('include(')<driver.index('function main()'))
check('loaded path report Test included',set(rd(D/'loaded-paths.json'))=={'SparseArrays','LinearAlgebra','TOML','Test','PrecompileTools'} and '(JSimplex,SparseArrays,LinearAlgebra,TOML,Test,PrecompileTools)' in driver)
check('raw before acceptance',driver.index('TOML.print(io,raw)')<driver.index('valid=raw['))
check('explicit inner limit',"seconds=cfg['seconds']-8" in (D/'control.py').read_text())
check('VM and terminal resource guard','(8 * 1024**3, 8 * 1024**3)' in (D/'guard.py').read_text() and "pressure(record['terminal_memory'])" in (D/'guard.py').read_text())
print(json.dumps(dict(accepted=True,findings=[],checks=checks,check_count=len(checks),time=time.time(),boot_id=boot,matches=matches,unreadable_exe_pids=unreadable,visibility_limit='Inaccessible executable links remain visibility limits, not proof of absence.',memory=memory,sealed_sha256=h(run/'sealed.json'),counts=dict(seal_files=1887,preparation=1865,runtime=609,red_stage=75,green_stage=81,groups_sessions=236,prospective_assertions=15093,test_groups=21),scope='Fresh independent read-only exact GREEN admission checks; no numerical execution'),indent=2))
