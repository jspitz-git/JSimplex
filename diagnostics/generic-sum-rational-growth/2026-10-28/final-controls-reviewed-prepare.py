from pathlib import Path
import json,hashlib
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-sum-rational-growth/2026-10-28')
s=(D/'finalize.py').read_text()
a=s.index("for n in ['publication-preparation-reviewed.json'");b=s.index("co=c.read('production-commit.json')",a)
s=s[:a]+'''# Validate the accepted preparation and every review binding before any mutation.
from publication_checks import verify_historical_maps
integration_map=c.read('integration-historical-path-map.json');protected=c.read('protected-before.json');baseline=c.read('baseline-tree.json');production=c.read('production-commit.json')
main_index=c.git(['rev-parse','--path-format=absolute','--git-path','index'])
prospective=dict(master_source_before=integration_map['source_before'],master_index_before=integration_map['master_index_before'])
verify_historical_maps(D,M,main_index,c.TARGET,production['names'],integration_map,prospective,protected,baseline,c.need,c.sha)
exact_before={**integration_map['source_before'],**integration_map['master_index_before']}
for n in ['finalization-preparation-review.json','publication-preparation-reviewed.json','production-review.json','commit-review.json','MASTER-run/result-review.json','GREEN-run/result-review.json']:
 r=c.read(n);c.need(r['accepted'] is True and r['findings']==[],'review '+n)
 for bound_path,bound_hash in r['bindings'].items():
  if c.sha(bound_path)==bound_hash:continue
  c.need(bound_path in exact_before,'unresolved prefinal review binding '+bound_path)
  old=exact_before[bound_path];c.need(old['sha256']==bound_hash and c.sha(old['before'])==bound_hash,'exact prefinal before binding '+bound_path)
'''+s[b:]
s=s.replace('Compilation is attributed to correctness and validation preparation; no candidate-specific cold-start saving is claimed.','Recorded compilation is attributed to correctness and validation preparation. Outer driver/startup work and a complete per-variant cold-specialization budget remain incompletely measured; no candidate-specific cold-start saving is claimed.')
s=s.replace('Two cold specialization methods and any captured-seed closure overhead are accounted for; no new persistent numerical cache or growing ledger is introduced.','Two cold specialization methods add compiler metadata whose full cold cost and retention were not separately measured. Per-call captured-seed closure overhead is included in the complete measured calls; native retention remains unqualified. No new persistent numerical cache or growing ledger is introduced.')
s=s.replace("(D/'finalize.py').resolve()","(D/'finalize-reviewed.py').resolve()").replace("shutil.copyfile(__file__,D/'finalize.py')","shutil.copyfile(__file__,D/'finalize-reviewed.py')")
compile(s,str(D/'finalize-reviewed.py'),'exec');(D/'finalize-reviewed.py').write_text(s)
s=(D/'closure.py').read_text();old="checks['verbatim_continuation_and_maps']=True";new="""from publication_checks import verify_historical_maps
c.need(hist['master_before']==c.TARGET,'exact continuation old master ref')
verify_historical_maps(D,M,mi,c.TARGET,co['names'],c.read('integration-historical-path-map.json'),hist,protected,base,c.need,digest)
checks['verbatim_continuation_and_maps']=True""";assert s.count(old)==1;s=s.replace(old,new)
s=s.replace("cmp['windows']==47448 and cmp['original_failed_assertions']","cmp['windows']==47448 and cmp['preparation']==2674 and cmp['original_failed_assertions']")
compile(s,str(D/'closure-reviewed.py'),'exec');(D/'closure-reviewed.py').write_text(s)
(D/'final-controls-review-fix.json').write_text(json.dumps(dict(Julia_executed=False,controls_executed=False,changes=['Finalizer requires accepted preparation and exact verified review bindings before writes; only validated original source/index beforeimages can resolve changed paths','Closure verifies exact source/index maps and master_before through existing helper plus explicit2674prep count','Report explicitly limits outer/startup/pervariantcoldmethodmetadata/native-retention coverage and separates included percallclosure overhead','Canonical finalizer self-copy target names reviewed script and cannot rewrite frozen original'],original={n:hashlib.sha256((D/n).read_bytes()).hexdigest() for n in ['finalize.py','closure.py']},canonical={n:hashlib.sha256((D/n).read_bytes()).hexdigest() for n in ['finalize-reviewed.py','closure-reviewed.py']}),indent=2)+'\n')
(D/'final-controls-reviewed-prepare.py').write_text(Path(__file__).read_text());print('canonical reviewed finalizer/closure fixes prepared UNEXECUTED; originals preserved')
