"""Independent attribution reconstruction; no prior script or Julia execution."""
from pathlib import Path
import json,sys,tomllib,collections,ast
D=Path(__file__).resolve().parent;sys.dont_write_bytecode=True;sys.path.insert(0,str(D))
import control as c
report=c.rd(D/'attribution.json');out=D/'runs/profile300/output';checks={}
def ck(n,v):
 checks[n]=bool(v)
 if not v:raise AssertionError(n)
def first_site(z):
 for f in z['stack'].splitlines():
  bits=f.split(' | ')
  if len(bits)>=2 and '/task3-driver-stages/green/src/' in bits[1]:return bits[1].split('/src/')[-1]
 return ''
def classify(z):
 site=first_site(z);typ=z['type'];frames=z['stack'].splitlines()
 if not any(f.startswith('lifecycle | ') for f in frames):return 'outside_lifecycle_timer_result'
 if not site and typ.startswith('Tuple{') and any('helpers.jl:45 |' in f for f in frames):return 'lifecycle_return_tuples'
 rules=[
 ('native_orientation_call_CSC_boxes',site=='_bgx_export.jl:84' and typ.startswith('SparseMatrixCSC')),
 ('refactor_call_CSC_policy_boxes',site=='_bgx_factor.jl:63' and (typ.startswith('SparseMatrixCSC') or typ=='JSimplex._NativePivotPolicy')),
 ('build_owner_and_factor_wrapper',typ=='JSimplex._BGXBuildOwner' or typ.startswith('JSimplex.BGExportFactor{')),
 ('import_result_tuple',site=='_bgx_import.jl:56' and typ.startswith('Tuple{')),
 ('nnz_argument_Int64_boxes',site in ('_bgx_export.jl:8','_bgx_export.jl:84') and typ=='Int64'),
 ('workspace_owner',typ=='JSimplex.BGExportWorkspace'),
 ('orientation_cache_tuple',typ=='NTuple{4, Vector{Float64}}' and '_bgx_scale_mode' in z['stack']),
 ('reference_build_type_metadata',site=='direct-factor.jl:144' and typ=='Core.SimpleVector'),
 ('reference_refactor_backend_box',site=='direct-factor.jl:172' and typ.startswith('JSimplex.DirectLowerBackend')),
 ('reference_normalization_temporary',site=='direct-factor.jl:84'),
 ('permutation_mask',site in ('factor-export.jl:54','_bgx_workspace.jl:9')),
 ('orientation_vectors',site in ('factor-export.jl:73','huangfu_hall_factorization.jl:180') or (site=='_bgx_workspace.jl:8' and '_bgx_scale_mode' in z['stack'])),
 ('orientation_matches_closure','#matches#' in typ)]
 matches=[name for name,pred in rules if pred]
 if len(matches)>1:raise AssertionError(('overlapping classifications',site,typ,matches))
 return matches[0] if matches else 'other_lifecycle_allocations'
ck('attribution_raw_hashes',len(report['sha256'])==16 and c.bindings(report) and report['script_sha256']==c.sha(D/'attribution.py'))
ast.parse((D/'attribution.py').read_text());ck('attribution_syntax_not_executed',True)
classified=[]
for i in range(1,17):
 raw=tomllib.loads((out/f'profile-{i}.toml').read_text());cnt=collections.Counter();detail=collections.Counter()
 for z in raw['allocations']:
  cat=classify(z);cnt[cat]+=z['count'];detail[(cat,first_site(z),z['type'],z['size'])]+=z['count']
 expected=report['profiles'][i-1]
 ck(f'full_partition_{i}',sum(cnt.values())==raw['profile_count'] and dict(cnt)==expected['categories'])
 ck(f'every_site_type_size_count_{i}',detail==collections.Counter({(x['category'],x['site'],x['type'],x['size']):x['count'] for x in expected['sites']}))
 native=raw['backend']=='native';candidate=raw['side']=='candidate';dense=raw['fixture'].startswith('dense')
 ck(f'closure_count_size_{i}',sum(z['count'] for z in raw['allocations'] if '#matches#' in z['type'])==(3 if native else 0) and all(z['size']==32 for z in raw['allocations'] if '#matches#' in z['type']))
 if candidate:
  ck(f'CSC_orientation_six48_{i}',sum(z['count'] for z in raw['allocations'] if first_site(z)=='_bgx_export.jl:84' and z['type'].startswith('SparseMatrixCSC') and z['size']==48)==(6 if native else 0))
  ck(f'refactor_CSC_two48_{i}',sum(z['count'] for z in raw['allocations'] if first_site(z)=='_bgx_factor.jl:63' and z['type'].startswith('SparseMatrixCSC') and z['size']==48)==2)
  ck(f'refactor_policy_two16_{i}',sum(z['count'] for z in raw['allocations'] if first_site(z)=='_bgx_factor.jl:63' and z['type']=='JSimplex._NativePivotPolicy' and z['size']==16)==2)
  ck(f'import_tuple_three16_{i}',sum(z['count'] for z in raw['allocations'] if first_site(z)=='_bgx_import.jl:56' and z['type'].startswith('Tuple{') and z['size']==16)==3)
  ck(f'dense_Int64_box_sites_{i}',cnt['nnz_argument_Int64_boxes']==(6*(2 if native else 1) if dense else 0) and all('ijl_box_int64' in z['stack'] and z['size']==8 for z in raw['allocations'] if classify(z)=='nnz_argument_Int64_boxes'))
 classified.append(cnt)
