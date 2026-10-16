"""Exclusive offline Task1 closure; exact historical mappings, no Julia."""
from pathlib import Path
import json,hashlib,subprocess,re
R=Path(__file__).resolve().parents[4];E=Path(__file__).resolve().parent;C=R/'diagnostics/direct-bg-block-upper/reproduce'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True).strip()
def need(c,m):
    if not c:raise RuntimeError(m)
def verify(record,maps):
    return all(sha(maps.get(k,Path(k)))==h for k,h in record['sha256'].items())
checks={}
checks['budget_initial_preserved_and_pins']=json.loads((E/'budget.json').read_text())['all_passed'] is False and verify(json.loads((E/'budget.json').read_text()),{str(C/'block-upper.jl'):E/'block-upper.jl.before-reserve-fix',str(C/'block-upper-tests.jl'):E/'block-upper-tests.jl.before-capacity-fix'})
checks['budget_final_pass_and_pins']=json.loads((E/'budget-final.json').read_text())['all_passed'] is True and verify(json.loads((E/'budget-final.json').read_text()),{str(C/'block-upper.jl'):E/'block-upper.jl.before-reserve-fix',str(C/'block-upper-tests.jl'):E/'block-upper-tests.jl.before-cursor-addition'})
checks['source_check33_and_pins']=len(json.loads((E/'source-check.json').read_text())['checks'])==33 and verify(json.loads((E/'source-check.json').read_text()),{str(E/'MEMORY-WORK.md'):E/'MEMORY-WORK.md.before-count-fix'})
for name in ('overlay.json','overlay-reviewed.json'):
    d=json.loads((E/name).read_text());O=Path(d['path'])
    checks[name+'_exact_membership']=len(d['sha256'])==78 and {str(p.relative_to(O)) for p in O.rglob('*') if p.is_file()}==set(d['sha256'])
    checks[name+'_full_hashes']=all(sha(O/k)==v for k,v in d['sha256'].items())
d=json.loads((E/'overlay-reviewed.json').read_text());O=Path(d['path'])
checks['canonical_candidate_stage_identity']=all((C/a).read_bytes()==(O/b).read_bytes() for a,b in [('block-upper.jl','src/block-upper.jl'),('block-oracles.jl','test/block-oracles.jl'),('block-upper-tests.jl','test/block-upper-tests.jl')])
review=(E/'independent-review-v1.md').read_text()
checks['independent_review_accepted']=review.startswith('# Independent Task1 offline review — PASS within the offline boundary') and all(sha(p) in review for p in [C/'block-upper.jl',C/'block-oracles.jl',C/'block-upper-tests.jl',E/'MEMORY-WORK.md'])
fb=json.loads((E/'independent-final-bindings-v1.json').read_text())
checks['review_final_bindings']=all(sha(R/k)==v for k,v in fb['sha256'].items())
ic=json.loads((E/'independent-check-v1.json').read_text())
checks['independent21_pass_and_pins']=ic['all_passed'] is True and len(ic['checks'])==21 and all(ic['checks'].values()) and all(sha(E/'MEMORY-WORK.md.before-count-fix' if k.endswith('/MEMORY-WORK.md') else R/k)==v for k,v in ic['sha256'].items())
checks['source_check_all_pass']=json.loads((E/'source-check.json').read_text())['all_passed'] is True
checks['tracked_originals_unchanged']=subprocess.run(['git','diff','--quiet','HEAD'],cwd=R).returncode==0
checks['index_empty']=not git('diff','--cached','--name-only')
h=json.loads((E/'host.json').read_text())
checks['local_refs_unchanged']=git('rev-parse','HEAD')==h['head'] and git('rev-parse','master')==h['master']
checks['remote_refs_unchanged']=git('ls-remote','--heads','origin','codex/simplex-core-architecture','master')==h['remote']
checks['no_candidate_in_actual_src']=not (R/'src/block-upper.jl').exists()
checks['foreign_process_scope_explicit']=all(not p['historical'] for p in h['matches']) and 'No Julia' in (E/'REPORT.md').read_text()
paths=sorted([p for p in E.iterdir() if p.is_file() and p.name not in ('closure.json','publication.json')]+[p for p in C.iterdir() if p.is_file()])
result=dict(all_passed=all(checks.values()),checks=checks,sha256={str(p.relative_to(R)):sha(p) for p in paths},scope='Task1 source/test preparation only. No Julia, runtime tests, new numerical measurements, Task2 or performance acceptance. Exact preserved old bindings verified; no old script rerun.')
with (E/'closure.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=result['all_passed'],checks=len(checks),bindings=len(paths),failed=[k for k,v in checks.items() if not v]),indent=2))
need(result['all_passed'],'Closure failed before publication')
