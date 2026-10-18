"""New, single-use offline amendment verification; no old checker is imported or run."""
from pathlib import Path
import hashlib,json,re
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
E=Path(__file__).resolve().parent;C=R/'diagnostics/direct-bg-export-workspace/reproduce'
readtime={}
def sha(p):
 p=Path(p);h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 readtime[str(p)]=h.hexdigest();return h.hexdigest()
def obj(p):sha(p);return json.loads(Path(p).read_text())
def verify(d,mapping=None):
 return {n:sha((mapping or {}).get(n,n))==h for n,h in d.items()}
a=obj(E/'source-check.json');initial=obj(E/'review.json');initial_check=obj(E/'reviewer-check.json');fix=obj(E/'review-fix.json');lineage=obj(E/'lineage.json')
expected={str(C/n):str(E/(n+'.before-review')) for n in ['import-tests.jl','work-memory-ledger.md']}
checks={'mapping_exactly_two_expected_paths':lineage['before_mapping']==expected and fix['before_mapping']==expected}
comparisons={
 'original_author_702':verify(a['readtime_sha256'],expected),
 'initial_review_readtime':verify(initial['readtime_sha256'],expected),
 'initial_review_evidence':verify(initial['evidence_sha256']),
 'initial_checker_readtime':verify(initial_check['readtime_sha256'],expected),
 'amendment_author_9':verify(fix['readtime_sha256']),
 'lineage':verify(lineage['sha256'])}
checks.update({k:all(v.values()) for k,v in comparisons.items()})
checks['initial_rejection_preserved']=initial['accepted'] is False and initial['critical']==0 and initial['important']==1 and initial['minor']==0 and initial['findings'][0]['id']=='R1'
checks['amendment_author_reports_eight_pass']=fix['all_passed'] is True and len(fix['checks'])==8 and all(fix['checks'].values())
checks['original_702_and_amendment_9_count']=len(a['readtime_sha256'])==702 and len(fix['readtime_sha256'])==9
manifest=obj(C/'source-manifest.json');seal=obj(manifest['seal']);stage=Path(manifest['stage'])
sealed={n:d['sha256'] for n,d in seal['inventory'].items() if n.startswith(str(stage)+'/') or '/.julia/' in n}
comparisons['original_seal_679']=verify(sealed)
checks['original_seal_679_match']=len(sealed)==679 and all(comparisons['original_seal_679'].values())
checks['complete_stage75_runtime604']=sum(n.startswith(str(stage)+'/') for n in sealed)==75 and sum('/.julia/' in n for n in sealed)==604 and {str(p) for p in stage.rglob('*') if p.is_file()}=={n for n in sealed if n.startswith(str(stage)+'/')}
names=['workspace.jl','export.jl','import.jl','workspace-tests.jl','import-tests.jl','work-memory-ledger.md','source-inverse.json','source-manifest.json']
checks['candidate_exact_eight_files']={p.name for p in C.iterdir() if p.is_file()}==set(names)
checks['only_expected_two_candidate_changes']={n for n in names if sha(C/n)!=a['readtime_sha256'][str(C/n)]}=={'import-tests.jl','work-memory-ledger.md'}
current=(C/'import-tests.jl').read_text();old=(E/'import-tests.jl.before-review').read_text();original_path=R/'diagnostics/direct-lu-policy-adapters/reproduce/lifecycle-tests.jl';sha(original_path);original=original_path.read_text()
compact=lambda s:re.sub(r'\s+','',s)
current_c=compact(current);original_c=compact(original.replace('backend','f'))
ops=['refactor_input=copy(B)','refactor_input.nzval .*= 2.0','lu!(f.factorization,refactor_input)','issuccess(f.factorization)','f.core.factors .= 7.0','f.diagonal .+= 1.0','reverse!(f.row_order)','for v in f.lower; v.values .+= 1.0; end','for v in f.upper; v.values .+= 1.0; end']
checks['original_backend_operations_retained']=all(compact(op) in current_c and compact(op) in original_c for op in ops)
checks['native_witness_added_once']=current.count('lu!(f.factorization,refactor_input)')==1 and 'lu!(f.factorization,refactor_input)' not in old
checks['coupled_witness_precedes_backend_mutation']=current.index('@test !export_identity(B,wrong)')<current.index('lu!(f.factorization,refactor_input)')
checks['complete_nine_array_owner_inventory']='export_arrays(e)=(e.lower.colptr,e.lower.rowval,e.lower.nzval,e.upper.colptr,e.upper.rowval,e.upper.nzval,e.rows,e.columns,e.scaling)' in current
checks['complete_export_snapshot']='export_snapshot(e)=(snapshot(e.lower),snapshot(e.upper),copy(e.rows),copy(e.columns),copy(bits(e.scaling)),e.divide_scaling)' in current
checks['source_and_export_owner_checks']=all(s in current for s in ['zip(export_arrays(e),export_arrays(ref))','zip(export_arrays(e),export_owners)','zip((B.colptr,B.rowval,B.nzval),input_owners)','refactor_input.colptr==B.colptr && refactor_input.rowval==B.rowval','isequal(refactor_input.nzval[k],2.0*B.nzval[k])','@test isequal(export_snapshot(e),frozen)','@test export_identity(B,e)'])
fixtures=R/'diagnostics/direct-lu-policy-adapters/reproduce/fixtures.jl';sha(fixtures)
fixture_names=re.findall(r'\(name=:(\w+),B=',fixtures.read_text())
checks['six_nonempty_fixtures_each_selected_backend']=len(fixture_names)==7 and fixture_names.count('empty')==1 and 'if size(B,1)>0' in current and '((:native,X._NATIVE_PIVOT_ONE),(:markowitz,X._NATIVE_PIVOT_DEFAULT))' in current
ledger=(C/'work-memory-ledger.md').read_text()
checks['added_test_work_memory_declared']=all(s in ledger for s in ['exactly six nonempty native','six Markowitz','14 full export snapshots','six native input CSC copies','Snapshot equality probes','rational export_identity','Tests remain UNEXECUTED'])
tests=current+(C/'workspace-tests.jl').read_text();sites=len(re.findall(r'@test(?:_throws)?\b',tests))
checks['78_static_sites_not_runtime_total']=sites==78 and fix['static_assertion_sites']==78
checks['no_task2_task3_or_autorun']=not (C/'factor.jl').exists() and not (C/'driver.jl').exists() and not re.search(r'^run_(workspace|import)_tests\(\)',tests,re.M)
# Bind all current local evidence, including closure/publication TEXT ONLY.
for p in sorted(E.iterdir()):
 if p.is_file():sha(p)
for n in names:sha(C/n)
result={'all_passed':all(checks.values()),'checks':checks,'comparisons':comparisons,'readtime_sha256':readtime,'static_assertion_sites':sites,'resolved_finding':'R1','scope':'Independent offline amendment hashes and literal text only; no old script run/import, Julia parse/load/execute, process scan, Git mutation, closure/publication execution'}
with (E/'amendment-reviewer-check.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({'all_passed':result['all_passed'],'checks':len(checks),'bindings':len(readtime),'static_sites':sites,'failed':[k for k,v in checks.items() if not v]}))
if not result['all_passed']:raise SystemExit(1)
