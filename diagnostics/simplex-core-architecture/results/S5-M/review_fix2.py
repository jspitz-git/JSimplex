"""Complete the same fail-closed finding; preserve first correction and review."""
from pathlib import Path
import hashlib,json,ast,tempfile,subprocess,sys
R=Path.cwd();H=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
s=(H/'audit-reviewed.py').read_text();start=s.index('p=json.loads(');end=s.index("with (H/'audit.json').open('x')")
body=s[start:end]
a=s[:start]+'try:\n'+''.join(' '+line+'\n' for line in body.splitlines())+'''except (OSError,ValueError,KeyError,TypeError) as error:
 x={'checks':{'audit_inputs_readable':False},'all_passed':False,'error':repr(error),'time_ns':time.time_ns(),'scope':'Incomplete evidence: qualification failed; preserve all existing guard artifacts and stop.'}
'''+s[end:]
with (H/'audit-final.py').open('x') as f:f.write(a)
t=(H/'launcher-reviewed.py').read_text().replace("PINS=B/'pins-reviewed.json'","PINS=B/'pins-final.json'")
with (H/'launcher-final.py').open('x') as f:f.write(t)
for code in (a,t):ast.parse(code)
header="R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');H=Path(__file__).resolve().parent;O=R/'.superpowers/simplex-core-architecture/S5-M/qualification-1'"
results=[]
with tempfile.TemporaryDirectory(prefix='s5m-audit-inputs-') as base:
 for label in ['missing_resources','missing_pin','missing_process','wrong_tables','missing_child']:
  root=Path(base)/label;h=root/'S5-M';o=root/'output';h.mkdir(parents=True);o.mkdir();(root/'S5-L').mkdir();(root/'S5-L/candidate.jl').write_text('unexecuted mock bytes')
  schema=json.loads((H/'schema.json').read_text());schema['candidate_sha256']=sha(root/'S5-L/candidate.jl');(h/'schema.json').write_text(json.dumps(schema));(h/'host-before.json').write_text(json.dumps({'user_hashes':{}}));(h/'command.json').write_text(json.dumps({'command':[]}))
  inventory={str(root/'absent'):{'sha256':'0'*64,'resolved':str(root/'absent')}} if label=='missing_pin' else {}
  (o/'pins.json').write_text(json.dumps({'inventory':inventory,'trees':[]}))
  if label!='missing_resources':(o/'resources.jsonl').write_text('')
  p={'reason':'launch_error','returncode':None,'pins_unchanged':True,'pins_sha256':sha(o/'pins.json'),'command':[],'cwd':str(root),'runner':{'pgid':999999999,'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()}}
  if label!='missing_process':(o/'process.json').write_text(json.dumps(p))
  if label=='wrong_tables':(o/'report.toml').write_text('checks=[1]\nobservations=42\n')
  code=a.replace(header,f'R=Path({str(root)!r});H=Path({str(h)!r});O=Path({str(o)!r})');script=h/'audit-mock.py';script.write_text(code)
  run=subprocess.run([sys.executable,str(script)],capture_output=True,text=True);x=json.loads((h/'audit.json').read_text()) if (h/'audit.json').exists() else None
  results.append({'case':label,'returncode':run.returncode,'failed_record':x is not None and x['all_passed'] is False,'stderr':run.stderr})
checks={'three_unconditional_inputs_RED':all(z in s for z in ["(O/'process.json').read_text()","(O/'resources.jsonl').read_text()","sha(f)==x['sha256']"]),'five_failure_records_GREEN':all(x['returncode']==1 and x['failed_record'] and not x['stderr'] for x in results),'acceptance_body_unchanged':a[a.index('try:\n')+5:a.index('except (OSError,ValueError,KeyError,TypeError)')]==''.join(' '+line+'\n' for line in body.splitlines()),'launcher_manifest_only':t.replace("PINS=B/'pins-final.json'","PINS=B/'pins-reviewed.json'")==(H/'launcher-reviewed.py').read_text(),'candidate_unchanged':sha(H.parent/'S5-L/candidate.jl')=='b553d449a0db620bfae1970861806a778bbf45d36465026e8b4a540e4b4f4288'}
x={'checks':checks,'all_passed':all(checks.values()),'cases':results,'sha256':{str(H/n):sha(H/n) for n in ['audit-reviewed.py','audit-final.py','launcher-reviewed.py','launcher-final.py','prelaunch-review.md','review_fix2.py']},'scope':'New Python-only synthetic failures, no candidate/parser/Julia execution; earlier correction and review preserved.'}
with (H/'review-fix2.json').open('x') as f:json.dump(x,f,indent=2);f.write('\n')
print(json.dumps(x));assert x['all_passed']
