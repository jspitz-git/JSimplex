from pathlib import Path
from fractions import Fraction as Q
import hashlib,json,re,struct,sys,tomllib
root=Path(__file__).resolve().parents[1];data=root/'results/S6-X'
source=data/'existing-failure-map.json';record=data/'historical-printed-points.json';old=json.loads(source.read_text());saved=json.loads(record.read_text());current=tomllib.loads((data/'census-1-report.toml').read_text())
A=[[8,-2,0,1,-3,2],[2,6,1,2,-2,-2],[1,-2,3,0,-1,3],[3,-1,0,5,-2,-2],[0,0,-1,0,6,-3],[0,0,-1,-2,-1,8]]
def f32(text):return struct.unpack('!f',struct.pack('!f',float(text.replace('f','e'))))[0]
checks=[];work=[]
for run in old['records']:
 for e in run['entries']:
  if e['line']!=211:continue
  text='\n'.join(e['details']);matches=re.findall(r'JSimplex\.Basis\(\[([^]]+)\], JSimplex\.VariableState\[([^]]+)\]\), Float32\[([^]]+)\]',text);assert len(matches)==2
  stored=next(s for s in saved['records'] if s['run']==run['run'] and s['log_line']==e['log_line'])
  for i,(basis,states,values) in enumerate(matches):
   literals=[s.strip() for s in values.split(',')];v=[f32(x) for x in literals]
   checks.append(stored['workspaces'][i]=={'basis':[int(x.strip()) for x in basis.split(',')],'states':states.split(', '),'printed_primal':literals,'primal':v,'bits':[struct.pack('!f',x).hex() for x in v]})
  x=list(map(Q,stored['workspaces'][0]['primal'][:6]));res=[sum(Q(a)*b for a,b in zip(row,x))-row[0]-row[1] for row in A];checks.append(list(map(str,res))==stored['phase_original_row_residual']);checks.append(res[2]==Q(256694483,2**51) and res[2]>Q(f32('1f-7')))
  checks.append(stored['events_printed']==re.findall(r'\[:refactor_initial[^]]*\]',text))
  # The workspace's final primitive fields follow its scratch closing parenthesis.
  phase_tail=text.split('), JSimplex.PhaseOneMap(',1)[0]
  original_tail=text.split('), JSimplex.NumericalPolicy{Float32}(',1)[0]
  tails=[]
  for fragment in (phase_tail,original_tail):
   match=re.search(r'\), (\d+), (\d+), false, 0, false, false, 20, 0, 9223372036854775807, 0, 0\)$',fragment)
   assert match;tails.append([int(x) for x in match.groups()])
  work.append({'run':run['run'],'log_line':e['log_line'],'phase_work':tails[0],'original_work':tails[1]});checks.append(tails==[[1,2],[1,3]])
checks.append(len(work)==8 and len(saved['records'])==8)
checks.append(all(s['workspaces'][0]['bits']==saved['records'][0]['workspaces'][0]['bits'] for s in saved['records']))
local=[c for c in current['records'] if c['scalar']=='Float32'];checks.append(all(c['after_original']['primal']==local[0]['after_original']['primal'] for c in local))
x=list(map(Q,local[0]['after_original']['primal'][:6]));res=[sum(Q(a)*b for a,b in zip(row,x))-row[0]-row[1] for row in A];checks.append(res[2]==Q(192128033,2**51) and res[2]<Q(f32('1f-7')))
report={'all_passed':all(checks),'check_count':len(checks),'work':work,'inputs':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (source,record,data/'census-1-report.toml')},'scope':'Exact parsed printed Float32 phase states only; no hidden export state/runtime certificate or scalar assignment for accepted=false group.'}
with Path(sys.argv[1]).open('x') as f:json.dump(report,f,indent=2);f.write('\n')
print({'all_passed':report['all_passed'],'check_count':len(checks)});assert report['all_passed']
