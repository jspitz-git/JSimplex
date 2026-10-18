from pathlib import Path
import json,hashlib,os,sys,subprocess,re
D=Path(__file__).resolve().parent;R=D.parents[3];C=R/'diagnostics/direct-bg-split-upper/reproduce';O=D.parent/'DIRECT-BG-BLOCK-DRIVER-PREPARATION';P=D.parent/'DIRECT-BG-SPLIT-ADAPTER-PREPARATION';L=R/'.superpowers/sdd/2026-10-18-direct-bg-split-free-blocks';W=Path('/home/jspitz/.codex/worktrees/native-pivot-production-integration/JSimplex.jl')
def need(v,m):
 if not v:raise RuntimeError(m)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rd(p):return json.loads(p.read_text())
def put(n,s):
 with (D/n).open('x') as f:f.write(s)
def save(n,j):put(n,json.dumps(j,indent=2)+'\n')
helpers={}
for name in ['guard.py','supervisor.py','recorder.jl']:
 put(name,(O/name).read_text());helpers[name]=dict(source=str(O/name),sha256=sha(O/name),byte_identical=True)
save('reused-helpers.json',helpers)
transforms={}
for name in ['control.py','seal.py','launch.py','audit.py','oracle.py','offline-tests.py','negative-supplement.py','freeze-preparation.py']:
 s=(O/name).read_text();changes=[('direct-bg-block-upper','direct-bg-split-upper'),('block BG','split BG'),('Dynamic BG correctness','Split BG correctness'),('8faca92005efbb65ad7212222b17844a248d208a','73216b71debb99c7515b3d265702e0d68afe7064')]
 for a,b in changes:s=s.replace(a,b)
 if name=='audit.py':
  s=s.replace('from oracle import test_results,timeout_only','from oracle import test_results,timeout_only,warning_log').replace("if pure:return", "require(not warning_log(log),'Warning/world-age outcome rejected')\n if pure:return").replace("(8 if cfg['mode']=='red' else 0)","(10 if cfg['mode']=='red' else 0)")
 if name=='oracle.py':
  s=s.replace('import math','import math,re\ndef warning_log(log):return re.search(r"(?i)\\bwarning\\b|world[ -]age",log) is not None')
  s=s.replace('def timeout_only(process,supervisor,raw,log,elapsed,seconds,loaded,phase):','def timeout_only(process,supervisor,raw,log,elapsed,seconds,loaded,phase):\n if warning_log(log):return False')
 put(name,s);transforms[name]=dict(source=str(O/name),source_sha256=sha(O/name),candidate_sha256=sha(D/name),scope='Identifier/scope/base changes; audit10 failures and explicit warning/world-age rejection additionally in audit/oracle')
save('control-lineage.json',transforms)
# Exact isolated stages: do not load either package.
stages={}
for mode,m in [('red',rd(O/'stages.json')['red']),('green',rd(P/'overlay.json'))]:
 src=Path(m['path']);baseline=m['sha256'];out=L/'task3-driver-stages'/mode
 need({str(p.relative_to(src)) for p in src.rglob('*') if p.is_file()}==set(baseline),'Source membership')
 need(not any(p.is_symlink() for p in src.rglob('*')) and all(sha(src/k)==v for k,v in baseline.items()),'Source hashes/symlinks')
 out.mkdir(parents=True,exist_ok=False)
 for k in baseline:
  q=out/k;q.parent.mkdir(parents=True,exist_ok=True)
  with q.open('xb') as f:f.write((src/k).read_bytes())
 stages[mode]=dict(path=str(out),source=str(src),master=m['master'],sha256={k:sha(out/k) for k in baseline},baseline_sha256=baseline)
 for name in ['Manifest.toml','LocalPreferences.toml']:need((out/name).read_bytes()==(W/name).read_bytes(),'environment'+name)
