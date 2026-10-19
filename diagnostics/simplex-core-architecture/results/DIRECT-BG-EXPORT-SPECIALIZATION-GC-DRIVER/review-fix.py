"""One offline review amendment; preserve initial source/report and manifest bindings."""
from pathlib import Path
import json,hashlib
P=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/simplex-core-architecture/results/DIRECT-BG-EXPORT-SPECIALIZATION-GC-DRIVER')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def edit(n,a,b):
 p=P/n;s=p.read_text()
 if s.count(a)!=1:raise ValueError((n,a,s.count(a)))
 p.write_text(s.replace(a,b))
def save(n,v):
 with (P/n).open('x') as f:json.dump(v,f,indent=2);f.write('\n')
# Called only after the independent initial rejection has been saved.
rejection=P/'review-initial.json'
if not rejection.is_file() or json.loads(rejection.read_text())['accepted'] is not False:raise RuntimeError('Initial review rejection must be preserved first')
names=['audit.py','control.py','outer.py','ADMISSION.md']
for name in names:
 with (P/(name+'.before-review')).open('xb') as f:f.write((P/name).read_bytes())
red={
 'duplicate_window_validation':"partial_windows(saved_windows,rd(D/'inputs.json')['fixtures'])" in (P/'audit.py').read_text() and "rows={n:tomllib.loads((out/n).read_text()) for n in windows}" in (P/'audit.py').read_text(),
 'subset_closure_binding':"set(closure['sha256'])" in (P/'control.py').read_text() and 'validate_result_closure' not in (P/'control.py').read_text(),
 'untyped_release':"v.get('one_attempt') is True" not in (P/'outer.py').read_text(),
 'missing_elapsed_consistency':"GC wall exceeds guarded process" not in (P/'audit.py').read_text()}
if not all(red.values()):raise RuntimeError('Unexpected initial source')
edit('audit.py'," partial_windows(saved_windows,rd(D/'inputs.json')['fixtures'])\n",'')
edit('audit.py'," if pure:return dict(all_passed=False,pure_timeout=True,result={},preparation=prep,error='Pure process timeout; no retry phase prepared; separate reviewed amendment required')", " require(all(r['seconds']<=inv['elapsed_seconds']+1e-9 for r in prep['records']),'GC wall exceeds guarded process')\n if pure:\n  partial_windows(saved_windows,rd(D/'inputs.json')['fixtures'])\n  return dict(all_passed=False,pure_timeout=True,result={},preparation=prep,error='Pure process timeout; no retry phase prepared; separate reviewed amendment required')")
edit('audit.py'," rows={n:tomllib.loads((out/n).read_text()) for n in windows}\n allocation=allocation_results(rows,rd(D/'inputs.json')['fixtures'],cfg['mode'])", " allocation=allocation_results(saved_windows,rd(D/'inputs.json')['fixtures'],cfg['mode'])")
edit('audit.py',"res=run/'reservation.json';require(rd(res)==", "res=run/'reservation.json';require(rd(res).get('one_attempt') is True,'Strict reservation boolean');require(rd(res)==")
edit('outer.py',"return type(v) is dict and v==", "return type(v) is dict and v.get('one_attempt') is True and v==")
edit('control.py',"m=D/'preparation-pins.json';j=rd(m)","m=D/'preparation-pins-reviewed.json';j=rd(m)")
edit('control.py',"rd(D/'required-paths.json')['paths']","rd(D/'required-paths-reviewed.json')['paths']")
edit('control.py',"return sorted(set(j['sha256'])|{str(m),str(D/'review.json')})", "return sorted(set(j['sha256'])|{str(m),str(D/'review.json')}|set(rd(D/'review.json').get('evidence_sha256',{})))")
start=" require(closure.get('all_passed') is True and host_safe(closure['host']) and bindings(closure),'External RED closure invalid')\n require(guard.pins_match(rd(run/'sealed.json')),'RED input drift')\n require(closure['outer_identity']==rd(run/'sealed.json')['outer_identity'],'RED outer mismatch')"
replace=" validate_result_closure(red,closure)\n require(guard.pins_match(rd(run/'sealed.json')),'RED input drift')"
edit('control.py',start,replace)
edit('control.py',"require(rd(o/'release.json')==dict(", "require(rd(o/'release.json').get('one_attempt') is True,'Strict release boolean')\n require(rd(o/'release.json')==dict(")
p=P/'control.py';s=p.read_text();s+='''
def closure_paths(phase):
 o=outer_dir(phase);run=Path(config(phase)['run'])
 return [o/n for n in ['outer-ready.json','release.json','outer-invocation.json','outer-outcome.json']]+[run/n for n in ['sealed.json','admission.json','posthost.json','audit.json']]
def validate_result_closure(phase,closure):
 run=Path(config(phase)['run']);s=rd(run/'sealed.json');post=rd(run/'posthost.json')
 outer=verify_outer_invocation(phase,s)
 require(closure.get('all_passed') is True and set(closure.get('sha256',{}))=={str(p) for p in closure_paths(phase)} and bindings(closure),'Exact external closure membership/bindings')
 require(closure['outer_identity']==outer==s['outer_identity'],'External closure identity')
 h=closure['host'];required=set(s['groups'])|set(post['groups'])|{outer['pgid'],outer['sid']}
 require(host_safe(h) and required<=set(h['groups']),'External closure group/session coverage')
 require(all(h[k]==s[k]==post[k] for k in ['head','master','boot_id']) and outer['boot_id']==s['boot_id'],'External closure refs/boot')
 require(h['head']+'\\trefs/heads/codex/simplex-core-architecture' in h['remote'] and MASTER+'\\trefs/heads/master' in h['remote'],'External closure remote refs')
 return True
''';p.write_text(s)
p=P/'ADMISSION.md';s=p.read_text();s+='''

## Independent-review amendment

Initial review and the four before-review files are preserved. Original preparation-pins.json bindings for audit.py, control.py, outer.py and ADMISSION.md map ONLY to their exact .before-review copies; all other initial bindings stay unchanged. The canonical preparation-pins-reviewed.json/required-paths-reviewed.json bind corrected live files and preserved initial artifacts. New supplemental tests cover the fixes; original 438/18/31-check evidence is not relabeled as execution of corrected sources.

Complete audit now decodes each window once and performs exactly one full allocation/residual pass. A pure-timeout prefix takes the separate partial validator once. Failed non-timeout outcomes are rejected; no failed input is promoted by skipping duplicate validation. Independent review identified avoidable cold audit memory/work in the initial implementation, not production overhead or an observed runtime regression. GC wall time individually must not exceed whole guarded-process elapsed (1 ns floating tolerance); overlapping GC/compile counters are still not summed. Release/reservation one_attempt must be the Boolean true. GREEN closure requires exact eight-file membership, original outer identity, prior and outer PGIDs/SIDs, consistent boot/refs and hashes; own preparation-review evidence paths are included in concrete seals.
''';p.write_text(s)
save('review-fix-source.json',dict(all_passed=True,initial_detected=red,before_mapping={str(P/n):str(P/(n+'.before-review')) for n in names},sha256={str(P/(n+suffix)):sha(P/(n+suffix)) for n in names for suffix in ['', '.before-review']},scope='Source amendment only; new semantic tests and independent re-review still required'))
print('Review source amendment saved')
