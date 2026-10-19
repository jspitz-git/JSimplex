from pathlib import Path
import json,hashlib,re,tomllib
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');C=R/'diagnostics/direct-bg-blocked-update/reproduce';Q=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-TASK2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks={}
first=json.loads((Q/'review-first.json').read_text())
changed=('factor.jl','factor-fault.jl','adapter-source-map.json','lifecycle-tests.jl','adapter-work-memory.md')
# Explicit named history resolution, never wildcard or a coincidentally matching blob.
resolution={str((C/n).relative_to(R)):str((Q/(n+'.before-review')).relative_to(R)) for n in changed}
resolution[str((Q/'REPORT.md').relative_to(R))]=str((Q/'REPORT.md.before-review').relative_to(R))
checks['initial_receipt_was_rejection']=first['accepted'] is False
checks['initial_exact_named_bindings']=all(sha(R/resolution.get(p,p))==h for p,h in first['sha256'].items())
checks['named_resolution_exactly_six']=len(resolution)==6 and all(p in first['sha256'] for p in resolution)
fix=json.loads((Q/'review-fix.json').read_text())
checks['corrected_binding']=all(sha(Path(p))==h for p,h in fix['sha256'].items())
a=(C/'factor.jl').read_text();m=json.loads((C/'adapter-source-map.json').read_text())
checks['source_map_actual_original']=m['original_suffix'] in (R/'src/triangular_factorization.jl').read_text()
checks['source_map_actual_candidate']=m['qualified_suffix'] in a
s=m['qualified_suffix'].replace('            _emit(probe,:pure,column_index,last_pure)\n','')
guard='''        if probe!==nothing
            _emit(probe,:scalar_pivot,column_index,J._upper_value(column,column_index),
                  J._upper_value(column,column_index+1),swapped)
        end
'''
checks['scalar_guard_exactly_once']=s.count(guard)==1
s=s.replace(guard,'')
for symbol in m['substitutions']['namespace_symbols']:s=s.replace('J.'+symbol,symbol)
s=re.sub(r'\bFloat64\b','T',s);s=re.sub(r'\br\b','position',s)
checks['corrected_scalar_inverse']=s==m['original_suffix']
checks['only_original_full_pure_lookahead']=a.count('J._last_pure_bartels_golub_swap(')==1 and 'if !blocked || iszero(J._upper_value(inner.upper[r],r))' in a
checks['corrected_adapter_fault_inverse']=(C/'factor-fault.jl').read_text().replace('BGBlockedAdapterFault','BGBlockedAdapter').replace('BGBlockedPanelFault','BGBlockedPanel')==a
s=(C/'panel-fault.jl').read_text().replace('BGBlockedPanelFault','BGBlockedPanel').replace(m['fault_control'],'')
for anchor,hook in m['fault_hooks']:
 checks['unique_'+hook.strip()]=s.count(anchor+hook)==1
 s=s.replace(anchor+hook,anchor)
checks['panel_fault_inverse']=s==(C/'panel.jl').read_text()
checks['task1_frozen']=all(sha(C/n)==first['sha256'][str((C/n).relative_to(R))] for n in ('panel.jl','panel-tests.jl','work-memory-ledger.md','source-map.json'))
checks['fixtures_numerical_tests_frozen']=all(sha(C/n)==first['sha256'][str((C/n).relative_to(R))] for n in ('fixtures.json','fixtures.toml','numerical-tests.jl','overlay-manifest.json','panel-fault.jl'))
l=(C/'lifecycle-tests.jl').read_text();ledger=(C/'adapter-work-memory.md').read_text()
checks['no_op_column_identity']='j=f.inner.column_order[end];@test f.inner.positions[j]==96' in l and 'a=Vector(B[:,j])' in l and 'J.replace_column!(f,x,j)' in l
checks['late_fault_assertions']=all(v in l for v in ('begins[]==2 && FK.arm!(:writeback,sentinel)','caught===sentinel && FK.hits[]==1 && begins[]==2','count(==(:panel_commit),events)==1 && !(:finish in events)','isempty(f.inner.updates) && failed_cache(f)'))
checks['corrected_ledger']=all(v in ledger for v in ('n96=11488','2copies,5 FTRAN entries','additional native identity constructors and12 elimination entries','O(sum(log(nnz(column)+1)))'))
o=json.loads((C/'overlay-manifest.json').read_text());stage=Path(o['stage'])
checks['overlay_original_hashes']=all(sha(R/p)==h for p,h in o['original_sha256'].items())
checks['overlay_stage_hashes']=all(sha(stage/p)==h for p,h in o['stage_sha256'].items())
checks['root_inverse']=(stage/'src/JSimplex.jl').read_text().replace(o['root_insertion'],'',1)==(R/'src/JSimplex.jl').read_text()
checks['ordinary_source_identity']=all(sha(R/'diagnostics/direct-lu-policy-adapters/reproduce'/p)==h and sha(stage/'src'/p)==h for p,h in o['ordinary'].items())
f=json.loads((C/'fixtures.json').read_text());t=tomllib.loads((C/'fixtures.toml').read_text())
checks['fixture_serializations']=f['fixtures']==t['fixtures']
initial_tests=json.loads((Q/'tests-first.json').read_text())
checks['tests_first_exact_preserved_versions']=all(sha(Q/(Path(p).name+'.before-author-fix'))==h for p,h in initial_tests['sha256'].items())
expected={'panel.jl','panel-tests.jl','work-memory-ledger.md','source-map.json','factor.jl','factor-fault.jl','panel-fault.jl','lifecycle-tests.jl','numerical-tests.jl','fixtures.json','fixtures.toml','overlay-manifest.json','adapter-source-map.json','adapter-work-memory.md'}
checks['candidate_full_fourteen_membership']={p.name for p in C.iterdir() if p.is_file()}==expected
out=dict(scope='Fresh final byte/source review checks only; no Julia, numerical simulation or old checker rerun',all_passed=all(checks.values()),checks=checks,initial_binding_resolution=resolution,sha256={str(p.relative_to(R)):sha(p) for p in sorted(C.iterdir()) if p.is_file()})
with (Q/'reviewer-final-check.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps({'all_passed':out['all_passed'],'checks':checks},indent=2))
