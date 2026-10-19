"""One-shot saved-result closure, no numerical or auditor rerun."""
from pathlib import Path
import sys,json
E=Path(__file__).resolve().parent;D=E.with_name('DIRECT-BG-P011-HARNESS');sys.path.insert(0,str(D))
import control as c
run=D/'runs/p011-300';phase='p011-300';checks={}
def check(k,v):checks[k]=bool(v)
v=c.rd(run/'result-review.json');files,_=c.result_review(phase,'P011 diagnostic result review','result-review.json')
check('independent_result_acceptance',v['accepted'] is True and not v['findings'] and c.bindings(v,'evidence_sha256'))
a=c.rd(run/'audit.json');check('saved_complete_audit',a['all_passed'] is True and a['pure_timeout'] is False and c.bindings(a))
check('external_process_closure',c.validate_result_closure(phase,c.rd(run/'outer-closure.json')))
z=c.rd(E/'author-checks.json');check('author_checks',z['all_passed'] is True and all(z['checks'].values()) and c.bindings(z))
c.preparation();check('frozen_preparation',True)
p=c.rd(run/'output/process.json');o=c.rd(D/'outers/p011-300/outer-outcome.json')
check('exit_and_outer',p['returncode']==0 and o['returncode']==0 and o['error']=='')
check('nonzero_diagnostic',a['result']['p011_accepted'] is False and a['result']['red_accepted'] is False and a['result']['causal_attribution']=='unresolved')
check('refs',c.git('rev-parse','HEAD')=='11ebe6bdd401084205ebe628d35539ebb2d5e8ae' and c.git('rev-parse','master')==c.MASTER)
check('no_tracked_edits',not c.git('diff','--name-only') and not c.git('diff','--cached','--name-only'))
h=c.full_host(c.rd(run/'outer-closure.json')['host']['groups']);c.save(E/'host-final.json',h);check('fresh_processes',c.host_safe(h) and len(h['groups'])==277)
w=c.R/'.superpowers/sdd/2026-10-19-direct-bg-blocked-update/progress.md';check('ledger_final',w.read_bytes()==(E/'progress.md.final-P011-result').read_bytes())
paths=sorted(set([p for p in E.iterdir() if p.is_file()]+[p for p in run.rglob('*') if p.is_file()]+[p for p in (D/'outers/p011-300').iterdir() if p.is_file()]+[D/'execution-entry.json']))
z=dict(all_passed=all(checks.values()),checks=checks,sha256={str(p):c.sha(p) for p in paths},scope='Saved diagnostic result and independent review closure only; no reruns')
c.save(E/'closure.json',z);print(json.dumps({'all_passed':z['all_passed'],'checks':checks,'bindings':len(paths)}))
if not z['all_passed']:raise SystemExit(1)
