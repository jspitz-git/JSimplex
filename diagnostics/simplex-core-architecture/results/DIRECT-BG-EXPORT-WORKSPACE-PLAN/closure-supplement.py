"""New documentation-only closure after preserved exe-permission gate failure. No numerical admission."""
from pathlib import Path
import json,hashlib,subprocess,time
R=Path.cwd();E=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def rd(n):return json.loads((E/n).read_text())
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
def path(n):return Path(n) if Path(n).is_absolute() else R/n
def verify(d):return all(sha(path(n))==h for n,h in d.items())
def save(n,d):
 with (E/n).open('x') as f:json.dump(d,f,indent=2);f.write('\n')
entry=rd('host.json');groups=set(entry['groups']);matches=[];unread=[];exe_unavailable=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  raw=(p/'stat').read_text();t=raw[raw.rfind(')')+2:].split();comm=(p/'comm').read_text().strip();args=(p/'cmdline').read_bytes().split(b'\0');argv0=args[0].decode(errors='replace');exe=''
  record=dict(pid=int(p.name),pgid=int(t[2]),sid=int(t[3]),start_ticks=int(t[19]),comm=comm,command=b' '.join(args).decode(errors='replace'))
  try:exe=str((p/'exe').resolve(strict=True))
  except PermissionError:exe_unavailable.append(record)
  except FileNotFoundError:pass
  if int(t[2]) in groups or int(t[3]) in groups or any(Path(s).name.lower().startswith('julia') for s in [comm,exe,argv0]):matches.append(record)
 except PermissionError:unread.append(int(p.name))
 except (FileNotFoundError,ProcessLookupError):pass
host=dict(time=time.time(),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),groups=sorted(groups),matches=matches,unreadable_stat_or_command=unread,unavailable_executable_links=exe_unavailable,head=git('rev-parse','HEAD'),master=git('rev-parse','master'),remote=git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'),scope='Full group/session plus readable comm/command and available exe survey for documentation closure only; unavailable executable links are NOT verified executable identities. No numerical admission.')
save('host-closure-supplement.json',host)
c=rd('closure.json');review=rd('amendment-review.json');cr=rd('closure-review.json');names=rd('publication-names-final.json')['names']
excluded={str((E/n).relative_to(R)) for n in ['closure-supplement.json','publication.json']}
actual={str(p.relative_to(R)) for p in E.rglob('*') if p.is_file()}|{'docs/superpowers/specs/2026-10-18-direct-bg-export-workspace.md','docs/superpowers/plans/2026-10-18-direct-bg-export-workspace.md'}
checks=dict(original_failure_preserved=c['all_passed'] is False and [k for k,v in c['checks'].items() if not v]==['fresh_host'],original_bindings=verify(c['sha256']),accepted_design=review['accepted'] is True and not review['findings'] and verify(review['readtime_sha256']) and verify(review['evidence_sha256']),correction_review=cr['accepted'] is True and not cr['findings'] and verify(cr['readtime_sha256']) and verify(cr['evidence_sha256']),fresh_documentation_host=not matches and not unread and len(groups)==246 and host['boot_id']==entry['boot_id'],refs_unchanged=host['head']==entry['head'] and host['master']==entry['master'] and host['remote']==entry['remote'] and git('branch','--show-current')=='codex/simplex-core-architecture',tracked_unchanged=not git('diff','--name-only') and not git('diff','--cached','--name-only'),no_candidate=not (R/'diagnostics/direct-bg-export-workspace').exists(),exact_names=len(names)==len(set(names)) and actual==set(names)-excluded)
record=dict(scope=host['scope'],all_passed=all(checks.values()),checks=checks,sha256={n:sha(R/n) for n in names if n not in excluded})
save('closure-supplement.json',record);print(json.dumps(dict(all_passed=record['all_passed'],checks=len(checks),bindings=len(record['sha256']),failed=[k for k,v in checks.items() if not v])))
if not record['all_passed']:raise SystemExit(1)
