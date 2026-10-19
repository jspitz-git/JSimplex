"""Independent offline plan/evidence review. No old module imports or Julia."""
from pathlib import Path
import hashlib,json,subprocess
D=Path(__file__).resolve().parent
R=D.parents[3]
P=D.with_name('DIRECT-BG-EXPORT-WORKSPACE-ALLOCATION-PROVENANCE-REVIEWED')
G=D.with_name('DIRECT-BG-EXPORT-WORKSPACE-GREEN2-PREPARATION')
O=D.with_name('DIRECT-BG-EXPORT-WORKSPACE-COST-PREPARATION')
C=R/'diagnostics/direct-bg-export-workspace/reproduce'
S=R/'docs/superpowers/specs/2026-10-19-direct-bg-export-specialization.md'
Q=R/'docs/superpowers/plans/2026-10-19-direct-bg-export-specialization.md'
checks={};read={}
def data(p):
 p=Path(p);b=p.read_bytes();read[str(p)]=hashlib.sha256(b).hexdigest();return b
def rd(p):return json.loads(data(p))
def tx(p):return data(p).decode()
def ck(n,v):checks[n]=bool(v)
def bindings(mapping):return all(hashlib.sha256(data(Path(k))).hexdigest()==v for k,v in mapping.items())
s,q=tx(S),tx(Q)
a=rd(D/'source-check.json')
ck('author185_bindings',len(a['sha256'])==185 and bindings(a['sha256']))
ck('author19_recorded_pass',len(a['checks'])==19 and a['all_passed'] and all(a['checks'].values()))
h=rd(D/'host.json')
ck('recorded_host_scope256',len(h['groups'])==256 and not h['matches'] and not h['unreadable_identity_pids'] and 'sessions' in h['scope'])
for ref,want in [('HEAD','39beb6ff4a9f287dbbfc4c2a3b821d47ce374d0d'),('master','26e2291745999f485a74f643298ca997d65c7205')]:
 ck('ref_'+ref,subprocess.check_output(['git','rev-parse',ref],cwd=R,text=True).strip()==want)
ck('no_tracked_changes',not subprocess.check_output(['git','diff','HEAD','--name-only'],cwd=R,text=True).strip())
ck('candidate_absent',not (R/'diagnostics/direct-bg-export-specialized').exists())
pr=rd(P/'runs/profile300/result-review.json')
ck('accepted_provenance_not_performance',pr['accepted'] and pr['allocation_provenance_accepted'] and not pr['performance_accepted'] and not pr['production_integration_accepted'])
ck('prior_result_bindings',bindings(pr['sha256']) and bindings(pr['evidence_sha256']))
pub=rd(P/'publication.json');ck('prior_publication_bindings',bindings(pub['sha256']))
at=rd(P/'attribution.json');ck('sixteen_raw_profile_bindings',len(at['sha256'])==16 and bindings(at['sha256']))
ck('known_native_red_deltas',[x['profiled_event_delta'] for x in at['pairs'] if x['backend']=='native']==[5,9,1,-6])
ck('complete_saved_pair_ledgers',len(at['pairs'])==8 and all(sum(v for k,v in x['category_deltas'].items() if k!='outside_lifecycle_timer_result')==x['lifecycle_heap_delta']==x['profiled_event_delta'] for x in at['pairs']))
ck('saved_harness_offsets',all(x['outside_timer_delta']==-14 and x['category_deltas']['lifecycle_return_tuples']==-2 for x in at['pairs']))
ck('saved_native_anomaly',any(x['fixture']=='dense96' and x['backend']=='native' and x['side']=='reference' and x['ordinary_events']-x['profiled_events']==41 for x in at['profiles']))
st=rd(P/'stages.json')['green'];stage=Path(st['path'])
ck('four_candidate_bodies_equal_profile_stage',all(data(C/(n+'.jl'))==data(stage/'src'/('_bgx_'+n+'.jl')) for n in ['workspace','export','import','factor']))
inv=rd(G/'inverse.json');old,new=Path(inv['original']),Path(inv['amended']);ot,nt=tx(old),tx(new)
ck('green2_amends_import_not_lifecycle',old.name==new.name=='import-tests.jl' and 'harness-fix' in str(new) and ot.count(inv['before'])==1 and nt.replace(inv['after'],inv['before'])==ot)
ck('green2_test_hashes',read[str(old)]==inv['original_sha256'] and read[str(new)]==inv['amended_sha256'])
gpins=rd(G/'runs/green2-300/launch-pins.json')['inventory'];driver=tx(G/'driver.jl')
ck('green2_actual_amended_import_is_sealed_and_included',gpins[str(new)]['sha256']==read[str(new)] and 'include("'+str(new)+'")' in driver and 'include("'+str(C/'lifecycle-tests.jl')+'")' in driver)
ck('plan_correctly_names_amended_import_source','actual accepted GREEN2 lifecycle test source' not in q and 'direct-bg-export-workspace-harness-fix/reproduce/import-tests.jl' in q)
# Bind inspected source and metadata; source comparisons above are independent of literal plan gates.
for p in [R/'AGENTS.md',D/'SELF-REVIEW.md',P/'REPORT.md',P/'result-review.md',O/'FINAL.md',O/'MEMORY-WORK.md',O/'cost.jl',O/'probe.jl',O/'analysis.py',O/'inputs.json',O/'inputs.toml',C/'workspace-tests.jl',C/'lifecycle-tests.jl',Path(__file__)]:data(p)
# Schedule derived from eight source-loop cells, two sides, ten pairs and eight updates.
ncells=4*2;windows=ncells*2*(3+7)
ck('schedule_arithmetic',windows==160 and windows+ncells*2+ncells*3+4==204 and 2*windows+ncells*4+ncells*6+12==412 and 8*windows+ncells*3*8==1472 and 16*windows+ncells*3*16==2944 and 8*windows+ncells*3*8==1472)
ck('orientation_bound_arithmetic',(windows//2)*3+4*6+4*9+8==308)
ck('seven_cores_bound',q.count('| `_bgxs_')==7 and 'same tuple result' in q and 'where {FT,LT,UT,PT,QT,ST,O,A}' in q)
ck('frozen_acceptance_gates',all(t in q for t in ['ALL8','0.95','1.10','3/7','10/14','compile/recompile0','No third timed arm','If GREEN allocation predicates fail, stop']))
ck('conditional_red_and_no_automatic_profile','only if independent review of the concrete driver/source supports that expectation; otherwise stop before launch' in q and 'No automatic Profile.Allocs or IR query' in q)
ck('identical_timeout_retry_limits','300/292s' in q and '600/592s' in q and 'only a verified pure timeout' in q and 'correctness/error/pin/compile failures are not timeouts' in s)
out={'all_passed':all(checks.values()),'checks':checks,'sha256':read,'scope':'Independent offline planning/evidence checks; no Julia, old auditors, runtime admission, or new process scan','findings':['P2: GREEN2 amended import-tests.jl is incorrectly described as lifecycle-tests.jl in plan lineage.'] if not checks['plan_correctly_names_amended_import_source'] else []}
with (D/'independent-check.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps({'all_passed':out['all_passed'],'checks':len(checks),'bindings':len(read),'failed':[k for k,v in checks.items() if not v]}))
