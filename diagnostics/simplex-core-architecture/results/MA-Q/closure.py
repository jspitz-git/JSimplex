from pathlib import Path
import hashlib,json,subprocess,time
R=Path.cwd(); E=R/'diagnostics/simplex-core-architecture/results/MA-Q'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=R,text=True).strip()
h=json.loads((E/'host.json').read_text()); review=json.loads((E/'review.json').read_text()); completion=json.loads((E/'completion-map.json').read_text()); groups=set(h['groups']); matches=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:
  fields=(p/'stat').read_text().rsplit(')',1)[1].split(); pgid,sid=int(fields[2]),int(fields[3]); command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace'); exe=(p/'exe').resolve().name
  if pgid in groups or sid in groups or exe.startswith('julia'):matches.append({'pid':int(p.name),'pgid':pgid,'sid':sid,'start_ticks':int(fields[19]),'exe':exe,'command':command})
 except (OSError,ValueError,IndexError):pass
checks={
 'accepted_review_no_findings':review.get('accepted') is True and not review.get('findings'),
 'review_bindings':all(sha(completion['mapping'][p]['preserved'] if p in completion['mapping'] else p)==s for p,s in review['sha256'].items()),
 'source14_pass':json.loads((E/'source-check.json').read_text())['all_passed'] is True,
 'source20_unchanged':all(sha(p)==s for p,s in json.loads((E/'source-check.json').read_text())['sha256'].items()),
 'completion_pass':json.loads((E/'completion-check.json').read_text())['all_passed'] is True,
 'completion_bindings':all(sha(p)==s for p,s in json.loads((E/'completion-check.json').read_text())['sha256'].items()),
 'six_previous_bindings':all(sha(x['preserved'])==x['sha256'] for x in json.loads((E/'continuation-map.json').read_text())['old_bindings']),
 'protected6':len(h['protected'])==6 and all(sha(p)==s for p,s in h['protected'].items()),
 'master514':len(h['master_identity'])==514 and all(sha(R/p)==s for p,s in h['master_identity'].items()),
 'refs_unchanged':git('rev-parse','HEAD')==h['refs']['head'] and git('rev-parse','master')==h['refs']['master'] and git('branch','--show-current')==h['refs']['branch'],
 'full158_groups_sessions_noJulia':len(groups)==158 and not matches,
 'no_unexpected_tracked_changes':set(git('diff','--name-only','HEAD').splitlines())=={'diagnostics/simplex-core-architecture/STATUS.md','docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'},
 'authored_diff_clean':subprocess.run(['git','diff','--check'],cwd=R,capture_output=True).returncode==0,
 'no_candidate_or_Julia_files':not list(E.glob('*.jl')) and not (R/'diagnostics/simplex-core-architecture/results/MA-R').exists(),
}
files=sorted([p for p in E.iterdir() if p.is_file()])+[R/'diagnostics/simplex-core-architecture/MA-DENSELU-BIGFLOAT-PLAN.md',R/'diagnostics/simplex-core-architecture/STATUS.md',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md',R/'docs/superpowers/plans/2026-10-14-ma-denselu-bigfloat.md',R/'docs/superpowers/specs/2026-10-14-ma-denselu-bigfloat-design.md']
obj={'checks':checks,'all_passed':all(checks.values()),'time':time.time(),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'groups':sorted(groups),'matches':matches,'sha256':{str(p):sha(p) for p in files}}
with (E/'closure.json').open('x') as out:json.dump(obj,out,indent=2);out.write('\n')
print(json.dumps({'checks':checks,'bindings':len(files)}))
if not obj['all_passed']:raise SystemExit(1)
