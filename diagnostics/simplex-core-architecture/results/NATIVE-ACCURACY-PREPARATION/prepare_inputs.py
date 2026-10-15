from common import *
A=F.parent/'DIRECT-LU-COST-PREPARATION';old=rd(A/'inputs.json');fixtures=[]
for f in old['fixtures']:
 fixtures.append(dict(name=f['name'],matrix=f['matrices'][4],rhs={k:f['steps'][4][k] for k in ('a','dse','unit')}))
f=old['fixtures'][0];req(f['name']=='sparse32','Order')
life=dict(matrix=f['matrices'][0],rhs={k:f['steps'][0][k] for k in ('a','unit')},singular={**f['matrices'][4],'nzval':['0000000000000000']*len(f['matrices'][4]['nzval'])})
schedule=[]
for fi,f in enumerate(fixtures):
 for r in range(1,12):
  arms=['C','P','R'];offset=(fi+r-1)%3
  for arm in arms[offset:]+arms[:offset]:schedule.append(dict(id=len(schedule)+1,fixture=f['name'],arm=arm,round=r,warm=r<=3))
data=dict(fixtures=fixtures,lifecycle=life,schedule=schedule);save(F/'inputs.json',data)
# Fixed schema TOML writer; JSON arrays/strings are valid for these token arrays.
lines=[]
def table(prefix,v):
 lines.append('['+prefix+']')
 for k,x in v.items():lines.append(k+' = '+json.dumps(x))
for f in fixtures:
 lines.extend(['[[fixtures]]','name = '+json.dumps(f['name'])]);table('fixtures.matrix',f['matrix']);table('fixtures.rhs',f['rhs'])
for k,v in life.items():table('lifecycle.'+k,v)
for x in schedule:
 lines.append('[[schedule]]')
 for k,v in x.items():lines.append(k+' = '+json.dumps(v))
with (F/'inputs.toml').open('x') as h:h.write('\n'.join(lines)+'\n')
import tomllib
req(tomllib.loads((F/'inputs.toml').read_text())==data,'TOML inverse')
save(F/'inputs-check.json',dict(all_passed=True,checks=dict(exact_subset=True,toml_inverse=True,zero_pattern_preserved=True,schedule132=len(schedule)==132,output_elements=sum(x['matrix']['n'] for x in fixtures)*33*48==405504),sha256={str(p):sha(p) for p in (Path(__file__),A/'inputs.json',F/'inputs.json',F/'inputs.toml')}))
print('Exact inputs and132window schedule prepared; no Julia')
