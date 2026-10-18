from pathlib import Path
import json,hashlib,subprocess
R=Path.cwd();Q=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-SPLIT-U-PREPARATION';N=R/'diagnostics/direct-bg-split-upper/reproduce'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
def read(n):return json.loads((Q/n).read_text())
NAMES=['MEMORY-WORK.md', 'REPORT.md', 'author-budget-fix.json', 'author-counter-fix.json', 'geometry-model.json', 'geometry-model.py', 'host-closure.json', 'host.json', 'oracles.before-author-counters.jl.txt', 'original-reserve-renamed.jl.txt', 'prepare.py', 'replacement-reserve.jl.txt', 'review-initial.json', 'review-initial.md', 'review.json', 'review.md', 'reviewer-check-v1.json', 'reviewer-check-v1.py', 'source-check.json', 'source-check.py', 'tests-first.json', 'tests.before-author-budget.jl.txt']
checks={};bindings={}
def check(k,v):checks[k]=bool(v)
def verify(mapping):
 for name,want in mapping.items():
  p=R/name
  if sha(p)!=want:raise RuntimeError('hash mismatch '+name)
  bindings[name]=want
for name in ['source-check.json','review-initial.json','review.json']:
 verify(read(name)['sha256'])
check('all_current_source_review_bindings',True)
verify(json.loads((N/'source-bindings.json').read_text())['sha256'])
check('generator_and_inverse_bindings',True)
first=read('tests-first.json')
for current,preserved in [('split-upper-tests.jl','tests.before-author-budget.jl.txt'),('split-oracles.jl','oracles.before-author-counters.jl.txt')]:
 check('tests_first_'+current,sha(Q/preserved)==first['sha256'][str((N/current).relative_to(R))])
final=read('review.json')
check('independent_acceptance',final['scope']=='split U Task1 candidate preparation' and final['accepted'] is True and not final['findings'] and all(v==0 for v in final['unresolved'].values()))
check('no_avoidable_cost_finding',final['unnecessary_work_or_memory_found'] is False)
check('source_checks',read('source-check.json')['all_passed'] is True)
check('geometry_checks',read('geometry-model.json')['all_passed'] is True)
check('review_checks',read('reviewer-check-v1.json')['all_passed'] is True)
check('tests_unexecuted',final['checks']['testsets_unexecuted']==25 and final['checks']['julia_runs']==0)
check('entry_refs',git('rev-parse','HEAD')=='c215f40966524dc16a63be42c6e9c540ff6b42d7' and git('rev-parse','master')=='26e2291745999f485a74f643298ca997d65c7205' and git('branch','--show-current')=='codex/simplex-core-architecture')
check('tracked_and_staged_unchanged',not git('diff','--name-only') and not git('diff','--cached','--name-only'))
h=read('host-closure.json');check('host_groups_sessions',len(h['groups'])==240 and not h['matches'] and h['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip())
check('exact_task1_membership',sorted(p.name for p in N.iterdir())==['source-bindings.json','split-oracles.jl','split-upper-tests.jl','split-upper.jl'])
check('exact_preclosure_membership',sorted(p.name for p in Q.iterdir())==sorted(NAMES+['closure.py','publication.py']))
for n in NAMES+['closure.py','publication.py']:bindings[str((Q/n).relative_to(R))]=sha(Q/n)
result={'scope':'Task1 offline candidate preparation closure','all_passed':all(checks.values()),'checks':checks,'sha256':bindings,'before_mapping':{'tests-first.json split-upper-tests.jl':'tests.before-author-budget.jl.txt','tests-first.json split-oracles.jl':'oracles.before-author-counters.jl.txt'},'no_julia_or_old_checker_rerun':True,'acceptance_boundary':'offline preparation only; Tasks2/3 and runtime not performed'}
with (Q/'closure.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({'all_passed':result['all_passed'],'checks':len(checks),'bindings':len(bindings)}))
if not result['all_passed']:raise SystemExit(1)
