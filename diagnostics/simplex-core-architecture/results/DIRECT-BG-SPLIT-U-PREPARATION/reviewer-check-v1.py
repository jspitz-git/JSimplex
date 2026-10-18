"""Independent one-shot OFFLINE source/hash/integer checks. Never loads Julia or author scripts."""
from pathlib import Path
import hashlib,json,re
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
Q=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-SPLIT-U-PREPARATION'
N=R/'diagnostics/direct-bg-split-upper/reproduce'
O=R/'diagnostics/direct-bg-block-upper/reproduce'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def txt(p):return p.read_text()
def ren(s):return s.replace('BGBlockUpper','BGSplitUpper').replace('_bgu_','_sbu_').replace('BGUInjectedAllocationFailure','SBUInjectedAllocationFailure')
c=txt(N/'split-upper.jl');old=ren(txt(O/'block-upper.jl'));t=txt(N/'split-upper-tests.jl');o=txt(N/'split-oracles.jl')
a=c.index('function _sbu_target(');b=c.index('function _sbu_link_block!(')
x=old.index('function _sbu_reserve_block!(');y=old.index('function _sbu_link_block!(')
split=c[a:b];checks={}
checks['unchanged_source_prefix_suffix']=c[:a]==old[:x] and c[b:]==old[y:]
checks['saved_reserve_regions']=split==txt(Q/'replacement-reserve.jl.txt') and old[x:y]==txt(Q/'original-reserve-renamed.jl.txt')
oldtests=ren(txt(O/'block-upper-tests.jl')).replace('function _sbu_structural_tests()','function _sbu_inherited_structural_tests()').replace('Include block-upper.jl and block-oracles.jl','Include split-upper.jl and split-oracles.jl')
checks['inherited_tests_exact']=t[:len(oldtests)]==oldtests
base=o[:o.index('\n# Test-only free extent fixture,')];u=base.index('    @assert sum(Int(U.capacity[b])');v=base.index('    livehandles=',u)
checks['inherited_oracles_exact_except_added_checks']=base[:u]+base[v:]==ren(txt(O/'block-oracles.jl'))
checks['testset_counts']=(len(re.findall('@testset "',oldtests)),len(re.findall('@testset "',t)))==(14,25)
publish=split.index('    _sbu_take!(U,b)')
checks['all_allocating_checked_work_before_unlink']=all(split.index(s)<publish for s in ('_sbu_append_slab!','_sbu_handle(suffix','_sbu_limit(nextstart','split U partition','_sbu_reserve_descriptors!')) and all(s not in split[publish:] for s in ('allocate(','checked_','_sbu_limit(','_sbu_handle('))
checks['no_added_coefficient_work']=all(s not in split for s in ('copyto!','_sbu_write!','_sbu_clear!','Vector{','zeros('))
checks['single_suffix_descriptor']=split.count('suffix=Base.Checked.checked_add(U.used,1)')==1 and 'U.used=suffix' in split
classes=(1,2,4,8,16,32);pairs=0
for required in range(1,33):
 target=1 << (required-1).bit_length()
 assert target==min(k for k in classes if k>=required)
 for cap in range(target,33):
  assert target+(cap-target)==cap and 0<=cap-target<=31
  for start in (1,4,25,225):assert start+target+(cap-target)-1==start+cap-1
  pairs+=1
checks['all_target_donor_integer_partitions']=pairs==373
sums=[]
for tail in range(1,32):
 cap=tail;copied=0
 while cap<32:
  copied+=cap;cap=1 << cap.bit_length()
 sums.append(copied)
checks['all_exact_tail_monotone_bounds']=max(sums)==31 and all(n<=31 for n in sums)
checks['independent_monotone_payload_arithmetic']=32*8+28*8+28*16+4096+24==5048 and 32+7+7+3+3==52 and 28*8==224 and sum((1,2,4,8,16))==31
checks['independent_persistent_payload']=16*256+4*64+28*16+32*40+656+8*40+24==7080
checks['monotone_allocation_vs_retained']=7080-(32*40+656+8*40)+224==5048
checks['conservative_bound_arithmetic']=16*419840+4*4672+28*22148+40*64+656+24*2461==7418552
checks['directory_and_descriptor_publication_counter']='observe();totals[:requests]+=1' in o and '_sbu_set_with!(U,r,c,v,allocate,typemax(Int32));observe()' in o and 'isbitstype(T) ? sizeof(T) : sizeof(Ptr{Cvoid})' in o
sourcecheck=json.loads(txt(Q/'source-check.json'));binding=json.loads(txt(N/'source-bindings.json'));geometry=json.loads(txt(Q/'geometry-model.json'))
checks['author_sourcecheck_hashes_current']=all(h(R/p)==value for p,value in sourcecheck['sha256'].items())
checks['candidate_binding_hashes_current']=all(h(R/p)==value for p,value in binding['sha256'].items())
checks['geometry_source_hash_current']=h(Q/'geometry-model.py')==geometry['executed_source_sha256']
first=json.loads(txt(Q/'tests-first.json'));af=json.loads(txt(Q/'author-counter-fix.json'));bf=json.loads(txt(Q/'author-budget-fix.json'))
checks['initial_oracle_snapshot_mapping']=h(Q/'oracles.before-author-counters.jl.txt')==first['sha256'][str((N/'split-oracles.jl').relative_to(R))]==af['before_sha256'] and h(N/'split-oracles.jl')==af['after_sha256']
checks['initial_tests_snapshot_mapping']=h(Q/'tests.before-author-budget.jl.txt')==first['sha256'][str((N/'split-upper-tests.jl').relative_to(R))]==bf['before_sha256'] and h(N/'split-upper-tests.jl')==bf['after_sha256']
inputs=sorted(set([R/p for p in sourcecheck['sha256']]+[Q/'source-check.json',R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-SPLIT-U-PLAN/review.md']))
result={'scope':'Independent offline text/hash/integer checks only; not Julia parser/runtime/numerical checks','all_passed':all(checks.values()),'checks':checks,'target_donor_pairs':pairs,'tail_copy_bounds':sums,'read_scope_sha256':{str(p.relative_to(R)):h(p) for p in inputs},'executed_source_sha256':h(Path(__file__))}
with (Q/'reviewer-check-v1.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({'all_passed':result['all_passed'],'checks':checks,'read_hash_count':len(inputs),'target_donor_pairs':pairs}))
if not result['all_passed']:raise SystemExit(1)
