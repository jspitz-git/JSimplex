from pathlib import Path
import sys,json
E=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/simplex-core-architecture/results/DIRECT-BG-ZERO-COUNTS-RUN');H=E.with_name('DIRECT-BG-ZERO-COUNTS-HARNESS');sys.path.insert(0,str(H));import control as c
run=H/'runs/zero-counts-300';review=c.rd(E/'result-review.json')
c.require(review['accepted'] is True and review['findings']==[] and c.bindings(review),'Result review')
if 'evidence_sha256' in review:c.require(c.bindings(review,'evidence_sha256'),'Review evidence')
c.validate_result_closure('zero-counts-300',c.rd(run/'outer-closure.json'));c.preparation()
h=c.full_host(c.rd(run/'outer-closure.json')['host']['groups']);c.require(c.host_safe(h),'Fresh closure host');c.save(E/'host-final.json',h)
ledger=c.R/'.superpowers/sdd/2026-10-19-direct-bg-blocked-update/progress.md'
c.require(ledger.read_bytes()==(E/'progress.md.before-zero-run').read_bytes(),'Ledger drift')
with ledger.open('a') as f:f.write('''

Immutable zero-count single300s run completed and independently accepted for narrow structural/comparison scope. Exact seal1871/admission1872/launch1876;350/350assertions,60records69payloads/sevenpreparationrecords,Julia+guardexit0/auditPASS. Four samplepairs each: zero/dimensions/concreteeligibility400B3events->0; observablemutableconstructor576B4->176B1 (discardedcandidate0 not allocation-free observable owner); original-shaped inner608B4->208B1, separatelyconsumed400B3->0. Allsamplecompile/recompileGC0. Consumedtime medians0.55–1.10us->0.10–0.20us are quantized/fourpairs, no universal/endtoendspeedup. Preparationload4.2795s223074072B overlaps two module loads, snapshots/testcompile reportedseparately. Guard9.5246s/supervised10.0694s under300;9samplesminRAM22002400KiBswap0/RSS584752KiB; external280groupsANDsessionsabsent/noJulia. Source204call schedule not optimizedruntimecount. Ruling: currentrequest authorized exactly this preparedrun; preserve allinputs/raw, noautomaticretry/promotion ornextnumericalstep. OriginalP011stillunaccepted/reducedwrapper208B1 remains; sixN026not reachedhistorically. No production/master/CI/globalSTATUSroadmapchange; no newrecurring scans/solves/growingmemory. Broaderplanopen. Next bounded work, if requested, must preserve this result and separately address the wrapper/originaltest qualification boundary.
''')
with (E/'progress.md.after-zero-run').open('xb') as f:f.write(ledger.read_bytes())
with (E/'finish.py').open('x') as f:f.write(Path(__file__).read_text())
checks={
 'admitted_run':c.rd(run/'admission.json')['accepted'] is True,
 'audit_pass':c.rd(run/'audit.json')['all_passed'] is True,
 'outer_closure':c.rd(run/'outer-closure.json')['all_passed'] is True,
 'result_review_accepted':review['accepted'] is True and review['findings']==[],
 'analysis_bindings':c.rd(E/'analysis.json')['all_passed'] is True and c.bindings(c.rd(E/'analysis.json')),
 '350_assertions':c.rd(E/'analysis.json')['structural_assertions']==350,
 '69_payload_60records':c.rd(E/'analysis.json')['payload_files']==69 and c.rd(E/'analysis.json')['records']==60,
 '300_bound':c.rd(E/'analysis.json')['supervised_elapsed_seconds']<=300,
 '280groups_absent':len(h['groups'])==280 and h['matches']==[],
 'master_unchanged':c.git('rev-parse','master')==c.MASTER,
 'tracked_index_clean':not c.git('diff','--name-only') and not c.git('diff','--cached','--name-only'),
 'ledger_preserved':ledger.read_bytes()==(E/'progress.md.after-zero-run').read_bytes(),
}
paths=sorted(p for folder in (E,run,H/'outers/zero-counts-300') for p in folder.rglob('*') if p.is_file())
c.save(E/'closure.json',dict(all_passed=all(checks.values()),checks=checks,sha256={str(p):c.sha(p) for p in paths}))
c.require(all(checks.values()),'Closure failed')
print(json.dumps(dict(all_passed=True,checks=len(checks),bindings=len(paths))))
