"""Fresh read/hash-only stdlib review. Never imports or runs the reviewed helpers."""
from pathlib import Path
import hashlib,json,os,subprocess,time,tomllib
D=Path(__file__).resolve().parents[2]; R=D.parents[3]; G=Path(__file__).resolve().parent
W=Path('/home/jspitz/.codex/worktrees/native-pivot-production-integration/JSimplex.jl')
C=R/'diagnostics/direct-lu-policy-adapters/reproduce'; P=D.parent/'DIRECT-LU-POLICY-ADAPTER-PREPARATION'
MASTER='26e2291745999f485a74f643298ca997d65c7205'; HEAD='bbee8f5cb680e981eae878c77f2110ed36c9d029'
checks=[]
def check(name,ok,detail=None):
 checks.append(dict(name=name,passed=bool(ok),detail=detail))
 if not ok: raise RuntimeError(name)
def rd(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def git(*a,cwd=R):return subprocess.check_output(['git',*a],cwd=cwd).decode().strip()
def hashes(m):return all(sha(Path(n) if Path(n).is_absolute() else R/n)==h for n,h in m.items())
def inventory(p):
 paths=set(p['files'])
 for rootname in p['trees']:
  root=Path(rootname)
  check('tree root '+rootname,root.is_dir() and not root.is_symlink())
  for f in root.rglob('*'):
   check_ok=not(f.is_symlink() and (f.is_dir() or not f.exists()))
   if not check_ok:raise RuntimeError('unsafe tree link '+str(f))
   if f.is_file():paths.add(str(f))
 check('inventory membership',paths==set(p['inventory']))
 check('inventory hashes and resolved paths',all(str(Path(n).resolve(strict=True))==v['resolved'] and sha(n)==v['sha256'] for n,v in p['inventory'].items()),len(paths))
 return paths
s=rd(G/'sealed.json'); cfg=rd(G/'config.json'); host=rd(G/'host.json')
check('fresh unreserved GREEN300',set(x.name for x in G.iterdir())=={'sealed.json','host.json','config.json',Path(__file__).name})
check('seal exact top schema',set(s)=={'phase','head','master','boot_id','groups','config','files','trees','inventory','inputs'})
check('phase and limit',s['phase']==cfg['phase']=='green300' and cfg['mode']=='green' and cfg['seconds']==300 and cfg['expected_exit']==0 and s['config']==cfg and s['inputs']==[])
check('config path',cfg['run']==str(G) and cfg['output']==str(G/'output'))
check('input file list unique sorted',s['files']==sorted(set(s['files'])))
manifest=rd(D/'preparation-pins.json')['sha256']; review=rd(D/'review.json')
check('preparation manifest',set(manifest)==set(rd(D/'required-paths.json')['paths']) and len(manifest)==78 and hashes(manifest))
check('preparation review',review['accepted'] is True and review['findings']==[] and review['scope']=='direct adapter driver preparation' and review['pins_sha256']==sha(D/'preparation-pins.json') and set(review['sha256'])==set(manifest)|{str(D/'preparation-pins.json')} and hashes(review['sha256']) and hashes(review['evidence_sha256']))
red=D/'runs/red300'; rv=rd(red/'result-review.json'); redfiles={str(p) for p in red.rglob('*') if p.is_file() and p!=red/'result-review.json'}
check('one RED predecessor',not (D/'runs/red600/result-review.json').exists())
check('RED full review membership',rv['accepted'] is True and rv['findings']==[] and rv['scope']=='direct adapter RED result' and rv['phase']=='red300' and set(rv['sha256'])==redfiles and hashes(rv['sha256']) and hashes(rv['evidence_sha256']),len(redfiles))
ra=rd(red/'audit.json'); check('RED audit acceptance',ra['all_passed'] is True and ra['pure_timeout'] is False and ra['phase']=='red300' and hashes(ra['sha256']))
raw=tomllib.loads((red/'output/raw.toml').read_text()); leaf=raw['tests']['children'][0]
check('RED exact saved raw',raw['complete'] is True and raw['fatal']=='' and len(raw['tests']['children'])==1 and [leaf[k] for k in ('pass','fail','error','broken')]==[0,7,0,0] and len(leaf['failures'])==7)
log=(red/'output/run.log').read_text(); check('RED exact immediate failures and warning',log.count('TEST FAILURE:')==7 and all(x in log for x in leaf['failures']) and 'Detected access to binding `Main.run_direct_lu_policy_red`' in log)
inventory(rd(red/'sealed.json'))
stages=rd(D/'stages.json'); baseline=rd(D/'baseline.json'); runtime=rd(D/'runtime-inputs-complete.json')['inventory']
expected=set(manifest)|{str(D/'preparation-pins.json'),str(D/'review.json')}|set(runtime)|redfiles|{str(red/'result-review.json'),str(G/'host.json'),str(G/'config.json')}
for label,root in [('diagnostic',R),('production',W)]:
 b=baseline[label]; expected.update(str(root/n) for n in b)
 check(label+' baseline membership',set(git('ls-files','src','test','.github','Project.toml',cwd=root).splitlines())==set(b),len(b))
 check(label+' baseline bytes',all(sha(root/n)==h for n,h in b.items()))
check('baseline sizes',len(baseline['diagnostic'])==514 and len(baseline['production'])==516)
for mode,stage in stages.items():
 root=Path(stage['path']); names={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}
 check(mode+' stage exact 75 files',names==set(stage['sha256']) and len(names)==75 and not any(p.is_symlink() for p in root.rglob('*')))
 check(mode+' stage hashes',all(sha(root/n)==h for n,h in stage['sha256'].items()))
 if mode=='green':expected.update(str(root/n) for n in names)
check('full seal files independently reconstructed',set(s['files'])==expected and len(expected)==1820,len(expected))
check('exact sealed trees',s['trees']==[cfg['stage'],str(C)] and cfg['stage']==stages['green']['path'])
inventory(s)
check('runtime 609 full inventory',len(runtime)==609 and all(s['inventory'][n]==v for n,v in runtime.items()))
check('runtime606 original preserved',all(runtime[n]==v for n,v in rd(D/'runtime-inputs.json')['inventory'].items()))
check('refs',git('rev-parse','HEAD')==s['head']==host['head']==HEAD and git('rev-parse','master')==git('rev-parse','HEAD',cwd=W)==s['master']==host['master']==MASTER)
check('remote master',git('ls-remote','origin','refs/heads/master')==MASTER+'\trefs/heads/master')
check('diagnostic candidate ancestry',subprocess.run(['git','merge-base','--is-ancestor','924e72e9a05634112dc107d6813f9b3a21e4ff54','HEAD'],cwd=R).returncode==0)
check('tracked/index clean',not git('diff','--name-only') and not git('diff','--cached','--name-only'))
source_names=git('ls-tree','-r','--name-only',MASTER,'--','src','Project.toml').splitlines(); check('master source membership',len(source_names)==71)
anchor=b'include("huangfu_hall_factorization.jl")\n'; addition=b'include("factor-export.jl")\ninclude("direct-factor.jl")\n'
for mode,stage in stages.items():
 root=Path(stage['path']); overlay=rd(P/('red-overlay.json' if mode=='red' else 'candidate-overlay.json'))
 check(mode+' source manifest membership',set(overlay['source_sha256'])==set(source_names))
 for n in source_names:
  original=subprocess.check_output(['git','show',MASTER+':'+n],cwd=R)
  check(mode+' master inverse '+n,(root/n).read_bytes()==(original.replace(anchor,anchor+addition) if n=='src/JSimplex.jl' else original) and hashlib.sha256(original).hexdigest()==overlay['source_sha256'][n])
 impl=C if mode=='green' else R/'diagnostics/direct-lu-markowitz/reproduce'
 check(mode+' implementation exact',all((root/'src'/n).read_bytes()==(impl/n).read_bytes() for n in ('factor-export.jl','direct-factor.jl')))
 check(mode+' environments exact',all((root/n).read_bytes()==(W/n).read_bytes() for n in ('Manifest.toml','LocalPreferences.toml')))
 check(mode+' overlay manifest',all(sha(root/n)==h for n,h in overlay['overlay_sha256'].items()))
ci=rd(P/'candidate-inverse.json'); newer=(C/'direct-factor.jl').read_text()
for old,new in reversed(ci['replacements']):
 check('candidate inverse replacement unique',newer.count(new)==1); newer=newer.replace(new,old)
check('candidate full byte inverse',newer==(R/'diagnostics/direct-lu-markowitz/reproduce/direct-factor.jl').read_text())
check('export and fixture byte identity',all((C/n).read_bytes()==(R/'diagnostics/direct-lu-markowitz/reproduce'/n).read_bytes() for n in ('factor-export.jl','fixtures.jl')))
cr=rd(P/'review.json');check('candidate accepted source hashes',cr['accepted'] is True and cr['findings']==[] and all(cr['sha256'].get(str(p))==sha(p) for p in C.iterdir() if p.is_file()))
counts=[2*(5+6*12)+(5+6*7+5+1),9+1+6*(1+3*2+2)+2,4*3,4*2+24*8,126*59+90*(8*19+5+3+7*4+32+4)+30,18*25,12*(55+2+2*2+6*4)+6*(55+8*2),6*(2*3+15+13)+3,9*(3*6+2*2+2+3)]
e=rd(D/'expected-tests.json'); et=tomllib.loads((D/'expected-tests.toml').read_text()); ledger=rd(D/'work-ledger.json')
check('nine GREEN assertions independently enumerated',counts==[207,66,12,200,27624,450,1446,207,243] and sum(counts)==e['green']['assertions']==30455 and counts==[x[1] for x in e['green']['groups']] and len(e['green']['groups'])==9,counts)
check('expected TOML/JSON exact',all(et[m]['assertions']==e[m]['assertions'] and [[g[k] for k in ('name','pass','fail','error','broken')] for g in et[m]['groups']]==e[m]['groups'] for m in ('red','green')))
check('ledger assertion tree',[(g['name'],g['assertions']) for g in ledger['assertion_formulas']]==[(x[0],x[1]) for x in e['green']['groups']])
l=ledger['groups']['lifecycles']; calc=dict(paired_setups=7*3*3*2,manager_constructions=7*3*3*2*2,refactor_attempts=90*2+126*2,of_which_singular=126,manager_copies=90,column_updates=90*(8*2+1),explicit_valid_solve_entries=126*(4+16+4)+90*(8*(4+4)+1+7*2+16+2),expected_rejected_solve_entries=(126+90)*4,exact_residual_oracles=126*(4+8+4)+90*(8*(4+4)+7*2+8+2),real_direct_exports=126+90+126,orientation_solve_upper_bound=72+60+84)
check('main lifecycle work independently enumerated',l==calc,calc)
check('frozen environment',all(os.environ.get(k)==v for k,v in rd(D/'environment.json').items()))
check('command exact options',cfg['command']==['/bin/bash','/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh','--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--history-file=no','--project='+cfg['stage'],str(D/'driver.jl'),cfg['output'],cfg['stage'],'green300'])
check('boot/groups prehost',s['boot_id']==host['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip() and s['groups']==host['groups'] and set(s['groups'])==set(rd(D/'host.json')['groups'])|set(rd(red/'posthost.json')['groups']) and len(s['groups'])==224 and host['matches']==[])
mem={a.split(':')[0]:int(a.split()[1]) for a in Path('/proc/meminfo').read_text().splitlines()}; resources=dict(available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree'])
check('fresh RAM and swap gate',resources['available_kib']>=6*1024**2 and resources['swap_used_kib']<=1024**2,resources)
matches=[];unreadable=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  a=(p/'stat').read_text().rsplit(')',1)[1].split();comm=(p/'comm').read_text().strip();exe=''
  try:exe=str((p/'exe').resolve(strict=True))
  except PermissionError:unreadable.append(int(p.name))
  except FileNotFoundError:pass
  if int(a[2]) in s['groups'] or int(a[3]) in s['groups'] or comm.lower().startswith('julia') or Path(exe).name.lower().startswith('julia'):matches.append(dict(pid=int(p.name),pgid=int(a[2]),sid=int(a[3]),start_ticks=int(a[19]),comm=comm,exe=exe,command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except (FileNotFoundError,ProcessLookupError):pass
check('fresh no Julia/groups/sessions',not matches,dict(groups=len(s['groups']),matches=matches,unreadable_exe_pids=unreadable))
result=dict(all_passed=all(c['passed'] for c in checks),scope='Independent GREEN300 offline exact-stage checks only',time=time.time(),checks=checks,seal_sha256=sha(G/'sealed.json'),counts=counts,julia_executed=False,reviewed_helpers_executed=False)
with (G/'admission-independent-checks.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=result['all_passed'],checks=len(checks),sealed_entries=len(s['inventory']),assertions=sum(counts),resources=resources)))
