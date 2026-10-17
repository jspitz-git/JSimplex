"""Independent read-only Python/source admission checks. Never launches Julia or old audits."""
from pathlib import Path
import hashlib,json,os,sys,subprocess,re,time
E=Path(__file__).resolve().parent;R=E.parents[3];D=E.parent/'DIRECT-BG-BLOCK-DRIVER-PREPARATION';run=D/'runs/red300';W=Path('/home/jspitz/.codex/worktrees/native-pivot-production-integration/JSimplex.jl');C=R/'diagnostics/direct-bg-block-upper/reproduce'
def rd(p):return json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def git(*a,cwd=R):return subprocess.check_output(['git',*a],cwd=cwd,text=True).strip()
checks=[]
def check(n,v):checks.append({'name':n,'passed':bool(v)})
def tree(p):return {str(x.relative_to(p)):sha(x) for x in p.rglob('*') if x.is_file()}
s=rd(run/'sealed.json');prep=rd(D/'preparation-pins.json')['sha256'];stages=rd(D/'stages.json');runtime=rd(D/'runtime-inputs-complete.json')['inventory'];base=rd(D/'baseline.json')
check('preparation exact required membership',set(prep)==set(rd(D/'required-paths.json')['paths']))
# Closure/publication files were written after the preparation seal, explicitly excluded by its scope.
excluded={'review.json','review.md','required-paths.json','preparation-pins.json','close.py','closure-host.json','closure-names.json','closure.json','publication.json','publish.py'}
names={str(p) for p in D.iterdir() if p.is_file() and not p.name.startswith('reviewer-') and p.name not in excluded}
names|={str(p) for p in C.rglob('*') if p.is_file()};names|=set(rd(D/'entry.json')['sha256']);names|={v['source'] for v in rd(D/'reused-helpers.json').values()};names|=set(runtime)
names|={str(Path(v['path'])/n) for v in stages.values() for n in v['sha256']};names|={str(root/n) for label,root in [('diagnostic',R),('production',W)] for n in base[label]};names.add(str(D/'required-paths.json'))
check('independently reconstructed preparation membership',names==set(prep))
check('all preparation hashes',all(sha(n)==h for n,h in prep.items()))
expected=set(prep)|{str(D/'preparation-pins.json'),str(D/'review.json'),str(run/'host.json'),str(run/'config.json')}|set(runtime)|{str(root/n) for label,root in [('diagnostic',R),('production',W)] for n in base[label]}|{str(Path(stages['red']['path'])/n) for n in stages['red']['sha256']}
check('exact seal file membership and no duplicates',set(s['files'])==expected and len(s['files'])==len(expected))
check('exact seal trees and no external inputs',s['trees']==[stages['red']['path'],str(C)] and s['inputs']==[])
paths=set(s['files'])|{str(p) for t in s['trees'] for p in Path(t).rglob('*') if p.is_file()}
inv={p:{'resolved':str(Path(p).resolve(strict=True)),'sha256':sha(p)} for p in sorted(paths)}
check('full seal inventory membership resolutions hashes',inv==s['inventory'])
check('runtime full resolutions hashes',all(inv.get(p)==v for p,v in runtime.items()))
for mode,v in stages.items():
 root=Path(v['path']);source=Path(v['source'])
 check(mode+' exact stage and original source bytes',tree(root)==v['sha256']==v['baseline_sha256']==tree(source))
 check(mode+' no stage symlinks',not root.is_symlink() and not any(p.is_symlink() for p in root.rglob('*')))
check('original accepted DIRECT comparator',stages['red']['sha256']==rd(D.parent/'DIRECT-LU-POLICY-ADAPTER-COST-PREPARATION/stages.json')['cost']['sha256'])
check('75 red and 81 green',len(stages['red']['sha256'])==75 and len(stages['green']['sha256'])==81)
for label,root in [('diagnostic',R),('production',W)]:
 check(label+' tracked membership and bytes',set(git('ls-files','src','test','.github','Project.toml',cwd=root).splitlines())==set(base[label]) and all(sha(root/n)==h for n,h in base[label].items()))
