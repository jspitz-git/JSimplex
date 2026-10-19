"""Pure offline preparation-record validation; not a full run auditor."""
import math
CELLS=('sparse32','dense32','sparse96')
PHASES=('redgc300','greengc300')
KEYS=set('phase fixture cell after_pair before_pair requested_full_gc calls cumulative_calls returned seconds bytes events gc_seconds compile_seconds recompile_seconds gc_pauses full_collections'.split())
def require(v,m):
 if not v:raise ValueError(m)
def validate_record(r,cell,phase):
 require(type(r) is dict and set(r)==KEYS,'record schema')
 require(type(cell) is int and 1<=cell<=3 and phase in PHASES,'expected identity')
 require(r['phase']==phase and r['fixture']==CELLS[cell-1],'identity')
 for key,expected in [('cell',cell),('after_pair',3),('before_pair',4),('calls',1),('cumulative_calls',cell)]:
  require(type(r[key]) is int and r[key]==expected,'schedule '+key)
 require(r['requested_full_gc'] is True and r['returned'] is True,'completed full request')
 for key in ('bytes','events','gc_pauses','full_collections'):
  require(type(r[key]) is int and r[key]>=0,'counter '+key)
 for key in ('seconds','gc_seconds','compile_seconds','recompile_seconds'):
  require(type(r[key]) is float and math.isfinite(r[key]) and r[key]>=0,'time '+key)
 # Compilation and GC may overlap; no sum or timing-subtraction oracle.
 return True
def validate_records(rows,phase,complete):
 require(type(rows) is dict and phase in PHASES and type(complete) is bool,'collection schema')
 require(0<=len(rows)<=3 and (not complete or len(rows)==3),'preparation count')
 require(set(rows)=={f'preparation-{i}.toml' for i in range(1,len(rows)+1)},'exact prefix')
 for cell in range(1,len(rows)+1):validate_record(rows[f'preparation-{cell}.toml'],cell,phase)
 return True
