"""New offline RED-repeat preparation closure; no numerical admission."""
from pathlib import Path
import sys,json
D=Path(__file__).resolve().parent;R=D.parents[3];sys.path.insert(0,str(D));import control as c
checks={}
def ck(k,v):
 checks[k]=bool(v)
 if not v:raise RuntimeError(k)
v=c.rd(D/'review.json');m=D/'preparation-pins.json';p=c.rd(m)
c.verify_review(v,m,list(p['sha256'])+[str(m)],'BG blocked typed RED repeat preparation')
ck('independent_preparation_only',v['accepted'] is True and v['findings']==[] and v.get('launch_admitted') is False)
ck('exact711_prepared_subjects',len(p['sha256'])==711 and bool(c.preparation()))
cp=c.rd(D/'copied-files.json');ck('all22copies_unchanged',len(cp)==22 and all(c.sha(D/n)==d['sha256']==c.sha(d['source']) for n,d in cp.items()))
t=c.rd(D/'tests.json');ck('new2378synthetic_PASS',t['all_passed'] is True and t['count']==2378 and c.bindings(t))
s=c.rd(D/'source-check.json');ck('source51PASS',s['all_passed'] is True and len(s['checks'])==51 and all(s['checks'].values()) and c.bindings(s))
c.validate_timeout_record();ck('prior_failure_never_promoted',True)
ck('no_numerical_artifacts',not (D/'runs').exists() and not (D/'outers').exists())
ck('current_refs',c.git('rev-parse','HEAD')=='67533adf18a5ba4929e77cafa73472c29d3dd5d0' and c.git('rev-parse','master')==c.MASTER)
ck('tracked_clean',c.git('diff','--name-only')==c.git('diff','--cached','--name-only')=='')
h=c.full_host();h['memory']=c.guard.memory();ck('fresh289groups_sessions_noJulia',len(h['groups'])==289 and c.host_safe(h));c.save(D/'host-closure.json',h)
ledger=R/'.superpowers/sdd/2026-10-19-direct-bg-blocked-update/progress.md';before=(D/'progress.md.before-red1800').read_bytes();ck('before_continuation_exact',ledger.read_bytes()==before)
text='\n\n## Separate RED1800 repeat conditions prepared\n\nAt the human request, DIRECT-BG-BLOCKED-UPDATE-TYPED-RED1800-HARNESS prepares one separate repeat with a 1800-second supervisor limit and a 1792-second guard. This gives bounded 30-minute headroom after the failed 300-second attempt; completion is not guaranteed. No numerical execution is authorized by this preparation record.\n\nThe external phase red1800 maps to the unchanged Julia and raw-data phase red300. New exclusive paths and receipt scopes prevent reuse of old outputs or reservations. All 22 copied files remain byte-identical, and six Python control transformations have exact inverses. The mathematical oracle changes only its finite cost-time maximum; the resource elapsed-time bound is extended accordingly. The same 28 units, 168 assertion sites, 11768 panel checks, six expected N026 failures, 60 payload files and 31 cost records remain required. Only RED is configured.\n\nPreparation passed 51 source checks and 2378 new synthetic checks. Independent review passed 1067 preparation and 1136 source/auditor checks, verified 711 preparation subjects and accepted without findings, with launch_admitted=false. No unnecessary additional production work or memory was found. Added cold lineage hashing and longer bounded resource sampling are documented.\n\nThe prior RED remains all_passed=false and pure_timeout=false. Unsaved unit11 mathematics remain unknown; diagnostic acceptance does not qualify RED. Its 81 bound lineage files remain unchanged. Fresh closure checked all 289 historical process groups AND sessions, with no visible Julia and explicit executable-link visibility limits.\n\nNo Julia query, parser, import, compilation, numerical run, outer, seal, reservation or release was executed. Historical checkers and evidence remain frozen. Master 26e2291, CI, global STATUS and roadmap remain unchanged. Future execution requires fresh host/ref/resource checks and independent exact-run admission before one attempt. Full RED, GREEN and wider Task2/Task3 remain open; no runtime, allocation, speedup or completion claim is made.\n'
after=before+text.encode()
with (D/'progress.md.after-red1800').open('xb') as f:f.write(after)
ledger.write_bytes(after);ck('continuation_exact_append',ledger.read_bytes()==after)
files=sorted(p for p in D.rglob('*') if p.is_file());c.save(D/'closure.json',dict(all_passed=True,launch_admitted=False,checks=checks,sha256={str(p):c.sha(p) for p in files},scope='Offline RED1800 preparation closure only'))
print(json.dumps(dict(all_passed=True,checks=len(checks),bindings=len(files),launch_admitted=False)))
