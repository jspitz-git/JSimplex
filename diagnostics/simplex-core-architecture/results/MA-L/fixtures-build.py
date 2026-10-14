"""One-shot, exact offline fixture preparation. No Julia or numerical backend."""
from pathlib import Path
from fractions import Fraction as F
from itertools import product
from math import gcd
import json
D=Path(__file__).resolve().parent
PRIMES=((3,5,7,11,13,17,19,23,29),(31,37,41,43,47,53,59,61,67))
def qstr(x):return None if x is None else str(x.numerator)+'/'+str(x.denominator)
def round_binary(x,bits):
 if not x:return x
 sign=-1 if x<0 else 1;x=abs(x);e=x.numerator.bit_length()-x.denominator.bit_length()
 if x<F(2)**e:e-=1
 scale=F(2)**(e-bits+1);v=x/scale;a,r=divmod(v.numerator,v.denominator)
 if 2*r>v.denominator or 2*r==v.denominator and a%2:a+=1
 return sign*a*scale
def extrema(c,lo,hi,p):
 terms=[];neg=False;pos=False
 for j,a in enumerate(c):
  if j==p or not a:continue
  mn,mx=(lo[j],hi[j]) if a>0 else (hi[j],lo[j])
  neg |= mn is None;pos |= mx is None
  terms.append([a*z for z in (lo[j],hi[j]) if z is not None] or [F(0)])
 vals=[sum(v,F(0)) for v in product(*terms)]
 return (None if neg else min(vals),None if pos else max(vals))
def implied(c,lo,hi,p,rhs):
 mn,mx=extrema(c,lo,hi,p);a=c[p]
 return ((None if mx is None else (rhs-mx)/a),(None if mn is None else (rhs-mn)/a)) if a>0 else ((None if mn is None else (rhs-mn)/a),(None if mx is None else (rhs-mx)/a))
def oracle(c,lo,hi,p,rhs):
 mn,mx=implied(c,lo,hi,p,rhs)
 return (lo[p] is None or mn is not None and mn>=lo[p]) and (hi[p] is None or mx is not None and mx<=hi[p])
def route(c,lo,hi,p,scalar,container):
 # Independent source-derived expectation; no timing/profit inference.
 if scalar!='Q' or container!='vector' or len(c)!=8:return dict(position=0,count=0,adds=0,trigger_bits=[],reason='fallback')
 if lo[p] is None and hi[p] is None:return dict(position=0,count=0,adds=0,trigger_bits=[],reason='free')
 a=c[p];mn=F(0) if (hi[p] if a>0 else lo[p]) is not None else None;mx=F(0) if (lo[p] if a>0 else hi[p]) is not None else None
 count=0;active=False;declined=False;at=0;adds=0;bits=[];why='no_qualifying_pair'
 for pos,(j,coef) in enumerate(enumerate(c),1):
  if pos>3 and not active:declined=True
  if j==p:continue
  l,h=(lo[j],hi[j]) if coef>0 else (hi[j],lo[j]);same=mn==mx # value equality only used for fixed reuse, arithmetic identical
  oldmn=mn
  for side,b in ((0,l),(1,h)):
   x=mn if side==0 else mx
   if x is None or b is None:y=None;result=None
   elif b==0:y=F(0);result=x
   else:
    y=coef*b
    if x==0:result=y
    elif side==1 and same and l==h and oldmn is not None:result=mn
    else:
     if not active and not declined and lo[p] is not None and hi[p] is not None and mn is not None and mx is not None and l is not None and h is not None and l!=h and y!=0 and x.denominator!=y.denominator:
      count+=1
      if count==2:
       bits=[abs(x.numerator).bit_length(),abs(y.numerator).bit_length()]
       active=(x>0)==(y>0) and min(bits)>=129
       if active:at=pos;why='selected'
       else:declined=True;why='sign_or_size_declined'
     if active:adds+=1
     result=x+y
   if side==0:mn=result
   else:mx=result
  if mn is None and mx is None:break
 return dict(position=at,count=count,adds=adds,trigger_bits=bits,reason=why)
def base(n=8,p=7,sgn=1,bits=160,family=0,style='general'):
 c=[];lo=[];hi=[]
 for j in range(n):
  d=PRIMES[family][j];v=(1<<(bits-1))+2*j+1
  while gcd(v,d)!=1:v+=1
  c.append(F(v,d));lo.append(F(1,2));hi.append(F(1))
 c[p]=F(sgn*2);lo[p]=F(-(1<<(bits+16)));hi[p]=-lo[p]
 for j in range(n):
  if j==p:continue
  if style in ('unit','cancel'):c[j]=F((-1 if j%2 else 1) if style=='cancel' else 1)
  if style in ('fixed','cancel'):lo[j]=hi[j]=F(1)
  if style=='zeros':lo[j]=hi[j]=F(0)
  if style=='late' and j<3:c[j]=F(1);lo[j]=hi[j]=F(1)
 return c,lo,hi,p,F(3)