master='26e2291745999f485a74f643298ca997d65c7205';head='c72bf6ee1fd2b17be803f020c1969bdc7f0f5a02'
check('refs',git('rev-parse','HEAD')==head==s['head'] and git('rev-parse','master')==master==s['master'] and git('rev-parse','HEAD',cwd=W)==master and master+'\trefs/heads/master'==git('ls-remote','origin','refs/heads/master'))
check('branch ancestry',git('branch','--show-current')=='codex/simplex-core-architecture' and subprocess.run(['git','merge-base','--is-ancestor','8faca92005efbb65ad7212222b17844a248d208a','HEAD'],cwd=R).returncode==0)
check('tracked clean',not git('diff','--name-only') and not git('diff','--cached','--name-only'))
check('environment exact',all(os.environ.get(k)==v for k,v in rd(D/'environment.json').items()))
sys.path.insert(0,str(D));import control
cfg=control.config('red300');check('immutable configuration',cfg==s['config']==rd(run/'config.json') and cfg['seconds']==300 and cfg['expected_exit']==1)
gc=control.guard_command(cfg,run/'launch-pins.json',1000.0);check('inner deadline292',gc[gc.index('--seconds')+1]=='292' and gc[gc.index('--deadline')+1]=='1292.0')
check('command constraints',all(x in cfg['command'] for x in ['--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--history-file=no']))
loaded=control.loaded_for(cfg);check('exact six loaded modules including Test',set(loaded)=={'JSimplex','Test','TOML','SparseArrays','LinearAlgebra','PrecompileTools'} and all(p in inv for p in loaded.values()))
red=(D/'red.jl').read_text();symbols=re.findall(r'@test isdefined\(JSimplex,:([^\)]+)\)',red)
check('eight RED source-only assertions',len(symbols)==8 and red.count('@test ')==8 and red.count('@testset ')==1)
check('RED symbols absent in original stage source',all(not re.search(r'(?<![\w])'+re.escape(x)+r'(?![\w])','\n'.join(p.read_text() for p in Path(cfg['stage']).joinpath('src').glob('*.jl'))) for x in symbols))
ex=rd(D/'expected-tests.json')['red'];check('expected exact failure tree',ex=={'assertions':8,'groups':[['Missing block BG U contracts (eight expected failures)',0,8,0,0]]})
h=control.full_host();mem=control.guard.memory();check('fresh host groups AND sessions no Julia',h['matches']==[] and h['groups']==s['groups'] and len(h['groups'])==234)
check('boot identity current and sealed',h['boot_id']==s['boot_id']==rd(run/'host.json')['boot_id'])
check('RAM and swap',mem['available_kib']>=6*1024**2 and mem['swap_used_kib']<=1024**2)
check('no reservation output invocation or other phase',{p.name for p in run.iterdir()}=={'host.json','config.json','sealed.json'} and {p.name for p in run.parent.iterdir()}=={'red300'})
v=rd(D/'review.json');check('preparation acceptance exact bindings',v['accepted'] is True and v['findings']==[] and v['scope']=='block BG driver preparation' and v['pins_sha256']==sha(D/'preparation-pins.json') and set(v['sha256'])==set(prep)|{str(D/'preparation-pins.json')} and all(sha(n)==h for n,h in v['sha256'].items()))
result={'all_passed':all(x['passed'] for x in checks),'checks':checks,'findings':[x['name'] for x in checks if not x['passed']],'host':h,'memory':mem,'counts':{'checks':len(checks),'sealed_files':len(s['files']),'inventory':len(inv),'preparation':len(prep),'runtime':len(runtime),'red_stage':75,'green_stage':81,'historical_groups':234},'sealed_sha256':sha(run/'sealed.json'),'julia_executed':False,'scope':'block BG exact-stage RED admission only'}
with (E/'independent-admission-check.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({k:result[k] for k in ['all_passed','findings','counts','memory','sealed_sha256']}))
