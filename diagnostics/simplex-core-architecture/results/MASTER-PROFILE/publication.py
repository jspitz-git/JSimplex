from pathlib import Path
import json,hashlib,subprocess
D=Path(__file__).resolve().parent;R=D.parents[3]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=R)
def main():
 names=json.loads((D/'publication-names.json').read_text());closure=json.loads((D/'closure.json').read_text());selfrel=str((D/'publication.json').relative_to(R));expected=sorted(set(names)-{selfrel})
 actual=git('diff','--cached','--name-only').decode().splitlines();blobs={p:git('rev-parse',':'+p).decode().strip() for p in actual}
 checks={'closure_PASS':closure['all_passed'] is True,'closure_bindings':all(sha(p)==h for p,h in closure['sha256'].items()),'exact_stage':sorted(actual)==expected,'exact_staged_bytes':all(git('show',':'+p)==(R/p).read_bytes() for p in actual),'staged_diff_clean':subprocess.run(['git','diff','--cached','--check'],cwd=R,capture_output=True).returncode==0}
 result=dict(all_passed=all(checks.values()),checks=checks,exact_names=names,sha256={str(R/p):sha(R/p) for p in actual},staged_blobs=blobs,scope='Every named blob checked before commit; publication itself excluded from self-hash and verified after staging externally')
 with (D/'publication.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 if not result['all_passed']:raise ValueError(checks)
 print('publication PASS',len(checks),'staged',len(actual),'complete names',len(names))
if __name__=='__main__':main()
