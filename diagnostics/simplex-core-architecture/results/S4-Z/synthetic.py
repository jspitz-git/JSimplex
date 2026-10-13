"""One-use pure Python admission tests; never executes launcher, guard, or Julia."""
from common import *
from audit import evidence_ok
import copy, tempfile, ast
checks={}
def test(name,condition):
 checks[name]=condition is True
 require(checks[name],name)
def fixture():
 cases=[]
 for kind in ('sparse','dense'):
  snapshots=[]
  for i in range(1,5):
   n=128 if i in (1,4) else 8;active=n if kind=='sparse' else 128
   s=dict.fromkeys(COUNT_FIELDS,0);s.update(label=f'stage_{i}',dimension=n,has_spare=i>1,spare_dimension=-1 if i==1 else (128 if i==2 else 8))
   for k in ('row_dictionary_count','column_dictionary_count','maxima_length','valid_length'):s[k]=128
   s['active_rows_length']=s['active_columns_length']=active;s['workspace_graph_bytes']=100;s['backend_graph_bytes']=200
   snapshots.append(s)
  cases.append({'kind':kind,'checks':dict.fromkeys(CHECKS,True),'snapshots':snapshots})
 return {'cases':cases,'errors':[],'all_passed':True}
raw=fixture();test('valid_66_predicates_8_snapshots',raw_ok(raw) and len(CHECKS)==33)
mutations={
 'missing_case':lambda r:r['cases'].pop(),
 'duplicate_case':lambda r:r['cases'].__setitem__(1,copy.deepcopy(r['cases'][0])),
 'missing_predicate':lambda r:r['cases'][0]['checks'].pop('saved_dimension'),
 'false_predicate':lambda r:r['cases'][0]['checks'].__setitem__('saved_dimension',False),
 'string_predicate':lambda r:r['cases'][0]['checks'].__setitem__('saved_dimension','true'),
 'integer_predicate':lambda r:r['cases'][0]['checks'].__setitem__('saved_dimension',1),
 'extra_predicate':lambda r:r['cases'][0]['checks'].__setitem__('extra',True),
 'missing_stage':lambda r:r['cases'][0]['snapshots'].pop(),
 'stage_order':lambda r:r['cases'][0]['snapshots'].reverse(),
 'wrong_dimension':lambda r:r['cases'][0]['snapshots'][1].__setitem__('dimension',128),
 'negative_graph':lambda r:r['cases'][0]['snapshots'][1].__setitem__('workspace_graph_bytes',-1),
 'float_graph':lambda r:r['cases'][0]['snapshots'][1].__setitem__('workspace_graph_bytes',1.5),
 'boolean_graph':lambda r:r['cases'][0]['snapshots'][1].__setitem__('workspace_graph_bytes',True),
 'wrong_dense_route':lambda r:r['cases'][1]['snapshots'][1].__setitem__('active_rows_length',8),
 'retained_owner_dimension':lambda r:r['cases'][0]['snapshots'][1].__setitem__('maxima_length',8),
 'error':lambda r:r['errors'].append('partial'),
 'false_aggregate':lambda r:r.__setitem__('all_passed',False),
 'malformed_root':lambda r:r.__setitem__('cases',None),
}
for name,mutate in mutations.items():
 r=copy.deepcopy(raw);mutate(r);test('reject_'+name,not raw_ok(r))