items=[]
def add(id,b,group='boundary',scalar='Q',container='vector',cost='',alias='',ambient=256,stored=256,mode='contain',expected_route=None):
 c,lo,hi,p,rhs=([*b[0]],[*b[1]],[*b[2]],b[3],b[4])
 if scalar!='Q':
  bits=53 if scalar=='Float64' else stored
  c=[round_binary(x,bits) for x in c];lo=[None if x is None else round_binary(x,bits) for x in lo];hi=[None if x is None else round_binary(x,bits) for x in hi];rhs=round_binary(rhs,bits)
 if mode in ('inside','equal','outside'):
  mn,mx=implied(c,lo,hi,p,rhs)
  if mn is None or mx is None:raise ValueError('tight unbounded')
  delta=F(1,1<<220)
  lo[p]=mn-delta if mode=='inside' else mn if mode=='equal' else mn+delta
  hi[p]=mx if mode=='equal' else mx+delta
  if scalar!='Q':raise ValueError('nonQ tight must use explicit stored-value fixture')
 r=route(c,lo,hi,p,scalar,container);want=oracle(c,lo,hi,p,rhs)
 if expected_route is not None and bool(r['position'])!=expected_route:raise ValueError((id,r,expected_route))
 if mode in ('inside','equal','outside') and want!=(mode!='outside'):raise ValueError('tight oracle '+id)
 items.append(dict(id=id,group=group,scalar=scalar,container=container,cost=cost,alias=alias,ambient=ambient,stored=stored,mode=mode,pivot=p+1,co=[qstr(x) for x in c],lo=[qstr(x) for x in lo],hi=[qstr(x) for x in hi],rhs=qstr(rhs),expected=want,route=r))
# Frozen 76 cost cases, also checked for correctness.
for bits,p,sgn,family in product((160,256,512),(0,7),(-1,1),(0,1)):
 add(f'target-{bits}-{p+1}-{sgn}-{family}',base(p=p,sgn=sgn,bits=bits,family=family),group='selection',cost='target',expected_route=True)
for n,style in product((2,4,7),('general','unit','cancel','fixed')):
 add(f'short-{n}-{style}',base(n=n,p=n-1,style=style),group='fallback',cost='control',expected_route=False)
for style in ('fixed','unit','zeros','cancel','lower','upper','free','small','late'):
 b=base(style=style if style not in ('lower','upper','free','small') else 'general',bits=16 if style=='small' else 160)
 if style in ('lower','free'):b[2][7]=None
 if style in ('upper','free'):b[1][7]=None
 add('ordinary-'+style,b,group='selection',cost='control',expected_route=False)
for style in ('zero','unit','fixed','cancel'):
 b=base()
 for j in range(2,7):
  if style=='zero':b[1][j]=b[2][j]=F(0)
  elif style=='unit':b[0][j]=F(1)
  elif style=='fixed':b[1][j]=b[2][j]=F(1)
  else:b[0][j]=F((-1)**j);b[1][j]=b[2][j]=F(1)
 add('tail-'+style,b,group='tail',cost='control',expected_route=True)
for scalar,n,style in product(('Float64','BigFloat256','BigFloat512'),(2,4,8),('general','unit','cancel')):
 stored=512 if scalar=='BigFloat512' else 256
 add(f'generic-{scalar}-{n}-{style}',base(n=n,p=n-1,style=style),group='fallback',scalar=scalar,cost='control',stored=stored,ambient=stored,expected_route=False)
# All pivot positions/signs, each with tight triple.
for p,sgn,mode in product(range(8),(-1,1),('inside','equal','outside')):
 add(f'pivot-{p+1}-{sgn}-{mode}',base(p=p,sgn=sgn),mode=mode)
# Exact trigger numerator sizes; activities may be positive or negative.
for bits,sgn,mode in product((128,129,130),(-1,1),('inside','equal','outside')):
 b=base(bits=bits)
 for j in range(7):b[0][j]*=sgn
 add(f'bits-{bits}-{sgn}-{mode}',b,mode=mode,expected_route=bits>=129)
for pos,sgn,mode in product((2,3,4),(-1,1),('inside','equal','outside')):
 b=base(p=7 if pos==2 else 0,sgn=sgn)
 if pos==4:b[1][2]=b[2][2]=F(0)
 add(f'position-{pos}-{sgn}-{mode}',b,mode=mode,expected_route=pos<=3)
