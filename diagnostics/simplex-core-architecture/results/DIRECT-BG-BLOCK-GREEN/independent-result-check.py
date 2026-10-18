"""New independent saved-result review, read-only; no prior scripts imported/executed."""
from pathlib import Path
import json,hashlib,tomllib,subprocess,os,time
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');D=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCK-DRIVER-PREPARATION';E=D.parent/'DIRECT-BG-BLOCK-GREEN';run=D/'runs/green300';checks=[]
def rd(p):return json.loads(Path(p).read_text())
def h(p):
 d=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):d.update(b)
 return d.hexdigest()
def check(n,c):
 checks.append(dict(name=n,passed=bool(c)))
 if not c:raise RuntimeError(n)
def bindings(m):return all(h(n)==v for n,v in m.items())
def inventory(j):
 paths=set(j['files'])
 for t in j['trees']:
  root=Path(t);check('tree nonsymlink '+t,not root.is_symlink() and not any(p.is_symlink() for p in root.rglob('*')));paths.update(str(p) for p in root.rglob('*') if p.is_file())
 return {n:dict(resolved=str(Path(n).resolve(strict=True)),sha256=h(n)) for n in sorted(paths)}
s=rd(run/'sealed.json');lp=rd(run/'launch-pins.json');ad=rd(run/'admission.json');a=rd(run/'audit.json');cfg=rd(run/'config.json');p=rd(run/'output/process.json');i=rd(run/'invocation.json');rv=rd(run/'reservation.json');pre=rd(run/'prehost.json');post=rd(run/'posthost.json')
check('seal unchanged1887',len(s['files'])==1887 and inventory(s)==s['inventory'])
check('admission exact1888',ad['accepted'] and ad['findings']==[] and ad['scope']=='block BG exact-stage admission' and ad['phase']=='green300' and ad['pins_sha256']==h(run/'sealed.json') and set(ad['sha256'])==set(s['files'])|{str(run/'sealed.json')} and bindings(ad['sha256']) and bindings(ad['evidence_sha256']))
check('launch inventory1890',len(lp['files'])==1890 and set(lp['files'])==set(s['files'])|{str(run/n) for n in ['sealed.json','admission.json','prehost.json']} and lp['trees']==s['trees'] and lp['inputs']==[] and inventory(lp)==lp['inventory'])
check('actual output pins exact', (run/'output/pins.json').read_bytes()==(run/'launch-pins.json').read_bytes())
check('audit exact result files',set(a['sha256'])=={str(f) for f in run.rglob('*') if f.is_file() and f.name!='audit.json'} and bindings(a['sha256']))
check('admitted audit accepted',a['all_passed'] is True and a['pure_timeout'] is False and a['phase']=='green300' and a['error']=='')
check('command and one attempt',rv['one_attempt'] is True and rv['max_seconds']==300 and rv['phase']=='green300' and cfg['command']==rv['command']==i['command']==p['command']==s['config']['command'])
check('invocation bindings',rv['pins_sha256']==i['pins_sha256']==p['pins_sha256']==h(run/'launch-pins.json') and rv['review_sha256']==i['review_sha256']==h(run/'admission.json') and i['reservation_sha256']==h(run/'reservation.json'))
gc=i['guard_command'];check('292 deadline exact',gc[gc.index('--seconds')+1]=='292' and float(gc[gc.index('--deadline')+1])==i['monotonic_start']+292 and gc[gc.index('--')+1:]==cfg['command'])
sup=i['supervisor'];check('successful no timeout cleanup',sup['accepted'] is True and sup['returncode']==0 and all(sup[k] is False for k in ['soft_timeout','hard_timeout','child_kill','guard_term','guard_kill']) and i['elapsed_seconds']<300 and p['elapsed_including_launch']<292 and p['reason']=='exit0' and p['returncode']==0 and p['pins_unchanged'] is True and 'error' not in p)
cur=rd(run/'output/current.json');check('process identity linkage',p['runner']==sup['guard_identity']==cur['runner'] and p['child']==cur['child'] and p['cwd']==str(R))
for role,pid,start in [('runner',692506,32309971),('child',692507,32310022)]:
 x=p[role];check(role+' identity',x['pid']==x['pgid']==x['sid']==pid and x['start_ticks']==start and x['boot_id']==s['boot_id'] and x['command'].strip()==' '.join(gc if role=='runner' else cfg['command']))