mandatory={str(D/n) for n in (*FINAL_NAMES,'common.py','guard.py','launcher.py','audit.py','admission.md','launch-pins.json','numerical-review.md')}|{str(Y/'driver-reviewed.jl')}
a={'accepted':True,'numerical_allowance':True,'unresolved_findings':[],'attempts':1,'stage':'S4-Z-qualification-1','human_authorization':'synthetic-only, never launch','refs':{'synthetic':'ref'},'command':command(),'output':str(OUT),'pins_sha256':'h','sha256':dict.fromkeys(mandatory,'h')}
identity=lambda n:{'pid':n,'pgid':n,'start_ticks':123,'boot_id':'boot','command':'synthetic'}
p={'reason':'exit0','returncode':0,'pins_unchanged':True,'elapsed_including_launch':1.0,'terminal_memory':{'available_kib':7*1024**2,'swap_used_kib':0},'runner':identity(900001),'child':identity(900002),'command':command(),'cwd':str(R),'pins_sha256':'h'}
host={'matches':[],'groups':sorted(GROUPS),'boot_id':'boot'}
post={**host,'groups':sorted(GROUPS|{900001,900002})}
inv={'returncode':0,'command':guard_command(),'started_ns':1,'ended_ns':2,'host':host,'post_host':post,'reservation_sha256':'h'}
res={'command':command(),'output':str(OUT),'pins_sha256':'h','refs':a['refs'],'allowance_sha256':'h'}
resources=[{'elapsed':0.1,'available_kib':7*1024**2,'swap_used_kib':0}]
args=[raw,p,inv,res,a,{},'h',resources]
test('valid_terminal_linkage',evidence_ok(*args,hashfn=lambda p:'h'))
for name,index,mutate in [
 ('nonzero_exit',1,lambda x:x.__setitem__('returncode',1)),
 ('overwall',1,lambda x:x.__setitem__('elapsed_including_launch',120.01)),
 ('terminal_RAM',1,lambda x:x['terminal_memory'].__setitem__('available_kib',1)),
 ('terminal_swap',1,lambda x:x['terminal_memory'].__setitem__('swap_used_kib',2*1024**2)),
 ('mismatched_pins',1,lambda x:x.__setitem__('pins_sha256','bad')),
 ('incomplete_terminal',1,lambda x:x.pop('elapsed_including_launch')),
 ('wrong_command',1,lambda x:x.__setitem__('command',[])),
 ('incomplete_invocation',2,lambda x:x.pop('post_host')),
 ('bad_reservation',2,lambda x:x.__setitem__('reservation_sha256','bad')),
 ('missing_session',2,lambda x:x['post_host'].__setitem__('groups',sorted(GROUPS))),
 ('changed_boot',2,lambda x:x['post_host'].__setitem__('boot_id','other')),
 ('missing_human_permission',4,lambda x:x.__setitem__('numerical_allowance',False)),
 ('extra_attempt',4,lambda x:x.__setitem__('attempts',2)),
 ('boolean_attempt',4,lambda x:x.__setitem__('attempts',True)),
 ('missing_allowance_binding',4,lambda x:x['sha256'].pop(str(D/'guard.py'))),
 ('no_resources',7,lambda x:x.clear()),
]:
 b=copy.deepcopy(args);mutate(b[index]);test('reject_'+name,not evidence_ok(*b,hashfn=lambda p:'h'))
with tempfile.TemporaryDirectory(prefix='jsimplex-s4z-synthetic-') as tmp:
 q=Path(tmp)/'sample';q.write_text('x');pin={'files':[str(q)],'trees':[],'inputs':[],'inventory':{str(q):{'resolved':str(q.resolve()),'sha256':sha(q)}}}
 test('valid_manifest',manifest_ok(pin,{str(q):sha(q)}))
 test('reject_missing_required_pin',not manifest_ok(pin,{str(q)+'missing':'h'}))
 q.write_text('changed');test('reject_changed_pin',not manifest_ok(pin,{}))
 out=Path(tmp)/'reserved';dump(out,{'test':1})
 try:dump(out,{'test':2});refused=False
 except FileExistsError:refused=True
 test('reject_reused_reservation',refused and read(out)=={'test':1})
 log=Path(tmp)/'launcher.log';log.write_text('old')
 try:
  with log.open('x'):pass
  refused=False
 except FileExistsError:refused=True
 test('reject_reused_launcher_log',refused and log.read_text()=='old')
 test('missing_raw_file_detectable',not (Path(tmp)/'retention.toml').is_file())
# The exact runtime require remains active under Python -O/-OO.
source=(D/'common.py').read_text();node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='require')
for level in (0,1,2):
 ns={};exec(compile(ast.Module(body=[node],type_ignores=[]),'require','exec',optimize=level),ns)
 try:ns['require'](False,'synthetic');refused=False
 except ValueError:refused=True
 test('optimized_require_'+str(level),refused)
test('launcher_main_guarded',"if __name__=='__main__':sys.exit(main())" in (D/'launcher.py').read_text())
test('guard_byteidentical_old_source',sha(D/'guard.py')==sha(D.parent/'S2-D/guard.py'))
# Pure helpers only: launcher and guard never imported or executed.
dump(D/'synthetic.json',{'checks':checks,'all_passed':all(checks.values()),'sha256':{str(p):sha(p) for p in (D/'common.py',D/'audit.py',D/'launcher.py',D/'guard.py',D/'synthetic.py')}})
print(json.dumps({'checks':len(checks),'all_passed':all(checks.values())}))
