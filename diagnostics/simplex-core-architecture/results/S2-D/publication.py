from pathlib import Path
import json,hashlib,subprocess
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/S2-D'
def sha(b):return hashlib.sha256(b).hexdigest()
def git(*a):return subprocess.check_output(['git',*a])
c=json.loads((D/'closure.json').read_text())
if not c['all_passed'] or not all(sha(Path(p).read_bytes())==h for p,h in c['sha256'].items()):raise SystemExit('closure/hash refusal')
paths=sorted([Path(p) for p in c['sha256']]+[D/'closure.json'])
if {p for p in D.rglob('*') if p.is_file()}!={p for p in paths if D in p.parents}:raise SystemExit('directory completeness refusal')
if git('diff','--cached','--name-only').strip():raise SystemExit('nonempty index')
names=[str(p.relative_to(R)) for p in paths];selfname=str((D/'publication.json').relative_to(R));expected=sorted(names+[selfname])
# Force only explicit reviewed D overlay environment copies, not actual user env.
subprocess.run(['git','add','-f','--',*names],check=True)
raw=subprocess.run(['git','diff','--cached','--check'],capture_output=True,text=True)
map_=json.loads((D/'overlay-map.json').read_text())
verbatim=[D/'overlay'/p for p in map_]+[D/'reference-audit.jl']
verified=all(sha(p.read_bytes())==map_[str(p.relative_to(D/'overlay'))]['sha256'] for p in verbatim[:-1])
original=(D.parent/'S2-C/original-primal-updates.jl').read_text();inverse=(D/'reference-audit.jl').read_text().replace('s2d_reference_price_audit','_primal_price_prediction_reliable').replace('JSimplex.','')
verified=verified and original.endswith(inverse)
authored=subprocess.run(['git','diff','--cached','--check','--','.',*[':(exclude)'+str(p.relative_to(R)) for p in verbatim]],capture_output=True,text=True)
checks={'closure_pass':c['all_passed'],'complete_directory':True,'all_hashes':True,'authored_clean':authored.returncode==0,'raw_whitespace_only_exact_source':raw.returncode in (0,2) and authored.returncode==0 and verified,'master_unchanged':git('rev-parse','master').decode().strip()=='d02416c108f06fcd41d58e0a1980b70a51fef9ef'}
o={'checks':checks,'all_passed':all(checks.values()),'expected_staged_names':expected,'sha256':{n:sha((R/n).read_bytes()) for n in names},'self_exclusion':'Own recursive hash excluded; actual staged bytes checked below.','raw_diff_check':{'returncode':raw.returncode,'stdout':raw.stdout,'stderr':raw.stderr},'authored_diff_check':{'returncode':authored.returncode,'stdout':authored.stdout,'stderr':authored.stderr}}
with (D/'publication.json').open('x') as f:json.dump(o,f,indent=2);f.write('\n')
if not o['all_passed']:raise SystemExit('publication rejected before commit/push')
subprocess.run(['git','add','--',selfname],check=True)
if sorted(git('diff','--cached','--name-only').decode().splitlines())!=expected:raise SystemExit('staged names mismatch')
for n in expected:
 if git('show',':'+n)!=(R/n).read_bytes():raise SystemExit('staged bytes mismatch '+n)
print(json.dumps({'checks':checks,'exact_staged_names_blobs':len(expected),'listed_hashes':len(names)}))
