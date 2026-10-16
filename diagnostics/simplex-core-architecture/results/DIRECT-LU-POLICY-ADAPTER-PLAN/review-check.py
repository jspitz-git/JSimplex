"""Independent one-shot source/design checks. Never imports or executes project code."""
from pathlib import Path
import hashlib,json,subprocess,time
P=Path(__file__).resolve().parent
R=P.parents[3]
W=Path('/home/jspitz/.codex/worktrees/native-pivot-production-integration/JSimplex.jl')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args,cwd=R):return subprocess.check_output(['git',*args],cwd=cwd,text=True).strip()
def need(v,m):
 if not v:raise RuntimeError(m)
def save(n,v):
 with (P/n).open('x') as f:json.dump(v,f,indent=2);f.write('\n')
m=json.loads((P/'source-inputs.json').read_text())
need(len(m['sha256'])==37,'Readtime pin membership')
current={n:sha(Path(n)) for n in m['sha256']}
drift={n:{'original':h,'current':current[n]} for n,h in m['sha256'].items() if h!=current[n]}
plan=R/'docs/superpowers/plans/2026-10-16-direct-lu-policy-adapters.md'
need(set(drift)=={str(plan)},'Only agreed plan revision expected')
baseline=json.loads((P/'baseline.json').read_text());counts={}
for label,root in [('diagnostic',R),('production',W)]:
 names=git('ls-files','src','test','.github','Project.toml',cwd=root).splitlines()
 need(set(names)==set(baseline[label]),'Baseline membership '+label)
 need(all(sha(root/n)==h for n,h in baseline[label].items()),'Baseline values '+label)
 need(not git('status','--porcelain','--','src','test','.github','Project.toml',cwd=root),'Production scope status '+label)
 counts[label]=len(names)
need(git('rev-parse','HEAD')=='cb757325ff6fe34e94479f7e622d6620fa7c1c8a','Diagnostic HEAD')
master='26e2291745999f485a74f643298ca997d65c7205'
need(git('rev-parse','master')==git('rev-parse','HEAD',cwd=W)==master,'Actual master')
remote=git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture')
need(master+'\trefs/heads/master' in remote,'Remote master')
for n,h in baseline['production'].items():
 b=subprocess.check_output(['git','show',master+':'+n],cwd=R)
 need(hashlib.sha256(b).hexdigest()==h,'Actual master tree '+n)
host0=json.loads((P/'host.json').read_text());groups=host0['groups'];need(len(groups)==len(set(groups))==222,'All historical groups')
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[];unreadable=[]
for q in Path('/proc').glob('[0-9]*'):
 try:
  a=(q/'stat').read_text().rsplit(')',1)[1].split();comm=(q/'comm').read_text().strip();exe=''
  try:exe=str((q/'exe').resolve(strict=True))
  except PermissionError:unreadable.append(int(q.name))
  except FileNotFoundError:pass
  if int(a[2]) in groups or int(a[3]) in groups or comm.lower().startswith('julia') or Path(exe).name.lower().startswith('julia'):
   matches.append(dict(pid=int(q.name),ppid=int(a[1]),pgrp=int(a[2]),session=int(a[3]),start_ticks=int(a[19]),comm=comm,exe=exe,command=(q/'cmdline').read_bytes().replace(bytes([0]),b' ').decode(errors='replace')))
 except (FileNotFoundError,ProcessLookupError):pass
need(boot==host0['boot_id'] and not matches,'Host clear on same boot')
save('review-host.json',dict(time=time.time(),boot_id=boot,groups=groups,matches=matches,unreadable_exe_pids=unreadable,scope='All /proc stat groups/sessions and comm plus readable exe; inaccessible exe links remain a visibility limit.',head=git('rev-parse','HEAD'),master=master,remote_refs=remote))
inputs=json.loads((P.parent/'DIRECT-LU-COST-PREPARATION/inputs.json').read_text())
need([(x['name'],x['n']) for x in inputs['fixtures']]==[('sparse32',32),('dense32',32),('sparse96',96),('dense96',96)],'Cost fixture order/names')
ledger=dict(green_setups=7*3*3*2,cost_cells=4*3*2,lifecycles=4*3*2*2*(3+7)*2,constructions=960,refactors=960*2,updates=960*8,ftran=960*8*2,btran=960*8,public_solves=3*2*2,red_contract_failures=3*2+1)
need(ledger==dict(green_setups=126,cost_cells=24,lifecycles=960,constructions=960,refactors=1920,updates=7680,ftran=15360,btran=7680,public_solves=12,red_contract_failures=7),'Ledger')
save('review-checks.json',dict(all_passed=True,scope='Source/design only; no executable admission',checks=dict(original_manifest37=True,only_agreed_revision=True,baseline_membership_and_bytes=True,actual_master_tree=True,master_remote=True,all222_groups_sessions_clear=True,cost_fixture_metadata=True,arithmetic_ledger=True),baseline_counts=counts,initial_source_sha256=m['sha256'],current_source_sha256=current,revision=drift,ledger=ledger,extra_work='Counts exclude separately admitted correctness/preflight and orientation/backend-internal work, which remain required future ledgers.'))
print('Independent source/design checks passed; baseline files',counts,'; ledger',ledger)
