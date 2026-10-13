"""Exclusive publication, preserving exact excerpt whitespace and checking authored files."""
from pathlib import Path
import subprocess,json,hashlib
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture';H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],text=True)
def dump(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
c=json.loads((H/'closure.json').read_text());assert c['all_passed'] is True and all(v is True for v in c['checks'].values()) and all(sha(k)==v for k,v in c['sha256'].items())
assert not git('diff','--cached','--name-only').strip()
paths=[H,D/'STATUS.md',D/'S5-CRASH-FALLBACK-OWNERSHIP.md',D/'S5-CRASH-FALLBACK-OWNERSHIP-REVIEW.md',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md',R/'docs/superpowers/plans/2026-10-13-crash-fallback-observer-oracle.md']
expected={str(p.relative_to(R)) for path in paths for p in (path.rglob('*') if path.is_dir() else [path]) if p.is_file()}
subprocess.run(['git','add','--',*[str(p.relative_to(R)) for p in paths]],check=True)
raw=subprocess.run(['git','diff','--cached','--check'],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
with (H/'diffcheck.txt').open('x') as f:f.write(raw.stdout)
e=json.loads((H/'evidence.json').read_text());excerpts=e['excerpts'];assert all(sha(x['path'])==x['sha256'] and Path(x['path']).read_text() in (R/x['source']).read_text() for x in excerpts)
allowed=[str(Path(x['path']).relative_to(R)) for x in excerpts]
warninglines=[x for x in raw.stdout.splitlines() if ': ' in x]
assert raw.returncode in (0,2) and all(any(x.startswith(p+':') for p in allowed) for x in warninglines)
subprocess.run(['git','diff','--cached','--check','--','.',*[f':(exclude){p}' for p in allowed]],check=True)
names=set(git('diff','--cached','--name-only').splitlines());assert names==expected
blobs={k:hashlib.sha256(subprocess.check_output(['git','show',':'+k])).hexdigest() for k in names};assert all(sha(R/k)==v for k,v in blobs.items())
checks=dict(closure_PASS=True,all_bindings_current=True,exact_names=True,exact_blobs=True,verbatim_excerpts_preserved=True,authored_diff_clean=True,only_excerpt_warnings=True)
dump(H/'publication-check.json',dict(checks=checks,all_passed=True,raw_diffcheck_returncode=raw.returncode,raw_diffcheck_sha256=sha(H/'diffcheck.txt'),warning_lines=warninglines))
for p in (H/'diffcheck.txt',H/'publication-check.json'):subprocess.run(['git','add','--',str(p.relative_to(R))],check=True)
names=set(git('diff','--cached','--name-only').splitlines());blobs={k:hashlib.sha256(subprocess.check_output(['git','show',':'+k])).hexdigest() for k in sorted(names)};assert all(sha(R/k)==v for k,v in blobs.items())
s=H/'staged-files.json';dump(s,dict(sha256=blobs,scope='All staged paths except this self record; self blob independently verified.'));subprocess.run(['git','add','--',str(s.relative_to(R))],check=True)
actual=set(git('diff','--cached','--name-only').splitlines());assert actual==names|{str(s.relative_to(R))} and all(subprocess.check_output(['git','show',':'+k])==(R/k).read_bytes() for k in actual)
print(json.dumps(dict(checks=checks,complete_staged=len(actual),preserved_warning_count=len(warninglines))))
