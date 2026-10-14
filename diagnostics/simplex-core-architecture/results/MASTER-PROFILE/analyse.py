from pathlib import Path
import tomllib,json,statistics,collections,re,csv,hashlib
D=Path(__file__).resolve().parent

def category(frames):
 js=[f for f in frames if '/src/' in f['file'] and 'JSimplex.jl' in f['file']]
 funcs=' '.join(f['func'].lower() for f in js);files=' '.join(Path(f['file']).name.lower() for f in js)
 if 'presolve' in files:return 'presolve'
 if any(s in funcs for s in ('cleanup','certificate','certification','restore_basis','_retry_original')):return 'cleanup/certification'
 if any(s in funcs for s in ('refactor','factorize')) or any(re.search(r'(^|#)(lu!?)(#|$)',f['func'].lower()) for f in frames):return 'factorization'
 if any(s in funcs for s in ('ftran','btran','forward_solve','transpose_solve')):return 'basis solves'
 if any(s in funcs for s in ('pricing','price_','update_duals')):return 'pricing'
 if any(s in funcs+' '+files for s in ('scaling','transformations','workspace','initialize','initialise')):return 'model/setup'
 return 'other'

def main():
 rows=[]
 for i in (1,2,3):
  out=D/f'run-{i}';audit=json.loads((D/f'audit-{i}.json').read_text())
  if not audit['all_passed']:raise ValueError('not accepted')
  for path in sorted(out.glob('*.toml')):
   if path.name=='raw.toml' or path.name.endswith('-stacks.toml'):continue
   c=tomllib.loads(path.read_text());st=tomllib.loads(path.with_name(path.stem+'-stacks.toml').read_text());counts=collections.Counter();inclusive=collections.Counter();leaf=collections.Counter();stack=[];total=0
   for ip in st['data']:
    if ip!='0':stack.extend(st['frames'][ip]);continue
    if not stack:continue
    total+=1;counts[category(stack)]+=1
    js=[f for f in stack if '/src/' in f['file'] and 'JSimplex.jl' in f['file']]
    inclusive.update(set(f['func']+' | '+Path(f['file']).name for f in js))
    if js:leaf[js[0]['func']+' | '+Path(js[0]['file']).name+':'+str(js[0]['line'])]+=1
    stack=[]
   if stack:raise ValueError('unterminated')
   plain=[w for w in c['windows'] if w['mode']=='plain'];diag=[w for w in c['windows'] if w['mode']=='diagnosed'];med=lambda k:statistics.median(w[k] for w in plain)
   row=dict(stage=i,id=c['id'],scalar=c['scalar'],rows=c['rows'],columns=c['columns'],nnz=c['nnz'],iterations=c['iterations'],refactorizations=c['refactorizations'],seconds=med('seconds'),seconds_range=[min(w['seconds'] for w in plain),max(w['seconds'] for w in plain)],bytes=med('bytes'),events=med('events'),gc_seconds=[w['gc_seconds'] for w in plain],diagnosed_seconds=statistics.median(w['seconds'] for w in diag),profile_seconds_per_call=c['profile']['seconds']/c['profile']['calls'],profile_samples=total,categories=dict(counts),shares={k:v/total for k,v in counts.items()},inclusive= inclusive.most_common(30),nearest_julia_source=leaf.most_common(30),kernel_seconds={k:statistics.median(w['kernel_seconds'][k] for w in diag) for k in diag[0]['kernel_seconds']},kernel_calls={k:[w['kernel_calls'][k] for w in diag] for k in diag[0]['kernel_calls']},event_counts=diag[0]['event_counts'],cold=c['cold'],parse_seconds=c['parse_seconds'],profile_compile_seconds=c['profile']['compile_seconds'])
   rows.append(row)
 bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for i in (1,2,3) for p in (D/f'run-{i}').glob('*.toml')}
 with (D/'summary.json').open('x') as f:json.dump(dict(cases=rows,sha256=bindings),f,indent=2);f.write('\n')
 for r in rows:print(r['scalar'],r['id'],'ms',round(r['seconds']*1000,3),'MB',round(r['bytes']/1e6,2),'samples',r['profile_samples'],'shares',{k:round(v*100,1) for k,v in r['shares'].items()},'top',r['nearest_julia_source'][:5])
if __name__=='__main__':main()
