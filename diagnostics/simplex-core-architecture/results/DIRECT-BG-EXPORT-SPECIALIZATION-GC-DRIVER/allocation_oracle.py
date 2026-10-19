"""Pure exact offline Task2 gates. All raw windows retained; no filesystem side effects."""
from analysis import require, matrix, window_ok, summarize
CELLS=('sparse32','dense32','sparse96')
def allocation_results(rows,fixtures,mode):
 require(mode in ('red','green'),'Mode')
 require(set(rows)=={f'window-{c}-{w}.toml' for c in range(1,4) for w in range(1,21)},'Window membership')
 selected=[f for f in fixtures if f['name'] in CELLS]
 require(tuple(f['name'] for f in selected)==CELLS,'Fixture order')
 result=[]
 for cell,f in enumerate(selected,1):
  matrices=[(matrix(m),matrix(m,True)) for m in f['matrices']];allrows=[]
  for pair in range(1,11):
   a=[]
   for order in (1,2):
    r=rows[f'window-{cell}-{2*(pair-1)+order}.toml']
    window_ok(r,f,1,pair,order,matrices)
    require(r['policy']=='threshold_one','Native policy');a.append(r);allrows.append(r)
   require(a[0]['outputs']==a[1]['outputs'] and a[0]['modes']==a[1]['modes'],'Paired bits/modes')
  s=summarize(allrows)
  require(s['allocation_gate'] is (mode=='green'),'Unexpected allocation predicate')
  result.append(dict(fixture=f['name'],statistics=s))
 return result

def partial_windows(rows,fixtures):
 selected=[f for f in fixtures if f['name'] in CELLS]
 require(tuple(f['name'] for f in selected)==CELLS,'Partial fixture order')
 schedule=[f'window-{c}-{w}.toml' for c in range(1,4) for w in range(1,21)]
 require(set(rows)==set(schedule[:len(rows)]),'Noncontiguous partial windows')
 for cell,f in enumerate(selected,1):
  matrices=None
  for w in range(1,21):
   name=f'window-{cell}-{w}.toml'
   if name not in rows:break
   if matrices is None:matrices=[(matrix(m),matrix(m,True)) for m in f['matrices']]
   r=rows[name];pair=(w+1)//2;order=(w-1)%2+1
   window_ok(r,f,1,pair,order,matrices);require(r['policy']=='threshold_one','Partial policy')
   if order==2:
    a=rows[f'window-{cell}-{w-1}.toml']
    require(a['outputs']==r['outputs'] and a['modes']==r['modes'],'Partial paired bits/modes')
 return True
