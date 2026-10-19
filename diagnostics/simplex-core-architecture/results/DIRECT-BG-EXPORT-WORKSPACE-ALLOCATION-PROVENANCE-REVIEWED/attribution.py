"""Post-run stack attribution only; no Julia and no old auditor execution."""
from pathlib import Path
import json,tomllib,hashlib,collections,re
D=Path(__file__).resolve().parent
P=D/'runs/profile300/output'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def require(v,s):
 if not v:raise RuntimeError(s)
def frames(x):return x['stack'].splitlines()
def site(x):
 fs=[f.split(' | ')[1].split('/src/')[-1] for f in frames(x) if '/task3-driver-stages/green/src/' in f]
 return fs[0] if fs else ''
def category(x):
 s=site(x);t=x['type'];stack=x['stack']
 if 'lifecycle |' not in stack:return 'outside_lifecycle_timer_result'
 if not s and 'helpers.jl:45' in stack and t.startswith('Tuple{'):return 'lifecycle_return_tuples'
 if s=='_bgx_export.jl:84' and t.startswith('SparseMatrixCSC'):return 'native_orientation_call_CSC_boxes'
 if s=='_bgx_factor.jl:63' and (t.startswith('SparseMatrixCSC') or t=='JSimplex._NativePivotPolicy'):return 'refactor_call_CSC_policy_boxes'
 if t in ['JSimplex._BGXBuildOwner'] or t.startswith('JSimplex.BGExportFactor{'):return 'build_owner_and_factor_wrapper'
 if s=='_bgx_import.jl:56' and t.startswith('Tuple{'):return 'import_result_tuple'
 if s in ['_bgx_export.jl:8','_bgx_export.jl:84'] and t=='Int64':return 'nnz_argument_Int64_boxes'
 if t=='JSimplex.BGExportWorkspace':return 'workspace_owner'
 if t=='NTuple{4, Vector{Float64}}' and '_bgx_scale_mode' in stack:return 'orientation_cache_tuple'
 if s=='direct-factor.jl:144' and t=='Core.SimpleVector':return 'reference_build_type_metadata'
 if s=='direct-factor.jl:172' and t.startswith('JSimplex.DirectLowerBackend'):return 'reference_refactor_backend_box'
 if s=='direct-factor.jl:84':return 'reference_normalization_temporary'
 if s=='factor-export.jl:54' or s=='_bgx_workspace.jl:9':return 'permutation_mask'
 if s in ['factor-export.jl:73','huangfu_hall_factorization.jl:180'] or (s=='_bgx_workspace.jl:8' and '_bgx_scale_mode' in stack):return 'orientation_vectors'
 if '#matches#' in t:return 'orientation_matches_closure'
 return 'other_lifecycle_allocations'
rows=[];files={str(p):sha(p) for p in sorted(P.glob('profile-*.toml'))};checks={}
for i in range(1,17):
 p=P/f'profile-{i}.toml';d=tomllib.loads(p.read_text());cats=collections.Counter();sites={}
 for x in d['allocations']:
  c=category(x);cats[c]+=x['count'];k=(c,site(x),x['type'],x['size'])
  sites[k]=sites.get(k,0)+x['count']
 require(sum(cats.values())==d['profile_count'],'Profile partition')
 inside=d['profile_count']-cats['outside_lifecycle_timer_result']
 require(not any(x['type']=='Core.Box' for x in d['allocations']),'Unexpected Core.Box')
 rows.append(dict(id=i,fixture=d['fixture'],backend=d['backend'],side=d['side'],ordinary_events=d['ordinary']['events'],profiled_events=d['profiled']['events'],ordinary_bytes=d['ordinary']['bytes'],profiled_bytes=d['profiled']['bytes'],profile_count=d['profile_count'],lifecycle_heap_records=inside,gc_minus_lifecycle_heap=d['profiled']['events']-inside,categories=dict(cats),sites=[dict(category=k[0],site=k[1],type=k[2],size=k[3],count=v) for k,v in sorted(sites.items())]))
pairs=[]
for a,b in zip(rows[::2],rows[1::2]):
 delta={k:b['categories'].get(k,0)-a['categories'].get(k,0) for k in sorted(a['categories'].keys()|b['categories'].keys())}
 require(a['gc_minus_lifecycle_heap']==b['gc_minus_lifecycle_heap'],'Unequal native/unprofiled residual')
 require(delta.get('other_lifecycle_allocations',0)==0,'Unexplained allocation count delta')
 require(a['categories'].get('outside_lifecycle_timer_result',0)==14 and b['categories'].get('outside_lifecycle_timer_result',0)==0,'Unexpected timer result partition')
 gc=b['profiled_events']-a['profiled_events'];inside=b['lifecycle_heap_records']-a['lifecycle_heap_records']
 require(gc==inside,'Delta reconciliation')
 require(delta.get('orientation_matches_closure',0)==0,'Closure count changed')
 pairs.append(dict(fixture=a['fixture'],backend=a['backend'],ordinary_event_delta=b['ordinary_events']-a['ordinary_events'],profiled_event_delta=gc,lifecycle_heap_delta=inside,outside_timer_delta=delta['outside_lifecycle_timer_result'],gc_minus_heap_per_side=a['gc_minus_lifecycle_heap'],category_deltas=delta))
checks={'all16_profiles_partitioned':len(rows)==16,'all8_GC_deltas_reconciled':len(pairs)==8,'unclassified_category_delta_zero':True,'outside_timer_records_separated':True,'no_Core_Box_records':True,'matching_closures_have_zero_delta':True,'dense96_native_ordinary_anomaly_preserved':rows[12]['ordinary_events']==2826 and rows[12]['profiled_events']==2785}
require(all(checks.values()),'Checks')
record=dict(checks=checks,all_passed=True,scope='New post-run stack attribution; not full native allocation ledger or speedup measurement',profiles=rows,pairs=pairs,sha256=files,script_sha256=sha(Path(__file__)))
with (D/'attribution.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
for pair in pairs:print(pair['fixture'],pair['backend'],pair['profiled_event_delta'],pair['category_deltas'])
