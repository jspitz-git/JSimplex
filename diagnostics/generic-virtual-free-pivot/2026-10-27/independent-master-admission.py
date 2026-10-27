from pathlib import Path
import json,hashlib,subprocess,os,datetime,ast
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-virtual-free-pivot/2026-10-27');Q=D/'MASTER-run';M=Path('/home/jspitz/JSimplex.jl');R=D.parents[2];base='1a6b9d81e89b44c5c75b95b6c92e0916c2d19730';target='c01900c2dff3de465846ae44333903889c867626'
def need(x,m):
 if not x:raise RuntimeError(m)
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2,sort_keys=True);f.write('\n')
def raw(a,root=M):return subprocess.check_output(['/usr/bin/git','-C',str(root),*a],env=dict(os.environ,GIT_OPTIONAL_LOCKS='0'))
def git(a,root=M):return raw(a,root).decode().strip()
for n in ['production-review.json','commit-review.json','GREEN-run/result-review.json','publication-preparation-reviewed.json','preparation-review.json']:
 v=read(D/n);need(v['accepted'] is True and not v['findings'],'review '+n)
 for p,h in v['bindings'].items():need(sha(p)==h,'review binding '+p)
need(git(['rev-parse','HEAD'])==git(['rev-parse','master'])==target and git(['branch','--show-current'])=='master','actual master')
need(git(['rev-parse','origin/master'])==git(['ls-remote','origin','refs/heads/master']).split()[0]==base,'unpushed tracking and remote')
need(git(['rev-list','--parents','-n','1',target]).split()==[target,base],'sole parent')
need(git(['rev-parse','HEAD'],R)==read(D/'host-before.json')['diagnostic_head'],'R original ref')
inv=read(D/'source-inverse.json');names=inv['names'];stage=D/'GREEN';baseline=read(D/'baseline-tree.json');hist=read(D/'integration-historical-path-map.json')
need({str(p.relative_to(stage)):sha(p) for p in stage.rglob('*') if p.is_file()}==inv['whole_stage'],'whole tested stage')
need({str(p.relative_to(D/'baseline')):sha(p) for p in (D/'baseline').rglob('*') if p.is_file()}==baseline,'original baseline')
for tree in ['src','test']:
 a={str(p.relative_to(M)):sha(p) for p in (M/tree).rglob('*') if p.is_file()};b={str(p.relative_to(stage)):sha(p) for p in (stage/tree).rglob('*') if p.is_file()};need(a==b,'actual/tested whole tree '+tree)
 for n,h in a.items():need(hashlib.sha256(raw(['show',target+':'+n])).hexdigest()==h,'actual committed file '+n)
need(not git(['diff','--name-only','HEAD','--','src','test','Project.toml']),'actual target clean')
original=read(D/'protected-before.json');current=read(Q/'protected-before.json');need(current['files']==original['files'],'same protected files')
for p,h in {**current['files'],**current['indexes']}.items():need(sha(p)==h,'current protected '+p)
mi=git(['rev-parse','--path-format=absolute','--git-path','index']);ri=git(['rev-parse','--path-format=absolute','--git-path','index'],R)
need(set(current['indexes'])==set(original['indexes']) and current['indexes'][ri]==original['indexes'][ri],'only master index refresh')
need(hist['master_before']==base and set(hist['master_index_before'])=={mi},'exact master map')
v=hist['master_index_before'][mi];need(v['before']==str(D/'before-master/master.index') and v['sha256']==original['indexes'][mi]==sha(v['before']),'original index beforeimage')
need(set(hist['source_before'])=={str(M/n) for n in names if n in baseline},'source map keys')
for p,v in hist['source_before'].items():
 n=str(Path(p).relative_to(M));need(v['before']==str(D/'baseline'/n) and v['sha256']==baseline[n]==sha(v['before']),'source beforeimage '+n)
