"""One offline amendment for three prelaunch Important findings; no Julia."""
from pathlib import Path
import json,hashlib,ast
I=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for n in ('launcher.py','audit.py','prelaunch.md'):
 with (I/(n+'.before-review')).open('xb') as f:f.write((I/n).read_bytes())
l=(I/'launcher.py').read_text();a=(I/'audit.py').read_text()
red={'both_tree_sets_absent':"trees={ROOT/'src',ROOT/'test',target/'src',target/'test'}" not in l,'raw_summary_check_absent':"'raw_logged_summary'" not in a,'GREEN_master_gate_absent':'master-source-comparison.json' not in l}
needle="  cmd=[sys.executable,str(GUARD),'freeze',str(pins),'--tree',str(target/'src'),'--tree',str(target/'test')]"
replacement="""  if label=='master-1':
   green=json.loads((BASE/'green-1/pins.json').read_text())['inventory']
   accepted=json.loads((HERE/'green-1-audit.json').read_text());assert accepted['all_passed']
   relative={str(Path(p).relative_to(ROOT)):v['sha256'] for p,v in green.items() if Path(p).is_relative_to(ROOT/'src') or Path(p).is_relative_to(ROOT/'test')}
   actual={str(p.relative_to(target)) for tree in ('src','test') for p in (target/tree).rglob('*') if p.is_file()}
   current={str(p.relative_to(ROOT)) for tree in ('src','test') for p in (ROOT/tree).rglob('*') if p.is_file()}
   assert actual==current==set(relative)
   assert all(sha(target/p)==sha(ROOT/p)==v for p,v in relative.items())
   comparison=HERE/'master-source-comparison.json'
   with comparison.open('x') as f:json.dump({'all_passed':True,'sha256':relative,'GREEN_pins_sha256':sha(BASE/'green-1/pins.json'),'GREEN_audit_sha256':sha(HERE/'green-1-audit.json')},f,indent=2);f.write('\\n')
   files.add(comparison)
  trees={ROOT/'src',ROOT/'test',target/'src',target/'test'}
  cmd=[sys.executable,str(GUARD),'freeze',str(pins)]
  for tree in sorted(trees):cmd+=['--tree',str(tree)]"""
assert l.count(needle)==1;l=l.replace(needle,replacement);(I/'launcher.py').write_text(l)
needle="resources=[json.loads(s) for s in (OUT/'resources.jsonl').read_text().splitlines()]"
replacement=needle+'''
log=re.sub(r'\\x1b\\[[0-9;]*m','',(OUT/'run.log').read_text())
header=re.search(r'^Test Summary:\\s*\\|\\s*Pass\\s+Total\\s+Time\\s*$',log,re.M)
row=re.search(r'^S5-I focused actual test suffix\\s*\\|\\s*(\\d+)\\s+(\\d+)\\s+(?:\\d+m)?\\d+(?:\\.\\d+)?s\\s*$',log,re.M)
'''
a=a.replace(needle,replacement).replace("checks={'exit0':", "checks={'raw_logged_summary':bool(header and row) and int(row[1])==int(row[2])==report['passes'] and report['fails']==report['errors']==report['broken']==0,'exit0':")
needle="x={'checks':checks,'all_passed':all(checks.values()),"
a=a.replace(needle,"""if label=='master-1':
 comparison=json.loads((HERE/'master-source-comparison.json').read_text())
 checks['master_GREEN_identity']=comparison['all_passed'] and all(sha(TARGET/p)==sha(ROOT/p)==v for p,v in comparison['sha256'].items()) and sha(ROOT/'.superpowers/simplex-core-architecture/S5-I/green-1/pins.json')==comparison['GREEN_pins_sha256'] and sha(HERE/'green-1-audit.json')==comparison['GREEN_audit_sha256']
"""+needle)
(I/'audit.py').write_text(a)
p=I/'prelaunch.md'
with p.open('a') as f:f.write('''
Prelaunch review amendment: the master freeze now compares complete relative src/
test file sets and SHA256 values on BOTH current and master checkouts to the saved
accepted GREEN inventory, recording master-source-comparison.json before freeze.
Both checkout trees are enumerated in master pins. Offline auditor reconciles the
raw Test Summary Pass/Total/Time row with the report and requires no nonpass fields;
master auditor also verifies the saved GREEN inventory/audit bindings. These are
three Important gate fixes; before-review files and original preparation792 remain.
''')
for n in ('launcher.py','audit.py'):ast.parse((I/n).read_text())
green={'both_tree_sets':"trees={ROOT/'src',ROOT/'test',target/'src',target/'test'}" in l,'raw_summary':"'raw_logged_summary'" in a and "header=re.search" in a,'GREEN_master_gate':"assert actual==current==set(relative)" in l and "sha(target/p)==sha(ROOT/p)==v" in l,'master_post_audit':"'master_GREEN_identity'" in a}
x={'red':red,'green':green,'all_passed':all(red.values()) and all(green.values()),'before_sha256':{n:sha(I/(n+'.before-review')) for n in ('launcher.py','audit.py','prelaunch.md')},'after_sha256':{n:sha(I/n) for n in ('launcher.py','audit.py','prelaunch.md')}}
with (I/'review-fix.json').open('x') as f:json.dump(x,f,indent=2);f.write('\n')
print(json.dumps(x));assert x['all_passed']
