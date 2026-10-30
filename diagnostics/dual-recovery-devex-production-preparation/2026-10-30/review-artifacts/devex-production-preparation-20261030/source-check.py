from pathlib import Path
import hashlib,json,re,sys,subprocess,difflib
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');D=W/'diagnostics/dual-recovery-devex-production-preparation/2026-10-30';Q=D/'prepared';O=W/'diagnostics/dual-recovery-devex-task4/2026-10-30';P=W/'diagnostics/dual-recovery-devex-cost-admission/2026-10-30'
sys.path.insert(0,str(P));import common as C
bindings={}
def sha(p):
 p=Path(p);h=hashlib.sha256(p.read_bytes()).hexdigest();bindings[str(p)]=h;return h
def read(p):sha(p);return json.loads(Path(p).read_text())
def git(*a):return subprocess.check_output(['git','-C',str(W),*a],text=True).strip()
m=read(D/'manifest.json');checks={};checks['exact11_payload_names']=sorted(str(p.relative_to(Q)) for p in Q.rglob('*') if p.is_file())==m['payload'] and len(m['payload'])==11
checks['all_payload_hashes']=all(sha(Q/n)==h for n,h in m['payload_sha256'].items());checks['baseline4_current_and_master']=len(m['baseline_sha256'])==4 and all(sha(D/'baseline'/n)==sha(W/n)==v and git('hash-object',str(W/n))==git('rev-parse','master:'+n) for n,v in m['baseline_sha256'].items());checks['all_exact_copies']=all(sha(p)==sha(v['copy'])==v['sha256'] for p,v in m['exact_copies'].items())
replayed={}
for rel,v in m['transforms'].items():
 s=Path(v['source']).read_text();sha(v['source']);need=sha(v['source'])==v['source_sha256']
 for r in v['replacements']:
  need=need and s.count(r['old'])==1;s=s.replace(r['old'],r['new'],1)
 replayed[rel]=need and s==(Q/rel).read_text()
checks['all6_full_transform_replays']=len(replayed)==6 and all(replayed.values())
source_names=('simplex_numerics.jl','simplex_recovery.jl','simplex_pivot.jl');G=W/'diagnostics/dual-recovery-devex-green-fixture-preparation/2026-10-30/prepared/overlays/candidate/src'
checks['three_production_sources_exact_qualified']=all(sha(Q/'src'/n)==sha(O/'overlays/candidate/src'/n)==sha(G/n) for n in source_names)
checks['only3_production_files']=sorted(n for n in m['payload'] if n.startswith('src/'))==sorted('src/'+n for n in source_names)
checks['runtests_exact5includes_only']=(Q/'test/runtests.jl').read_text().replace(''.join('    include("'+n+'")\n' for n in m['ordered_new_includes']),'',1)==(W/'test/runtests.jl').read_text()
checks['new_ordered_includes_exist_once']=all((Q/'test'/n).is_file() and (Q/'test/runtests.jl').read_text().count('include("'+n+'")')==1 for n in m['ordered_new_includes'])
old_asserts=[s.strip().replace('revalidation.value','revalidation').replace('reset.value','reset') for s in (O/'endpoint.jl').read_text().splitlines() if s.lstrip().startswith('@test')];new_asserts=[s.strip() for s in (Q/'test/recovery_devex_pivot_tests.jl').read_text().splitlines() if s.lstrip().startswith('@test')]
checks['endpoint23_assertions_retained_ordered_plus_work']=len(old_asserts)==23 and len(new_asserts)==24 and new_asserts[:-1]==old_asserts and new_asserts[-1]=='@test calls==(1,3) && (f.builder.last.forwards,f.builder.last.backwards)==(2,4)'
checks['no_permanent_profile_serialization_driver_hooks']=all(not any(t in (Q/'test'/n).read_text() for t in ('@timed','TOML','TASK4_OUTPUT','Base.summarysize','push_testset','pop_testset','AbstractTestSet','/diagnostics/','.superpowers/')) for n in m['ordered_new_includes'])
# No numerical source/compiler/parser execution: these are explicit fixed-text checks.
checks['new_test_helpers_exact']=sha(Q/'test/support/devex_refinement_reference.jl')==sha(O/'tests/reference.jl') and sha(Q/'test/support/devex_legacy_rebuild_reference.jl')==sha(O/'tests/legacy_rebuild_reference.jl')
checks['support_includes_resolve']=all((Q/'test'/n).is_file() for n in ('support/devex_refinement_reference.jl','support/devex_legacy_rebuild_reference.jl'))
checks['no_module_name_collisions']=all(not any(('module '+name) in p.read_text() for p in (W/'test').rglob('*.jl')) for name in ('RefinementOutcomeTests','RefinementReferenceComparison','RecoveryWeightTests','RecoveryDevexFallbackTests','RecoveryDevexPivotTests','LegacyRecoveryWeights'))
fixture_paths=[W/'test/fixtures/solver/netlib/adlittle.mps',W/'test/fixtures/solver/generated/wide-bound129.mps'];checks['both_existing_regression_fixtures_available']=all(p.is_file() and p.stat().st_size>0 for p in fixture_paths)
for p in fixture_paths:sha(p)
patch=[]
for rel in m['payload']:
 old=(D/'baseline'/rel).read_text() if (D/'baseline'/rel).exists() else '';new=(Q/rel).read_text();patch.append(f'diff --git a/{rel} b/{rel}\n')
 if not (D/'baseline'/rel).exists():patch.append('new file mode 100644\n')
 patch.extend(difflib.unified_diff(old.splitlines(keepends=True),new.splitlines(keepends=True),fromfile='a/'+rel if (D/'baseline'/rel).exists() else '/dev/null',tofile='b/'+rel))
