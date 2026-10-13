import ast,json,sys,types
from pathlib import Path
D=Path(__file__).resolve().parent
mode=sys.argv[1];suffix='-reviewed' if mode=='green' else ''
g=(D/('guard'+suffix+'.py')).read_text();c=(D/('control_reviewed.py' if mode=='green' else 'control.py')).read_text();l=(D/('launcher'+suffix+'.py')).read_text();a=(D/('admission'+suffix+'.md')).read_text()
# Execute ONLY extracted signal helper against fake identities/functions. No real
# /proc reads, pidfd, signal, subprocess, launcher/guard invocation or Julia.
identities={11:dict(pid=11,pgid=11,sid=11,start_ticks=100,boot_id='boot',command='julia'),12:dict(pid=12,pgid=12,sid=11,start_ticks=101,boot_id='boot',command='worker')}
sent=[]
def killpg(group,sig):sent.extend(i for i,v in identities.items() if v['pgid']==group)
fakeos=types.SimpleNamespace(killpg=killpg,pidfd_open=lambda p,f:p,close=lambda p:None)
fakesignal=types.SimpleNamespace(pidfd_send_signal=lambda fd,sig,a,b:sent.append(fd))
names={'signal_owned','identity_owned','same_identity'};nodes=[n for n in ast.parse(g).body if isinstance(n,ast.FunctionDef) and n.name in names]
ns=dict(os=fakeos,signal=fakesignal,active_group_members=lambda leader:list(identities),process_identity=lambda pid:dict(identities[pid]))
exec(compile(ast.Module(body=nodes,type_ignores=[]),'<new fake-only helper test>','exec'),ns)
ns['signal_owned'](types.SimpleNamespace(pid=11),9)
checks={'E1_all_session_groups_signalled':set(sent)=={11,12}}
if mode=='green':
 checks['E1_reused_identity_rejected']=not ns['same_identity'](identities[11],dict(identities[11],start_ticks=102))
 checks['E1_nonmember_rejected']=not ns['identity_owned'](dict(identities[11],pgid=99,sid=99),11)
# Extract only pure refs predicate, inject synthetic path/entry.
b=[n for n in ast.parse(c).body if isinstance(n,ast.FunctionDef) and n.name=='baseline_refs_ok']
ns={'PRIMARY':Path('/primary')}
if b:exec(compile(ast.Module(body=b,type_ignores=[]),'<refs predicate>','exec'),ns)
fn=ns.get('baseline_refs_ok',lambda *a:False);entry={'refs':{'master':'M','branch':'codex/simplex-core-architecture'}}
checks['E2_frozen_refs']=bool(b) and fn({'/primary':'M'},'M','codex/simplex-core-architecture',entry) and not fn({'/primary':'other'},'M','codex/simplex-core-architecture',entry) and not fn({'/primary':'M'},'other','codex/simplex-core-architecture',entry)
main=next(n for n in ast.parse(l).body if isinstance(n,ast.FunctionDef) and n.name=='main')
checks['E3_clock_at_entry']=isinstance(main.body[0],ast.Assign) and ast.unparse(main.body[0])=='started = time.monotonic()'
checks['E4_rows432']='and432upper row publications' in a and 'and456upper row publications' not in a
checks['E5_precise_reservation']='preflight\nrefusals launch no Julia and do not consume a numerical attempt' in a
out={'all_passed':all(checks.values()),'checks':checks,'scope':'extracted fake-only helpers/source checks; no process signal or numerical execution'}
with (D/('review-fix-'+mode+'.json')).open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(out)
if not out['all_passed']:raise SystemExit(1)
