"""Independent offline review checks. Never imports or executes preparation scripts or Julia."""
from pathlib import Path
import hashlib,json,tomllib,subprocess,struct
from fractions import Fraction
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
D=R/'diagnostics/simplex-core-architecture/results/NATIVE-ACCURACY-PREPARATION'
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for block in iter(lambda:f.read(1048576),b''):h.update(block)
 return h.hexdigest()
checks={};details={}
def check(name,value):checks[name]=bool(value)
required=read(D/'required-paths.json');pins=read(D/'preparation-pins.json');baseline=read(D.parent/'DIRECT-LU-PREPARATION/baseline.json')['sha256']
check('exact_48_unique_absolute_review_paths',len(required)==len(set(required))==48 and all(Path(p).is_absolute() for p in required))
check('fixed_review_set_excludes_mutable_publication_and_review_outputs',all(p not in {str(R/'diagnostics/simplex-core-architecture/STATUS.md'),str(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md')} and not (Path(p).parent==D and Path(p).name in ('continue.py','closure.py','review.json','reviewer-check.py','reviewer-check.json')) for p in required))
check('preparation_pin_count_1166',len(pins['files'])==len(set(pins['files']))==len(pins['inventory'])==1166 and pins['trees']==[])
bad=[]
for p,record in pins['inventory'].items():
 if record!={'resolved':str(Path(p).resolve(strict=True)),'sha256':sha(p)}:bad.append(p)
check('every_preparation_pin_matches_independently',not bad and set(pins['files'])==set(pins['inventory']));details['mismatched_pins']=bad
check('baseline_514_unchanged',len(baseline)==514 and all(sha(R/p)==h for p,h in baseline.items()))
check('baseline_and_required_fully_pinned',set(str(R/p) for p in baseline)<=set(pins['files']) and set(required)<=set(pins['files']) and str(D/'required-paths.json') in pins['files'])
check('expected_refs',subprocess.check_output(['git','rev-parse','HEAD','master'],cwd=R,text=True).splitlines()==['d5d829ac61ab37cd0d0785cc26047a2e6bf664b4','6f68e24e8ddac42b948da8fcc2d636c010751194'])
data=read(D/'inputs.json');old=read(D.parent/'DIRECT-LU-COST-PREPARATION/inputs.json')
expected_f=[dict(name=f['name'],matrix=f['matrices'][4],rhs={k:f['steps'][4][k] for k in ('a','dse','unit')}) for f in old['fixtures']]
check('exact_four_B4_step5_token_subset',data['fixtures']==expected_f and [f['name'] for f in data['fixtures']]==['sparse32','dense32','sparse96','dense96'])
f=old['fixtures'][0];life=dict(matrix=f['matrices'][0],rhs={k:f['steps'][0][k] for k in ('a','unit')},singular={**f['matrices'][4],'nzval':['0000000000000000']*len(f['matrices'][4]['nzval'])})
check('exact_B0_step1_and_zero_B4_pattern',data['lifecycle']==life)
check('complete_TOML_JSON_inverse',tomllib.loads((D/'inputs.toml').read_text())==data)
expected_s=[]
for fi,f in enumerate(expected_f):
 for rnd in range(1,12):
  for k in range(3):expected_s.append(dict(id=len(expected_s)+1,fixture=f['name'],arm='CPR'[(fi+rnd-1+k)%3],round=rnd,warm=rnd<=3))
check('fixed_rotating_132_schedule',data['schedule']==expected_s and len(expected_s)==132)
counts=dict(fresh=len(expected_s)+3*3,refactor=3*3,copy=3,ftran=len(expected_s)*32+3*7,btran=len(expected_s)*16+3*7,snapshot=4*3)
check('entry_counts_6378',counts==dict(fresh=141,refactor=9,copy=3,ftran=4245,btran=2133,snapshot=12));details['counts']=counts
check('storage_ledger',sum(f['matrix']['n'] for f in expected_f)*33*48==405504 and 132*4*48==25344 and 3*14*32==1344)
check('206_historical_groups',len(read(D/'host.json')['groups'])==len(set(read(D/'host.json')['groups']))==206)
fix=read(D/'preparation-fix.json');offline=read(D/'offline-tests.json')['sha256']
check('old_seal_launcher_test_bindings_preserved',all(offline[p]==m['old_sha256']==sha(m['preserved']) and sha(p)==m['new_sha256'] for p,m in fix['mappings'].items()))
check('future_stage_absent',not (D.parent/'NATIVE-ACCURACY-QUALIFICATION').exists())
S=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia/stdlib/v1.13/SparseArrays/src/solvers')
u=(S/'umfpack.jl').read_text();w=(S/'wrappers.jl').read_text();lib=(S/'LibSuiteSparse.jl').read_text();driver=(D/'driver.jl').read_text();guard=(D/'guard.py').read_text()
missing=['UMFPACK_STRATEGY_USED','UMFPACK_STATUS','UMFPACK_IR_TAKEN','UMFPACK_IR_ATTEMPTED','UMFPACK_SOLVE_FLOPS']
check('blocking_metadata_namespace_defect_demonstrated',all('API.'+n in driver and n not in u and 'const '+n+' = ' in w for n in missing) and 'const PREFIXES = ["cholmod_", "CHOLMOD_", "umfpack_"]' in lib)
details['unbound_metadata_names_in_SparseArrays_UMFPACK']=missing
check('missing_resident_high_water_evidence_demonstrated','VmHWM' not in guard and 'ru_maxrss' not in guard and "('VmRSS:', 'VmPeak:', 'VmSwap:')" in guard)
check('constructor_private_control_and_workspace_source',all(s in u for s in ('copy(control), Vector{Float64}(undef, UMFPACK_INFO)','copy(nonzeros(S))','refinement ? 5 * size(S, 2) : size(S, 2)','control[JL_UMFPACK_IRSTEP] = 0')))
check('copy_shared_CSC_private_scratch_source',all(s in u for s in ('F.colptr,\n        F.rowval,\n        F.nzval,','copy(F.control),\n        copy(F.info),\n        ReentrantLock()','ws=UmfpackWS(F)')))
check('metadata_slot_values',all('const UMFPACK_'+n+' = '+str(v)+'\n' in w for n,v in dict(STATUS=0,STRATEGY_USED=18,IR_TAKEN=80,IR_ATTEMPTED=81,SOLVE_FLOPS=84,SIZE_OF_UNIT=3,NUMERIC_SIZE=40,PEAK_MEMORY=41,SYM_PIVOT_TOLERANCE=15,IRSTEP=7).items()))
# Independent nonsymmetric rational example exercises CSR-L, CSC-U, both row-scale orientations.
B=[[Fraction(2),Fraction(3)],[Fraction(8),Fraction(4)]];p=[1,0];q=[1,0];rs=[Fraction(2),Fraction(4)]
L=[[Fraction(1),Fraction(0)],[Fraction(3,2),Fraction(1)]];U=[[Fraction(1),Fraction(2)],[Fraction(0),Fraction(-2)]]
for reciprocal in (False,True):
 scale=[1/v for v in rs] if reciprocal else rs
 scaled=[[a*scale[i] if reciprocal else a/scale[i] for a in row] for i,row in enumerate(B)]
 check('independent_factor_orientation_'+str(reciprocal),all(sum(L[i][k]*U[k][j] for k in range(2))==scaled[p[i]][q[j]] for i in range(2) for j in range(2)))
x=[Fraction(1),Fraction(2)];b=[Fraction(18),Fraction(11)]
check('independent_nonsymmetric_transpose_RHS',all(sum(B[j][i]*x[j] for j in range(2))==b[i] for i in range(2)) and any(sum(B[i][j]*x[j] for j in range(2))!=b[i] for i in range(2)))
result=dict(all_checks_passed=all(checks.values()),checks=checks,details=details,pins_sha256=sha(D/'preparation-pins.json'),required_paths_sha256=sha(D/'required-paths.json'),sha256={p:sha(p) for p in required},reviewer_source_sha256=sha(Path(__file__)),scope='Independent new Python/source/hash checks only. Existing scripts never executed/imported. No Julia execution/query/parser/import/compile. Defect demonstration checks pass when defects exist; this is not acceptance.')
with (D/'reviewer-check.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(dict(all_checks_passed=result['all_checks_passed'],checks=len(checks),failed=[k for k,v in checks.items() if not v],pins=len(pins['inventory']),baseline=len(baseline),required=len(required))))