before=read(D/'integration-before.json');entries=raw(['ls-files','--stage','-z']).decode().split('\0');unrelated=lambda rows:[x for x in rows if x and x.split('\t',1)[1] not in names];need(unrelated(entries)==unrelated(before['entries']) and raw(['diff','--cached','--raw','-z']).decode()==before['staged'],'unrelated index entries/staging')
for n in names:need(any(x=='100644 '+read(D/'production-commit.json')['blobs'][n]+' 0\t'+n for x in entries),'new index target '+n)
pins=read(Q/'pins.json');need(set(pins['files'])==set(pins['inventory']) and len(pins['inventory'])==701,'701 pins')
for p,v in pins['inventory'].items():need(str(Path(p).resolve(strict=True))==v['resolved'] and sha(p)==v['sha256'],'current pin '+p)
need(set(pins['trees'])=={str(M/'src'),str(M/'test')},'actual pin trees')
for t in pins['trees']:need({str(p) for p in Path(t).rglob('*') if p.is_file()}=={p for p in pins['inventory'] if Path(p).is_relative_to(t)},'pin tree membership')
c=read(Q/'contract.json');g=read(D/'GREEN-run/contract.json');a=read(D/'GREEN-run/audit.json');need(c['files']==g['files'] and len(c['files'])==36,'same 36 files');need(c['expected_total']==a['total']==218625 and c['expected_failures']==c['expected_exit']==0 and c['expected_failure_locations']==[],'frozen exact total')
need(c['arm']=='MASTER' and c['source_root']==str(M) and c['attempts']==1 and c['shared_limit_seconds']==2400 and c['guard_limit_seconds']==2392,'actual runtime contract')
need(c['command']==[x.replace(str(D/'GREEN-run'),str(Q)).replace('--project='+str(stage),'--project='+str(M)) for x in g['command']],'actual pinned command')
need((Q/'tests.jl').read_text()==(D/'GREEN-run/tests.jl').read_text().replace(str(stage),str(M)).replace('pivot GREEN','pivot MASTER').replace('COMPLETED GREEN','COMPLETED MASTER'),'same ordinary full-file driver')
for n in ['launch.py','audit.py','guard/entry_gate.py','guard/guard_reviewed.py','guard/supervisor_reviewed.py']:
 need((Q/n).read_bytes()==(D/'GREEN-run'/n).read_bytes(),'same guarded helper '+n);ast.parse((Q/n).read_text())
expected=(D/'GREEN-run/common.py').read_text().replace("TARGET='"+base+"'","TARGET='"+target+"'").replace("git(['rev-parse','HEAD'])==git(['rev-parse','master'])==git(['rev-parse','origin/master'])==TARGET","git(['rev-parse','HEAD'])==git(['rev-parse','master'])==TARGET and git(['rev-parse','origin/master'])=='"+base+"'");need((Q/'common.py').read_text()==expected,'only expected common ref change')
need(not (Q/'output').exists() and not (Q/'reservation.json').exists(),'unlaunched actual run')
vars=['JULIA_PROJECT','JULIA_LOAD_PATH','JULIA_BINDIR','JULIA_CPU_TARGET','JULIA_DEPOT_PATH','LD_PRELOAD','LD_LIBRARY_PATH','LD_AUDIT','BASH_ENV','ENV','PYTHONPATH','PYTHONHOME'];need(all(not os.environ.get(k) for k in vars),'environment overrides');found={k:os.environ[k] for k in vars+['JULIA_NUM_THREADS','OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'] if k in os.environ};need(found==read(Q/'environment.json')['inherited']==read(D/'environment.json')['inherited'],'same environment')
seed=read(Q/'host-seed.json');groups=set(seed['groups']);need(len(groups)==605,'605 groups');boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();need(boot==seed['boot_id'],'boot')
allow=R/'diagnostics/generic-quality-local/2026-10-27/host-identity-allowance.json';need(sha(allow)=='f0b6a5093b9c1875ec8718bca8775bc44ba4d6d6ab98a1ac23adfe52d69f2a92','allowance');allowed=read(allow)['identities'];procs=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  st=(p/'stat').read_text().rsplit(')',1)[1].split();args=[v.decode(errors='replace') for v in (p/'cmdline').read_bytes().split(b'\0') if v];comm=(p/'comm').read_text().strip();v=dict(pid=int(p.name),pgid=int(st[2]),sid=int(st[3]),start_ticks=int(st[19]),command=args,boot_id=boot)
  need(not any(Path(x).name.lower().startswith('julia') for x in [comm]+args[:1]),'active Julia')
  if v['pgid'] in groups or v['sid'] in groups:need(v in allowed,'historical identity')
  procs.append(v)
 except (FileNotFoundError,ProcessLookupError):pass
