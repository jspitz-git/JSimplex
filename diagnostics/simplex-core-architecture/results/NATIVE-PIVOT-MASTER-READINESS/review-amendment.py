"""One separate offline correction; original review and inputs preserved."""
from control import *
for name in ['oracle.py','control.py','audit.py','finalize.py','REPORT.md','continuation-text.md','preparation-pins.json','required-paths.json']:
 p=D/name
 with p.with_name(name+'.before-review').open('xb') as f:f.write(p.read_bytes())
p=D/'oracle.py';s=p.read_text().replace('def timeout_only(process,supervisor,raw,log,elapsed,seconds):','def timeout_only(process,supervisor,raw,log,elapsed,seconds,loaded=None):')
a=s.index(' if raw is not None and (raw.get(');b=s.index(' if any(s in log',a)
s=s[:a]+''' if raw is not None:
  # A present record is evidence only when its entire partial schema is valid.
  def valid_node(t):
   return (type(t) is dict and set(t)=={'name','pass','fail','error','broken','failures','children'}
    and type(t['name']) is str and bool(t['name'])
    and all(integer(t[k]) for k in ['pass','fail','error','broken'])
    and t['fail']==t['error']==t['broken']==0 and t['failures']==[]
    and type(t['children']) is list and all(valid_node(c) for c in t['children']))
  if not (type(raw) is dict and set(raw)=={'complete','fatal','loaded','threads','blas_threads','tests'}
   and raw['complete'] is False and raw['fatal']==''
   and type(raw['threads']) is int and raw['threads']==1
   and type(raw['blas_threads']) is int and raw['blas_threads']==1
   and loaded is not None and raw['loaded']==loaded and valid_node(raw['tests'])
   and raw['tests']['name']=='root' and raw['tests']['pass']==0):return False
''' + s[b:];p.write_text(s)
p=D/'control.py';s=p.read_text();old=" return list(j['sha256'])+[str(m),str(D/'review-final.json')]";require(s.count(old)==1,'Preparation anchor');s=s.replace(old," return sorted({str(path(n)) for n in j['sha256']}|{str(m),str(D/'review-final.json')})");p.write_text(s)
p=D/'audit.py';s=p.read_text();old="pure=timeout_only(p,sup,raw,log,inv['elapsed_seconds'],cfg['seconds'])";require(s.count(old)==1,'Audit anchor');p.write_text(s.replace(old,"pure=timeout_only(p,sup,raw,log,inv['elapsed_seconds'],cfg['seconds'],rd(D/'loaded-paths.json'))"))
p=D/'finalize.py';s=p.read_text().replace("required_selfbinding3=rd(D/'required-binding-check.json')['all_passed'])","required_selfbinding3=rd(D/'required-binding-check.json')['all_passed'],review_amendment=rd(D/'review-amendment-tests.json')['all_passed'])");p.write_text(s)
for name in ['REPORT.md','continuation-text.md']:
 p=D/name
 with p.open('a') as f:f.write('\nIndependent review correction: present malformed timeout records are rejected; only a valid partial test tree with exact loaded paths and integer thread counts can support a pure-timeout classification. Missing final raw remains permitted after all other integrity/resource/process/log gates. Readiness inventory keys retain their historical spelling relative to the diagnostic checkout; runtime seal file paths are normalized to absolute paths independently of the caller working directory. Initial source, manifests, rejected review and reproductions are preserved in separate before-review records. No Julia or production-code change.\n')
print('Separate offline review corrections prepared; original inputs preserved')
