from pathlib import Path
import json
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/simplex-core-architecture/results/MA-E')
# Original files are NEVER rewritten. New canonical versions have explicit names.
renames={'control.py':'control_reviewed.py','guard.py':'guard-reviewed.py','launcher.py':'launcher-reviewed.py','seal.py':'seal-reviewed.py','admission.md':'admission-reviewed.md','admission-pins.json':'admission-pins-reviewed.json','required-paths.json':'required-paths-reviewed.json','review.json':'review-final.json','review.md':'review-final.md'}
def changed(s):
 for a,b in renames.items():s=s.replace(a,b)
 return s.replace('from control import *','from control_reviewed import *')
for old,new in [('control.py','control_reviewed.py'),('guard.py','guard-reviewed.py'),('launcher.py','launcher-reviewed.py'),('seal.py','seal-reviewed.py')]:
 s=changed((D/old).read_text())
 if old=='control.py':
  s+='''\nPRIMARY=Path('/home/jspitz/JSimplex.jl')
def baseline_refs_ok(current,master_ref,branch,entry):
 try:return current[str(PRIMARY)]==entry['refs']['master']==master_ref and branch==entry['refs']['branch'] and branch=='codex/simplex-core-architecture'
 except (KeyError,TypeError):return False

def current_baseline_ok(current):
 master=subprocess.check_output(['git','-C',str(R),'rev-parse','master'],text=True).strip()
 branch=subprocess.check_output(['git','-C',str(R),'branch','--show-current'],text=True).strip()
 return baseline_refs_ok(current,master,branch,read(D/'host.json'))
'''
 if old=='seal.py':
  s=s.replace("pins=read(D/'admission-pins-reviewed.json');", "require(current_baseline_ok(refs()),'frozen master/primary/branch changed')\n pins=read(D/'admission-pins-reviewed.json');")
 if old=='launcher.py':
  s=s.replace('def main():\n','def main():\n started=time.monotonic()\n')
  s=s.replace("a=read(D/'execution-seal.json');", "require(current_baseline_ok(refs()),'frozen master/primary/branch changed')\n a=read(D/'execution-seal.json');")
  s=s.replace("save(D/'attempt-reserved.json'", "require(time.monotonic()-started<750,'entry checks exhausted whole cap')\n save(D/'attempt-reserved.json'")
  s=s.replace('started=time.monotonic();cost_start=None;', 'cost_start=None;')
  s=s.replace("require(refs()==a['refs'],'refs changed')", "require(refs()==a['refs'] and current_baseline_ok(refs()),'refs changed')")
 if old=='guard.py':
  a=s.index('def signal_owned(');b=s.index('\n\ndef stop_owned',a)
  s=s[:a]+'''def identity_owned(identity,leader):
    return identity['pgid']==leader or identity['sid']==leader

def same_identity(a,b):
    return all(a[k]==b[k] for k in ('pid','start_ticks','boot_id','command'))

def signal_owned(child, sig):
    # Leader is unreaped, reserving its PID/PGID/SID. pidfd prevents signaling a
    # reused member PID; double-read verifies identity and continued membership.
    for pid in active_group_members(child.pid):
        fd = None
        try:
            before=process_identity(pid)
            fd=os.pidfd_open(pid,0)
            after=process_identity(pid)
            if same_identity(before,after) and identity_owned(after,child.pid):
                signal.pidfd_send_signal(fd,sig,None,0)
        except (FileNotFoundError,ProcessLookupError):
            pass
        finally:
            if fd is not None:os.close(fd)
''' +s[b:]
  s=s.replace('guard_started = time.monotonic()',"guard_started = time.monotonic()\n    if not hasattr(os,'pidfd_open') or not hasattr(signal,'pidfd_send_signal'):\n        raise ValueError('pidfd unavailable; no launch')")
 with (D/new).open('x') as f:f.write(s)
s=changed((D/'admission.md').read_text()).replace('Fixed48records\nand456upper row publications','Fixed48records\nand432upper row publications')
s=s.replace('reservation consumed on refusal\nor failure','reservation consumed on any refusal or failure AFTER reservation; preflight\nrefusals launch no Julia and do not consume a numerical attempt')
s+='''\n## Independent review correction

Initial review rejected four issues, all original sources/manifests preserved.
Canonical guard-reviewed.py signals every still-owned PGID OR SID member using
pidfd plus boot/startticks/command double-read; it does not assume killpg reaches
separate descendant groups. Whole clock begins at launcher main entry, before
all seal/hash/refs/host work, with explicit expiry check before reservation.
seal-reviewed/launcher-reviewed explicitly require original frozen master AND
primary HEAD and diagnostic branch. Qualification trace count is432rows, while
456is selected products per48case sweep. Future MA-F uses reviewed canonical
filenames and reviewed pins, not original rejected launcher/seal/guard/control.
Synthetic tests prove helper logic and source ordering; no live kill/signal trial
or Julia run occurred. Descendants escaping BOTH owned group and session are not
claimed tracked; no spawn-capable workload is admitted and existing-mode loader
prevents fresh Julia compilecache workers. No OS isolation guarantee is claimed.
'''
with (D/'admission-reviewed.md').open('x') as f:f.write(s)
print('created four reviewed Python files and reviewed admission')
