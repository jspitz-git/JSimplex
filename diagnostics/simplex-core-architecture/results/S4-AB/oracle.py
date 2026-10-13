"""Fail-closed schema and independent paired statistics; no numerical execution."""
import math
from statistics import median

def require(ok,msg):
 if not ok:raise ValueError(msg)
def checks(c,expected):require(set(c)==set(expected) and all(v is True for v in c.values()),'literal predicates')
def analyze(raw):
 require(set(raw)=={'lifecycles','work','cost','errors','ambient_restored','all_passed','source','Julia_version'},'raw keys')
 require(raw['errors']==[] and raw['all_passed'] is True and raw['ambient_restored'] is True,'raw failure')
 require(raw['source']=='/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/src/JSimplex.jl' and raw['Julia_version']=='1.13.0','source/runtime')
 types=('Float32','Float64','BigFloat','Rational{BigInt}')
 require(len(raw['work'])==4 and len(raw['lifecycles'])==24 and len(raw['cost'])==12,'case counts')
 for x,(n,H) in zip(raw['work'],((3,3),(3,64),(8,8),(8,64))):
  require(set(x)=={'n','H','checks','counts'} and type(x['n']) is int and type(x['H']) is int and (x['n'],x['H'])==(n,H),'work identity')
  checks(x['checks'],[s+'_'+k for s in ('reference','candidate') for k in ('counts','failure','clear_and_retain')])
  require(len(x['counts'])==2,'work count schema')
  for c,s in zip(x['counts'],('reference','candidate')):
   expect=[2]*n+[1]*(H-n) if s=='reference' else [1]*n+[0]*(H-n)
   require(set(c)=={'side','row_reads'} and c['side']==s and c['row_reads']==expect and all(type(v) is int for v in c['row_reads']),'independent row read counts')
 expected=[(t,d,k) for t in types for d in ('Dict','OrderedDict') for k in ('sparse','dense','storedzeros')]
 for c,(t,d,k) in zip(raw['lifecycles'],expected):
  require(set(c)=={'type','dictionary','kind','checks','stages'} and (c['type'],c['dictionary'],c['kind'])==(t,d,k),'lifecycle identity')
  ck=[f'stage{i}_{q}' for i in range(1,5) for q in ('same_factor','reference_solves','candidate_solves','private_owners')]+['saved_reference','saved_candidate','inputs_preserved']
  checks(c['checks'],ck);require(len(c['stages'])==4,'stages')
  for s,n in zip(c['stages'],(24,6,6,24)):
   require(set(s)=={'dimension','reference_workspace_graph','candidate_workspace_graph','row_capacity'} and s['dimension']==n and s['row_capacity']==24,'stage dimensions/capacity')
   require(all(type(v) is int and v>=0 for v in s.values()),'graph schema')
 expected=[(t,k) for t in types for k in ('sparse','retained','dense')];summaries=[]
 for c,(t,k) in zip(raw['cost'],expected):
  require(set(c)=={'type','kind','n','H','checks','windows','reference_graph','candidate_graph'},'cost keys')
  require((c['type'],c['kind'],c['n'],c['H'])==(t,k,32,256 if k=='retained' else 32),'cost identity')
  checks(c['checks'],[f'pair{i}_same_factor' for i in range(1,11)]+['reference_solves','candidate_solves','input_preserved','compile_zero'])
  require(type(c['reference_graph']) is int and type(c['candidate_graph']) is int and c['reference_graph']>0 and c['candidate_graph']>0,'cost graphs')
  require(len(c['windows'])==20,'window count');pairs={}
  for j,w in enumerate(c['windows']):
   pair=j//2+1;side=('reference','candidate')[j%2] if pair%2 else ('candidate','reference')[j%2]
   metrics={'seconds','bytes','events','gc_seconds','compile_seconds','recompile_seconds'}
   require(set(w)==metrics|{'pair','side','phase','repetitions'},'window keys')
   require(w['pair']==pair and type(w['pair']) is int and w['side']==side and w['phase']==('warm' if pair<=3 else 'measured') and w['repetitions']==4 and type(w['repetitions']) is int,'schedule')
   require(all(type(w[m]) in (int,float) and math.isfinite(w[m]) and w[m]>=0 for m in metrics) and w['seconds']>0 and type(w['bytes']) is int and type(w['events']) is int,'metrics')
   if pair>3:
    require(w['compile_seconds']==0 and w['recompile_seconds']==0,'compilation')
    pairs.setdefault(pair,{})[side]=w
  ratios=[p['candidate']['seconds']/p['reference']['seconds'] for p in pairs.values()]
  out={'type':t,'kind':k,'paired_ratio_median':median(ratios),'paired_ratio_range':[min(ratios),max(ratios)],'reference_graph':c['reference_graph'],'candidate_graph':c['candidate_graph']}
  for side in ('reference','candidate'):
   ws=[p[side] for p in pairs.values()]
   out[side]={m+'_per_refactor_median':median(w[m]/4 for w in ws) for m in ('seconds','bytes','events')}
   out[side]['gc_seconds_total']=sum(w['gc_seconds'] for w in ws)
  summaries.append(out)
 return summaries

def raw_ok(raw):
 try:analyze(raw);return True
 except (ValueError,KeyError,TypeError,ZeroDivisionError):return False