raw=tomllib.loads((run/'output/raw.toml').read_text());root=raw['tests'];expected=rd(D/'expected-tests.json')['green'];rows=[[x[k] for k in ['name','pass','fail','error','broken']] for x in root['children']]
check('raw complete no fatal exact21 tree',raw['phase']=='green300' and raw['complete'] is True and raw['fatal']=='' and len(rows)==21 and rows==expected['groups']==a['result']['groups'] and all(root[k]==0 for k in ['pass','fail','error','broken']) and root['failures']==[] and all(x['children']==[] and x['failures']==[] for x in root['children']))
check('15093 observed all passes',sum(x[1] for x in rows)==expected['assertions']==a['result']['assertions']==15093 and all(x[2:]==[0,0,0] for x in rows))
loaded=dict(rd(D/'loaded-paths.json'),JSimplex=str(Path(cfg['stage'])/'src/JSimplex.jl'));check('six loaded paths and threads',raw['loaded']==loaded and raw['threads']==raw['blas_threads']==1)
log=(run/'output/run.log').read_text();names=['block storage','lifecycles','rejection_and_aliases','export_modes','focused_updates','block_boundaries','storage_failure_boundaries','new_scratch_aliases'];want=['BEGIN block BG driver green300']
for n in names:want.extend(['BEGIN '+n,'END '+n])
check('exact clean checkpoint log',log.splitlines()==want)
launcher=(run/'launcher.log').read_text();check('launcher process record',json.loads(launcher)==p)
res=[json.loads(l) for l in (run/'output/resources.jsonl').read_text().splitlines()];check('19 samples and terminal safe',len(res)==19 and all(x['available_kib']>=6*1024**2 and x['swap_used_kib']<=1024**2 for x in res+[p['terminal_memory']]) and all(0<=x['elapsed']<292 for x in res))
check('saved pre/post identities',pre['head']==post['head']==s['head'] and pre['master']==post['master']==s['master'] and pre['boot_id']==post['boot_id']==s['boot_id'] and pre['matches']==post['matches']==[] and set(pre['groups'])==set(s['groups']) and set(post['groups'])==set(s['groups'])|{692506,692507} and len(post['groups'])==238)
red=D/'runs/red300';rr=rd(red/'result-review.json');check('RED predecessor unchanged',rr['accepted'] and rr['findings']==[] and set(rr['sha256'])=={str(f) for f in red.rglob('*') if f.is_file() and f.name!='result-review.json'} and bindings(rr['sha256']) and inventory(rd(red/'sealed.json'))==rd(red/'sealed.json')['inventory'])
for mode,st in rd(D/'stages.json').items():
 t=Path(st['path']);check(mode+' stage membership/hashes',set(st['sha256'])=={str(f.relative_to(t)) for f in t.rglob('*') if f.is_file()} and all(h(t/n)==v for n,v in st['sha256'].items()))
for label,t in [('diagnostic',R),('production',Path('/home/jspitz/.codex/worktrees/native-pivot-production-integration/JSimplex.jl'))]:
 b=rd(D/'baseline.json')[label];check(label+' baseline',set(subprocess.check_output(['git','ls-files','src','test','.github','Project.toml'],cwd=t,text=True).splitlines())==set(b) and all(h(t/n)==v for n,v in b.items()) and not subprocess.check_output(['git','diff','--name-only','HEAD'],cwd=t,text=True).strip())
check('refs unchanged',subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()==s['head'] and subprocess.check_output(['git','rev-parse','master'],cwd=R,text=True).strip()==s['master'] and subprocess.check_output(['git','ls-remote','origin','refs/heads/master'],cwd=R,text=True).strip()==s['master']+'\trefs/heads/master')
check('environment unchanged',all(os.environ.get(k)==v for k,v in rd(D/'environment.json').items()))
matches=[];unreadable=[];groups=set(post['groups']);boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
for proc in Path('/proc').glob('[0-9]*'):
 try:
  stat=(proc/'stat').read_text().rsplit(')',1)[1].split();comm=(proc/'comm').read_text().strip();exe=''
  try:exe=str((proc/'exe').resolve(strict=True))
  except PermissionError:unreadable.append(int(proc.name))
  except FileNotFoundError:pass
  if int(stat[2]) in groups or int(stat[3]) in groups or comm.lower().startswith('julia') or Path(exe).name.lower().startswith('julia'):matches.append(int(proc.name))
 except (FileNotFoundError,ProcessLookupError):pass
check('fresh238 groups/sessions no visible Julia',not matches and boot==s['boot_id'])
print(json.dumps(dict(all_passed=True,findings=[],checks=checks,check_count=len(checks),time=time.time(),scope='Independent saved exact GREEN result integrity and raw test-tree review; no rerun or performance qualification',observed_assertions=15093,observed_groups=21,resources=dict(samples=len(res),min_available_kib=min(x['available_kib'] for x in res),max_swap_used_kib=max(x['swap_used_kib'] for x in res),terminal=p['terminal_memory'],child_maxrss_kib=p['child_maxrss_kib'],inclusive_seconds=i['elapsed_seconds']),host=dict(boot_id=boot,groups=len(groups),matches=matches,unreadable_exe_pids=unreadable,visibility_limit='Inaccessible executable links remain a visibility limitation.'),result_sha256={str(f):h(f) for f in run.rglob('*') if f.is_file()}),indent=2))
