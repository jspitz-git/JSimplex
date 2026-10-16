"""One-shot author source/provenance checks; no Julia syntax/runtime claim."""
from pathlib import Path
import json,hashlib,subprocess
E=Path(__file__).resolve().parent;R=E.parents[3];C=R/'diagnostics/direct-bg-dynamic-upper/reproduce';P=E.parent/'DIRECT-BG-DYNAMIC-U-PREPARATION'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(p):return json.loads(p.read_text())
checks={}
def ck(k,v):checks[k]=bool(v)
s=(C/'dynamic-bg-reviewed.jl').read_text();t=(C/'dynamic-bg-tests-reviewed.jl').read_text()
for name in ['overlay.json','overlay-reviewed.json']:
 o=rd(E/name);O=Path(o['path']);ck(name+'_membership',set(o['sha256'])=={str(p.relative_to(O)) for p in O.rglob('*') if p.is_file()});ck(name+'_hashes',all(sha(O/n)==h for n,h in o['sha256'].items()))
 src=Path(o['source']);a=b'\n'+o['root_addition'].encode()+b'\nend\n';root=(O/'src/JSimplex.jl').read_bytes()
 ck(name+'_inverse',root.count(a)==1 and root.replace(a,b'\nend\n')==(src/'src/JSimplex.jl').read_bytes() and all(sha(O/n)==h for n,h in o['baseline'].items() if n!='src/JSimplex.jl'))
for name in ['reference-bindings.json','reference-bindings-reviewed.json','actual-dispatch-bindings.json']:
 ck(name+'_bindings',all(sha(Path(n))==h for n,h in rd(C/name)['sha256'].items()))
ck('accepted_Task1_entry_pins',all(sha(Path(n))==h for n,h in rd(E/'entry.json')['sha256'].items()))
original=rd(P/'publication.json')['sha256'];ck('all_prior_Task1_publication_files_unchanged',all(sha(R/n)==h for n,h in original.items()))
tf=rd(E/'tests-first.json');ck('first_test_bytes_preserved',(E/'dynamic-bg-tests.jl.tests-first').read_bytes()==(E/'dynamic-bg-tests.jl.tests-first').read_bytes() and sha(E/'dynamic-bg-tests.jl.tests-first')==tf['sha256'][str(C/'dynamic-bg-tests.jl')])
fixture=R/'diagnostics/direct-lu-policy-adapters/reproduce/fixtures.jl';ck('frozen_exact_fixtures',sha(C/'fixtures.jl')==sha(fixture))
original_oracle=(C/'slot-upper-tests-reviewed.jl').read_text().split('function _bg_test_matrix()',1)[0].replace('::BGSlotUpper','::J.BGSlotUpper')
ck('Task1_oracle_inverse',(C/'slot-oracles.jl').read_text()==original_oracle)
ck('separate_factor_type','mutable struct DynamicBGFactor{F}\n' in s and ' <: ' not in s)
ck('no_global_dispatch_replacement','const DirectLUFactor' not in s and '::ComposedRowFactorization' not in s and '_direct_packed_upper(' not in s)
ck('policy_before_factorization',s.index('unsupported dynamic BG backend/policy')<s.index('ordinary=factorize('))
ck('slot_import_q','_bg_slots(parts.upper,parts.columns)' in s)
ck('same_arithmetic_order','old-m*U.value[s]' in s and 'value-=U.value[s]*w[row]' in s and 'w[row]-=U.value[s]*value' in s)
ck('same_two_slot_provenance','cache.next=3-cache.next' in s and 'entry.destination===direction && isequal(entry.direction,direction)' in s)
ck('no_hot_checker_or_materialization','_check_bg_slots' not in s and '_bg_selected_state' not in s and 'Matrix(' not in s and 'sort' not in s)
ck('transactional_refactor',s.index('candidate=_dynamic_bg_with_exporter(B')<s.index('typeof(candidate)===typeof(f)')<s.index('for name in fieldnames(typeof(f))'))
ck('tests_only_explicit_entry',t.count('function run_dynamic_bg_tests()')==1 and t.count('run_dynamic_bg_tests()')==2)
ck('seven_fixtures_both_policies','DirectLUFixtures.export_fixtures(), (backend,policy) in ARMS' in t)
ck('specific_success_and_failure','history(r)==history(d)==[' in t and 'er.info==ed.info==1' in t)
ck('nonfinite_intermediate_and_different_maps','all(isfinite,M.nzval)' in t and 'sd.upper.row_order!=sd.row_cache.order' in t)
ck('fill_growth_and_trace','d.upper.capacity==33 && d.upper.live_count==21' in t and 'observed==trace' in t)
ck('unsupported_before_backend','struct RejectBackend end' in t and 'unexpected dimension call' in t)
ck('R1_R2_fix_gates',all(rd(E/'review-fix.json')['checks'].values()))
ck('source_access_four_cases',len(rd(E/'lookup-work-witness.json')['rows'])==4)
paths=[Path(__file__).resolve(),C/'dynamic-bg-reviewed.jl',C/'dynamic-bg-tests-reviewed.jl',C/'reference-bindings-reviewed.json',C/'actual-dispatch-bindings.json',E/'REPORT.md',E/'overlay-reviewed.json',E/'overlay.json',E/'review-fix.json',E/'lookup-work-witness.json',E/'tests-first.json',E/'dynamic-bg-tests.jl.tests-first',fixture]
with (E/'offline-check.json').open('x') as f:json.dump(dict(scope='Offline literal/provenance checks only; Julia tests UNEXECUTED',all_passed=all(checks.values()),checks=checks,sha256={str(p):sha(p) for p in paths}),f,indent=2);f.write('\n')
print('Author offline checks',sum(checks.values()),'/',len(checks))
if not all(checks.values()):raise SystemExit(1)
