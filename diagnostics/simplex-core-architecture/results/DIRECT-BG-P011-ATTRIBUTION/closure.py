"""One-shot closure of source-only attribution. Never runs Julia or old checkers."""
from pathlib import Path
import sys,json
E=Path(__file__).resolve().parent;D=E.with_name('DIRECT-BG-P011-HARNESS');sys.path.insert(0,str(D));import control as c
v=c.rd(E/'review.json');s=c.rd(E/'source-check.json')
checks={'review_acceptance':v['accepted'] is True and v['findings']==[], 'review_bindings':c.bindings(v) and c.sha(E/'review.md')==v['review_sha256'], 'source_checks':s['all_passed'] is True and len(s['checks'])==15 and all(s['checks'].values()), 'source_bindings':c.bindings(s), 'refs':c.git('rev-parse','HEAD')=='fb8f47d9a22b8f87a5db468813ec81202a7e8450' and c.git('rev-parse','master')==c.MASTER, 'tracked_unchanged':not c.git('diff','--name-only') and not c.git('diff','--cached','--name-only')}
c.require(all(checks.values()),'Preclosure refusal')
w=c.R/'.superpowers/sdd/2026-10-19-direct-bg-blocked-update/progress.md';c.require(w.read_bytes()==(E/'progress.md.before-P011-attribution').read_bytes(),'Ledger drift')
w.write_bytes(w.read_bytes()+b'\nP011 residual SOURCE-ONLY attribution accepted:15literalchecks30bindings/sevenlaunchmatchedsources/independent8checks15bindings. Candidate _bgb_dimensions ntuple(zero,20) uses installedBaseInt>10noinlinearray/splatfallback, strongestavoidableconstruction for400B3events; exactobject/byteattributionUNPROVEN. Proposalonly: privateimmutableNTuple20zero constant viaVal20 reusedthreefixedsites, distinctmutableBGPanelCounts, noarithmetic/gate/oraclechange. Noimplementation/Julia/IRquery/rerun. Next prepareisolatedamendmentandstructuraltests; anynewdiagnosticneedsseparateadmission. OriginalP011failed/sixN026unreached andallrawfrozen; broaderplanopen/masterunchanged.\n')
(E/'progress.md.after-P011-attribution').write_bytes(w.read_bytes());checks['ledger_preserved']=True
files=sorted(p for p in E.iterdir() if p.is_file());c.save(E/'closure.json',dict(all_passed=True,checks=checks,sha256={str(p):c.sha(p) for p in files},scope='Offline closure, no old scripts or Julia invoked'))
print(json.dumps({'all_passed':True,'checks':len(checks),'bindings':len(files)}))
