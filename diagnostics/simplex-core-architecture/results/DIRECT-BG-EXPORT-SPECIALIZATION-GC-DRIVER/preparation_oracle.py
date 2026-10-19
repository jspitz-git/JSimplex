"""Pure prefix/counter reconciliation. Ordering is source-bound, not timestamp capture."""
from preparation_schema import validate_records,require
from oracle import strip_preparation

def preparation_results(rows,windows,raw,phase,complete):
 validate_records(rows,phase,complete)
 schedule=[f'window-{c}-{w}.toml' for c in range(1,4) for w in range(1,21)]
 require(set(windows)==set(schedule[:len(windows)]),'GC window prefix')
 n=len(windows);done=len(rows)
 # GC is reached after warm window 6 in each cell and before window 7.
 for cell in range(1,4):
  boundary=(cell-1)*20+6
  require(f'preparation-{cell}.toml' not in rows or n>=boundary,'GC before warm pair completion')
  require(n<=boundary or f'preparation-{cell}.toml' in rows,'Observed window without preparation')
 if complete:require(n==60 and raw is not None,'Complete output missing')
 if raw is not None:
  strip_preparation(raw)
  calls=raw['preparation_calls'];finished=raw['preparations_completed']
  require(finished==done,'Saved GC/completed count mismatch')
  require(calls==done or (calls==done+1 and n==done*20+6),'Unfinished GC not at boundary')
  if complete:require(calls==finished==3 and raw['complete'] is True,'Complete GC counters')
 return {'records':[rows[f'preparation-{i}.toml'] for i in range(1,done+1)],
         'saved_preparations':done,'saved_windows':n,
         'raw_counters_available':raw is not None,
         'scope':'Full GC API requests only; no finalizer/native-free proof. Inner GC timing excludes helper compilation, record creation and I/O; whole-process elapsed includes them. Timings overlap and are not additive.'}
