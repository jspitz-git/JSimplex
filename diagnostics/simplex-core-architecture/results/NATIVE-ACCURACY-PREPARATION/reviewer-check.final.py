"""Fresh independent corrected-preparation review. No Julia or existing-script execution."""
from pathlib import Path
import json,hashlib,re,ast,math,tomllib,subprocess
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
D=R/'diagnostics/simplex-core-architecture/results/NATIVE-ACCURACY-PREPARATION'
S=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia/stdlib/v1.13/SparseArrays/src')
def rd(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
checks={}
def check(n,v):checks[n]=bool(v)
reqs=rd(D/'required-paths-reviewed.json');pins=rd(D/'preparation-pins-reviewed.json');oldpins=rd(D/'preparation-pins.json');oldreview=rd(D/'review.json');fix=rd(D/'review-fix.json');mapping=fix['mappings']
check('exact66_required_unique_absolute',len(reqs)==len(set(reqs))==66 and all(Path(n).is_absolute() for n in reqs))
check('exact1184_pins_membership',len(pins['files'])==len(set(pins['files']))==len(pins['inventory'])==1184 and pins['trees']==[] and set(pins['files'])==set(pins['inventory']))
check('all1184_current_resolutions_and_hashes',all(v==dict(resolved=str(Path(n).resolve(strict=True)),sha256=sha(n)) for n,v in pins['inventory'].items()))
check('required_and_required_manifest_pinned',set(reqs)|{str(D/'required-paths-reviewed.json')}<=set(pins['files']))
excluded={str(R/'diagnostics/simplex-core-architecture/STATUS.md'),str(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md')}|{str(D/n) for n in ('continue.py','closure.py','review-final.json','review-final.md','reviewer-check.final.py','reviewer-check.final.json')}
check('no_mutable_or_final_output_bindings',not(set(reqs)&excluded) and not(set(pins['files'])&excluded))
check('original_review_digest_preserved',oldreview['accepted'] is False and len(oldreview['findings'])==2 and oldreview['pins_sha256']==sha(D/'preparation-pins.json'))
check('original48_review_bindings_reconciled',len(oldreview['sha256'])==48 and all(sha(mapping[n]['preserved'] if n in mapping else n)==h for n,h in oldreview['sha256'].items()))
check('original1166_pins_reconciled',len(oldpins['inventory'])==1166 and all(sha(mapping[n]['preserved'] if n in mapping else n)==v['sha256'] for n,v in oldpins['inventory'].items()))
check('fix_exact5_preserved_files',len(mapping)==5 and all(sha(m['preserved'])==m['sha256']==oldreview['sha256'][n] for n,m in mapping.items()))
check('initial6_review_outputs_frozen',all(str(D/n) in reqs and sha(D/n)==pins['inventory'][str(D/n)]['sha256'] for n in ('reviewer-check.initial.py','reviewer-check.initial.json','reviewer-check.py','reviewer-check.json','review.md','review.json')))
check('fix_records_current_bindings',all(sha(n)==h for r in ('review-fix.json','review-fix-tests.json') for n,h in rd(D/r)['sha256'].items()))
base=rd(D.parent/'DIRECT-LU-PREPARATION/baseline.json')['sha256']
check('baseline514_unchanged',len(base)==514 and all(sha(R/n)==h for n,h in base.items()))
check('expected_refs',subprocess.check_output(['git','rev-parse','HEAD','master'],cwd=R,text=True).splitlines()==['d5d829ac61ab37cd0d0785cc26047a2e6bf664b4','6f68e24e8ddac42b948da8fcc2d636c010751194'])
check('no_numerical_stage',not(D.parent/'NATIVE-ACCURACY-QUALIFICATION').exists())
driver=(D/'driver.jl').read_text();original=(D/'driver.jl.before-review').read_text()
check('driver_only_constant_owner_change',driver.replace('\nconst CAPI=SparseArrays.LibSuiteSparse','').replace('CAPI.UMFPACK_','API.UMFPACK_')==original)
w=(S/'solvers/wrappers.jl').read_text();u=(S/'solvers/umfpack.jl').read_text();lib=(S/'solvers/LibSuiteSparse.jl').read_text()
constants=re.findall(r'(?<!\w)CAPI\.(UMFPACK_\w+)',driver)
check('all8_constants_resolve_direct_owner',len(constants)==8 and all(re.search(r'^const '+n+r' = \d+$',w,re.M) for n in constants) and 'include("solvers/LibSuiteSparse.jl")' in (S/'SparseArrays.jl').read_text() and 'include("wrappers.jl")' in lib)
api=set(re.findall(r'(?<!\w)API\.(\w+)',driver))
check('remaining_API_qualified_symbols_resolve',api=={'UmfpackLU','get_umfpack_control','umf_lunz','umfpack_dl_get_numeric','umferror'} and all(n in u for n in api-{'umfpack_dl_get_numeric'}) and 'function umfpack_dl_get_numeric(' in w and '"umfpack_"' in lib)
g=(D/'guard.py').read_text();go=(D/'guard.py.before-review').read_text()
check('guard_only_HWM_and_terminal_read_change',g.replace("('VmRSS:', 'VmHWM:', 'VmPeak:', 'VmSwap:')","('VmRSS:', 'VmPeak:', 'VmSwap:')").replace("\n                record['child_maxrss_kib'] = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss",'')==go)
check('single_child_reaped_before_accepted_terminal_peak',g.count('subprocess.Popen(')==1 and g.index("child.wait()\n                        record['reason'] = f'exit{child.returncode}'")<g.index("record['child_maxrss_kib']") and "record['reason'] == 'exit0'" in g)
seal=(D/'seal.py').read_text()
check('seal_only_reviewed_manifest_path_changes',seal.replace('preparation-pins-reviewed.json','preparation-pins.json').replace('required-paths-reviewed.json','required-paths.json').replace('review-final.json','review.json')==(D/'seal.py.before-review').read_text())
e=(D/'evidence.py').read_text();eo=(D/'evidence.py.before-review').read_text();tree=ast.parse(e)
helper=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='memory_report')
helper_lines=e.splitlines(True)[helper.lineno-1:helper.end_lineno]
stripped=e.replace(''.join(helper_lines),'').replace('import guard,math','import guard').replace(' mem=memory_report(resources,p)\n','').replace(" result['process_memory']=mem\n",'').replace(" checks['resident_memory']=True\n",'')
check('evidence_only_memory_addition',stripped==eo)
# Execute only the NEW pure memory helper AST in an empty explicit namespace.
# No preparation module imports, main blocks, auditor, guard, or process routines execute.
def require(v,m):
 if not v:raise ValueError(m)
ns={'math':math,'req':require};exec(compile(ast.Module(body=[helper],type_ignores=[]),'<isolated-new-memory-helper>','exec'),ns)
f=ns['memory_report']
def rows(rss=40,hwm=50,vpeak=400):return [{'child_memory':[f'VmRSS: {rss} kB',f'VmHWM: {hwm} kB',f'VmPeak: {vpeak} kB','VmSwap: 0 kB']}]
def refuse(n,s,p):
 try:f(s,p)
 except (ValueError,KeyError,TypeError):check(n,True)
 else:check(n,False)
v=f(rows(),{'child_maxrss_kib':60})
check('isolated_memory_preserves_resident_virtual_distinction',v['samples']==[dict(VmRSS=40,VmHWM=50,VmPeak=400,VmSwap=0)] and v['child_maxrss_kib']==60)
for name,p in [('missing',{}),('bool',{'child_maxrss_kib':True}),('nan',{'child_maxrss_kib':math.nan}),('zero',{'child_maxrss_kib':0}),('lower_than_sample',{'child_maxrss_kib':49})]:refuse('memory_reject_terminal_'+name,rows(),p)
refuse('memory_reject_RSS_above_HWM',rows(rss=51),{'child_maxrss_kib':60})
refuse('memory_reject_absent_samples',[],{'child_maxrss_kib':60})
refuse('memory_reject_virtual_only',[{'child_memory':['VmPeak: 400 kB']}],{'child_maxrss_kib':60})
refuse('memory_reject_duplicate',[{'child_memory':rows()[0]['child_memory']+['VmRSS: 40 kB']}],{'child_maxrss_kib':60})
refuse('memory_reject_negative',rows(rss=-1),{'child_maxrss_kib':60})
refuse('memory_reject_wrong_unit',[{'child_memory':[s.replace('kB','MB') for s in rows()[0]['child_memory']]}],{'child_maxrss_kib':60})
check('numerical_and_launch_artifacts_unchanged',all(sha(D/n)==oldreview['sha256'][str(D/n)] for n in ('inputs.json','inputs.toml','analysis.py','control.py','launch.py','supervisor.py','config.json','host.json','environment.json')))
data=rd(D/'inputs.json');old=rd(D.parent/'DIRECT-LU-COST-PREPARATION/inputs.json');expect=[dict(name=f['name'],matrix=f['matrices'][4],rhs={k:f['steps'][4][k] for k in ('a','dse','unit')}) for f in old['fixtures']]
check('exact_four_fixture_subset_and_TOML',data['fixtures']==expect and tomllib.loads((D/'inputs.toml').read_text())==data)
s=[]
for fi,f in enumerate(expect):
 for rnd in range(1,12):
  for k in range(3):s.append(dict(id=len(s)+1,fixture=f['name'],arm='CPR'[(fi+rnd-1+k)%3],round=rnd,warm=rnd<=3))
check('schedule132_and_entry_budget',data['schedule']==s and len(s)==132 and len(s)*48+3*14==6378 and len(s)+9==141 and len(s)*32+21==4245 and len(s)*16+21==2133)
check('206_historical_groups_retained',len(rd(D/'host.json')['groups'])==len(set(rd(D/'host.json')['groups']))==206)
result=dict(all_passed=all(checks.values()),checks=checks,pins_sha256=sha(D/'preparation-pins-reviewed.json'),required_paths_sha256=sha(D/'required-paths-reviewed.json'),sha256={n:sha(n) for n in reqs},checker_sha256=sha(Path(__file__)),scope='Independent offline current hashes/source/inverses. Only isolated NEW pure memory_report AST executed with synthetic data; no existing scripts or old auditor/test rerun, no Julia execution/query/parser/import/compile. No stage admission.')
with (D/'reviewer-check.final.json').open('x') as out:json.dump(result,out,indent=2);out.write('\n')
print(json.dumps(dict(all_passed=result['all_passed'],checks=len(checks),failed=[n for n,v in checks.items() if not v],pins=1184,required=66,baseline=514)))
