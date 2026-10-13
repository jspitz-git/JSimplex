"""Exact binary rounding and fixture/output audit, no Julia or subprocess."""
from fractions import Fraction as F
from statistics import median
import math

def require(ok,msg):
 if not ok:raise ValueError(msg)
def fraction(s):return F(s.replace('//','/'))
def rounded(x,bits):
 if not bits or not x:return x
 sign=-1 if x<0 else 1;x=abs(x)
 e=x.numerator.bit_length()-x.denominator.bit_length()
 pow2=lambda k:F(2**k) if k>=0 else F(1,2**(-k))
 if x<pow2(e):e-=1
 step=pow2(e-bits+1);q=x/step;k,r=divmod(q.numerator,q.denominator)
 if 2*r>q.denominator or (2*r==q.denominator and k%2):k+=1
 return sign*k*step

def analyze(raw):
 require(set(raw)=={'cases','errors','all_passed','ambient_restored','MA_source','MA_version','Julia_version'},'raw keys')
 require(raw['errors']==[] and raw['all_passed'] is True and raw['ambient_restored'] is True,'raw failure')
 require(raw['MA_version']=='1.8.1' and raw['MA_source']=='/home/jspitz/.julia/packages/MutableArithmetics/SaQfc/src/MutableArithmetics.jl','MA identity')
 require(raw['Julia_version']=='1.13.0','runtime version')
 expected=[(bits,n,z) for bits in (128,256,512,0) for n,z in ((32,False),(256,False),(256,True))]
 require(type(raw['cases']) is list and len(raw['cases'])==12,'case count')
 summaries=[]
 for c,(bits,n,z) in zip(raw['cases'],expected):
  require(set(c)=={'type','bits','n','mostlyzero','checks','windows','exact_dot','absolute_error_bound','input_a','input_b','scratch_leaf_count','scratch_graph_bytes','setup'},'case keys')
  require(type(c['bits']) is int and type(c['n']) is int and type(c['mostlyzero']) is bool and (c['bits'],c['n'],c['mostlyzero'])==(bits,n,z),'case identity')
  require(c['type']==('BigFloat' if bits else 'Rational{BigInt}'),'type')
  keys={'private_scratch','precision','outputs','input_and_owner_preservation','measured_compile_zero'}
  require(set(c['checks'])==keys and all(v is True for v in c['checks'].values()),'checks')
  a=[rounded(F(0) if z and i%8 else F(((17*i)%61-30)*2**80+(-1 if i%2 else 1),17),bits) for i in range(1,n+1)]
  b=[rounded(F((13*i)%47-23,19),bits) for i in range(1,n+1)]
  require(list(map(fraction,c['input_a']))==a and list(map(fraction,c['input_b']))==b,'input formula/binary rounding')
  exact=sum(x*y for x,y in zip(a,b));mag=sum(abs(x*y) for x,y in zip(a,b));u=F(1,2**bits) if bits else F(0)
  bound=(2*n*u)/(1-2*n*u)*mag
  require(fraction(c['exact_dot'])==exact and fraction(c['absolute_error_bound'])==bound,'exact oracle')
  seq=F(0)
  for x,y in zip(a,b):seq=rounded(seq+rounded(x*y,bits),bits)
  require(abs(seq-exact)<=bound,'independent error bound')
  require(c['scratch_leaf_count']==(2 if bits else 12),'scratch leaves')
  require(type(c['scratch_graph_bytes']) is int and c['scratch_graph_bytes']>0,'scratch graph')
  for k,v in c['setup'].items():require(type(v) in (int,float) and math.isfinite(v) and v>=0,'setup metric')
  require(set(c['setup'])=={'seconds','bytes','allocations','compile_seconds','recompile_seconds'},'setup keys')
  windows=c['windows'];require(type(windows) is list and len(windows)==20,'window count')
  pairs={}
  bools={'same_sequential_result','exact_or_bounded','inputs_preserved','scratch_owners_preserved','precision_preserved'}
  metrics={'seconds','bytes','allocations','gc_seconds','compile_seconds','recompile_seconds'}
  for j,w in enumerate(windows):
   pair=j//2+1;side=('plain','buffered')[j%2] if pair%2 else ('buffered','plain')[j%2]
   require(set(w)==bools|metrics|{'side','pair','phase','repetitions','output'},'window keys')
   require(w['side']==side and type(w['pair']) is int and w['pair']==pair and w['phase']==('warm' if pair<=3 else 'measured') and type(w['repetitions']) is int and w['repetitions']==32,'schedule')
   require(all(w[k] is True for k in bools),'window predicates')
   require(fraction(w['output'])==seq,'independent sequential output')
   for k in metrics:require(type(w[k]) in (int,float) and math.isfinite(w[k]) and w[k]>=0,'metric')
   require(w['seconds']>0 and type(w['bytes']) is int and type(w['allocations']) is int,'counters')
   if pair>3:
    require(w['compile_seconds']==0 and w['recompile_seconds']==0,'measured compilation')
    pairs.setdefault(pair,{})[side]=w
  ratios=[p['buffered']['seconds']/p['plain']['seconds'] for p in pairs.values()]
  s={'bits':bits,'n':n,'mostlyzero':z,'paired_time_ratio_median':median(ratios),'paired_time_ratio_range':[min(ratios),max(ratios)],'setup':c['setup'],'scratch_graph_bytes':c['scratch_graph_bytes']}
  for side in ('plain','buffered'):
   ws=[p[side] for p in pairs.values()]
   s[side]={k+'_per_dot_median':median(w[k]/32 for w in ws) for k in ('seconds','bytes','allocations')}
   s[side]['gc_seconds_total']=sum(w['gc_seconds'] for w in ws)
   s[side]['bytes_per_dot_range']=[min(w['bytes']/32 for w in ws),max(w['bytes']/32 for w in ws)]
  summaries.append(s)
 return summaries

def raw_ok(raw):
 try:analyze(raw);return True
 except (ValueError,KeyError,TypeError,ZeroDivisionError,OverflowError):return False
