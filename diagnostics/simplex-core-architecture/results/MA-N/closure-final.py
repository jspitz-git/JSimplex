"""One-shot supplemental closure after exact frozen-source whitespace review."""
from pathlib import Path
import hashlib,json,subprocess,time
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-N'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
def require(ok,msg):
 if not ok:raise ValueError(msg)
old=read(D/'closure.json');pub=read(D/'publication.json');supp=read(D/'publication-whitespace-supplement.json');rev=read(D/'publication-amendment-review.json');host=read(D/'host.json');names=read(D/'publication-names-final.json')
gate=read(D/'publication-gate-review.json')
checks={
 'final_gate_independently_accepted':gate['accepted'] is True and not gate['findings'] and all(gate['checks'].values()) and all(sha(p)==h for p,h in gate['sha256'].items()),
 'original_closure_PASS_unchanged_bindings':old['all_passed'] is True and all(old['checks'].values()) and all(sha(p)==h for p,h in old['sha256'].items()),
 'initial_publication_FALSE_preserved':pub['all_passed'] is False and pub['checks']==dict(closure_pass=True,closure_bindings=True,exact_stage_before_self=True,staged_bytes_exact=True,staged_diff_clean=False),
 'supplement_six_PASS_and_bindings':supp['all_passed'] is True and len(supp['checks'])==6 and all(supp['checks'].values()) and all(sha(p)==h for p,h in supp['sha256'].items()),
 'amendment_independently_accepted':rev['accepted'] is True and not rev['findings'] and all(rev['checks'].values()) and all(sha(p)==h for p,h in rev['sha256'].items()),
 'initial_staged_blobs_unchanged':all(git('rev-parse',':'+p)==h for p,h in pub['staged_blobs'].items()),
 'protected_files_unchanged':all(sha(p)==h for p,h in host['protected'].items()),
 'refs_unchanged':git('rev-parse','HEAD')==host['refs']['head'] and git('rev-parse','master')==host['refs']['master'] and git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture')==host['refs']['remote'],
 'no_production_change':not git('diff','HEAD','--','src','test','Project.toml','.github'),
 'no_numerical_outputs_or_admission':all(not(D/n).exists() for n in ('run-1','run-2','run-3','sequence-reservation.json','admission-review.json')),
}
extra=[R/'diagnostics/simplex-core-architecture/STATUS.md',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md',R/'diagnostics/simplex-core-architecture/MA-PRESOLVE-HARNESS-REPAIR.md',R/'docs/superpowers/plans/2026-10-14-ma-presolve-repaired-qualification.md']
expected={str(p.relative_to(R)) for p in D.rglob('*') if p.is_file()}|{str(p.relative_to(R)) for p in extra}|{str((D/n).relative_to(R)) for n in ('closure-final.json','publication-final.json')}
checks['expanded_exact_names_complete']=len(names)==len(set(names)) and set(names)==expected
r=subprocess.run(['git','diff','--cached','--check'],capture_output=True,text=True)
checks['exact_frozen_whitespace_only']=r.returncode==2 and r.stdout==supp['expected_diagnostics'] and not r.stderr
groups=host['groups'];boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  s=(p/'stat').read_text();f=s[s.rfind(')')+2:].split()
  if int(f[2]) in groups or int(f[3]) in groups or (p/'comm').read_text().strip().lower().startswith('julia'):
   matches.append(dict(pid=p.name,pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),boot_id=boot,command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except FileNotFoundError:pass
checks['full140groups_ANDsessions_noJulia']=len(groups)==140 and not matches
v=dict(all_passed=all(checks.values()),checks=checks,sha256={str(R/n):sha(R/n) for n in names if Path(n).name not in ('closure-final.json','publication-final.json')},host=dict(time=time.time(),boot_id=boot,groups=groups,matches=matches),scope='Supplemental offline closure. Initial FALSE publication and original PASS closure unchanged; exact two whitespace lines preserved.')
with(D/'closure-final.json').open('x') as f:json.dump(v,f,indent=2);f.write('\n')
print(json.dumps(checks,indent=2));require(v['all_passed'],'closure failed; no commit/push')
