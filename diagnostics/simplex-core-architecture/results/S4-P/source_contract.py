from pathlib import Path
import json,hashlib,subprocess
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture';E=D/'results/S4-P';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();checks={}
def ck(k,v):checks[k]=bool(v)
s=(R/'src/huangfu_hall_factorization.jl').read_text();G=json.loads((D/'results/S4-G/publication-1-pins.json').read_text())['inventory'];M=json.loads((D/'results/S4-M/cost-1-pins.json').read_text())['inventory'];host=json.loads((E/'host-before.json').read_text())
for f in ['src/huangfu_hall_factorization.jl','src/factorization.jl']:ck('G_source_match_'+f,sha(R/f)==G[str(R/f)]['sha256'])
ck('all554_M_launchpins_current',len(M)==554 and all(sha(p)==v['sha256'] for p,v in M.items()))
ck('user6_unchanged',len(host['user_hashes'])==6 and all(sha(p)==h for p,h in host['user_hashes'].items()))
ck('production_test_ci_equal_master',not subprocess.check_output(['git','diff','master','--','src','test','.github']))
ck('HH_reference_reuse_disabled','lu!(F,convert(SparseMatrixCSC{Float64,Int},B);reuse_symbolic=false)' in s)
f=s[s.index('function _hh_forward!'):s.index('function _unit_transpose_rhs')]
ck('prepared_copies_two_vectors',all(x in f for x in ['prepare && copyto!(f.prepared_partial,x)','copyto!(f.prepared_direction,destination);f.prepared_valid=true']))
ck('ordinary_forward_no_prepare','_hh_forward!(destination,f,rhs,false)' in f)
ck('forward_history_once','for t in f.updates;_hh_apply!(x,t,false);end' in f)
b=s[s.index('function transpose_solve!'):s.index('# Count and pack')];ck('backward_history_reverse_once','for t in Iterators.reverse(f.updates);_hh_apply!(x,t,true);end' in b)
u=s[s.index('function replace_column!'):s.index('_hh_refactor_lu!')]
ck('prepared_update_copy','copyto!(u,f.prepared_partial)' in u)
ck('one_update_unit_transpose',u.count('_hh_unit_transpose!(f,p)')==1)
ck('update_consumes_prepared','push!(f.updates,candidate)' in u and 'f.prepared_valid=false' in u)
ck('default_pivot_safeguard','_positive_tolerance(T,1//10^12)' in u and '_pivot_magnitude(mu)>tolerance' in u)
r=s[s.index('function refactorize!'):s.index('function copy_basis_factorization')]
ck('extract_before_retire',r.index('_hh_extract_base(')<r.index('_hh_retire_pair!'))
ck('private_suffix_retirement','(f.shared_update_count+1):length(f.updates)' in r)
ck('publish_clears_history_prepared','empty!(f.updates);f.prepared_valid=false' in r)
sc=s[s.index('function _hh_scale_mode'):s.index('function _hh_scale_mode')+6500]
# Bounded specifically to the next function rather than count arbitrary later code.
sc=sc[:sc.index('\nfunction ',1)]
ck('at_most_one_native_orientation_entry',sc.count('ldiv!(')==1)
inputs=json.loads((E/'offline-input-checks.json').read_text());ck('exact_input_10_checks',len(inputs['checks'])==10 and all(inputs['checks'].values()));ck('19138_bits_frozen',inputs['bit_roundtrips']==19138 and sha(E/'exact-inputs.json')==inputs['exact_inputs_sha256'])
plan=R/'docs/superpowers/plans/2026-10-12-hh-history-lifecycle-cost-measurement.md';p=plan.read_text()
ck('nested_windows_not_added','Inner windows are SUBSETS' in p and 'outer-minus-inner' in p)
ck('no_owner_escape','return NOTHING rather than' in p and 'never retain any factor' in p)
ck('compilation_stop_no_retry','compile_time==recompile_time==0' in p and 'No exception retry' in p)
ck('native_retention_open','Native retention remains OPEN' in p)
ck('zero_execution_scope','No execution has occurred' in p)
ck('balanced8pairs_eachfixture','Four pairs of each order per fixture' in p)
files=set(M)|set(host['user_hashes']);files.update(str(x) for x in [E/'exact-inputs.json',E/'offline-input-checks.json',E/'prepare_inputs.py',E/'host-before.json',Path(__file__).resolve(),plan,R/'docs/superpowers/plans/2026-10-12-hh-history-lifecycle-cost-contract.md',D/'S4-HISTORY-LIFECYCLE-COST-CONTRACT.md',D/'S4-SYMBOLIC-PUBLICATION.md',D/'S4-SYMBOLIC-PUBLICATION-REVIEW.md',D/'S4-ALLOCATION-COUNTER-ATTRIBUTION.md',D/'S4-ALLOCATION-COUNTER-ATTRIBUTION-REVIEW.md',D/'results/S4-O/source-attribution.json'])
obj=dict(checks=checks,all_passed=all(checks.values()),sha256={p:sha(p) for p in sorted(files)},scope='P read-time source/evidence hashes; NOT numerical launch pins; no Julia/native/factor calls')
with (E/'source-contract.json').open('x') as out:json.dump(obj,out,indent=2);out.write('\n')
print(len(checks),len(files),checks);assert obj['all_passed']
