"""Saved RED failure review; read-only control definitions, no Julia/auditor/closure rerun."""
from pathlib import Path
import json,sys,hashlib
H=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-HARNESS');D=H.with_name('DIRECT-BG-BLOCKED-UPDATE-RED');R=H.parents[3];W=Path('/home/jspitz/.codex/worktrees/native-pivot-production-integration/JSimplex.jl');Q=H.with_name('DIRECT-BG-BLOCKED-UPDATE-TASK2')
sys.path.insert(0,str(H));import control as c
run=H/'runs/red300';outer=H/'outers/red300';out=run/'output';checks={}
def ck(n,v):
 checks[n]=bool(v)
 if not v:raise RuntimeError(n)
def rd(p):return json.loads(Path(p).read_text())
def sha(p):return c.sha(c.path(str(p)))
s=rd(run/'sealed.json');p=rd(out/'process.json');lp=rd(run/'launch-pins.json');inv=rd(run/'invocation.json');cur=rd(out/'current.json');audit=rd(run/'audit.json');closure=rd(run/'outer-closure.json');outcome=rd(outer/'outer-outcome.json');summary=rd(D/'summary.json');cfg=rd(run/'config.json')
c.verify_seal(cfg,s);ck('sealed_inventory_current',True)
ck('1880_exact_paths',len(s['files'])==len(s['inventory'])==1880)
ck('launch_pins_membership',set(lp['files'])==set(s['files'])|{str(run/n) for n in ['sealed.json','admission.json','prehost.json']}|{str(outer/n) for n in ['release.json','outer-invocation.json']} and lp['trees']==s['trees'])
ck('launch_pins_current',c.guard.pins_match(lp) and rd(out/'pins.json')==lp)
ck('seal_launch_subset',all(lp['inventory'].get(n)==v for n,v in s['inventory'].items()))
c.verify_review(rd(run/'admission.json'),run/'sealed.json',s['files']+[str(run/'sealed.json')],'BG blocked U exact-stage admission','red300');ck('original_admission_intact',True)
c.verify_outer_invocation('red300',s);ck('release_invocation_identity',True)
c.validate_result_closure('red300',closure);ck('saved_external_closure',True)
expected_run={'admission.json','audit.json','config.json','host.json','invocation.json','launch-pins.json','launcher.log','outer-closure.json','output/current.json','output/pins.json','output/process.json','output/resources.jsonl','output/run.log','posthost.json','prehost.json','reservation.json','sealed.json'}
ck('exact_run_membership',{str(x.relative_to(run)) for x in run.rglob('*') if x.is_file()}==expected_run)
ck('exact_outer_membership',{x.name for x in outer.iterdir()}=={'outer-invocation.json','outer-outcome.json','outer-ready.json','release.json'})
ck('no_symlink_outputs',not any(x.is_symlink() for x in list(run.rglob('*'))+list(outer.rglob('*'))))
for label,v in [('audit',audit),('closure',closure),('summary',summary)]:ck(label+'_saved_hashes',c.bindings(v))
ck('summary_complete_run_outer_binding',set(summary['sha256'])=={str(x) for root in [run,outer] for x in root.rglob('*') if x.is_file()})
ck('summary_values',summary['qualification_pass'] is False and summary['units_saved']==0 and summary['units']==[] and summary['raw'] is None and summary['process']==p and summary['invocation']==inv and summary['outer']==outcome and summary['audit']==audit)
ck('no_qualification_review',not (run/'result-review.json').exists())
ck('audit_rejected_load_failure',audit['all_passed'] is False and audit['pure_timeout'] is False and audit['error']=="RuntimeError('Missing raw/units')" and audit['result']=={})
ck('one_reservation',rd(run/'reservation.json')==dict(one_attempt=True,phase='red300',command=cfg['command'],pins_sha256=sha(run/'launch-pins.json'),review_sha256=sha(run/'admission.json'),max_seconds=300))
ck('invocation_reservation_link',inv['reservation_sha256']==sha(run/'reservation.json') and inv['review_sha256']==sha(run/'admission.json'))
ck('pins_hash_linkage',p['pins_sha256']==cur['pins_sha256']==inv['pins_sha256']==sha(run/'launch-pins.json') and p['pins_unchanged'] is True)
ck('exact_commands',p['command']==cur['command']==inv['command']==cfg['command'] and p['cwd']==str(R))
ck('guard_command',inv['guard_command']==c.guard_command(cfg,run/'launch-pins.json',inv['monotonic_start']))
ck('identity_linkage',cur['runner']==p['runner']==inv['supervisor']['guard_identity'] and cur['child']==p['child'])
ck('identities_isolated',all(p[r]['pid']==p[r]['pgid']==p[r]['sid'] and p[r]['start_ticks']>0 and p[r]['boot_id']==s['boot_id'] and p[r]['command'] for r in ['runner','child']))
ck('expected_process_exit_but_not_qualification',p['reason']=='exit1' and p['returncode']==1 and inv['supervisor']['returncode']==0 and inv['supervisor']['accepted'] is True and outcome['returncode']==2 and outcome['launched'] is True)
ck('inclusive300',0<p['elapsed_including_launch']<=292 and 0<inv['elapsed_seconds']<=300 and 0<inv['supervisor']['elapsed_seconds']<=300)
ck('no_timeout_kill',all(inv['supervisor'][k] is False for k in ['soft_timeout','hard_timeout','child_kill','guard_term','guard_kill']))
ck('outer_error_preserved','Failed attempt preserved; no automatic retry' in outcome['error'])
log=(out/'run.log').read_text();ck('load_failure',log.startswith('ERROR: LoadError: UndefVarError: `_NativePivotPolicy` not defined in `JSimplex`'))
ck('before_test_entry',all(x not in log for x in ['BEGIN BG blocked U driver','UNIT BEGIN','TEST FAILURE:']))
ck('no_test_output',{x.name for x in out.iterdir()}=={'current.json','pins.json','process.json','resources.jsonl','run.log'})
resources=[json.loads(x) for x in (out/'resources.jsonl').read_text().splitlines()]
ck('resource_limits',len(resources)==4 and all(x['available_kib']>=6*1024**2 and x['swap_used_kib']<=1024**2 for x in resources+[p['terminal_memory']]))
ck('summary_resources',summary['resources']==dict(samples=len(resources),min_available_kib=min(x['available_kib'] for x in resources),max_swap_used_kib=max(x['swap_used_kib'] for x in resources)))
ck('rss_record',p['child_maxrss_kib']==540740)
h=c.full_host(closure['host']['groups']);m=c.guard.memory();ck('fresh_full_host_closure',c.host_safe(h) and all(h[k]==s[k] for k in ['head','master','boot_id']))
ck('all_271_groups_sessions',len(h['groups'])==271 and set(s['groups'])|{s['outer_identity']['pgid'],p['runner']['pgid'],p['child']['pgid']}==set(h['groups']))
c.validate_sources();ck('production_diagnostic_stage_runtime_unchanged',True)
# Establish the earliest missing dependency from source and staging provenance.
stage=Path(cfg['stage']);factor=stage/'src/factorization.jl';direct=stage/'src/direct-factor.jl';master=W/'src/factorization.jl';builder=Q/'fixtures.py';overlay=R/'diagnostics/direct-bg-blocked-update/reproduce/overlay-manifest.json'
ck('staged_factor_equals_diagnostic',sha(factor)==sha(R/'src/factorization.jl'))
ck('production_has_policy_definition',master.read_text().splitlines()[16]=='@enum _NativePivotPolicy::UInt8 _NATIVE_PIVOT_DEFAULT _NATIVE_PIVOT_ONE')
ck('staged_policy_undefined',not any('@enum _NativePivotPolicy' in x.read_text() or 'struct _NativePivotPolicy' in x.read_text() for x in (stage/'src').rglob('*.jl')))
ck('direct_struct_policy_dependency',direct.read_text().splitlines()[2]=='struct DirectLowerBackend{R,F}' and direct.read_text().splitlines()[9].strip()=='pivot_policy::_NativePivotPolicy')
ck('source_failure_order',(H/'driver.jl').read_text().splitlines()[2]=='using JSimplex' and (stage/'src/JSimplex.jl').read_text().splitlines()[19]=='include("factorization.jl")' and (stage/'src/JSimplex.jl').read_text().splitlines()[78]=='include("direct-factor.jl")')
ck('builder_uses_diagnostic_src',"for p in sorted((R/'src').rglob('*')):" in builder.read_text() and "shutil.copyfile(p,dest)" in builder.read_text())
ck('manifest_provenance',rd(overlay)['original_sha256']['src/factorization.jl']==sha(R/'src/factorization.jl') and rd(overlay)['stage_sha256']['src/factorization.jl']==sha(factor))
ck('master_matches_git',c.git('show','master:src/factorization.jl')==master.read_text().strip())
source_files=[factor,direct,master,R/'src/factorization.jl',stage/'src/JSimplex.jl',builder,overlay,H/'driver.jl',H/'guard.py',H/'control.py',H/'audit.py',H/'supervisor.py',H/'admission-independent-check.py']
# The prelaunch checker lives in D, not H.
source_files[-1]=D/'admission-independent-check.py'
all_files=sorted({str(x) for root in [run,outer] for x in root.rglob('*') if x.is_file()}|{str(D/'summary.json')}|{str(x) for x in source_files})
record=dict(all_passed=True,check_count=len(checks),checks=checks,qualification_accepted=False,assertions_executed=0,expected_red_failures=6,observed_test_failures=0,host=h,memory=m,source_evidence={str(x):sha(x) for x in source_files},sha256={n:sha(n) for n in all_files},scope=__doc__)
with (D/'result-independent-check.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=True,checks=len(checks),bindings=len(all_files),groups=len(h['groups']),memory=m,qualification_accepted=False)))
