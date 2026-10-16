"""Offline arithmetic enumeration of fixed test branches, not Julia execution."""
from pathlib import Path
import json
D=Path(__file__).resolve().parent
# Expressions below follow individual test bodies; no result-dependent tuning.
groups=[
('Owned export identity and core row relocation',2*(5+6*12)+(5+6*7+5+1),'native: empty5 +six12 twice; Mark: empty5+six7+coupled5+core1'),
('Malformed export versus unsupported backend',9+1+6*(1+3*2+2)+2,'9 malformed+unsupported+six generic cases+two singular'),
('Actual orientation helper selects multiply, divide or neither',2*3+2*3,'two valid orientations and two unavailable, three checks each'),
('Normalization rejection and both original-row scaling conventions',4*2+2*2*3*2*(2+4+2),'four rejection pairs;24 cases each mode/identity+check_solutions+two aliases'),
('Three managers preserve solves, copies and prepared direction provenance',36*59+90*(59+152+5+3+28+32+4)+30,'36 n<2 base59;90 n>=2 add8*19+copy5+refactor3+7*4+indexed32+saved4;BG30'),
('Typed direct to fallback to direct refactors are transactional',18*25,'18cases: old24 +saved_fallback intent1'),
('Policy survives empty/copy/refactor/fallback and real controls',12*(55+2+2*2+6*4)+6*(55+8*2),'base55;native fallback2+two empty2+six controls4;Mark eight2'),
('Markowitz policy rejected before Float64 factory/export; compatibility',6*(2*3+15+13)+3,'six manager/normalize:two rejection triples+native15+Mark13;invalid3'),
('Other precisions retain ordinary arithmetic and input ownership',9*(3*6+2*2+2+3),'nine type/manager:three validarms6+two legacy2+two rejects+three ownership')]
expected=dict(green=dict(assertions=sum(n for _,n,_ in groups),groups=[[name,n,0,0,0] for name,n,_ in groups]),red=dict(assertions=7,groups=[['Missing direct policy contract (seven expected failures)',0,7,0,0]]))
ledger=dict(scope='Prospective source-derived test-entry ledger; no observed calls or complete native instruction/allocation count',assertion_formulas=[dict(name=a,assertions=b,derivation=c) for a,b,c in groups],groups={
'exports':dict(backend_constructions=21,real_export_calls=42,native_lu_refactors=12,export_identity_oracles=40,orientation_solve_upper_bound=24),
'rejections':dict(backend_construction_attempts=26,of_which_singular=2,generic_forward_solves=18,independent_backslash_factor_solves=18,unsupported_exports=6,malformed_checked_exports=9),
'orientation':dict(dense_lu_constructions=3,scale_helper_calls=4,orientation_solve_upper_bound=4),
'normalization':dict(backend_constructions=24,synthetic_exporters=24,checked_synthetic_exports=24,normalization_rejections=4,explicit_solve_entries=96,export_identity_oracles=24),
'lifecycles':dict(paired_setups=126,manager_constructions=252,refactor_attempts=432,of_which_singular=126,manager_copies=90,column_updates=1530,explicit_valid_solve_entries=11754,expected_rejected_solve_entries=864,exact_residual_oracles=11664,real_direct_exports=342,orientation_solve_upper_bound=216),
'fallback':dict(backend_constructions_and_refactors=72,manager_copies=36,explicit_solve_entries=144,real_exports=36,unavailable_exporters=18,throwing_exporters=18,orientation_solve_upper_bound=24),
'policy_transitions':dict(sequences=18,backend_construction_attempts=162,of_which_singular=18,exporter_entries=144,real_exports=126,unavailable_exporters=18,throw_after_real_export=18,manager_copies=36,explicit_solve_entries=252,orientation_solve_upper_bound=60,native_nonempty_control_observations=72,markowitz_observations=48),
'forwarders':dict(real_backend_constructions=24,real_exports=24,explicit_solve_entries=48,float64_nondefault_rejections=12,invalid_manager_backend_rejections=2,orientation_solve_upper_bound=12,native_control_observations=6),
'generic_policy':dict(ordinary_constructions=45,ordinary_refactors=27,manager_copies=27,explicit_solve_entries=126,prework_nondefault_rejections=18)
},notes=[
'All construction/refactor entries include native/Markowitz work, plus18 independent B\\rhs factorizations and3 direct dense LU setups. Singular and injected errors are separate branches, never silently zero work.',
'Orientation is conditional: native export may return immediately for empty/unit scaling or attempt _hh_scale_mode. Listed upper bounds count one direct solve per eligible real export; _hh_scale_mode also has four sparse matvecs and vector scans. Markowitz extraction has no orientation solve.',
'Explicit manager solves are API entries; indexed/alias forwarding and prepared-spike recomputation are internal work, not added as if independent API entries. Full primitive counts depend on sparse routing and update chains<=8 (saved copied branch<=3). No instrumentation or production method overwrite.',
'Test snapshots/owner tuples/control copies/oracles are outside any performance claim. _dl_factor_snapshot and export snapshots detach values; exact residual oracles allocate Rational arrays/matvecs, bounded fixture maxn16. BigFloat256/Rational fallback matrices n2. Controls20 copied per observed nonempty native entry plus private20default vector.',
'No public solve/problem, LP import or large model; no timing/alloc benchmark. Native constructor/internal Markowitz dense LU and wrapper allocation totals are not observed. Full phase assertion tree is exact; native operation estimates remain explicitly bounded/source-derived.'
])
for name,obj in [('expected-tests.json',expected),('work-ledger.json',ledger)]:
 with (D/name).open('x') as f:json.dump(obj,f,indent=2);f.write('\n')
with (D/'expected-tests.toml').open('x') as f:
 for mode in ('red','green'):
  f.write('['+mode+']\nassertions = '+str(expected[mode]['assertions'])+'\n')
  for name,p,fail,err,broken in expected[mode]['groups']:
   f.write('[[ '+mode+'.groups ]]\nname = '+json.dumps(name)+'\npass = '+str(p)+'\nfail = '+str(fail)+'\nerror = '+str(err)+'\nbroken = '+str(broken)+'\n')
print('Expected GREEN',expected['green']['assertions'],[n for _,n,_ in groups],'; RED seven expected failures, zero factors')
