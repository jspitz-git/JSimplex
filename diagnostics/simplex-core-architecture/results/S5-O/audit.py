"""S5-O exclusive offline audit; unreadable/malformed evidence is failure, never retry."""
from common import *
import sys,tomllib,time

def evaluate(label,out):
 s=read(H/'schema.json');target=R if label=='green-1' else MAIN
 p=read(out/'process.json');pins=read(out/'pins.json');r=tomllib.loads((out/'raw/report.toml').read_text());raw=tomllib.loads((out/'raw/case.toml').read_text())
 c=raw.get('checks');v=raw.get('observations');resources=[json.loads(l) for l in (out/'resources.jsonl').read_text().splitlines()]
 assert isinstance(c,dict) and isinstance(v,dict) and isinstance(r,dict)
 text=(target/REL).read_bytes();prefix=text[:19080];suffix=text[19080:];executed=(out/'raw/executed-suffix.jl').read_text()
 patches=tomllib.loads((H/'insertions.toml').read_text())['insertions'];inverse=executed
 for patch in reversed(patches):
  joint=patch['insert']+patch['anchor'];assert inverse.count(joint)==1
  inverse=inverse.replace(joint,patch['anchor'])
 expected=tomllib.loads((H/'expected.toml').read_text());helpers='\n'.join(h['text'] for h in expected['helpers'])
 checks={
  'exit0':p['reason']=='exit0' and p['returncode']==0,
  'pins_guard_identity':p['pins_unchanged'] is True and sha(out/'pins.json')==p['pins_sha256']==sha(B/(label+'-pins.json')),
  'full_inventory':all(sha(f)==x['sha256'] and str(Path(f).resolve())==x['resolved'] for f,x in pins['inventory'].items()),
  'tree_membership':all({str(f) for f in Path(t).rglob('*') if f.is_file()}=={f for f in pins['inventory'] if Path(f).is_relative_to(t)} for t in pins['trees']),
  'raw_schema':set(raw)=={'checks','observations'} and set(c)==set(s['checks']) and set(v)==set(s['observations']),
  'forty_literal_true':len(c)==40 and all(x is True for x in c.values()),
  'types':all(type(v.get(k)) is int and v[k]>=0 for k in s['integer_observations']) and all(type(v.get(k)) is str for k in ('outcome_type','cause_type','last_event')),
  'wrapper_identity_flag':v.get('outcome_type') in s['outcome_types'] and v.get('cause_type') in s['cause_types'] and c.get('wrapper') is True and c.get('same_cause') is True,
  'one_latch_hit':type(v.get('latch_count')) is int and type(v.get('hit_count')) is int and v.get('latch_count')==v.get('hit_count')==1,
  '42_test_results':all(type(r.get(k)) is int for k in ('passes','fails','errors','broken')) and (r.get('passes'),r.get('fails'),r.get('errors'),r.get('broken'))==(42,0,0,0),
  'one_case_entries':r.get('entry_counts')==[1,1,1] and all(type(x) is int for x in r['entry_counts']),
  'actual_test':sha(target/REL)==r.get('test_sha256')==s['candidate_sha256'],
  'prefix_suffix':hashlib.sha256(prefix).hexdigest()==r.get('prefix_sha256')==s['prefix_sha256'] and hashlib.sha256(suffix).hexdigest()==r.get('suffix_sha256')==s['suffix_sha256'],
  'instrumentation_inverse':inverse.encode()==suffix and sha(out/'raw/executed-suffix.jl')==r.get('executed_sha256')==expected['executed'],
  'actual_three_helpers':(out/'raw/actual-helpers.jl').read_text()==helpers and sha(out/'raw/actual-helpers.jl')==r.get('helpers_sha256') and all(prefix.decode().count(h['text'])==1 and hashlib.sha256(h['text'].encode()).hexdigest()==h['sha256'] for h in expected['helpers']),
  'source_root':r.get('source_root')==str(target) and Path(r['module_path']).resolve()==(target/'src/JSimplex.jl').resolve(),
  'threads':r.get('julia_threads')==r.get('blas_threads')==1,
  'command':p['command']==command(label) and p['cwd']==str(R),
  'resources':bool(resources) and min(x['available_kib'] for x in resources)>=6*1024**2 and max(x['swap_used_kib'] for x in resources)<=1024**2 and max(x['elapsed'] for x in resources)<=120,
  'user6':all(sha(f)==v for f,v in read(H/'host-before.json')['user_hashes'].items()),
  'child_created':isinstance(p.get('child'),dict) and type(p['child'].get('pgid')) is int}
 checks['work_stops']=checks['types'] and v['entry_iterations']<=v['final_iterations']==v['throw_iterations'] and v['entry_refactors']<=v['final_refactors']==v['throw_refactors']
 checks['event_prefix']=checks['types'] and v['callback_count']==v['throw_callbacks']>=2 and v['throw_phase_events']==v['final_phase_events']>0 and v['last_event']=='pricing_phase_reset'
 groups=[p['runner']['pgid']]
 if checks['child_created']:groups.append(p['child']['pgid'])
 if label=='master-1':
  green=read(B/'green-1/process.json');groups.extend([green['runner']['pgid'],green['child']['pgid']])
 host=absent(groups);checks['groups_absent']=not host['matches'] and host['boot_id']==p['runner']['boot_id']
 return {'all_passed':all(checks.values()),'checks':checks,'observations':v,'pin_count':len(pins['inventory']),'host':host,'resources':{'samples':len(resources),'min_available_kib':min(x['available_kib'] for x in resources),'max_swap_kib':max(x['swap_used_kib'] for x in resources)},'raw_sha256':{str(f.relative_to(out)):sha(f) for f in out.rglob('*') if f.is_file()}}
def safe_evaluate(label,out):
 try:return evaluate(label,out)
 except (OSError,ValueError,KeyError,TypeError,AssertionError,AttributeError) as error:
  return {'all_passed':False,'checks':{'complete_valid_evidence':False},'error':repr(error),'scope':'Preserve every original artifact and STOP; no retry or inferred solver defect.'}
if __name__=='__main__':
 label,=sys.argv[1:];assert label in ('green-1','master-1')
 x=safe_evaluate(label,B/label);x['time_ns']=time.time_ns();dump(H/(label+'-audit.json'),x)
 print(json.dumps(x));raise SystemExit(0 if x['all_passed'] else 1)
