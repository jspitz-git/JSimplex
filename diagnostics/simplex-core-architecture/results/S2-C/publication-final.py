from pathlib import Path
import json,hashlib,subprocess
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/S2-C'
def sha(b):return hashlib.sha256(b).hexdigest()
closure=json.loads((D/'closure-final.json').read_text());assert closure['all_passed']
assert all(sha(Path(p).read_bytes())==h for p,h in closure['sha256'].items())
paths=sorted([Path(p) for p in closure['sha256']]+[D/'closure-final.json'])
assert set(p for p in D.iterdir() if p.is_file())==set(p for p in paths if p.parent==D)
assert not subprocess.check_output(['git','diff','--cached','--name-only'],text=True).strip()
names=[str(p.relative_to(R)) for p in paths];selfname=str((D/'publication-final.json').relative_to(R));expected=sorted(names+[selfname])
subprocess.run(['git','add','--',*names],check=True)
raw=subprocess.run(['git','diff','--cached','--check'],text=True,capture_output=True)
verbatim=['original-primal-updates.jl','candidate-primal-updates.jl','candidate-tests.jl','integration-original.jl','adapter.jl.txt','roadmap.md.before-whitespace']
excluded=[str((D/n).relative_to(R)) for n in verbatim]
authored=subprocess.run(['git','diff','--cached','--check','--','.',*[':(exclude)'+p for p in excluded]],text=True,capture_output=True)
allowed=raw.returncode==0 or (raw.returncode==2 and all(any(line.startswith(p+':') for p in excluded) and line.endswith('new blank line at EOF.') for line in raw.stdout.splitlines()))
checks={'closure_pass':closure['all_passed'],'complete_new_directory':True,'all_bound_hashes':True,'authored_diff_clean':authored.returncode==0,'raw_diff_only_preserved_terminal_blank_lines':allowed,'master_unchanged':subprocess.check_output(['git','rev-parse','master'],text=True).strip()=='d02416c108f06fcd41d58e0a1980b70a51fef9ef'}
o={'checks':checks,'all_passed':all(checks.values()),'expected_staged_names':expected,'sha256':{n:sha((R/n).read_bytes()) for n in names},'self_exclusion':'This JSON excludes its own recursive hash; its exact staged bytes are checked after staging.','raw_diff_check':{'returncode':raw.returncode,'stdout':raw.stdout,'stderr':raw.stderr},'authored_diff_check':{'returncode':authored.returncode,'stdout':authored.stdout,'stderr':authored.stderr}}
with (D/'publication-final.json').open('x') as f:json.dump(o,f,indent=2);f.write('\n')
assert o['all_passed'],checks
subprocess.run(['git','add','--',selfname],check=True)
actual=sorted(subprocess.check_output(['git','diff','--cached','--name-only'],text=True).splitlines());assert actual==expected
for n in expected:assert subprocess.check_output(['git','show',':'+n])==(R/n).read_bytes(),n
print(json.dumps({'checks':checks,'exact_staged_names_and_blobs':len(expected),'listed_hashes':len(names)}))
