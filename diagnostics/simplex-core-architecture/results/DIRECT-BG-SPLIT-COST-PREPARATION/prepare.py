from pathlib import Path
import json,re,hashlib,shutil
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');E=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-SPLIT-COST-PREPARATION';O=E.parent/'DIRECT-BG-BLOCK-COST-PREPARATION';G=E.parent/'DIRECT-BG-SPLIT-DRIVER-PREPARATION';C=R/'diagnostics/direct-bg-split-upper/reproduce';W=R/'.superpowers/sdd/2026-10-18-direct-bg-split-free-blocks'
def save(n,t):
 with (E/n).open('x') as f:f.write(t)
def js(n,v):save(n,json.dumps(v,indent=2)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
reused={}
for n,src in [('guard.py',G/'guard.py'),('supervisor.py',G/'supervisor.py'),('inputs.json',O/'inputs.json'),('inputs.toml',O/'inputs.toml'),('baseline.json',G/'baseline.json'),('runtime-inputs-complete.json',G/'runtime-inputs-complete.json'),('environment.json',G/'environment.json')]:
 save(n,src.read_text());reused[n]={'source':str(src),'sha256':sha(src)}
def rebase(t):
 return t.replace('direct-bg-block-upper','direct-bg-split-upper').replace('DIRECT-BG-BLOCK-DRIVER-PREPARATION','DIRECT-BG-SPLIT-DRIVER-PREPARATION').replace('block BG','split BG').replace('2642947bc35143bbd72c1c4b9509a4a3e3bcc86d','fae75df5b4b998a768fbee0608695e5b3930174e').replace('_block_bg','_split_bg').replace('_block_probe_counts','_split_probe_counts').replace('_bgu_','_sbu_').replace('Block invariant','Split invariant')
for n in ['control.py','analysis.py','evidence.py','seal.py','launch.py','audit.py','cost.jl','probe.jl']:
 save(n,rebase((O/n).read_text()))
loaded=json.loads((G/'loaded-paths.json').read_text());del loaded['Test'];js('loaded-paths.json',loaded)
run=G/'runs/green300';rv=json.loads((run/'result-review.json').read_text());paths=set(rv['sha256'])|set(rv.get('evidence_sha256',{}))|{str(run/'result-review.json')}
js('lineage.json',{'sha256':{n:sha(n) for n in sorted(paths)},'scope':'Accepted Split BG GREEN only; no numerical rerun'})
u=(C/'split-upper.jl').read_text();b=(C/'split-bg.jl').read_text();oracle=(C/'split-oracles.jl').read_text();a=oracle.split('function _sbu_materialize')[0];helper=oracle[oracle.index('function _sbu_test_free('):oracle.index('function _sbu_test_handles(')]
renames={x:'_probe'+x for x in sorted(set(re.findall(r'\b(?:_sbu_|_sbg_|_split_bg_)[A-Za-z0-9_!]*',u+b+a+helper)))}
renames.update(BGSplitUpper='ProbeBGSplitUpper',SplitBGFactor='ProbeSplitBGFactor')
def rename(t):
 for x,z in sorted(renames.items(),key=lambda x:-len(x[0])):t=re.sub(r'(?<![A-Za-z0-9_])'+re.escape(x)+r'(?![A-Za-z0-9_!])',z,t)
 return t
injections=[];replacements=[]
def replace(old,new):
 global u
 if u.count(old)!=1:raise RuntimeError(('replace',old,u.count(old)))
 u=u.replace(old,new);replacements.append({'old':old,'new':new})
def inject(anchor,code):
 global u
 if u.count(anchor)!=1:raise RuntimeError(('anchor',anchor,u.count(anchor)))
 mark='\n    # SPLIT_COST_PROBE_BEGIN\n'+code+'\n    # SPLIT_COST_PROBE_END\n';u=u.replace(anchor,anchor+mark);injections.append(dict(anchor=anchor,code=code))
j=json.loads((O/'probe-inverse.json').read_text())
old='_sbu_allocate(::Type{T},n::Int) where {T}=Vector{T}(undef,n)'
new='_sbu_allocate(::Type{T},n::Int) where {T}=(_split_count!(:allocation_requests,1);_split_count!(:requested_payload_bytes,n*Base.elsize(Vector{T}));Vector{T}(undef,n))'
replace(old,new)
for v in j['injections']:
 anchor=v['anchor'].replace('_bgu_','_sbu_');code=v['code'].replace('_block_','_split_')
 if 'row_growths' in code:code+='\n    _split_count!(:row_new_payload,4*C)'
 if 'descriptor_growths' in code:code+='\n    _split_count!(:descriptor_new_payload,28*C);_split_count!(:descriptor_copied_payload,28*length(U.slab))'
 if 'slab_appends' in code:code+='\n    _split_count!(:append_descriptors,8);_split_count!(:slab_new_payload,4096)'
 if 'directory_growths' in code:code+='\n    _split_count!(:directory_new_payload,24*D)'
 inject(anchor,code)
inject('    target=1','    _split_count!(:target_calls,1);_split_count!(:target_comparisons,1)')
replace('    while target<required;target*=2;end','    while target<required;target*=2;_split_count!(:target_comparisons,1);end')
inject('    for c in required:32','        _split_count!(:bin_inspections,1)')
inject('    target=_sbu_target(required)','    _split_count!(:reserve_requests,1);_split_count!(_split_target_keys[target],1)')
replace('    cap==target && return b','    if cap==target;_split_count!(:exact_fit_requests,1);return b;end')
inject('    U.used=suffix','    _split_count!(:free_splits,1);_split_count!(:split_descriptors,1);_split_count!(_split_remainder_keys[remainder],1)')
inject('        donor=_sbu_take!(U,reserve);s=Int(U.slab[donor]);start=Int(U.start[donor])','        _split_count!(:relocations,1);_split_count!(:relocation_old_capacity_clears,Int(U.capacity[b]))')
inject('@inline function _sbu_clear!(U,b::Int,k::Int)','    _split_count!(:cleared_cells,1)')
keys=j['counts']+['row_new_payload','descriptor_new_payload','descriptor_copied_payload','append_descriptors','slab_new_payload','directory_new_payload','target_calls','target_comparisons','bin_inspections','reserve_requests','exact_fit_requests','free_splits','split_descriptors','relocations','relocation_old_capacity_clears','cleared_cells']+['target_'+str(i) for i in (1,2,4,8,16,32)]+['remainder_'+str(i) for i in range(1,33)]
header='const _split_probe_counts=Dict{Symbol,Int}('+','.join(':'+k+'=>0' for k in keys)+')\n_split_count!(k,n)=(_split_probe_counts[k]+=n;nothing)\n_split_max!(k,n)=(_split_probe_counts[k]=max(_split_probe_counts[k],n);nothing)\nconst _split_target_keys=('+','.join(':target_'+str(i) if i in (1,2,4,8,16,32) else ':unused' for i in range(1,33))+')\nconst _split_remainder_keys=('+','.join(':remainder_'+str(i) for i in range(1,33))+')\n'
save('probe-upper.jl',header+rename(u));save('probe-bg.jl',rename(b));save('probe-oracles.jl',a+rename(a+helper))
js('probe-inverse.json',dict(renames=renames,injections=injections,replacements=replacements,header=header,sources={str(C/n):sha(C/n) for n in ['split-upper.jl','split-bg.jl','split-oracles.jl']},counts=keys,helper=helper))
s=json.loads((G/'stages.json').read_text())['green'];stage=W/'task3-cost-stage';stage.mkdir(exist_ok=False)
for n,h in s['sha256'].items():
 src=Path(s['path'])/n
 if sha(src)!=h:raise RuntimeError('GREEN stage drift '+n)
 dest=stage/n;dest.parent.mkdir(exist_ok=True,parents=True);shutil.copyfile(src,dest)
root=stage/'src/JSimplex.jl';t=root.read_text();at=t.rfind('\nend')
if at<0:raise RuntimeError('root end')
includes='\ninclude("probe-upper.jl")\ninclude("probe-bg.jl")\ninclude("probe-oracles.jl")\n';root.write_text(t[:at]+includes+t[at:])
for n in ['probe-upper.jl','probe-bg.jl','probe-oracles.jl']:shutil.copyfile(E/n,stage/'src'/n)
js('stages.json',{'cost':{'path':str(stage),'sha256':{str(p.relative_to(stage)):sha(p) for p in sorted(stage.rglob('*')) if p.is_file()},'source':s['path'],'baseline_sha256':s['sha256'],'inserted_includes':includes}})
js('reused-files.json',reused)
js('authorization.json',dict(scope='Prepare Split BG Task3 cost driver/admission and independent review ONLY; no Julia/query/parser/import/compile/seal/reservation/run.',entry='fae75df5b4b998a768fbee0608695e5b3930174e'))
print('New84-file stage and',len(keys),'probe counters prepared; no Julia')
