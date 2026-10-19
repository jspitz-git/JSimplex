"""One-shot offline structural/source check. No Julia syntax or runtime claim."""
from pathlib import Path
import hashlib,json,re,subprocess
D=Path(__file__).resolve().parent;R=D.parents[3];C=R/'diagnostics/direct-bg-export-specialized/reproduce';P=D.with_name('DIRECT-BG-EXPORT-WORKSPACE-ALLOCATION-PROVENANCE-REVIEWED');A=D.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-PLAN')
checks={};pins={}
def data(p):
 p=Path(p);b=p.read_bytes();pins[str(p)]=hashlib.sha256(b).hexdigest();return b
def tx(p):return data(p).decode()
def rd(p):return json.loads(data(p))
def ck(n,v):checks[n]=bool(v)
def ren(s):return s.replace('_bgx_','_bgxs_').replace('BGExport','BGSpecializedExport').replace('_BGXBuildOwner','_BGXSBuildOwner')
def unren(s):return s.replace('_bgxs_','_bgx_').replace('BGSpecializedExport','BGExport').replace('_BGXSBuildOwner','_BGXBuildOwner')
inverse=rd(C/'source-inverse.json');counts=0
for n,e in inverse['files'].items():
 original=data(e['source']);candidate=tx(C/(n+'.jl'));back=candidate
 for edit in reversed(e['edits']):
  ck(n+'_unique_'+str(counts),back.count(edit['after'])==1);back=back.replace(edit['after'],edit['before']);counts+=1
 ck(n+'_whole_inverse',unren(back).encode()==original)
 ck(n+'_hashes',pins[e['source']]==e['source_sha256'] and pins[str(C/(n+'.jl'))]==e['candidate_sha256'])
ck('nine_method_splits',counts==9)
allcode='\n'.join(tx(C/(n+'.jl')) for n in inverse['files'])
ck('bounded_ten_inline_annotations',allcode.count('@inline ')==10)
ck('no_global_generation_or_value_specialization',not any(t in allcode for t in ['@eval','@generated','Val{n}','Val{l}','Val{u}']))
ck('no_old_candidate_definitions',not re.search(r'(?:function |struct )_?BGExport|function _bgx_',allcode))
prepared=rd(D/'tests-prepared.json');ck('test_first',prepared['candidate_absent'] is True)
for n,e in prepared['test_lineage'].items():
 ck(n+'_exact_test_inverse',tx(C/n)==ren(tx(e['source'])) and pins[e['source']]==e['original_sha256'])
ck('boundary_source_prepared_first',data(C/'boundary-tests.jl')==data(D/'boundary-tests.input.jl'))
boundary=tx(C/'boundary-tests.jl')
ck('three_explicit_boundary_tests',all('function '+n+'()' in boundary for n in ['boundary_request_equivalence','boundary_hook_order','boundary_hot_and_hook_agree']) and boundary.count('@testset ')==3)
ck('fixed_test_logs_and_sentinels','undef,256' in boundary and 'undef,5' in boundary and 'err===log.sentinel' in boundary and 'err===a.sentinel' in boundary)
manifest=rd(C/'overlay-manifest.json');stage=Path(manifest['stage']);base=Path(manifest['base']);prior=rd(P/'stages.json')['green']
ck('base_matches_saved79',manifest['base_sha256']==prior['sha256'] and len(prior['sha256'])==79)
for label,root,mapping in [('base',base,manifest['base_sha256']),('stage',stage,manifest['stage_sha256'])]:
 actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}
 ck(label+'_exact_membership',actual==set(mapping))
 ck(label+'_all_hashes',all(hashlib.sha256(data(root/p)).hexdigest()==h for p,h in mapping.items()))
ck('83files',len(manifest['stage_sha256'])==83)
ck('root_exact_include_inverse',tx(stage/'src/JSimplex.jl').replace(manifest['root_addition'],'')==tx(base/'src/JSimplex.jl') and tx(stage/'src/JSimplex.jl').count(manifest['root_addition'])==1)
ck('staged_candidate_exact',all(data(stage/'src'/('_bgxs_'+n+'.jl'))==data(C/(n+'.jl')) for n in inverse['files']))
for n in ['workspace-tests.jl','import-tests.jl','lifecycle-tests.jl','boundary-tests.jl']:
 for path in re.findall(r'include\("([^"\n]+)"\)',tx(C/n)):
  target=(C/path).resolve();data(target)
ck('top_level_test_order',manifest['test_order']==[str(C/n) for n in ['workspace-tests.jl','import-tests.jl','lifecycle-tests.jl','boundary-tests.jl']])
for name in ['review.json','publication.json']:
 j=rd(A/name);ck('accepted_plan_'+name,all(hashlib.sha256(data(Path(p) if Path(p).is_absolute() else R/p)).hexdigest()==h for p,h in j['sha256'].items()))
ck('plan_accepted',rd(A/'review.json')['accepted'] is True)
for p in [R/'AGENTS.md',D/'host.json',D/'prepare.py',D/'tests-prepare.py',Path(__file__),C/'work-memory-ledger.md',D/'REPORT.md',R/'docs/superpowers/specs/2026-10-19-direct-bg-export-specialization.md',R/'docs/superpowers/plans/2026-10-19-direct-bg-export-specialization.md',R/'diagnostics/direct-bg-export-workspace/reproduce/composition-ledger.md',R/'diagnostics/direct-bg-export-workspace/reproduce/work-memory-ledger.md']:data(p)
ck('tracked_untouched',not subprocess.check_output(['git','diff','HEAD','--name-only'],cwd=R,text=True).strip() and not subprocess.check_output(['git','diff','--cached','--name-only'],cwd=R,text=True).strip())
out=dict(all_passed=all(checks.values()),checks=checks,sha256=pins,scope='Offline literal/source inverses and current hashes only; no Julia/parser/runtime or allocation/timing qualification')
with (D/'source-check.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps({'all_passed':out['all_passed'],'checks':len(checks),'bindings':len(pins),'failed':[k for k,v in checks.items() if not v]}))
if not out['all_passed']:raise RuntimeError('Preserve failed check')
