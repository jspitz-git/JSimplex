"""Exclusive Task2 offline closure; historical mappings explicit, no old scripts."""
from pathlib import Path
import json,hashlib,subprocess
R=Path(__file__).resolve().parents[4];E=Path(__file__).resolve().parent;C=R/'diagnostics/direct-bg-block-upper/reproduce'
NEW=('block-bg.jl','block-bg-tests.jl','fixtures.jl','prepare-adapter-overlay.py','adapter-source-bindings.json','prepare-adapter-overlay-reviewed.py','adapter-source-bindings-reviewed.json')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(n):return json.loads((E/n).read_text())
def path(k):return Path(k) if Path(k).is_absolute() else R/k
def pins(d,maps=None):return all(sha((maps or {}).get(k,path(k)))==v for k,v in d['sha256'].items())
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True).strip()
def need(c,m):
 if not c:raise RuntimeError(m)
checks={}
checks['reviewed_source40_pass_bindings']=read('source-check-reviewed.json')['all_passed'] is True and len(read('source-check-reviewed.json')['checks'])==40 and pins(read('source-check-reviewed.json'))
checks['alias_fix9_pass_bindings']=read('review-fix.json')['all_passed'] is True and len(read('review-fix.json')['checks'])==9 and pins(read('review-fix.json'))
checks['alias_runtime_readtime_bindings']=all(sha(Path(k))==v for k,v in read('review-fix.json')['readtime_runtime_sources'].items())
checks['stage_source7_pass_bindings']=read('stage-source-map.json')['all_passed'] is True and len(read('stage-source-map.json')['checks'])==7 and pins(read('stage-source-map.json'))
oldmaps={str((C/'block-bg.jl').relative_to(R)):E/'block-bg.jl.before-alias-review',str((C/'block-bg-tests.jl').relative_to(R)):E/'block-bg-tests.jl.before-alias-review',str((E/'MEMORY-WORK.md').relative_to(R)):E/'MEMORY-WORK.md.before-alias-review',str((E/'SOURCE-MAP.md').relative_to(R)):E/'SOURCE-MAP.md.before-alias-review'}
checks['initial_source_record_preserved_mapped']=pins(read('source-check.json'),oldmaps)
v1maps={str((C/'block-bg.jl').relative_to(R)):E/'block-bg.jl.before-alias-review',str((C/'block-bg-tests.jl').relative_to(R)):E/'block-bg-tests.jl.before-coverage-amendment'}
checks['initial_reviewer_pins_mapped']=pins(read('reviewer-source-check-v1.json'),v1maps)
checks['test_first_pins_mapped']=pins(read('tests-first.json'),{str(C/'block-bg-tests.jl'):E/'block-bg-tests.jl.before-coverage-amendment'})
checks['original_generator_failure_preserved']=read('prepare-adapter-failure.json')['exit_code']==1
checks['initial_inverse_source_preserved']=read('adapter-inverse.json')['candidate_sha256']==sha(E/'block-bg.jl.before-alias-review')
inv=read('adapter-inverse-reviewed.json');s=(C/'block-bg.jl').read_text()
checks['final_candidate_binding']=sha(C/'block-bg.jl')==inv['candidate_sha256']
for e in reversed(inv['edits']):
 need(s.count(e['after'])==e.get('count',1),'Inverse selector');s=s.replace(e['after'],e['before'])
for a,b in reversed(inv['renames']):s=s.replace(b,a)
checks['whole_source_inverse']=s.encode()==Path(inv['reference']).read_bytes()
for n in ('overlay.json','overlay-reviewed.json'):
 d=read(n);O=Path(d['path']);checks[n+'_81_exact']=len(d['sha256'])==81 and {str(p.relative_to(O)) for p in O.rglob('*') if p.is_file()}==set(d['sha256']) and all(sha(O/k)==v for k,v in d['sha256'].items())
review=(E/'independent-review-final.md').read_text()
checks['independent_final_acceptance']='PASS for OFFLINE Task2 source preparation only. No unresolved blocking findings remain' in review and all(sha(p) in review for p in [C/'block-bg.jl',C/'block-bg-tests.jl',E/'MEMORY-WORK.md'])
checks['independent_final_checks']=read('reviewer-final-check.json')['all_passed'] is True and pins(read('reviewer-final-check.json'))
checks['independent_final_bindings']=pins(read('reviewer-final-bindings.json'))
checks['independent_stage_agrees']=read('reviewer-final-check.json')['stage_sha256']==read('overlay-reviewed.json')['sha256']
checks['Task1_frozen_bindings']=pins(json.loads((E.parent/'DIRECT-BG-BLOCK-U-PREPARATION/closure.json').read_text()))
checks['tracked_originals_unchanged']=subprocess.run(['git','diff','--quiet','HEAD'],cwd=R).returncode==0
checks['index_empty']=not git('diff','--cached','--name-only')
h=read('host.json');checks['local_refs_unchanged']=git('rev-parse','HEAD')==h['head'] and git('rev-parse','master')==h['master']
checks['remote_refs_unchanged']=git('ls-remote','--heads','origin','codex/simplex-core-architecture','master')==h['remote']
checks['no_actual_candidate']=not (R/'src/block-bg.jl').exists()
checks['no_historical_process_match']=not any(p['historical'] for p in h['matches'])
checks['scope_explicit']='No Julia' in (E/'REPORT.md').read_text() and 'Task3 driver/admission and production integration were not started' in (E/'REPORT.md').read_text()
files=sorted([p for p in E.iterdir() if p.is_file() and p.name not in ('closure.json','publication.json')]+[C/n for n in NEW])
d=dict(all_passed=all(checks.values()),checks=checks,sha256={str(p.relative_to(R)):sha(p) for p in files},new_candidate_names=list(NEW),scope='Offline Task2 only, no Julia or actual src/test/env/CI/master/continuation changes; no old script rerun.')
with (E/'closure.json').open('x') as f:json.dump(d,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=d['all_passed'],checks=len(checks),bindings=len(files),failed=[k for k,v in checks.items() if not v]),indent=2));need(d['all_passed'],'Closure failed')