save('stages.json',stages)
sys.path.insert(0,str(D));import guard
prior=rd(O/'runtime-inputs-complete.json');paths=sorted(set(prior['inventory'])|{sys.executable,str(Path(sys.executable).resolve())});current=guard.inventory(paths,[])
need(all(current[k]==v for k,v in prior['inventory'].items()),'Runtime drift; stop')
save('runtime-inputs-complete.json',dict(scope='Fresh readtime runtime/wrapper/library/source; not launch or actual load proof',inventory=current,provenance=str(O/'runtime-inputs-complete.json')))
loaded=rd(O/'loaded-paths.json');need(set(loaded)=={'SparseArrays','LinearAlgebra','TOML','Test','PrecompileTools'},'loaded schema');need(all(p in current for p in loaded.values()),'loaded membership');save('loaded-paths.json',loaded)
keys=list(rd(O/'environment.json'));save('environment.json',{k:os.environ.get(k) for k in keys})
baseline={}
for label,root in [('diagnostic',R),('production',W)]:
 names=subprocess.check_output(['git','ls-files','src','test','.github','Project.toml'],cwd=root,text=True).splitlines();baseline[label]={k:sha(root/k) for k in names}
save('baseline.json',baseline)
entry=[R/'AGENTS.md',R/'docs/superpowers/specs/2026-10-18-direct-bg-split-free-blocks.md',R/'docs/superpowers/plans/2026-10-18-direct-bg-split-free-blocks.md']
for name in ['DIRECT-BG-SPLIT-U-PREPARATION','DIRECT-BG-SPLIT-ADAPTER-PREPARATION']:
 entry += [D.parent/name/k for k in ['REPORT.md','MEMORY-WORK.md','review.md','review.json','closure.json','publication.json']]
save('entry.json',dict(scope='Current accepted Task1/Task2 closure/report/review references; historical mappings preserved, no old script execution',sha256={str(p):sha(p) for p in entry}))
# New source-anchored RED contracts: allocator additions + adapter ownership interfaces.
symbols=['BGSplitUpper','_sbu_target','_sbu_reserve_block!','_sbu_build','_sbu_insert_at!','_sbu_rotate_rows!','SplitBGFactor','_split_bg_factor','_split_bg_replace!','_split_bg_copy_with']
put('red.jl','# Ten NEW missing contracts; no numerical calls. UNEXECUTED.\nfunction run_split_bg_red()\n    @testset "Missing split BG U contracts (ten expected failures)" begin\n'+''.join('        @test isdefined(JSimplex,:'+n+')\n' for n in symbols)+'    end\nend\n')
names=sorted(set(re.findall(r'\b_sbu_[A-Za-z0-9_]+!?',(C/'split-upper.jl').read_text())))
put('split-suite.jl','module SplitStorageTests\nusing Test,SparseArrays\nimport JSimplex\nimport JSimplex: BGSplitUpper, '+', '.join(names)+'\ninclude(joinpath(dirname(pathof(JSimplex)),"../test/split-oracles.jl"))\ninclude(joinpath(dirname(pathof(JSimplex)),"../test/split-upper-tests.jl"))\nend\n')
s=(O/'driver.jl').read_text()
for a,b in [('block BG','split BG'),('run_block_bg_red','run_split_bg_red'),('block-suite.jl','split-suite.jl'),('block-bg-tests.jl','split-bg-tests.jl'),('BlockStorageTests','SplitStorageTests'),('_bgu_structural_tests','_sbu_structural_tests'),('BlockBGTests','SplitBGTests'),('BEGIN block storage','BEGIN split storage'),('END block storage','END split storage')]:s=s.replace(a,b)
s=s.replace(':block_boundaries,:storage_failure_boundaries,:new_scratch_aliases)',':block_boundaries,:storage_failure_boundaries,:new_scratch_aliases,:split_allocator_differentials)')
put('driver.jl',s)
save('preparation-source.json',dict(script_sha256=sha(__file__),stages={k:len(v['sha256']) for k,v in stages.items()},runtime_files=len(current),julia_executed=False))
print('Prepared stages, controls and UNEXECUTED driver',len(current),'runtime files')
