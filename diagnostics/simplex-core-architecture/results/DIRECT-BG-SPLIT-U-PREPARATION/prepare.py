from pathlib import Path
import json,hashlib
R=Path.cwd(); Q=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-SPLIT-U-PREPARATION'; N=R/'diagnostics/direct-bg-split-upper/reproduce'
old=R/'diagnostics/direct-bg-block-upper/reproduce/block-upper.jl'
source=old.read_text();renamed=source.replace('BGBlockUpper','BGSplitUpper').replace('_bgu_','_sbu_')
a=renamed.index('function _sbu_reserve_block!(');z=renamed.index('function _sbu_link_block!',a)
replacement='function _sbu_target(required::Int)::Int\n    1<=required<=32 || throw(ArgumentError("split U required capacity"))\n    target=1\n    while target<required;target*=2;end\n    return target\nend\nfunction _sbu_reserve_block!(U::BGSplitUpper,required::Int,allocate,limit::Integer)::Int\n    target=_sbu_target(required)\n    b=_sbu_free_block(U,target)\n    if b==0;_sbu_append_slab!(U,allocate,limit);b=Int(U.bins[32]);end\n    # Local validation only; all fallible work precedes unlinking the free donor.\n    1<=b<=U.used || throw(ArgumentError("split U free descriptor"))\n    _sbu_handle(b,32,limit)\n    cap=Int(U.capacity[b]);s=Int(U.slab[b]);start=Int(U.start[b])\n    U.count[b]==0 && U.column[b]==0 && target<=cap<=32 || throw(ArgumentError("split U free extent"))\n    1<=s<=U.slabs || throw(ArgumentError("split U slab"))\n    last=Base.Checked.checked_add(start,cap-1);_sbu_limit(last,limit)\n    1<=start<=last<=length(U.values[s]) && length(U.values[s])==length(U.row_ids[s])==length(U.row_backs[s]) || throw(ArgumentError("split U extent bounds"))\n    cap==target && return b\n    suffix=Base.Checked.checked_add(U.used,1);_sbu_handle(suffix,32,limit)\n    nextstart=Base.Checked.checked_add(start,target);_sbu_limit(nextstart,limit)\n    remainder=cap-target\n    Base.Checked.checked_add(nextstart,remainder-1)==last || throw(ArgumentError("split U partition"))\n    _sbu_reserve_descriptors!(U,suffix,allocate,limit)\n    # Completed descriptor growth is allowed on later failure, but no active extent changes.\n    _sbu_take!(U,b)\n    U.capacity[b]=Int32(target)\n    U.slab[suffix]=Int32(s);U.start[suffix]=Int32(nextstart);U.capacity[suffix]=Int32(remainder)\n    U.count[suffix]=0;U.column[suffix]=0;U.prev[suffix]=0;U.next[suffix]=0\n    U.used=suffix\n    _sbu_free!(U,b);_sbu_free!(U,suffix)\n    return b # Still free; caller consumes exactly one reservation at its commit point.\nend\n'
removed=renamed[a:z]
with (Q/'original-reserve-renamed.jl.txt').open('x') as f:f.write(removed)
with (Q/'replacement-reserve.jl.txt').open('x') as f:f.write(replacement)
new=renamed[:a]+replacement+renamed[z:]
with (N/'split-upper.jl').open('x') as f:f.write(new)
inverse=new.replace(replacement,removed,1).replace('BGSplitUpper','BGBlockUpper').replace('_sbu_','_bgu_')
if inverse!=source:raise RuntimeError('whole source inverse')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
record={'scope':'Task1 offline candidate only; UNEXECUTED','inverse_equal':True,'renames':{'BGBlockUpper':'BGSplitUpper','_bgu_':'_sbu_'},'changed_region':'only reserve_block! replaced, adding target helper','sha256':{str(p.relative_to(R)):sha(p) for p in [old,N/'split-upper.jl',Q/'original-reserve-renamed.jl.txt',Q/'replacement-reserve.jl.txt',Path(__file__).resolve()]}}
with (N/'source-bindings.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps({'whole_source_inverse':True,'candidate_lines':len(new.splitlines()),'sha256':sha(N/'split-upper.jl')}))