oldcells=c.rd(D.with_name('DIRECT-BG-EXPORT-WORKSPACE-COST-PREPARATION')/'runs/cost1-300/audit.json')['cells']
for j in range(8):
 r,v=classified[2*j:2*j+2];delta={k:v[k]-r[k] for k in set(r)|set(v)}
 ck(f'paired_full_delta_{j}',delta==report['pairs'][j]['category_deltas'] and sum(n for k,n in delta.items() if k!='outside_lifecycle_timer_result')==report['pairs'][j]['profiled_event_delta'])
 ck(f'residual_group_delta_zero_{j}',delta['other_lifecycle_allocations']==0)
 old=oldcells[j]['statistics']['events']
 ck(f'old_cost_delta_matches_{j}',old['candidate']['median']-old['reference']['median']==report['pairs'][j]['profiled_event_delta'])
ck('sparse32_net_plus5_and_intrinsic_plus7',sum(v for k,v in report['pairs'][0]['category_deltas'].items() if k!='outside_lifecycle_timer_result')==5 and sum(v for k,v in report['pairs'][0]['category_deltas'].items() if k not in ('outside_lifecycle_timer_result','lifecycle_return_tuples'))==7)
ck('native_net_deltas',[report['pairs'][i]['profiled_event_delta'] for i in (0,2,4,6)]==[5,9,1,-6])
ck('dense96_orientation_savings',classified[12]['orientation_vectors']==24 and classified[13]['orientation_vectors']==8 and classified[13]['orientation_cache_tuple']==1)
ck('sparse32_no_mask_orientation_savings',classified[0]['permutation_mask']==classified[1]['permutation_mask']==9 and classified[0]['orientation_vectors']==classified[1]['orientation_vectors']==24)
stage=Path(c.rd(D/'stages.json')['green']['path'])/'src'
ck('candidate_stage_exact_sources',all((stage/f'_bgx_{name}.jl').read_bytes()==(c.C/(name+'.jl')).read_bytes() for name in ('workspace','export','import','factor')))
timing=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia/base/timing.jl').read_text()
ck('outer_timed_result_after_GC_snapshot',timing.index('local diff = GC_Diff(gc_num(), stats)',timing.index('macro timed(ex)'))<timing.index('value=val,',timing.index('macro timed(ex)')))
text=(D/'REPORT.md').read_text()
ck('limitations_preserved',all(x in text for x in ('+41 anomaly','14 reference-only','Two additional reference-only return tuples','not a complete native malloc/calloc/realloc ledger','not each boxed integer','not a new performance qualification','200000-record check happens **after**')))
ck('report_closure_scope','three on each side' in text and 'Core.Box' in text and 'does not claim closures are allocation-free' in text)
result=dict(all_passed=all(checks.values()),checks=checks,check_count=len(checks),
 scope='Independent raw stack/site/type/size and count-ledger verification; no Julia, typed IR or old attribution script execution',
 sha256={str(D/n):c.sha(D/n) for n in ('REPORT.md','attribution.py','attribution.json','source-check.json','result-integrity-check.json')})
with (D/'attribution-review-check.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=result['all_passed'],checks=len(checks))))
