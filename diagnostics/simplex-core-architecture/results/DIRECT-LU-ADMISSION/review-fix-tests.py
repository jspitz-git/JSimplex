"""Synthetic files and read-only validators only; no process or Julia launch."""
from pathlib import Path
import json,tempfile,copy
from unittest.mock import patch
import control_reviewed as c,evidence_reviewed as e,audit_reviewed as a,guard
D=c.D;checks={}
def dump(p,v):p.write_text(json.dumps(v))
def rejected(name,fn):
    try:v=fn()
    except (ValueError,OSError,KeyError):checks[name]=True
    else:checks[name]=isinstance(v,dict) and not all(v.values())
with tempfile.TemporaryDirectory() as td:
    d=Path(td);out=d/'red-run';out.mkdir();inp=d/'input';inp.write_text('source')
    cfg=dict(seconds=30,expected_exit=1,project=str(d/'reference'),output=str(out),command=['synthetic-not-executed'],groups=[dict(name='reference-contract',counts=[0,3,0,0])])
    dump(d/'config.json',dict(phases=dict(red=cfg)))
    sealed=dict(files=[str(inp)],trees=[],inventory=guard.inventory([str(inp)],[]),phase='red',head='head',master='master',boot_id='boot')
    sp=d/'red-sealed-pins.json';dump(sp,sealed)
    rp=d/'red-admission.json';dump(rp,dict(accepted=True,findings=[],pins_sha256=c.sha(sp),sha256={str(p):c.sha(p) for p in [inp,sp]}))
    files=[str(inp),str(sp),str(rp)];pins=dict(files=files,trees=[],inventory=guard.inventory(files,[]))
    pp=d/'red-launch-pins.json';dump(pp,pins);dump(out/'pins.json',pins)
    host=dict(matches=[],head='head',master='master',boot_id='boot',groups=[10,11])
    for name in ['seal-host','prehost','posthost']:dump(d/f'red-{name}.json',host)
    res=d/'red-reservation.json';dump(res,dict(one_attempt=True,phase='red',command=cfg['command'],pins_sha256=c.sha(pp),review_sha256=c.sha(rp),max_seconds=30))
    identity=lambda n:dict(pid=n,pgid=n,sid=n,start_ticks=n,boot_id='boot',command='synthetic')
    p=dict(command=cfg['command'],pins_sha256=c.sha(pp),runner=identity(10),child=identity(11))
    dump(out/'current.json',p)
    p.update(returncode=1,reason='exit1',pins_unchanged=True,terminal_memory=dict(available_kib=7*1024**2,swap_used_kib=0))
    dump(out/'process.json',p)
    inv=dict(command=cfg['command'],pins_sha256=c.sha(pp),review_sha256=c.sha(rp),reservation_sha256=c.sha(res),elapsed_seconds=1,supervisor=dict(returncode=1,guard_identity=identity(10),elapsed_seconds=1,soft_timeout=False,hard_timeout=False))
    dump(d/'red-invocation.json',inv)
    (out/'resources.jsonl').write_text(json.dumps(p['terminal_memory'])+'\n');(out/'run.log').write_text('synthetic');(d/'red-launcher.log').write_text('synthetic')
    row='name = "reference-contract"\npass = 0\nfail = 3\nerror = 0\nbroken = 0\nexpected = [0, 3, 0, 0]\ncounts_match = true\n'
    (out/'group-1.toml').write_text(row);(out/'started-1.toml').write_text('name = "reference-contract"\nexpected = [0, 3, 0, 0]\n')
    (out/'raw.toml').write_text('phase = "red"\ncompleted = true\nall_expected = true\nfatal = ""\nloaded_path = '+json.dumps(str(d/'reference/src/JSimplex.jl'))+'\ntotal_pass = 0\ntotal_fail = 3\ntotal_error = 0\ntotal_broken = 0\n[[groups]]\n'+row)
    with patch.object(c,'D',d),patch.object(e,'D',d),patch.object(a,'D',d):
        values=e.phase_checks('red');checks['complete_red_semantics']=all(values.values())
        result=a.audit('red');checks['audit_accepts_complete_only']=result['all_passed'] and len(result['sha256'])==17
        checks['predecessor_complete']=len(e.validate_predecessor())==18
        for path in e.phase_paths('red',cfg):
            saved=path.read_bytes();path.unlink();rejected('missing_'+path.name,e.validate_predecessor);path.write_bytes(saved)
            path.write_bytes(saved+b' ');rejected('changed_'+path.name,e.validate_predecessor);path.write_bytes(saved)
        for path in [d/'red-extra.json',out/'extra']:
            path.write_text('extra');rejected('extra_'+path.name,e.validate_predecessor);path.unlink()
        ap=d/'red-audit.json';saved=ap.read_bytes()
        for name,mutate in [('false_audit',lambda v:v.update(all_passed=False)),('missing_hash',lambda v:v['sha256'].pop(str(out/'raw.toml'))),('false_checks',lambda v:v.update(checks={'invented':True}))]:
            v=json.loads(saved);mutate(v);dump(ap,v);rejected(name,e.validate_predecessor);ap.write_bytes(saved)
        # Semantic rejection even if somebody regenerated an audit SHA map.
        mutations=[('invocation_reservation',d/'red-invocation.json',lambda v:v.update(reservation_sha256='wrong')),
            ('invocation_review',d/'red-invocation.json',lambda v:v.update(review_sha256='wrong')),
            ('command',out/'process.json',lambda v:v.update(command=['wrong'])),
            ('process_exit',out/'process.json',lambda v:v.update(returncode=0)),
            ('remaining_group',d/'red-posthost.json',lambda v:v.update(matches=[{'pid':11}])),
            ('unscanned_group',d/'red-posthost.json',lambda v:v.update(groups=[10])),
            ('deadline',d/'red-invocation.json',lambda v:v.update(elapsed_seconds=31))]
        for name,path,mutate in mutations:
            b=path.read_bytes();v=json.loads(b);mutate(v);dump(path,v);rejected(name,lambda:e.phase_checks('red'));path.write_bytes(b)
        b=(out/'started-1.toml').read_bytes();(out/'started-1.toml').write_text('name = "wrong"\nexpected = [0,3,0,0]\n');rejected('wrong_start_marker',lambda:e.phase_checks('red'));(out/'started-1.toml').write_bytes(b)
        inp.write_text('changed source');rejected('changed_source',lambda:e.phase_checks('red'));inp.write_text('source')
        checks['restored_complete']=len(e.validate_predecessor())==18
checks['correct_work_ledger']='| focused selections | 99 | 346 | 115 | 127 | 22 |' in (D/'admission-reviewed.md').read_text() and '| Total | 670 | 5,368 | 3,139 | 1,147 | 106 |' in (D/'admission-reviewed.md').read_text()
checks['green_seal_gate']='extra=validate_predecessor()' in (D/'seal-reviewed.py').read_text()
s=(D/'launch-reviewed.py').read_text();checks['green_launch_gate_before_reservation']=s.index("if phase=='green':validate_predecessor()")<s.index("phase+'-reservation.json'")
checks['unchanged_initial_pins']=guard.pins_match(c.rd(D/'preparation-pins.json'))
c.save(D/'review-fix-tests.json',dict(all_passed=all(checks.values()),checks=checks,scope='Synthetic temporary files/read-only helpers only. No Julia/guard/supervisor/sealer/launcher execution.'))
print(json.dumps(dict(passed=sum(checks.values()),checks=len(checks))))
c.req(all(checks.values()),'Synthetic amendment failed')
