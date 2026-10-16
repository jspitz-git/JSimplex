"""Independent amendment check; saved before execution; no prior script is executed."""
from pathlib import Path
import hashlib,json,difflib,statistics,tomllib
Q=Path(__file__).resolve().parent;R=Q.parents[3];B=Q.parent;P=R/'docs/superpowers/plans/2026-10-16-native-pivot-production-integration.md'
bindings={};checks={}
def read(p):
 p=Path(p);b=p.read_bytes();bindings[str(p.relative_to(R))]=hashlib.sha256(b).hexdigest();return b
def txt(p):return read(p).decode()
def js(p):return json.loads(read(p))
def test(n,v):
 checks[n]=bool(v)
 if not v:raise RuntimeError(n)
read(__file__)
main=js(Q/'review-checks.json');test('independent307PASS',main['all_passed'] and len(main['checks'])==307)
fix=js(Q/'review-fix.json');test('author_amendment6PASS',fix['all_passed'] and len(fix['checks'])==6 and all(fix['checks'].values()))
for p,h in fix['sha256'].items():test('fix_binding:'+p,hashlib.sha256(read(R/p)).hexdigest()==h)
old=txt(Q/'plan.before-review.md');new=txt(P);initial=js(Q/'review-initial.json')
test('initial_finding_preserved',initial['accepted'] is False and initial['sha256'][str(P.relative_to(R))]==hashlib.sha256(old.encode()).hexdigest())
test('exact_two_plan_changes',sum(1 for line in difflib.unified_diff(old.splitlines(True),new.splitlines(True)) if line.startswith('@@ '))==2)
test('readiness_not_launch', 'pre-FF review accepts commit/application preparation ONLY; it is NOT launch' in new)
test('postFF_actual_master_final_seal_review','AFTER the local master fast-forward, seal the actual master refs, source' in new and 'acceptance of THIS final\n  actual-master seal BEFORE any Julia launch' in new)
test('600_same_final_admission','Apply this same post-FF actual-master sealing and acceptance\n  requirement to the separately labelled600s pure-timeout attempt' in new)
test('changed_inputs_reseal','any later ref/source/environment change requires a new\n  seal and review' in new)
test('timeout_failure_classification',all(t in new for t in ('Missing final raw','Mixed/unknown failure','no observed test failure/error/broken','fixed5s deadline','without another permission question')))
finalize=txt(Q/'finalize.py');publication=txt(Q/'publication.py');continuation=txt(Q/'continuation-text.md')
test('closure_author_old_plan_mapping_only','if record is not review and target==PLAN:target=Q/\'plan.before-review.md\'' in finalize)
test('closure_review_scope_and_gate',"review['accepted'] is True and not review['findings']" in finalize and "review['scope']=='production integration preparation'" in finalize)
test('closure_four_continuation_mappings',"need(len(maps)==4,'Four mappings')" in finalize and 'need(sha(before)==sha(live)==h' in finalize)
test('publication_exact_staged_names_blobs',all(t in publication for t in ('Stage membership','Final stage membership','Final staged bytes','Index not empty','Closure changed')))
test('publication_git_errors_fail_closed',"w.returncode in (0,2)" in publication and 'not w.stderr' in publication)
test('continuation_actual_master_launch_gate', 'readiness review' in continuation and 'ACTUAL master refs/source/command/environment' in continuation and 'launch' in continuation)
# Disambiguate difference-of-medians versus median paired allocation differences.
summary=js(B/'NATIVE-PIVOT-COST/summary.json');windows=[];run=B/'NATIVE-PIVOT-COST-PREPARATION/runs/cost/output'
for i in range(1,89):
 w=tomllib.loads(txt(run/('window-%03d.toml'%i)))
 if not w['schedule']['warm']:windows.append(w)
meddiff={};paired={}
for f in ('sparse32','dense32','sparse96','dense96'):
 a={x:{w['schedule']['round']:w['total']['bytes'] for w in windows if w['schedule']['fixture']==f and w['schedule']['arm']==x} for x in ('C','P')}
 meddiff[f]=statistics.median(a['P'].values())-statistics.median(a['C'].values())
 paired[f]=statistics.median(a['P'][r]-a['C'][r] for r in a['C'])
 v=summary['comparisons'][f+':total']['bytes'];test('total_byte_medians:'+f,v['Pmedian']-v['Cmedian']==meddiff[f])
test('report_delta_of_medians',[meddiff[f] for f in meddiff]==[24,-32,32,0])
# Main check source bindings remain current except explicitly root-refined unexecuted publication draft.
changes=[]
for p,h in main['sha256'].items():
 pp=Path(p) if Path(p).is_absolute() else R/p
 actual=hashlib.sha256(pp.read_bytes()).hexdigest()
 if actual!=h:changes.append(p)
test('only_expected_publication_draft_change',changes in [[],[str((Q/'publication.py').relative_to(R))]])
result=dict(all_passed=True,checks=checks,sha256=bindings,details=dict(initial_finding_resolved=True,main_changed_paths=changes,bytes_difference_of_arm_medians=meddiff,bytes_median_of_paired_differences=paired,numerical_admission=False))
with (Q/'review-amendment-checks.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(len(checks),'PASS',len(bindings),'bindings')
