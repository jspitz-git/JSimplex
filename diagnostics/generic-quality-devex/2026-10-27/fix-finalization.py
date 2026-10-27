from pathlib import Path
import shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-quality-devex/2026-10-27')
for n in ['finalize.py','closure.py','diagnostic-publish.py']:shutil.copyfile(D/n,D/(n+'.before-review-fix'))
(D/'finalization_checks.py').write_text('''from pathlib import Path

def verify_protected_files(files, continuations, allowed, current_bindings, sha, need):
    need(set(continuations)==set(allowed),"exact continuation mapping keys")
    for path, old_hash in files.items():
        if path in continuations:
            entry=continuations[path]
            need(entry["sha256"]==old_hash and sha(entry["before"])==old_hash,
                 "exact protected continuation beforeimage "+path)
            need(path in current_bindings and sha(path)==current_bindings[path],
                 "reviewed current continuation "+path)
            need(Path(path).read_bytes().endswith(Path(entry["before"]).read_bytes()),
                 "verbatim protected continuation "+path)
        else:
            need(sha(path)==old_hash,"protected file "+path)
''')
p=D/'finalize.py';s=p.read_text();s=s.replace("co=c.read('production-commit.json');", """prep=c.read('preparation-review.json')
c.need(prep['accepted'] is True and prep['findings']==[],'accepted finalization preparation')
for p,h in prep['bindings'].items():c.need(c.sha(p)==h,'preparation binding '+p)
co=c.read('production-commit.json');""",1);s=s.replace("shutil.copyfile(__file__,D/'finalize.py')", "if Path(__file__).resolve()!=(D/'finalize.py').resolve():shutil.copyfile(__file__,D/'finalize.py')");p.write_text(s)
p=D/'closure.py';s=p.read_text().replace("co=c.read('production-commit.json');", "from finalization_checks import verify_protected_files\nco=c.read('production-commit.json');",1)
old="for p,h in protected['files'].items():c.need(digest(p)==h,'protected '+p)";assert s.count(old)==1
new="""allowed={str(R/'diagnostics/simplex-core-architecture/STATUS.md'),str(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md')}
verify_protected_files(protected['files'],hist['continuation_before'],allowed,c.read('final-review.json')['bindings'],digest,c.need)""";s=s.replace(old,new);p.write_text(s)
p=D/'diagnostic-publish.py';s=p.read_text().replace("os.environ['GIT_OPTIONAL_LOCKS']='0'", "from finalization_checks import verify_protected_files\nos.environ['GIT_OPTIONAL_LOCKS']='0'",1)
needle="co=c.read('production-commit.json');";s=s.replace(needle,"""hist=c.read('historical-path-map.json')
allowed={str(R/'diagnostics/simplex-core-architecture/STATUS.md'),str(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md')}
def protect_files():
 verify_protected_files(c.read('protected-before.json')['files'],hist['continuation_before'],allowed,c.read('closure.json')['bindings'],c.sha,c.need)
def protect_indexes(include_diagnostic):
 diagnostic=c.git(['rev-parse','--path-format=absolute','--git-path','index'],R)
 for p,h in c.read('MASTER-run/protected-before.json')['indexes'].items():
  if include_diagnostic or p!=diagnostic:c.need(c.sha(p)==h,'protected index '+p)
co=c.read('production-commit.json');""",1)
s=s.replace("# Fresh prepublication observation", "protect_files();protect_indexes(True)\n# Fresh prepublication observation",1)
s=s.replace("subprocess.run(['/usr/bin/git','-C',str(R),'push'", "protect_files();protect_indexes(False)\nsubprocess.run(['/usr/bin/git','-C',str(R),'push'",1)
old="""for p,h in c.read('protected-before.json')['files'].items():c.need(c.sha(p)==h,'protected userfile '+p)
for p,h in c.read('MASTER-run/protected-before.json')['indexes'].items():
 if p!=g(['rev-parse','--path-format=absolute','--git-path','index']):c.need(c.sha(p)==h,'unrelated index '+p)""";assert s.count(old)==1;s=s.replace(old,"protect_files();protect_indexes(False)");p.write_text(s)
for n in ['finalize.py','closure.py','diagnostic-publish.py','finalization_checks.py']:compile((D/n).read_text(),str(D/n),'exec')
shutil.copyfile(__file__,D/'fix-finalization.py');print('Offline fixes prepared; original unexecuted scripts preserved; no runtime/master input change')
