"""Fresh offline checks, not a Julia syntax/runtime qualification."""
from pathlib import Path
import json,hashlib,subprocess,importlib.util
P=Path(__file__).resolve().parent;R=P.parents[3];C=R/'diagnostics/direct-lu-policy-adapters/reproduce';O=R/'diagnostics/direct-lu-markowitz/reproduce';W=Path('/home/jspitz/.codex/worktrees/native-pivot-production-integration/JSimplex.jl');L=R/'.superpowers/sdd/2026-10-16-direct-lu-policy-adapters'
checks={}
def need(ok,name):
 checks[name]=bool(ok)
 if not ok:raise RuntimeError(name)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,j):
 with p.open('x') as f:json.dump(j,f,indent=2);f.write('\n')
def git(*a):return subprocess.check_output(['git',*a],cwd=R)
def rd(p):return json.loads(p.read_text())
inv=rd(P/'candidate-inverse.json');s=(C/'direct-factor.jl').read_text()
need(sha(C/'direct-factor.jl')==inv['candidate_sha256'],'candidate_hash')
for old,new in reversed(inv['replacements']):
 need(s.count(new)==1,'inverse_'+str(len(checks)));s=s.replace(new,old,1)
need(s.encode()==(O/'direct-factor.jl').read_bytes(),'whole_candidate_inverse')
for name in ('factor-export.jl','fixtures.jl'):need((C/name).read_bytes()==(O/name).read_bytes(),'unchanged_'+name)
for label,root in [('diagnostic',R),('production',W)]:
 base=rd(P/'baseline.json')[label]
 need(all(sha(root/n)==h for n,h in base.items()),label+'_baseline')
 need(set(subprocess.check_output(['git','ls-files','src','test','.github','Project.toml'],cwd=root,text=True).splitlines())==set(base),label+'_membership')
need(git('rev-parse','master').decode().strip()=='26e2291745999f485a74f643298ca997d65c7205','master_ref')
need(all((W/n).read_bytes()==git('show','master:'+n) for n in rd(P/'baseline.json')['production']),'production_actual_git_tree')
for mode in ('red','candidate'):
 out=L/(mode+'-overlay');m=rd(out/'overlay.json');m_source=m['source_sha256']
 need(len(m_source)==71 and m['master']=='26e2291745999f485a74f643298ca997d65c7205','overlay_source_'+mode)
 need(all(hashlib.sha256(git('show',m['master']+':'+n)).hexdigest()==h for n,h in m_source.items()),'master_blobs_'+mode)
 need(all(sha(out/n)==h for n,h in m['overlay_sha256'].items()),'overlay_hashes_'+mode)
 root=(out/'src/JSimplex.jl').read_bytes();addition=b'include("factor-export.jl")\ninclude("direct-factor.jl")\n'
 need(root.count(addition)==1 and root.replace(addition,b'')==git('show',m['master']+':src/JSimplex.jl'),'root_inverse_'+mode)
 need(all(sha(out/n)==h for n,h in m_source.items() if n!='src/JSimplex.jl'),'unchanged_originals_'+mode)
 need(set(m['overlay_sha256'])==set(m_source)|{'src/factor-export.jl','src/direct-factor.jl'},'exact_overlay_membership_'+mode)
 need(not (out/'Manifest.toml').exists() and not (out/'LocalPreferences.toml').exists(),'no_environment_'+mode)
 save(P/(mode+'-overlay.json'),m)
# Exercise refusal behavior of the NEW Python builder only.
spec=importlib.util.spec_from_file_location('offline_overlay',C/'prepare-overlay.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
for mode,dest in [('candidate',L/'candidate-overlay'),('invalid',L/'must-not-exist')]:
 try:mod.prepare(dest,mode)
 except RuntimeError:need(True,'builder_refuses_'+mode)
 else:need(False,'builder_refuses_'+mode)
need(not (L/'must-not-exist').exists(),'invalid_mode_no_output')
oldchecks=rd(P/'tests-before-candidate.json');revision=rd(P/'test-revision.json')
for n,h in oldchecks.items():
 preserved=R/revision['preserved'] if n.endswith('lifecycle-tests.jl') else R/n
 need(sha(preserved)==h,'test_first_'+Path(n).name)
need(sha(C/'lifecycle-tests.jl')==revision['after_sha256'],'current_lifecycle_revision')
need(sha(Path(__file__).resolve())!='','source_check_self_readable')
source_paths=set(C.glob('*'))|set(P.glob('*'))
source_paths|={R/'docs/superpowers/plans/2026-10-16-direct-lu-policy-adapters.md',R/'docs/superpowers/specs/2026-10-16-direct-lu-policy-adapters.md'}
source_paths|={O/n for n in ('direct-factor.jl','factor-export.jl','fixtures.jl')}
source_paths|={R/'diagnostics/simplex-core-architecture/results/DIRECT-LU-TEST-REPAIR/correctness.jl'}
source_paths|={W/'src'/n for n in ('factorization.jl','triangular_factorization.jl','markowitz_factorization.jl','huangfu_hall_factorization.jl','JSimplex.jl')}
source_paths|={W/'Manifest.toml',W/'LocalPreferences.toml'}
source_paths={p for p in source_paths if p.is_file()}
save(P/'source-check.json',dict(all_passed=True,checks=checks,sha256={str(p):sha(p) for p in sorted(source_paths)},scope='OFFLINE only; no Julia parsing or runtime test'))
print('Offline source checks PASS',len(checks),';',len(source_paths),'readtime hashes; Julia UNEXECUTED')
