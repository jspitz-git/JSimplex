"""New exact analysis of preserved partial output only. No Julia or old audit run."""
from pathlib import Path
from fractions import Fraction as Q
import struct,json,tomllib,statistics,hashlib
D=Path(__file__).resolve().parent;A=D.parent/'DIRECT-LU-COST-PREPARATION';OUT=A/'cost1-run'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def num(t):return struct.unpack('>d',bytes.fromhex(t))[0]
def ints(tokens):
 a=[num(t).as_integer_ratio() for t in tokens];e=max((q.bit_length()-1 for _,q in a),default=0)
 return [p*2**(e-(q.bit_length()-1)) for p,q in a],e

def mat(m,trans=False):
 v,e=ints(m['nzval']);rows=[[] for _ in range(m['n'])]
 for j in range(m['n']):
  for k in range(m['colptr'][j]-1,m['colptr'][j+1]-1):
   i=m['rowval'][k]-1;row,col=(j,i) if trans else (i,j);rows[row].append((col,v[k]))
 return rows,e,max(sum(abs(v) for _,v in row) for row in rows)

def exact(M,xt,bt):
 rows,em,nm=M;x,ex=ints(xt);b,eb=ints(bt);e=max(em+ex,eb)
 residual=[sum(v*x[j] for j,v in row)*2**(e-em-ex)-b[i]*2**(e-eb) for i,row in enumerate(rows)]
 bound=Q(128*len(rows),2**52)*max(Q(1),Q(nm*max(map(abs,x)),2**(em+ex)),Q(max(map(abs,b)),2**eb))
 maximum=max(map(abs,residual));ratio=Q(maximum,2**e)/bound
 return dict(pass_=ratio<=1,ratio=float(ratio),exact_ratio=str(ratio),residual_inf=str(Q(maximum,2**e)),bound=str(bound),worst_row=1+max(range(len(rows)),key=lambda i:abs(residual[i])),signed_worst=str(Q(residual[max(range(len(rows)),key=lambda i:abs(residual[i]))],2**e)))

fixtures=json.loads((A/'inputs.json').read_text())['fixtures'];records=[];failed=[];cells=[];paths=[A/'inputs.json',D/'partial-analysis.py']
for c in range(1,25):
 start=OUT/f'started-{c}.toml'
 if not start.exists():continue
 identity=tomllib.loads(start.read_text());paths.append(start);f=next(f for f in fixtures if f['name']==identity['fixture']);Ms=[(mat(m),mat(m,True)) for m in f['matrices']];windows=[]
 for w in range(1,21):
  p=OUT/f'window-{c}-{w}.toml'
  if not p.exists():continue
  paths.append(p);r=tomllib.loads(p.read_text());details=[]
  for k,s in enumerate(f['steps']):
   for offset,(label,ma,rhs) in enumerate([('entering',Ms[k][0],s['a']),('dse',Ms[k][0],s['dse']),('btran',Ms[k+1][1],s['unit'])]):
    result=exact(ma,r['outputs'][3*k+offset],rhs)
    details.append(result)
    if not result['pass_']:failed.append(dict(cell=c,window=w,step=k+1,operation=label,**result))
  expected_side='reference' if ((r['pair']%2==1)==(r['order']==1)) else 'candidate'
  checks=dict(exact_residuals=all(x['pass_'] for x in details),input_report=r['inputs_unchanged'] is True,mode_report=r['modes']==(['ordinary']*3 if r['side']=='reference' else ['normalized']*3),schedule=r['pair']==(w+1)//2 and r['order']==1+(w-1)%2 and r['side']==expected_side and r['measured']==(r['pair']>3),compile=(not r['measured']) or r['compile_seconds']==r['recompile_seconds']==0)
  records.append(dict(cell=c,window=w,side=r['side'],checks=checks,raw_correct=r['correct'],max_residual_ratio=max(x['ratio'] for x in details),exact_pass=sum(x['pass_'] for x in details)))
  windows.append(r)
 cell=dict(cell=c,**identity,windows=len(windows),complete=len(windows)==20,descriptive_only=True)
 if len(windows)==20:
  pairs=[{r['side']:r for r in windows if r['pair']==p} for p in range(4,11)]
  def stat(v):
   med=statistics.median(v);return dict(values=v,median=med,mad=statistics.median(abs(x-med) for x in v),minimum=min(v),maximum=max(v))
  cell['time_ratio']=stat([p['candidate']['seconds']/p['reference']['seconds'] for p in pairs])
  for metric in ('bytes','events','retained_bytes'):
   cell[metric]=dict(reference_median=statistics.median(p['reference'][metric] for p in pairs),candidate_median=statistics.median(p['candidate'][metric] for p in pairs),paired_ratios=[p['candidate'][metric]/p['reference'][metric] for p in pairs])
  cell['faster_pairs']=sum(p['candidate']['seconds']<p['reference']['seconds'] for p in pairs)
  cell['gc_nonzero_windows']=sum(r['measured'] and r['gc_seconds']>0 for r in windows)
 cells.append(cell)
result=dict(scope='Partial preserved-data diagnosis, NOT canonical pass or two-process performance acceptance',windows=records,cells=cells,failed_residuals=failed,total_outputs=len(records)*24,exact_pass=sum(r['exact_pass'] for r in records),raw_exact_agree=all(r['raw_correct']==all(r['checks'].values()) for r in records),sha256={str(p):sha(p) for p in paths})
with (D/'partial-analysis.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps(dict(windows=len(records),outputs=result['total_outputs'],exact_pass=result['exact_pass'],failed=failed,cells=cells),indent=2))
