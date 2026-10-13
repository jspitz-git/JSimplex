from pathlib import Path
H=Path(__file__).resolve().parent;U=H.parent/'S5-U';Y=H.parent/'S5-Y'
s=(U/'audit-final.py').read_text().replace('S5-U','S5-AA').replace('common_final','common').replace('7647','4774').replace("T/'append.jl'","T/'append-reviewed.jl'")
y=(Y/'audit.py').read_text();a=s.index('def data_checks(');b=s.index('def audit(',a)
s=s[:a]+y[y.index('def data_checks('):y.index('def audit(')]+s[b:]
s=s.replace('c=data_checks(raw,report,schema,expected)', '''c=data_checks(raw,schema)
  c.update(test52=all(type(report[k]) is int and report[k]==v for k,v in {'passes':52,'fails':0,'errors':0,'broken':0}.items()),entries_one=report['entry_counts']==[1,1,1,1] and all(type(x) is int for x in report['entry_counts']),source_hashes=all(report[k+'_sha256']==expected[v] for k,v in [('test','candidate'),('prefix','prefix'),('suffix','suffix'),('executed','executed')]),threads=type(report['julia_threads']) is int and report['julia_threads']==1 and type(report['blas_threads']) is int and report['blas_threads']==1)
  cur=read(output/'current.json');c['current_matches']=all(cur[k]==process[k] for k in ('runner','child','command','cwd','pins_sha256','started'))
  c['complete_raw']=set(str(p.relative_to(output)) for p in output.rglob('*') if p.is_file())==GREEN_RAW''')
s=s.replace("type(process.get('elapsed_including_launch')) in (int,float) and 0<=process['elapsed_including_launch']<=120", "terminal_ok(process)")
s=s.replace("suffix.count('JSimplex.initialize_from_basis(')==suffix.count('checks=_basis_initialization_stop_checks()')==suffix.count('@testset')==1", "suffix.count('JSimplex.initialize_workspace(')==suffix.count('JSimplex._crash_workspace(')==suffix.count('checks = crash_fallback_observer_checks()')==suffix.count('@testset')==1")
s=s.replace("and 0<=x['elapsed']<=120", "and type(x['elapsed']) in (int,float) and math.isfinite(x['elapsed']) and 0<=x['elapsed']<=120")
s=s.replace("observations=raw['observations'],at_throw=raw['at_throw'],after_unwind=raw['after_unwind']", "raw=raw")
with (H/'audit.py').open('x') as f:f.write(s)
