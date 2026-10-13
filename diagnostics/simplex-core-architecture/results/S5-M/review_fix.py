"""One offline prelaunch revision. Preserve originals; no Julia/parser/numerics."""
from pathlib import Path
import hashlib,json,ast,tempfile,subprocess,sys
R=Path.cwd();H=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
s=(H/'audit.py').read_text();a=s.replace("c=raw.get('checks',{});v=raw.get('observations',{})", "raw_tables_valid=isinstance(raw.get('checks'),dict) and isinstance(raw.get('observations'),dict)\nc=raw.get('checks',{}) if isinstance(raw.get('checks'),dict) else {}\nv=raw.get('observations',{}) if isinstance(raw.get('observations'),dict) else {}")
a=a.replace("'raw_schema':set(raw)==", "'raw_schema':raw_tables_valid and set(raw)==")
a=a.replace("groups={53479,53481,52772,52774,49081,49084,23249,23257,p['runner']['pgid'],p['child']['pgid']};matches=[]", "checks['child_created']=isinstance(p.get('child'),dict) and type(p['child'].get('pgid')) is int\ngroups={53479,53481,52772,52774,49081,49084,23249,23257,p['runner']['pgid']}\nif checks['child_created']:groups.add(p['child']['pgid'])\nmatches=[]")
assert a!=s
with (H/'audit-reviewed.py').open('x') as f:f.write(a)
t=(H/'launcher.py').read_text().replace("PINS=B/'pins.json'","PINS=B/'pins-reviewed.json'")
with (H/'launcher-reviewed.py').open('x') as f:f.write(t)
for x in (a,t):ast.parse(x)
# Run the complete auditor on three isolated synthetic offline failure records.
# Only the fixed repository/H/output constants are substituted; no old auditor
# or numerical file executes. Test records are not qualification evidence.
header="R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');H=Path(__file__).resolve().parent;O=R/'.superpowers/simplex-core-architecture/S5-M/qualification-1'"
results=[]
with tempfile.TemporaryDirectory(prefix='s5m-audit-failures-') as base:
 for label,raw in [('missing_raw',None),('wrong_tables','checks = [1, 2]\nobservations = 42\n'),('wrong_value_types','[checks]\nwrapper = "true"\n[observations]\nhit_count = "one"\n')]:
  root=Path(base)/label;h=root/'S5-M';o=root/'output';h.mkdir(parents=True);o.mkdir();(root/'S5-L').mkdir()
  (root/'S5-L/candidate.jl').write_text('unexecuted mock bytes')
  schema=json.loads((H/'schema.json').read_text());schema['candidate_sha256']=sha(root/'S5-L/candidate.jl');(h/'schema.json').write_text(json.dumps(schema))
  (h/'command.json').write_text(json.dumps({'command':[]}));(h/'host-before.json').write_text(json.dumps({'user_hashes':{}}))
  pins={'inventory':{},'trees':[]};(o/'pins.json').write_text(json.dumps(pins));(o/'resources.jsonl').write_text('')
  p={'reason':'launch_error','returncode':None,'pins_unchanged':True,'pins_sha256':sha(o/'pins.json'),'command':[],'cwd':str(root),'runner':{'pgid':999999999,'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()}}
  (o/'process.json').write_text(json.dumps(p))
  if raw is not None:(o/'report.toml').write_text(raw)
  code=a.replace(header,f'R=Path({str(root)!r});H=Path({str(h)!r});O=Path({str(o)!r})');assert code.count('R=Path(')==1
  script=h/'audit-mock.py';script.write_text(code);run=subprocess.run([sys.executable,str(script)],capture_output=True,text=True)
  output=json.loads((h/'audit.json').read_text()) if (h/'audit.json').exists() else None
  results.append({'case':label,'returncode':run.returncode,'failed_audit_written':output is not None and output['all_passed'] is False and output['checks']['child_created'] is False and output['checks']['raw_schema'] is False,'stderr':run.stderr})
checks={'original_child_assumption_RED':"p['child']['pgid']" in s,'original_tables_unchecked_RED':"c=raw.get('checks',{});v=raw.get('observations',{})" in s,'three_new_failure_records_GREEN':len(results)==3 and all(x['returncode']==1 and x['failed_audit_written'] and not x['stderr'] for x in results),'candidate_unchanged':sha(H.parent/'S5-L/candidate.jl')=='b553d449a0db620bfae1970861806a778bbf45d36465026e8b4a540e4b4f4288','launcher_only_new_manifest':t.replace("PINS=B/'pins-reviewed.json'","PINS=B/'pins.json'")==(H/'launcher.py').read_text()}
x={'checks':checks,'all_passed':all(checks.values()),'synthetic_failure_cases':results,'sha256':{str(H/n):sha(H/n) for n in ['audit.py','audit-reviewed.py','launcher.py','launcher-reviewed.py','review_fix.py']},'scope':'Python offline synthetic failure records only; no Julia, native or numerical attempt; original744 manifest preserved.'}
with (H/'review-fix.json').open('x') as f:json.dump(x,f,indent=2);f.write('\n')
print(json.dumps(x));assert x['all_passed']
