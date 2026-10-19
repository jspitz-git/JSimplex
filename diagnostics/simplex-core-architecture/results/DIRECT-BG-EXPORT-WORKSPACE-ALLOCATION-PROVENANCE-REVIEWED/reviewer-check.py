"""Fresh corrected provenance admission; Python/read-only checks, no Julia."""
from pathlib import Path
import json,sys,ast,re,tomllib
D=Path(__file__).resolve().parent;sys.dont_write_bytecode=True;sys.path.insert(0,str(D))
import control as c
import evidence as e
A=D.with_name('DIRECT-BG-EXPORT-WORKSPACE-ALLOCATION-PROVENANCE');run=D/'runs/profile300';sp=run/'sealed.json'
checks={}
def ck(n,v):
 checks[n]=bool(v)
 if not v:raise AssertionError(n)
def save(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
s=c.rd(sp);p=c.rd(D/'preparation-pins.json');cfg=c.config('profile300')
ck('preparation_exact2379',len(p['sha256'])==2379 and set(p['sha256'])==set(c.rd(D/'required-paths.json')['paths']) and c.bindings(p))
ck('initial_rejection_preserved',c.rd(A/'review-rejected.json')['accepted'] is False and len(c.rd(A/'review-rejected.json')['findings'])==1 and c.bindings(c.rd(A/'review-rejected.json')) and c.bindings(c.rd(A/'review-rejected.json'),'evidence_sha256'))
ck('initial_seal_intact',c.guard.pins_match(c.rd(A/'runs/profile300/sealed.json')))
ck('initial_never_attempted',{x.name for x in (A/'runs/profile300').iterdir()}=={'sealed.json','config.json','host.json'})
old=(A/'driver.jl').read_text();new=(D/'driver.jl').read_text()
ck('exact_three_private_renames',old.count('summary(')==3 and new.count('bg_alloc_summary(')==3 and new.replace('bg_alloc_summary(','summary(')==old)
ck('no_unqualified_Base_summary',not re.search(r'(?<![\w])summary\(',new))
copied=['guard.py','supervisor.py','analysis.py','inputs.json','inputs.toml','baseline.json','runtime-inputs-complete.json','environment.json','control.py','evidence.py','helpers.jl','helper-inverse.json','stages.json','loaded-paths.json','seal.py','launch.py','audit.py','authorization.json']
ck('all_copied_files_exact',all((D/n).read_bytes()==(A/n).read_bytes() for n in copied))
inv=c.rd(D/'helper-inverse.json');orig=Path(inv['source']).read_text()
ck('whole_helper_source_inverse',c.sha(inv['source'])==inv['source_sha256'] and c.sha(D/'helpers.jl')==inv['helpers_sha256'] and (D/'helpers.jl').read_text()==orig[orig.index(inv['begin']):orig.index(inv['end'])])
ck('original_inputs_json_toml',c.rd(D/'inputs.json')==tomllib.loads((D/'inputs.toml').read_text()))
stage=c.rd(D/'stages.json')['green'];root=Path(stage['path'])
ck('exact79_stage',len(stage['sha256'])==79 and {str(x.relative_to(root)) for x in root.rglob('*') if x.is_file()}==set(stage['sha256']) and all(c.sha(root/n)==h for n,h in stage['sha256'].items()))
ck('stage_no_symlinks',not root.is_symlink() and not any(x.is_symlink() for x in root.rglob('*')))
ck('only_original_uninstrumented_factory','factory(::Val{:candidate},F,B,backend) = J._bgx_factor(B,backend,policy(backend))' in (D/'helpers.jl').read_text() and '_bgxp_' not in new+(D/'helpers.jl').read_text())
for path in D.glob('*.py'):ast.parse(path.read_text(),filename=str(path))
ck('Python_only_syntax',True)
c.validate_environment();c.validate_sources();pre=c.preparation();pred,groups=c.predecessor('profile300')
ck('current_environment_sources_predecessor',bool(pre) and bool(pred) and len(groups)==254)
expected=sorted(set(pre+list(c.rd(D/'runtime-inputs-complete.json')['inventory'])+
 [str(r/n) for label,r in [('diagnostic',c.R),('production',c.W)] for n in c.rd(D/'baseline.json')[label]]+
 [str(root/n) for n in stage['sha256']]+pred+[str(run/'host.json'),str(run/'config.json')]))
ck('seal_exact2382_membership',len(s['files'])==len(set(s['files']))==2382 and s['files']==expected)
ck('all_sealed_hashes_resolutions',c.guard.inventory(s['files'],s['trees'])==s['inventory'])
ck('trees_and_config',s['trees']==[cfg['stage'],str(c.C)] and s['config']==cfg==c.rd(run/'config.json') and s['inputs']==[])
runtime=c.rd(D/'runtime-inputs-complete.json')['inventory']
ck('all_runtime_current',all(c.sha(x)==v['sha256'] and str(Path(x).resolve(strict=True))==v['resolved'] for x,v in runtime.items()) and set(runtime)<=set(s['files']))
extra=[x for x in s['files'] if '/stdlib/v1.13/Profile/' in x or '/stdlib/v1.13/StyledStrings/' in x]
ck('twelve_profile_styled_sources',len(extra)==12)
alloc=Path(c.rd(D/'loaded-paths.json')['Profile']).with_name('Allocs.jl').read_text()
ck('profile_API_signatures',all(t in alloc for t in ('function start(; sample_rate::Real)','function stop()','function clear()','function fetch()','type::Any','stacktrace::StackTrace','size::Int')))
ck('profile_decode_then_cap',new.index('data=Profile.Allocs.fetch()')<new.index('length(data.allocs)<=200000'))
ck('full_symbolic_stacks_poststop',new.index('Profile.Allocs.stop()')<new.index('for a in data.allocs') and all(t in new for t in ('s.func','s.file','s.line','s.from_c','s.inlined')))
ck('profile_always_stopped','finally\n        Profile.Allocs.stop()' in new and new.count('Profile.Allocs.clear()')==4)
ck('observed_compile_zero',new.count('Compilation in observed lifecycle')==1 and 'ordinary["compile_seconds"]==ordinary["recompile_seconds"]==profiled["compile_seconds"]==profiled["recompile_seconds"]==0' in new)
ck('three_warm_fixed_schedule','for _ in 1:3' in new and 'for input in inputs, backend in (Val(:native),Val(:markowitz))' in new)
ck('profile_rate_and_no_code_typed','start(sample_rate=1.0)' in new and 'code_typed' not in new)
ck('exact22_output_names',len(e.expected_names())==22 and len([x for x in e.expected_names() if x.startswith('profile-')])==16)
ck('fixed_work_budget',4*2*2*(3+1+1)==80 and 80*2==160 and 80*8==640 and 80*16==1280 and 16*2*24==768)
cmd=['/bin/bash',c.base.WRAPPER,'--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--history-file=no','--project='+cfg['stage'],str(D/'driver.jl'),'profile300',str(run/'output'),cfg['stage']]
ck('exact_command_limits',cfg['command']==cmd and cfg['seconds']==300 and cfg['expected_exit']==0)
ck('guard292',c.guard_command(cfg,run/'launch-pins.json',1000.)==[sys.executable,'-B',str(D/'guard.py'),'run',str(run/'launch-pins.json'),str(run/'output'),'--seconds','292','--deadline','1292.0','--expected-exit','0','--',*cmd])
ck('only_unattempted_seal',{x.name for x in run.iterdir()}=={'sealed.json','config.json','host.json'})
h=c.full_host(groups+s['groups']);h['memory']=c.guard.memory();h['remote']=c.git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture');h['status']=c.git('status','--porcelain')
save(D/'reviewer-host.json',h)
ck('fresh254groups_sessions_clear',c.host_safe(h) and len(h['groups'])==254 and set(h['groups'])==set(groups)==set(s['groups']))
ck('fresh_boot_refs',all(h[k]==s[k]==c.rd(run/'host.json')[k] for k in ('head','master','boot_id')) and h['head']=='ed3d83e73478b4af00a40dd7e7dc02d5029b159d' and h['master']==c.MASTER)
ck('remote_refs',h['head']+'\trefs/heads/codex/simplex-core-architecture' in h['remote'] and h['master']+'\trefs/heads/master' in h['remote'])
ck('resources',not c.guard.pressure(h['memory']))
ck('tracked_clean',not c.git('diff','--name-only') and not c.git('diff','--cached','--name-only'))
ck('final_seal_unchanged',c.guard.pins_match(s))
result=dict(all_passed=all(checks.values()),checks=checks,check_count=len(checks),pins_sha256=c.sha(sp),scope='Corrected exact-stage admission review only; no Julia, old checker, seal or launch execution',profile_records_cap_is_post_decode=True,
 work=dict(constructors=80,refactors=160,updates=640,FTRAN=1280,BTRAN=640,observed_vectors=768,native_orientation_upper_bound=120))
save(D/'reviewer-check.json',result)
print(json.dumps(dict(all_passed=result['all_passed'],checks=len(checks),memory=h['memory'],sealed_files=len(s['files']))))
