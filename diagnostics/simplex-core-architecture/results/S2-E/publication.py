"""Prepare complete publication and validate all actual staged names/blobs; fail closed."""
from pathlib import Path
import json,hashlib,subprocess
R=Path.cwd();E=R/'diagnostics/simplex-core-architecture/results/S2-E';D=E.parent/'S2-D'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],text=True).strip()
closure=json.loads((E/'closure.json').read_text());newD={'launch-pins.json','allowance.json','numerical-review.md','attempt-reserved.json','invocation.json','launcher.log','audit.json'}
extra={R/'diagnostics/simplex-core-architecture'/n for n in ['STATUS.md','S2-PRICE-AUDIT-VALUES-QUALIFICATION.md','S2-PRICE-AUDIT-VALUES-QUALIFICATION-REVIEW.md']}|{R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'}
paths={p for p in E.rglob('*') if p.is_file()}|{D/n for n in newD}|extra
raw={p for p in (E/'qualification-1').rglob('*') if p.is_file()}
whitespace=[]
for p in sorted(paths-raw):
 run=subprocess.run(['git','diff','--no-index','--check','/dev/null',str(p)],capture_output=True,text=True)
 if run.returncode or run.stdout or run.stderr:whitespace.append({'path':str(p),'returncode':run.returncode,'stdout':run.stdout,'stderr':run.stderr})
trackedE=set(git('ls-files','--',str(E.relative_to(R))).splitlines());trackedD=set(git('ls-files','--',str(D.relative_to(R))).splitlines());actualnewD={str(p.relative_to(R)) for p in D.rglob('*') if p.is_file()}-trackedD
checks={'closure_pass':closure['all_passed'] is True and all(closure['checks'].values()),'closure_all_bindings':all(sha(p)==h for p,h in closure['sha256'].items()),'complete_new_E_and_exact_new_D':not trackedE and actualnewD=={str((D/n).relative_to(R)) for n in newD},'authored_whitespace_clean':not whitespace,'master_unchanged':git('rev-parse','master')=='d02416c108f06fcd41d58e0a1980b70a51fef9ef','index_empty':not git('diff','--cached','--name-only')}
selfpath=E/'publication.json';expected=sorted(str(p.relative_to(R)) for p in paths|{selfpath})
o={'checks':checks,'all_passed':all(checks.values()),'expected_staged_names':expected,'sha256':{str(p):sha(p) for p in sorted(paths)},'self_exclusion':'Own recursive hash excluded; exact actual staged bytes including this file are verified before commit.','authored_whitespace':whitespace,'raw_preserved_paths':sorted(str(p) for p in raw)}
with selfpath.open('x') as f:json.dump(o,f,indent=2);f.write('\n')
print(json.dumps({'checks':checks,'expected_names':len(expected),'listed_hashes':len(paths)}))
if not o['all_passed']:raise SystemExit(1)
subprocess.run(['git','add','-f','--',*expected],check=True)
actual=git('diff','--cached','--name-only').splitlines()
if set(actual)!=set(expected):raise SystemExit('staged name mismatch')
for p in expected:
 if subprocess.check_output(['git','show',':'+p])!=(R/p).read_bytes():raise SystemExit('staged blob mismatch: '+p)
print('PASS exact',len(expected),'actual staged names and blobs; ready for failfast commit/push')
