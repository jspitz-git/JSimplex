from pathlib import Path
import hashlib,json,subprocess
R=Path.cwd(); Q=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-SPLIT-U-PLAN'
def read(name):return json.loads((Q/name).read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
checks={}; bindings={}
def check(k,v):checks[k]=bool(v)
fix=read('review-fix.json')['bindings']
def verify_map(mapping,old=False,local=False):
 for name,want in mapping.items():
  p=(Q/name) if local else Path(name)
  if not p.is_absolute():p=R/p
  rel=str(p.relative_to(R))
  if old and rel in fix:p=R/fix[rel]['before_path']
  if sha(p)!=want:raise RuntimeError('binding mismatch '+str(p))
  bindings[str(p.relative_to(R))]=want
for name,key in [('author-check.json','source_readtime_sha256'),('review-initial.json','readtime_sha256'),('reviewer-check-v1.json','readtime_sha256')]:verify_map(read(name)[key],old=True)
check('initial_bindings_preserved',True)
final=read('review.json');verify_map(final['final_readtime_sha256'])
for name in ['review-initial.json','reviewer-amendment-v2.json','review.json']:verify_map(read(name)['evidence_sha256'],local=True)
check('final_and_evidence_bindings',True)
check('initial_rejection_preserved',read('review-initial.json')['accepted'] is False and read('review-initial.json')['important']==1)
check('review_accepted',final['scope']=='split free block BG plan' and final['accepted'] is True and all(final[k]==0 for k in ['critical','important','minor']) and not final['findings'])
check('offline_checks_pass',all(read(n)['all_passed'] is True for n in ['author-check.json','review-fix.json','reviewer-check-v1.json','reviewer-amendment-v2.json']))
for name,record in fix.items():
 check('before_after_'+name,sha(R/record['before_path'])==record['before_sha256'] and sha(R/name)==record['after_sha256'])
check('tracked_unchanged',not git('diff','--name-only') and not git('diff','--cached','--name-only'))
check('entry_refs',git('rev-parse','HEAD')=='c0fe2e2b107d6cfc38a8d4bdead355f651cca8e0' and git('rev-parse','master')=='26e2291745999f485a74f643298ca997d65c7205' and git('branch','--show-current')=='codex/simplex-core-architecture')
h=read('host-closure.json');check('fresh_host_groups_sessions',len(h['groups'])==240 and not h['matches'] and h['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip())
check('no_candidate',not (R/'diagnostics/direct-bg-split-upper').exists())
names=['author-check.json','host.json','host-closure.json','spec.before-review.md','plan.before-review.md','review-fix.json','review-initial.md','review-initial.json','reviewer-check-v1.py','reviewer-check-v1.json','reviewer-record-initial.py','reviewer-amendment-v2.py','reviewer-amendment-v2.json','review.md','review.json','reviewer-record-final.py','closure.py','publication.py']
check('exact_new_evidence',sorted(p.name for p in Q.iterdir())==sorted(names))
for name in names:bindings[str((Q/name).relative_to(R))]=sha(Q/name)
result={'scope':'new split free block BG plan closure only','all_passed':all(checks.values()),'checks':checks,'sha256':bindings,'before_mapping':fix,'no_old_checker_rerun':True,'no_julia_or_implementation':True}
with (Q/'closure.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({'all_passed':result['all_passed'],'checks':len(checks),'bindings':len(bindings)}))
if not result['all_passed']:raise SystemExit(1)
