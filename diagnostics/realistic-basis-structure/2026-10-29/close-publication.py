from pathlib import Path
import json,hashlib,subprocess
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');D=W/'diagnostics/realistic-basis-structure/2026-10-29'
def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb')as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
(D/'REVIEW-FINAL.md').write_text('''# Final report review

Reviewer /root/long_chain_review ACCEPTED finalreportwithno factual/scopecorrections. Independently verified newblockcounts,couplingproportions,jointU/historyexample,intervalcomparisons,graph-overheadandresidualmaximum. Proposedblock-preservingorder+graphlocalSSexplicitlyfuturedesignwithnumeric/coupling/matching/lifecycle/GC/samplinglimits. NoJulia/remeasurement/edits.

REPORT.md SHA2561fa6d3d75bd2783d3e43f1ca18c15cd0261311667ea8fc89bb162179d7f0d812.\n''')
a=json.loads((D/'analysis-1.json').read_text());v=json.loads((D/'witness-verification.json').read_text());pins=json.loads((D/'pins.json').read_text());binding=json.loads((D/'result-bindings.json').read_text())
checks={'analysis51PASS':a['accepted']and len(a['checks'])==51 and all(a['checks'].values()),'savedwitnesses76':v['accepted']and v['verified_witnesses']==76 and not v['omitted_witnesses'],'sourcepins101':len(pins['inventory'])==101 and all(sha(k)==r['sha256']for k,r in pins['inventory'].items()),'resultbindings':all(sha(D/k)==h for k,h in binding.items()),'finalreviewreport':sha(D/'REPORT.md')=='1fa6d3d75bd2783d3e43f1ca18c15cd0261311667ea8fc89bb162179d7f0d812','masterunchanged':subprocess.check_output(['git','-C','/home/jspitz/JSimplex.jl','rev-parse','master'],text=True).strip()=='c0fa748ffa61ccb7c1caaf248c40324f60bc737b','productiondiffabsent':not subprocess.check_output(['git','diff','HEAD','--name-only','--','src','test','Project.toml','.github'],cwd=W)}
if not all(checks.values()):raise RuntimeError(checks)
with(D/'closure.json').open('x')as f:json.dump({'accepted':True,'checks':checks,'witness_scope':'Only text hashes/paths published; all .bin matrices remain local outsidegit'},f,indent=2);f.write('\n')
subprocess.run(['git','add','--',str(D.relative_to(W))],cwd=W,check=True)
r=subprocess.run(['git','diff','--cached','--check'],cwd=W,capture_output=True,text=True)
with(D/'whitespace-check.json').open('x')as f:json.dump({'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr},f,indent=2);f.write('\n')
print('CHECKS',checks,'WHITESPACE',r.returncode,r.stdout[:2000],r.stderr)
