from pathlib import Path
import json,re,hashlib,shutil
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');E=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCK-COST-PREPARATION';O=E.parent/'DIRECT-BG-DYNAMIC-COST-PREPARATION';G=E.parent/'DIRECT-BG-BLOCK-DRIVER-PREPARATION';C=R/'diagnostics/direct-bg-block-upper/reproduce';W=R/'.superpowers/sdd/2026-10-16-direct-bg-block-upper'
def save(n,t):
 with (E/n).open('x') as f:f.write(t)
def js(n,v):save(n,json.dumps(v,indent=2)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
shutil.copyfile(__file__,E/'prepare.py')
reused={}
for n,src in [('guard.py',G/'guard.py'),('supervisor.py',G/'supervisor.py'),('inputs.json',O/'inputs.json'),('inputs.toml',O/'inputs.toml'),('baseline.json',G/'baseline.json'),('runtime-inputs-complete.json',G/'runtime-inputs-complete.json'),('environment.json',G/'environment.json')]:
 save(n,src.read_text());reused[n]={'source':str(src),'sha256':sha(src)}
for new,old in [('control.py','control_reviewed.py'),('analysis.py','analysis_reviewed.py'),('evidence.py','evidence_reviewed.py'),('seal.py','seal_reviewed.py'),('launch.py','launch_reviewed.py'),('audit.py','audit_reviewed.py')]:
 t=(O/old).read_text().replace('control_reviewed','control').replace('analysis_reviewed','analysis').replace('evidence_reviewed','evidence').replace('audit_reviewed','audit').replace('direct-bg-dynamic-upper','direct-bg-block-upper').replace('DIRECT-BG-DYNAMIC-DRIVER-PREPARATION','DIRECT-BG-BLOCK-DRIVER-PREPARATION').replace('dynamic BG','block BG').replace('preparation-pins-reviewed.json','preparation-pins.json').replace('required-paths-reviewed.json','required-paths.json').replace('0601df628f30ee3f226066d5ace9ab16928193aa','2642947bc35143bbd72c1c4b9509a4a3e3bcc86d')
 if new=='audit.py':t=t.replace("['FATAL COST:','ERROR:','Traceback']","['FATAL COST:','ERROR:','Traceback','WARNING:','Warning:','world age']")
 if new=='evidence.py':t=t[:t.index('def probe_ok(')] # new explicit schema below
 save(new,t)
# No inherited Test key; driver reports exactly five modules.
loaded=json.loads((G/'loaded-paths.json').read_text());del loaded['Test'];js('loaded-paths.json',loaded)
# Frozen GREEN lineage, including each immutable result and supplementary files.
run=G/'runs/green300';rv=json.loads((run/'result-review.json').read_text());paths=set(rv['sha256'])|set(rv.get('evidence_sha256',{}))|{str(run/'result-review.json')}
js('lineage.json',{'sha256':{n:sha(n) for n in sorted(paths)},'scope':'Accepted Block BG GREEN only; no old numerical rerun'})
# New probe clone; only identifier substitutions and marked integer bookkeeping.
u=(C/'block-upper.jl').read_text();b=(C/'block-bg.jl').read_text()
renames={x:'_probe'+x for x in sorted(set(re.findall(r'\b(?:_bgu_|_bbg_|_block_bg_)[A-Za-z0-9_!]*',u+b)))}
renames.update(BGBlockUpper='ProbeBGBlockUpper',BlockBGFactor='ProbeBlockBGFactor')
# identifiers ending ! are matched with lexical lookarounds, not word boundaries.
def rename(t):
 for a,z in sorted(renames.items(),key=lambda x:-len(x[0])):t=re.sub(r'(?<![A-Za-z0-9_])'+re.escape(a)+r'(?![A-Za-z0-9_!])',z,t)
 return t
injections=[]
def inject(anchor,code):
 global u
 if u.count(anchor)!=1:raise RuntimeError(('anchor',anchor,u.count(anchor)))
 mark='    # BLOCK_COST_PROBE_BEGIN\n'+code+'\n    # BLOCK_COST_PROBE_END\n'
 u=u.replace(anchor,anchor+'\n'+mark);injections.append({'anchor':anchor,'code':code})
# Turn allocator one-line into same expression plus prefixed request counting, inverse explicitly saved.
old='_bgu_allocate(::Type{T},n::Int) where {T}=Vector{T}(undef,n)'
new='_bgu_allocate(::Type{T},n::Int) where {T}=(_block_count!(:allocation_requests,1);_block_count!(:requested_payload_bytes,n*sizeof(T));Vector{T}(undef,n))'
if u.count(old)!=1:raise RuntimeError('allocator')
u=u.replace(old,new)
inject('    s=Int(U.slab[b]);i=Int(U.start[b])+k-1','    _block_count!(:tuple_writes,1);_block_count!(:row_handle_repairs,1)')
inject('    b,k=_bgu_decode(h);U.row_backs[Int(U.slab[b])][Int(U.start[b])+k-1]=Int32(p)','    _block_count!(:back_repairs,1)')
inject('        h=a[g-1];a[g+l-1]=h;a[g-1]=0;_bgu_back!(U,h,g+l-1);g-=1','        _block_count!(:gap_moves,1)')
inject('        h=a[g+l];a[g]=h;a[g+l]=0;_bgu_back!(U,h,g);g+=1','        _block_count!(:gap_moves,1)')
inject('    a=allocate(Int32,C)::Vector{Int32};length(a)==C || throw(ArgumentError("allocator length"));gap=C-d','    _block_count!(:row_growths,1);_block_count!(:row_copied_bytes,4*d)\n    _block_max!(:row_coexist_payload,4*(length(U.rows[r])+C))')
inject('    copyto!(a,1,old,1,length(old))','    _block_count!(:grown_copied_bytes,sizeof(T)*length(old))')
inject('    C==length(U.slab) && return nothing','    _block_count!(:descriptor_growths,1);_block_max!(:descriptor_coexist_payload,28*(length(U.slab)+C))')
inject('    used=Base.Checked.checked_add(U.used,8);ns=Base.Checked.checked_add(U.slabs,1)','    _block_count!(:slab_appends,1)')
inject('        av=allocate(Vector{Float64},D);ar=allocate(Vector{Int32},D);ap=allocate(Vector{Int32},D)','    _block_count!(:directory_growths,1);_block_count!(:directory_copied_bytes,24*U.slabs)\n    _block_max!(:directory_coexist_payload,24*(length(U.values)+D))')
inject('function _bgu_stage!(U,b::Int,offset::Int=0)','    _block_count!(:merge_stage_reads,Int(U.count[b]));_block_count!(:merge_stage_writes,Int(U.count[b]))')
inject('    left=Int(U.count[b]);_bgu_stage!(U,b);_bgu_stage!(U,n,left)','    _block_count!(:merges,1);_block_count!(:merge_tuple_moves,total)')
inject('    for i in k:cnt-1','        _block_count!(:delete_tuple_moves,1)')
inject('            U.values[s][idx]=v;U.row_ids[s][idx]=rid;U.row_backs[s][idx]=p','            _block_count!(:extent_tuple_moves,1)')
inject('    if count==32','    _block_count!(:splits,1);_block_count!(:split_stage_reads,32);_block_count!(:split_stage_writes,33);_block_count!(:split_final_writes,33)')
inject('        for k in count:-1:pos','            _block_count!(:insert_tuple_moves,1)')
inject('            _bgu_write!(U,bh,kh,y...);_bgu_write!(U,bt,kt,x...);i+=1;k+=1','            _block_count!(:swap_tuple_moves,2)')
inject('            _bgu_write!(U,b,k,y...);b=nb;k=nk','            _block_count!(:rotation_tuple_moves,1)')
inject('        _bgu_write!(U,b,k,x...)','        _block_count!(:rotation_tuple_moves,1)')
keys=['allocation_requests','requested_payload_bytes','tuple_writes','row_handle_repairs','back_repairs','gap_moves','row_growths','row_copied_bytes','row_coexist_payload','grown_copied_bytes','descriptor_growths','descriptor_coexist_payload','slab_appends','directory_growths','directory_copied_bytes','directory_coexist_payload','merge_stage_reads','merge_stage_writes','merges','merge_tuple_moves','delete_tuple_moves','extent_tuple_moves','splits','split_stage_reads','split_stage_writes','split_final_writes','insert_tuple_moves','swap_tuple_moves','rotation_tuple_moves']
header='const _block_probe_counts=Dict{Symbol,Int}('+','.join(':'+k+'=>0' for k in keys)+')\n_block_count!(k,n)=(_block_probe_counts[k]+=n;nothing)\n_block_max!(k,n)=(_block_probe_counts[k]=max(_block_probe_counts[k],n);nothing)\n'
save('probe-upper.jl',header+rename(u));save('probe-bg.jl',rename(b))
# only pure invariant function; do not import Test or failure helpers
oracle=(C/'block-oracles.jl').read_text().split('function _bgu_materialize')[0]
save('probe-oracles.jl',oracle+rename(oracle))
js('probe-inverse.json',dict(renames=renames,injections=injections,allocator={'old':old,'new':new},header=header,sources={str(C/'block-upper.jl'):sha(C/'block-upper.jl'),str(C/'block-bg.jl'):sha(C/'block-bg.jl'),str(C/'block-oracles.jl'):sha(C/'block-oracles.jl')},counts=keys))
# Separate ordinary stage: GREEN files unchanged except three new includes/files.
s=json.loads((G/'stages.json').read_text())['green'];stage=W/'task3-cost-stage';stage.mkdir(exist_ok=False)
for n,h in s['sha256'].items():
 src=Path(s['path'])/n
 if sha(src)!=h:raise RuntimeError('GREEN stage drift '+n)
 dest=stage/n;dest.parent.mkdir(exist_ok=True,parents=True);shutil.copyfile(src,dest)
root=stage/'src/JSimplex.jl';t=root.read_text();at=t.rfind('\nend');assert at>0
includes='\ninclude("probe-upper.jl")\ninclude("probe-bg.jl")\ninclude("probe-oracles.jl")\n'
root.write_text(t[:at]+includes+t[at:])
for n in ['probe-upper.jl','probe-bg.jl','probe-oracles.jl']:shutil.copyfile(E/n,stage/'src'/n)
js('stages.json',{'cost':{'path':str(stage),'sha256':{str(p.relative_to(stage)):sha(p) for p in sorted(stage.rglob('*')) if p.is_file()},'source':s['path'],'baseline_sha256':s['sha256'],'inserted_includes':includes}})
# same lifecycle and preflight, Block factory only, probe functions live in J.
cost=(O/'cost.jl').read_text().replace('include("probe-oracles.jl")\n','').replace('_dynamic_bg','_block_bg')
save('cost.jl',cost)
js('reused-files.json',reused)
js('authorization.json',dict(scope='Prepare Block BG Task3 cost driver/admission and independent review ONLY; no Julia/query/parser/import/compile/seal/reservation/run.',entry='2642947bc35143bbd72c1c4b9509a4a3e3bcc86d'))
with (W/'progress.md').open('a') as f:f.write('\nTask3 cost preparation: in progress at2642947b. User requests concrete driver/conditions/review ONLY, no Julia. Fresh host238groups ANDsessions empty. Separate ordinary84-file stage, unchanged timed candidate, new renamed instrumented probe only; all accepted scripts/raw remain frozen.\n')
print('Prepared new controls,84-file stage,29 probe metrics,unchanged fixture tokens; NO Julia')
