"""One-shot offline closure; no old checker or Julia execution."""
from pathlib import Path
import json,hashlib,subprocess
D=Path(__file__).resolve().parent;R=D.parents[3]
def rd(n):return json.loads((D/n).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git','-C',str(R),*a],text=True).strip()
r=rd('review.json');old=rd('source-check.json');fix=rd('review-note-check.json')
checks={
 'review_accepted':r['disposition']=='ACCEPTED — PREPARATION ONLY' and r['findings']==[] and r['blocking_findings']==0,
 'no_julia_review':r['runtime_executed'] is False and r['julia_invoked'] is False,
 'review_bindings':all(sha(p)==v['sha256'] for p,v in r['files'].items()),
 'review_text':sha(D/'review.md')==r['review_md_sha256'],
 'source_checks':old['all_passed'] is True and all(old['checks'].values()),
 'source_report_mapping':old['sha256']['REPORT.md']==sha(D/'REPORT.md.before-review-note'),
 'source_other_bindings':all(sha(D/n)==v for n,v in old['sha256'].items() if n!='REPORT.md'),
 'note_fix':fix['all_passed'] is True and all(sha(D/n)==v for n,v in fix['sha256'].items()),
 'author_check':rd('author-check.json')['all_passed'] is True,
 'frozen_dependencies':all(sha(p)==v['sha256'] for p,v in rd('source-bindings.json')['files'].items()),
 'no_outputs':not any((D/n).exists() for n in ['runs','output','reservation.json','launch-pins.json']),
 'host_entry':len(rd('host-entry.json')['groups'])==274 and rd('host-entry.json')['matches']==[],
 'head':git('rev-parse','HEAD')=='7b814faa9942ff7c9a0a3b1c3f522ae8fc62f651',
 'master':git('rev-parse','master')=='26e2291745999f485a74f643298ca997d65c7205',
 'branch':git('branch','--show-current')=='codex/simplex-core-architecture',
 'no_tracked_changes':not git('diff','HEAD','--name-only'),
 'ledger':(D/'progress.md.after-P011').read_bytes()==(R/'.superpowers/sdd/2026-10-19-direct-bg-blocked-update/progress.md').read_bytes(),
}
files=['driver.jl','REPORT.md','REPORT.md.before-review-note','review.md','review.json','source_check.py','source-check.json','source-bindings.json','author-check.json','review-note-check.json','host-entry.json','progress.md.before-P011','progress.md.after-P011','closure.py','publication.py']
result=dict(all_passed=all(checks.values()),checks=checks,sha256={n:sha(D/n) for n in files},scope='Preparation only; no runtime qualification or admission')
with (D/'closure.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=result['all_passed'],checks=len(checks),bindings=len(files))))
if not result['all_passed']:raise RuntimeError('Closure refusal')
