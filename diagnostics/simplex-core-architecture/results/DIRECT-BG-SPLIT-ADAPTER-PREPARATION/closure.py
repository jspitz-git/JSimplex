from pathlib import Path
import json,hashlib,subprocess
R=Path.cwd();E=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-SPLIT-ADAPTER-PREPARATION';N=R/'diagnostics/direct-bg-split-upper/reproduce'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def at(k):return Path(k) if Path(k).is_absolute() else R/k
def pins(j,mapping=None):
 mapping=mapping or {}
 return all(sha(mapping.get(k,at(k)))==h for k,h in j['sha256'].items())
review=json.loads((E/'review.json').read_text());author=json.loads((E/'source-check-2.json').read_text());initial=json.loads((E/'source-check.json').read_text());o=json.loads((E/'overlay.json').read_text());S=Path(o['path']);host=json.loads((E/'host-closure.json').read_text());names=json.loads((E/'publication-names.json').read_text())['names']
mem=str((E/'MEMORY-WORK.md').relative_to(R));sm=str((E/'SOURCE-MAP.md').relative_to(R))
checks=dict(independent_acceptance=review['acceptance']=='PASS_OFFLINE_PREPARATION' and not review['unresolved_findings'],independent_all_checks=review['all_checks_passed'] and all(review['final_checks'].values()),review_all_current_hashes=pins(review),author22pass=author['all_passed'] and len(author['checks'])==22,author_hashes_preserved=pins(author,{mem:E/'MEMORY-WORK.before-review.md'}),initial_false_preserved=not initial['all_passed'] and not initial['checks']['current_original_stage_sources'],initial_bindings_preserved=pins(initial,{mem:E/'MEMORY-WORK.before-author-fix.md',sm:E/'SOURCE-MAP.before-author-fix.md'}),fix8pass=json.loads((E/'review-fix.json').read_text())['all_passed'],host_groups=not host['matches'] and len(host['groups'])==240,refs_unchanged=all(subprocess.check_output(['git','rev-parse',k],text=True).strip()==v for k,v in host['refs'].items()),stage81=len(o['sha256'])==81 and all(sha(S/k)==v for k,v in o['sha256'].items()),stage_membership={str(p.relative_to(S)) for p in S.rglob('*') if p.is_file()}==set(o['sha256']),actual_tracked_unchanged=subprocess.run(['git','diff','--quiet','HEAD'],cwd=R).returncode==0,index_empty=not subprocess.check_output(['git','diff','--cached','--name-only']),new_names_unique=len(names)==len(set(names)),only_new_scope=all(k.startswith(str(E.relative_to(R))+'/') or k in [str((N/x).relative_to(R)) for x in ['split-bg.jl','split-bg-tests.jl','fixtures.jl','adapter-source-bindings.json','prepare-adapter-overlay.py']] for k in names),no_unlisted_new_evidence={str(p.relative_to(R)) for p in E.iterdir() if p.is_file()}=={k for k in names if k.startswith(str(E.relative_to(R))+'/') and Path(k).name not in ['closure.json','publication.json']})
existing=[R/k for k in names if Path(k).name not in ['closure.json','publication.json']]
r=dict(scope='PASS only offline Task2 preparation; Julia UNEXECUTED; no Task3 admission.',all_passed=all(checks.values()),checks=checks,sha256={str(p.relative_to(R)):sha(p) for p in existing})
with (E/'closure.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=r['all_passed'],checks=len(checks),bindings=len(existing),failed=[k for k,v in checks.items() if not v])))
if not r['all_passed']:raise RuntimeError('closure rejected')
