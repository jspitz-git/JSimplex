"""New independent author-side read-only recomputation; exclusive result."""
from pathlib import Path
import hashlib,json,re,subprocess
R=Path.cwd();H=Path(__file__).resolve().parent;D=H.parent.parent;e=json.loads((H/'evidence.json').read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
c={}
c['full166']=len(e['sha256'])==166 and all(sha(k)==v for k,v in e['sha256'].items())
c['literal21']=len(e['checks'])==21 and e['all_passed'] is True and all(v is True for v in e['checks'].values())
c['blocks24']=len(e['blocks'])==24 and all((R/b['file']).read_text().find(b['text'])>=0 and hashlib.sha256(b['text'].encode()).hexdigest()==b['sha256'] for b in e['blocks'])
c['original_rows48']=len(e['rows'])==48 and all((R/f".superpowers/simplex-core-architecture/S6-A/ci-inventory-1/{x['run']}-failed.log").read_text().splitlines()[x['line']-1]==x['raw'] and re.sub(r'(?:\x1b|\^\[)\[[0-9;]*m','',x['raw'])==x['normalized'] for x in e['rows'])
c['511_separately_failed']=all(sum(x['passed'] for x in e['rows'] if x['run']==run)==511 and all(x['conclusion']=='failure' for x in e['rows'] if x['run']==run) for run in ['38142752357','38149970679'])
c['32_historical_wholefiles']=len(e['comparisons'])==32 and all(x['equal'] and sha(R/x['file'])==x['current_sha256']==x['historical_sha256'] for x in e['comparisons'])
c['excerpts4']=len(e['excerpts'])==4 and all(sha(x['path'])==x['sha256'] and Path(x['path']).read_text() in (R/x['source']).read_text() for x in e['excerpts'])
c['event_forwarder']='_diagnostic_event!(workspace.progress.diagnostics, reason, workspace)' in (R/'src/simplex.jl').read_text()
c['master_source_test_equal']=not subprocess.check_output(['git','diff','master','--','src','test','.github','Project.toml'])
files=[Path(__file__),H/'collect.py',H/'evidence.json',H/'entry.json',H/'host.json',D/'S5-CRASH-FALLBACK-OWNERSHIP.md',R/'docs/superpowers/plans/2026-10-13-crash-fallback-observer-oracle.md']
result=dict(checks=c,all_passed=all(c.values()),sha256={str(p):sha(p) for p in files})
with (H/'independent.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(dict(checks=c,bindings=len(files))));assert result['all_passed']