for sgn,mode in product((-1,1),('inside','equal','outside')):
 b=base(sgn=sgn);b[1][1]=F(0)
 for j in range(2,7):b[1][j]=b[2][j]=F(0)
 add(f'ordinal1-{sgn}-{mode}',b,mode=mode,expected_route=False)
 b=base(sgn=sgn);b[0][1]=-b[0][1]
 add(f'opposite-{sgn}-{mode}',b,mode=mode,expected_route=False)
for sgn,which in product((-1,1),('lower','upper','free')):
 b=base(sgn=sgn)
 if which in ('lower','free'):b[2][7]=None
 if which in ('upper','free'):b[1][7]=None
 add(f'infinite-pivot-{sgn}-{which}',b,expected_route=False)
for sgn,position,side in product((-1,1),(1,4),('lower','upper')):
 b=base(sgn=sgn);b[1 if side=='lower' else 2][position-1]=None
 add(f'infinite-term-{sgn}-{position}-{side}',b,group='tail',expected_route=position==4)
for sgn,mode in product((-1,1),('inside','equal','outside')):
 b=base(sgn=sgn);b[1][0]=b[2][0]=F(1)
 add(f'prefix-diverge-{sgn}-{mode}',b,group='ownership',mode=mode,expected_route=True)
 b=base(sgn=sgn);b[0][2]=-(b[0][0]+b[0][1])/2;b[1][2]=b[2][2]=F(1)
 add(f'zero-reuse-{sgn}-{mode}',b,group='ownership',mode=mode,expected_route=True)
for alias,mode in product(('repeated','numerator','denominator'),('inside','equal','outside')):
 b=base()
 if alias=='repeated':b[0][1]=b[0][0]
 elif alias=='numerator':
  N=(1<<160)*3*5+1;b[0][0]=F(N,3);b[0][1]=F(N,5)
 else:b[0][1]=F(b[0][0].numerator+3,b[0][0].denominator)
 add(f'alias-{alias}-{mode}',b,group='ownership',alias=alias,mode=mode,expected_route=True)
for container,n in product(('tuple','iterator'),(2,8,9)):
 add(f'container-{container}-{n}',base(n=n,p=n-1),group='fallback',container=container,expected_route=False)
add('typed-length9',base(n=9,p=8),group='fallback',expected_route=False)
for offset,ambient in product((-1,0,1),(64,512)):
 t=F(1,1<<200);b=([F(2),3+t,5-t+offset*t],[F(1)]*3,[F(1)]*3,0,F(10))
 add(f'lowbits-{offset}-{ambient}',b,group='fallback',scalar='BigFloat256',ambient=ambient,stored=256,expected_route=False)
if len(items)>256:raise ValueError('correctness cap')
cost=[x for x in items if x['cost']]
if len(cost)!=76 or sum(x['cost']=='target' for x in cost)!=24:raise ValueError('cost grid')
if len({x['id'] for x in items})!=len(items):raise ValueError('duplicate IDs')
# Encode literal, executable-free fixture data for future Julia tests (no JSON dependency).
def jl(v):
 if v is None:return 'nothing'
 if isinstance(v,bool):return 'true' if v else 'false'
 if isinstance(v,int):return str(v)
 if isinstance(v,str):return json.dumps(v)
 if isinstance(v,list):return '['+','.join(jl(x) for x in v)+']'
 raise TypeError(type(v))
lines=['# Frozen MA-L fixtures; canonical source is fixtures.json. UNEXECUTED.','const MAL_FIXTURES = [']
for x in items:
 fields={k:v for k,v in x.items() if k!='route'}
 fields.update(route_position=x['route']['position'],route_count=x['route']['count'],route_adds=x['route']['adds'])
 lines.append('    ('+', '.join(k+'='+jl(v) for k,v in fields.items())+',),')
lines.append(']')
record=dict(scope='Exact offline preparation only; no Julia behavior or allocation acceptance.',count=len(items),cost_count=len(cost),fixtures=items,exclusions=['Not a Cartesian product: tight triples for finite Q cases only; nonQ stored endpoints have independent oracles.','With pivot at position1 the second addition cannot occur at position2. Position3 covers that pivot placement.','No activation at position4 by contract; ordinal1 cannot trigger.','Length9 is direct-helper fallback correctness only, not public aggregation coverage.'],counts=dict(cost_targets=24,cost_controls=52,tight_triples=sum(x['mode']=='equal' for x in items),selected=sum(bool(x['route']['position']) for x in items)))
with (D/'fixtures.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
with (D/'fixtures.jl').open('x') as f:f.write('\n'.join(lines)+'\n')
print(json.dumps({'count':len(items),'cost_count':len(cost),'counts':record['counts']}))
if __name__!='__main__':raise RuntimeError('Do not import or rerun this one-shot generator')
