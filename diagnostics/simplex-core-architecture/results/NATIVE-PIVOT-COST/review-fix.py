"""One narrow offline correction of diagnostic RHS wording; no rerun."""
from pathlib import Path
import json,hashlib,tomllib
D=Path(__file__).resolve().parent;Q=D.parent/'NATIVE-PIVOT-COST-PREPARATION';RUN=Q/'runs/cost'
def rd(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def require(x,m):
 if not x:raise RuntimeError(m)
def save(p,z):
 with p.open('x') as f:json.dump(z,f,indent=2);f.write('\n')
initial=rd(D/'reviewer-initial-finding.json')
protected=[RUN/'audit.json',D/'summary.json',Q/'cost-driver.jl',D/'postcheck.json',D/'finalize-final.py',D/'publication.py'];before={str(p):sha(p) for p in protected}
changes=[('REPORT.md','REPORT.md.before-review','sparse96 unit-RHS/BTRAN results','sparse96 DSE-RHS/FTRAN results'),('continuation-text.md','continuation-text.md.before-review','176knownsparse96BTRANfalse','176knownsparse96DSE-FTRANfalse')]
checks={}
for name,saved,old,new in changes:
 p=D/name;s=p.read_text();require(s.count(old)==1,'Exact original phrase '+name)
 with (D/saved).open('xb') as f:f.write(p.read_bytes())
 checks['RED_'+name]=old in s and new not in s
 p.write_text(s.replace(old,new,1))
 checks['GREEN_'+name]=old not in p.read_text() and new in p.read_text()
 checks['inverse_'+name]=p.read_text().replace(new,old,1)==(D/saved).read_text()
a=rd(RUN/'audit.json');res=a['result']['residuals'];ws={i:tomllib.loads((RUN/f'output/window-{i:03d}.toml').read_text())['schedule'] for i in range(1,89)}
failed=[z for z in res if not z['passed']]
checks['all176_DSE_forward']=len(failed)==176 and all(ws[z['window']]['fixture']=='sparse96' and ws[z['window']]['arm']=='C' and z['solve']%3==2 for z in failed)
unit=[z for z in res if ws[z['window']]['fixture']=='sparse96' and ws[z['window']]['arm']=='C' and z['solve']%3==0]
checks['unit_BTRAN176_pass']=len(unit)==176 and all(z['passed'] for z in unit)
s=(Q/'cost-driver.jl').read_text();checks['source_rhs_order']='for k in ("a","dse","unit")' in s and 'if j==3\n                c.transpose+=1;J._backend_transpose_solve!' in s and 'else\n                c.forward+=1;J._backend_forward_solve!' in s
checks['protected_unchanged']=all(sha(Path(n))==v for n,v in before.items())
files=protected+[D/'review-fix.py',D/'reviewer-initial-finding.json']+[D/n for row in changes for n in row[:2]]
save(D/'review-fix.json',dict(all_passed=all(checks.values()),checks=checks,sha256={str(p):sha(p) for p in files},scope='Only two wording substitutions; initial report/continuation bindings map exactly to corresponding before-review copies. Frozen report generator describes before-review text and must not rerun. All raw/audit/summary unchanged.'))
require(all(checks.values()),'Fix failed: preserve');print(dict(checks=len(checks),bindings=len(set(files)),all_passed=True))