mem={x.split(':')[0]:int(x.split()[1]) for x in Path('/proc/meminfo').read_text().splitlines()};need(mem['MemAvailable']>=6*1024**2 and mem['SwapTotal']-mem['SwapFree']<=1024**2,'memory/swap')
put(Q/'independent-review-host.json',dict(time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),boot_id=boot,groups=sorted(groups),processes=procs,no_Julia=True,available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree']))
report='''Independent ACTUAL MASTER admission — PASS, pre-execution only.

Actual /home/jspitz/JSimplex.jl master/HEAD is c01900c2dff3de465846ae44333903889c867626, with sole original parent1a6b9d81; origin/master and freshly read remote master still equal that original base. Entire actual src/test membership and bytes equal reviewed GREEN and actual committed blobs. Independent production, actual-commit, GREEN-result and both preparation reviews remain accepted with verified bindings.

All701current pins and resolved targets pass, including complete actual source/test tree inventories. The original536-file baseline and537-file tested stage remain intact. Exact original source maps cover only six previously existing changed files; the seventh new test has no fabricated beforeimage. The original master index copy matches its original protected hash. Current master index target entries equal reviewed blobs; all unrelated entries and staged diff match integration-before. Diagnostic index, user files, configuration and inherited environment remain unchanged. Only the current master index binding is refreshed after ff; original evidence is preserved.

The contract selects actual master project/source ROOT, the same36whole test files as GREEN, ordinary Test with no recorder or manual Test stack, zero failures/errors/skips, frozen218625total, one attempt, and shared2400seconds/2392guard. The driver differs from GREEN only in actual source root and phase label. Launch/auditor/entry/guard/supervisor bytes are identical to accepted GREEN; common differs only in expected local target and still-original tracking ref. Thread/BLAS1,GC1,0,compiled-modulesexisting,heap2GiBhint,address-space8GiB,hostavailable6GiB andswap<=1GiB safeguards remain. Outputs/reservation are absent.

Fresh605historical groups AND sessions pass full boot/start_ticks/command checks with noJulia; only the established exact unrelated-process identity allowance is accepted. This reviewer ran only the new offline Git/hash/proc admission checker, never Julia, a launcher or an old checker. Source bytes introduce no change beyond the reviewed scalar-local optimizations; no unnecessary new production work or retained numerical memory is found.

Accepted for the single concrete ACTUAL MASTER launch. This is not result acceptance or permission to skip independent post-exit review. Normal push remains gated on exact218625all-pass result, unchanged bindings, new independent acceptance and publication checks. Full-suite/x64 remain open.
'''
with (Q/'ADMISSION-REVIEW.md').open('x') as f:f.write(report)
bound={p:v['sha256'] for p,v in pins['inventory'].items()}
for p in [Q/'pins.json',Q/'independent-review-host.json',Q/'ADMISSION-REVIEW.md',D/'independent-master-admission.py',D/'integration-before.json',D/'integration-after.json',D/'integration-historical-path-map.json',D/'before-master/master.index',D/'commit-review.json',D/'GREEN-run/result-review.json',D/'source-inverse.json',D/'production-review.json']:bound[str(p)]=sha(p)
put(Q/'admission.json',dict(accepted=True,findings=[],bindings=bound,arm='MASTER',whole_files=36,expected_total=218625,pins=701,historical_groups=605,one_attempt=True,shared_limit_seconds=2400,no_Julia_executed=True,source_root=str(M),commit=target))
print(json.dumps(dict(accepted=True,arm='MASTER',pins=701,whole_files=36,expected_total=218625,historical_groups=605)))
