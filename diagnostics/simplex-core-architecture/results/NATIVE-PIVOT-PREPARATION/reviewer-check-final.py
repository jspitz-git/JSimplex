"""Bounded independent final review: saved bytes and text only; no old script or Julia execution."""
from pathlib import Path
import hashlib,json,difflib
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
Q=R/'diagnostics/simplex-core-architecture/results/NATIVE-PIVOT-PREPARATION'
def rd(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def path(p):return Path(p) if Path(p).is_absolute() else R/p
req=rd(Q/'review-final-required.json')['paths'];pins={p:sha(p) for p in req}
fix=rd(Q/'review-fix.json');maps=fix['mappings'];checks={}
checks['required130_unique']=len(req)==len(pins)==130
checks['five_exact_preserved_maps']=len(maps)==5 and all(sha(v['preserved'])==v['sha256'] for v in maps.values())
def bindings(z):
    remapped=[]
    for p,h in z.items():
        p=str(path(p))
        if sha(p)==h:continue
        if p not in maps or maps[p]['sha256']!=h or sha(maps[p]['preserved'])!=h:return False,remapped
        remapped.append(p)
    return True,remapped
records={}
for p in req:
    if p.endswith('.json'):
        z=rd(p)
        if isinstance(z,dict) and isinstance(z.get('sha256'),dict):
            okay,remapped=bindings(z['sha256']);records[p]={'count':len(z['sha256']),'matched':okay,'mapped_to_preserved':remapped}
checks['all_current_or_explicit_preserved_bindings']=all(z['matched'] for z in records.values())
checks['review_fix10_checks14_currentbindings']=fix['all_passed'] and len(fix['checks'])==10 and all(fix['checks'].values()) and len(fix['sha256'])==14 and all(sha(p)==h for p,h in fix['sha256'].items())
checks['initial_rejection_preserved']=rd(Q/'review.json')['accepted'] is False and len(rd(Q/'review.json')['findings'])==1
inv=rd(Q/'inverse.json');good=True
for p,h in inv['original'].items():
    rel=str(Path(p).relative_to(R));s=(Q/'candidate'/rel).read_text()
    good=good and sha(p)==h
    for edit in reversed([e for e in inv['edits'] if e['file']==rel]):
        assert s.count(edit['after'])==1
        s=s.replace(edit['after'],edit['before'])
    good=good and s==Path(p).read_text()
checks['production7_inverse28_unchanged']=len(inv['original'])==7 and len(inv['edits'])==28 and good and all(sha(p)==h for p,h in inv['candidate'].items())
manifest=rd(Q/'overlay-manifest.json');oldmanifest=rd(Q/'overlay-manifest.before-review.json');normalized=json.loads(json.dumps(manifest))
for e in normalized['candidate']:
    if e['destination']=='test/native_pivot_policy_tests.jl':e['sha256']=maps[str(Q/'candidate/test/native_pivot_policy_tests.jl')]['sha256']
checks['only_overlay_test_hash_changed']=normalized==oldmanifest
checks['all_current_overlay_sources_match']=all(sha(e['source'])==e['sha256'] for arm in ('reference','candidate') for e in manifest[arm])
old=(Q/'tests.before-review.jl').read_text();new=(Q/'candidate/test/native_pivot_policy_tests.jl').read_text()
start='        # A copied nonempty prefix survives independent resets on each side.'
end='@testset "precision_and_factory_dispatch"'
checks['tests_outside_copy_failure_unchanged']=old.split(start)[0]==new.split(start)[0] and old.split(end)[1]==new.split(end)[1]
copy_part=new.split(start)[1].split('        # Fresh failure')[0]
checks['observed_populated_spare_before_copy']=copy_part.index('J.refactorize!(f,B)')<copy_part.index('private_spare=f.base.spare')<copy_part.index('@test private_spare !== nothing')<copy_part.index('saved=J.copy_basis_factorization(f)') and '@test f.base.spare === private_spare' in copy_part and '@test saved.base.spare === nothing' in copy_part
failure=new.split('        # Fresh failure and private-spare failure are separate states.')[1].split(end)[0]
checks['saved_copy_preserved_failure_and_recovery']='for with_spare in (false,true)' in failure and failure.index('saved=J.copy_basis_factorization(f)')<failure.index('@test_throws SingularException') and failure.count('saved.base.factorization === owner && history(saved)==saved_hist')==2 and failure.count('controls(saved.base,symbol);solves(saved,matrix)')==2 and failure.count('owner.control === control_owner && owner.control == ctrl')==2
# Counts are component call deltas over 4 managers * 2 policies; solves helper calls F and B once.
copy_delta=new.count('J.copy_basis_factorization(f)')-old.count('J.copy_basis_factorization(f)')
refactor_delta=new.count('J.refactorize!(f,B)')-old.count('J.refactorize!(f,B)')
solve_delta=new.count('controls(saved.base,symbol);solves(saved,matrix)')-old.count('controls(saved.base,symbol);solves(saved,matrix)')
counts={'refactor_entries':4*2*refactor_delta,'manager_copies':4*2*2*copy_delta,'basis_solves':4*2*2*solve_delta*2,'forward':4*2*2*solve_delta,'transpose':4*2*2*solve_delta}
checks['test_only_deltas8_16_64_32_32']=counts=={'refactor_entries':8,'manager_copies':16,'basis_solves':64,'forward':32,'transpose':32}
ledger=(Q/'WORK-AND-TEST-LEDGER.md').read_text();checks['ledger_agrees']='adds8refactor entries,16manager copies and64basis-solve' in ledger and '(32F/32B)' in ledger
pins[str(Q/'review-final-required.json')]=sha(Q/'review-final-required.json');pins[str(Q/'reviewer-check-final.py')]=sha(Q/'reviewer-check-final.py')
result={'all_passed':all(checks.values()),'checks':checks,'recorded_binding_maps':records,'test_only_component_deltas':counts,'sha256':pins,'scope':'Bounded OFFLINE final correction review. Julia and overlay UNEXECUTED; no old scripts rerun. Historical hashes reconcile only through five explicit preserved copies.'}
with (Q/'reviewer-check-final.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({'all_passed':result['all_passed'],'checks':len(checks),'required_inputs':len(req),'recorded_maps':len(records),'component_deltas':counts}))
assert result['all_passed']
