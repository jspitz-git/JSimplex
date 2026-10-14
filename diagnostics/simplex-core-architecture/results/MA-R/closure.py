from pathlib import Path
import hashlib,json,subprocess,time
R=Path.cwd(); E=R/'diagnostics/simplex-core-architecture/results/MA-R'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],text=True).strip()
h=json.loads((E/'host.json').read_text()); review=json.loads((E/'review-final.json').read_text())
maps=[json.loads((E/n).read_text())['mapping'] for n in ['review-fix-map.json','completion-map.json']]
def resolves(p,s):
 return sha(p)==s or any(p in m and m[p]['sha256']==s and sha(m[p]['preserved'])==s for m in maps)
groups=set(h['groups']); matches=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:
  fields=(p/'stat').read_text().rsplit(')',1)[1].split(); pgid,sid=int(fields[2]),int(fields[3]); exe=(p/'exe').resolve().name
  if pgid in groups or sid in groups or exe.startswith('julia'):matches.append(dict(pid=int(p.name),pgid=pgid,sid=sid,start_ticks=int(fields[19]),exe=exe,command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except (OSError,ValueError,IndexError):pass
checks={
 'accepted_final_review_no_findings':review.get('accepted') is True and review.get('findings')==[],
 'source15_pass':json.loads((E/'source-check.json').read_text())['all_passed'] is True,
 'fix6_pass':json.loads((E/'review-fix.json').read_text())['all_passed'] is True,
 'completion8_pass':json.loads((E/'completion-check.json').read_text())['all_passed'] is True,
 'all_preservation_maps':all(sha(v['preserved'])==v['sha256'] for m in maps for v in m.values()),
 'six_MAQ_continuation_bindings':all(sha(x['preserved'])==x['sha256'] for x in json.loads((E/'continuation-map.json').read_text())['old_bindings']),
 'protected6':len(h['protected'])==6 and all(sha(p)==s for p,s in h['protected'].items()),
 'master514':len(h['master_identity'])==514 and all(sha(R/p)==s for p,s in h['master_identity'].items()),
 'refs_unchanged':git('rev-parse','HEAD')==h['refs']['head'] and git('rev-parse','master')==h['refs']['master'] and git('branch','--show-current')==h['refs']['branch'],
 'same_boot_full158groups_ANDsessions_noJulia':Path('/proc/sys/kernel/random/boot_id').read_text().strip()==h['boot_id'] and len(groups)==158 and not matches,
 'only_two_expected_tracked_changes':set(git('diff','--name-only','HEAD').splitlines())=={'diagnostics/simplex-core-architecture/STATUS.md','docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'},
 'authored_tracked_diff_clean':subprocess.run(['git','diff','--check'],capture_output=True).returncode==0,
 'no_MAS_driver_or_launch':not (E.parent/'MA-S').exists(),
}
for n,count in [('source-check.json',38),('review.json',46),('review-amendment.json',5),('review-fix.json',9),('review-final.json',58),('completion-check.json',8)]:
 d=json.loads((E/n).read_text())['sha256']; checks[n+'_bindings']=len(d)==count and all(resolves(p,s) for p,s in d.items())
files=sorted(p for p in E.rglob('*') if p.is_file())+[R/'diagnostics/simplex-core-architecture/MA-DENSELU-BIGFLOAT-PREPARATION.md',R/'diagnostics/simplex-core-architecture/STATUS.md',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md']
obj={'checks':checks,'all_passed':all(checks.values()),'time':time.time(),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'groups':sorted(groups),'matches':matches,'sha256':{str(p):sha(p) for p in files},'scope':'Offline closure only. Accepted MA-R candidate and unexecuted tests; no runtime, allocation or speedup acceptance. No old script rerun.'}
with (E/'closure.json').open('x') as f:json.dump(obj,f,indent=2);f.write('\n')
print(json.dumps({'checks':checks,'bindings':len(files),'all_passed':obj['all_passed']}))
if not obj['all_passed']:raise SystemExit(1)
