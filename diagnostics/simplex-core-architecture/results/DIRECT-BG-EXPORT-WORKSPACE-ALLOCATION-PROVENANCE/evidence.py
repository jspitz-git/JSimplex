"""New saved profile validation, no execution on import."""
from pathlib import Path
import json,tomllib,math
from analysis import matrix,residual
def require(v,msg):
 if not v:raise ValueError(msg)
def expected_names():return {'pins.json','current.json','process.json','resources.jsonl','run.log','raw.toml'}|{f'profile-{i}.toml' for i in range(1,17)}
def output_checks(out,cfg):
 from control import D,rd,loaded_for
 require({p.name for p in out.iterdir()}==expected_names(),'Exact output membership')
 raw=tomllib.loads((out/'raw.toml').read_text());require(raw['complete'] is True and raw['fatal']=='' and raw['records']==16 and raw['phase']=='profile300','Complete raw')
 require(raw['loaded']==loaded_for(cfg) and raw['threads']==raw['blas_threads']==1,'Actual loaded paths/threads')
 rows=[];i=0
 for f in rd(D/'inputs.json')['fixtures']:
  matrices=[(matrix(m),matrix(m,True)) for m in f['matrices']]
  for backend in ('native','markowitz'):
   pair=[]
   for side in ('reference','candidate'):
    i+=1;x=tomllib.loads((out/f'profile-{i}.toml').read_text());pair.append(x)
    require(x['id']==i and x['fixture']==f['name'] and x['backend']==backend and x['side']==side,'Exact profile schedule')
    require(x['warm_lifecycles']==3 and x['sample_rate']==1.0 and x['inputs_unchanged'] is True,'Profile scope')
    for name in ('ordinary','profiled'):
     r=x[name];require(r['compile_seconds']==r['recompile_seconds']==0,'Observed compilation')
     require(type(r['bytes']) is int and type(r['events']) is int and r['bytes']>=0 and r['events']>=0,'Metrics')
     require(len(r['outputs'])==24 and len(r['modes'])==3 and all(m in ('normalized','direct','fallback') for m in r['modes']),'Output/mode shape')
     for k,s in enumerate(f['steps']):
      require(residual(matrices[k][0],r['outputs'][3*k],s['a']) and residual(matrices[k][0],r['outputs'][3*k+1],s['dse']) and residual(matrices[k+1][1],r['outputs'][3*k+2],s['unit']),'Exact residual')
    require(x['ordinary']['outputs']==x['profiled']['outputs'] and x['ordinary']['modes']==x['profiled']['modes'],'Profile comparison')
    require(0<x['profile_count']<=200000 and all(type(z['count']) is int and z['count']>0 and type(z['size']) is int and z['size']>=0 and isinstance(z['type'],str) and isinstance(z['stack'],str) for z in x['allocations']),'Profile schema')
    require(sum(z['count'] for z in x['allocations'])==x['profile_count'] and sum(z['count']*z['size'] for z in x['allocations'])==x['profile_bytes'],'Profile totals')
    rows.append(dict(id=i,fixture=f['name'],backend=backend,side=side,ordinary_events=x['ordinary']['events'],ordinary_bytes=x['ordinary']['bytes'],profile_count=x['profile_count'],profile_bytes=x['profile_bytes']))
   require(pair[0]['ordinary']['outputs']==pair[1]['ordinary']['outputs'] and pair[0]['ordinary']['modes']==pair[1]['ordinary']['modes'],'Reference candidate match')
 return rows,dict(profiles=16,observed_vectors=768,completed_lifecycles=80,constructors=80,refactors=160,updates=640,FTRAN=1280,BTRAN=640)
