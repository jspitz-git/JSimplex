from pathlib import Path
import hashlib,json,subprocess
D=Path(__file__).resolve().parent;R=D.parents[3]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True).strip()
checks={}
def check(k,v):
 checks[k]=bool(v)
 if not v:raise RuntimeError(k)
review=json.loads((D/'independent-review.json').read_text())
check('review_accepted',review['disposition']=='ACCEPTED — PREPARATION ONLY' and not review['findings'] and review['all_source_checks_passed'])
check('review_bindings',all(sha(Path(p))==s for p,s in review['reviewed_bindings'].items()))
check('review_text',sha(D/'independent-review.md')==review['review_markdown_sha256'])
check('no_runtime_acceptance',not review['runtime_executed'] and not review['launch_authorized'])
source=json.loads((D/'source-check.json').read_text())
check('source_checks',source['all_passed'] and all(source['checks'].values()))
check('source_bindings',all(sha(D/p)==s for p,s in source['bindings'].items()))
check('stage_bindings',all(sha(Path(p))==s for p,s in json.loads((D/'stage-supplement.json').read_text())['bindings'].items()))
check('head',git('rev-parse','HEAD')=='f179c815dfdd0db969b485a0685fe4d247225fb0')
check('master',git('rev-parse','master')=='26e2291745999f485a74f643298ca997d65c7205')
check('tracked_unchanged',git('diff','--name-only')=='' and git('diff','--cached','--name-only')=='')
ledger=R/'.superpowers/sdd/2026-10-19-direct-bg-blocked-update/progress.md'
check('ledger_before',ledger.read_bytes()==(D/'progress.md.before-p011-repair').read_bytes())
append=b'\n\nP011 typed measurement repair OFFLINE independently accepted, no findings. Separate panel-tests exact inverse except helper insertion/P011 block; original P001-P094 preserved except P011 expression, eight new P095-P102. Four strict zero byte/event assertions for direct and observable typed-Ref arms; invalid sentinel reset per consumed call/full decision fields/value and selected-owner checks. Source12 + stage2 + independent12 checks PASS, review24 bindings. Source-only preparation, no Julia/parser/import/compile/IR or old rerun. Cold probe5warm4measured+P012=10 entries versus3; two snapshots104leaf arrays+3containers/141owner references each, not allocation measurements. No production work/memory/safeguard change; historical208B object unproven, original RED2/P011 failure and six unreachedN026 preserved. Next separate driver/auditor preparation must bind shared-zero panel/master stage/new test IDs and exact RED comparator; no old admission reuse or automatic launch. Master/CI/globalSTATUSroadmap unchanged; broaderplanopen.\n'
after=ledger.read_bytes()+append
with (D/'progress.md.after-p011-repair').open('xb') as f:f.write(after)
ledger.write_bytes(after)
check('ledger_preserved_and_updated',ledger.read_bytes()==after and after.startswith((D/'progress.md.before-p011-repair').read_bytes()))
files=['REPORT.md','helpers.jl','host-entry.json','independent-review.json','independent-review.md','inputs.json','original-block.txt','panel-tests.jl','prepare.py','progress.md.before-p011-repair','replacement.txt','source-before.json','source-check.json','source-check.py','stage-supplement.json','progress.md.after-p011-repair','closure.py','publication.py']
with (D/'closure.json').open('x') as f:json.dump({'all_passed':True,'checks':checks,'scope':'OFFLINE preparation only; no Julia','bindings':{p:sha(D/p) for p in files}},f,indent=2);f.write('\n')
print(json.dumps({'closure_checks':len(checks),'bindings':len(files),'all_passed':True}))