checks['patch_exact_rebuilt_from_payload']=''.join(patch)==(D/'production.patch').read_text();sha(D/'production.patch')
# Preserve prior publications without executing any historical checker/auditor main.
prior={}
for folder in ('dual-recovery-devex-reference-cost-result','dual-recovery-devex-candidate-cost-result'):
 base=W/'diagnostics'/folder/'2026-10-30';pub=read(base/'publication.json')
 for rel in pub['expected_names']:
  p=W/rel;prior[str(p)]=sha(p);checks.setdefault('all264_cost_publication_blobs_unchanged',True);checks['all264_cost_publication_blobs_unchanged'] &= git('hash-object',str(p))==git('rev-parse','HEAD:'+rel)
checks['all264_cost_publication_blobs_unchanged'] &= len(prior)==264
C.validate_closed('reference-cost');C.validate_closed('candidate-cost');checks['both_closed_runtime_memberships_unchanged']=True
for phase in ('reference-cost','candidate-cost'):
 for p in C.out(phase).rglob('*'):
  if p.is_file():sha(p)
for name in ('dual-recovery-devex-green2-result','dual-recovery-devex-reference-cost-result','dual-recovery-devex-candidate-cost-result'):
 base=W/'diagnostics'/name/'2026-10-30';r=read(base/'review-final.json');checks['accepted_'+name]=r['accepted'] is True and r['runtime_accepted'] is True and r['production_admission'] is False
for p in [W/'docs/superpowers/plans/2026-10-30-dual-recovery-devex-fallback.md',W/'docs/superpowers/specs/2026-10-30-dual-recovery-devex-fallback-design.md',D/'host.json',D/'prepare.py',Path(__file__)]:sha(p)
checks['head_master_tree_index_unchanged']=git('rev-parse','HEAD')==m['baseline_head'] and git('rev-parse','master')==git('rev-parse','origin/master')==m['master'] and not git('diff','HEAD','--name-only') and not git('diff','--cached','--name-only') and not git('diff','master','HEAD','--','src','test','Project.toml','.github')
checks['source_only_no_new_numerical_time']=m['prepared_runtime_unexecuted'] is True and read(D/'host.json')['used_seconds']==1108.3747013349202
result=dict(accepted=all(checks.values()),scope='source preparation only; Julia syntax/runtime/assembled permanent test execution UNEXECUTED',checks=checks,bindings=bindings,transform_replays=replayed,prior_publications=prior,lexical_test_sites=m['lexical_test_sites'],permanent_endpoint_explicit_sites=dict(original=23,prepared=24),patch_apply_check=dict(command='git apply --check diagnostics/dual-recovery-devex-production-preparation/2026-10-30/production.patch',observed_exit=0,provenance='previous direct tool execution in this turn; not rerun by this checker'),no_new_numerical_time=True)
with (D/'source-check.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
with (D/'source-check.py').open('xb') as f:f.write(Path(__file__).read_bytes())
print(json.dumps(dict(accepted=result['accepted'],checks=len(checks),bindings=len(bindings),payload_files=11,endpoint_old_sites=23,endpoint_new_sites=24,failed=[k for k,v in checks.items() if not v])))
if not result['accepted']:raise SystemExit(1)
