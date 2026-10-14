from pathlib import Path
import hashlib,json,tomllib,subprocess,time
R=Path.cwd(); D=R/'diagnostics/simplex-core-architecture/results/MA-W'; B=D.parent
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],text=True).strip()
def require(ok,msg):
 if not ok:raise ValueError(msg)
e=read(D/'evidence.json');entry=read(D/'entry.json');h=read(D/'host.json');maps=read(D/'continuation-map.json')['old_bindings'];checks={}
checks['evidence_33_fresh_hashes']=len(e['sha256'])==33 and all(sha(p)==v for p,v in e['sha256'].items())
checks['entry_6_fresh_hashes']=len(entry['sha256'])==6 and all(sha(p)==v for p,v in entry['sha256'].items())
checks['computed_records_positive']=e['all_passed'] is True and len(e['checks'])==19 and all(v is True for v in e['checks'].values()) and entry['all_passed'] is True and len(entry['checks'])==14 and all(v is True for v in entry['checks'].values())
checks['six_preserved_continuation_bindings']=len(maps)==6 and all(sha(m['preserved'])==m['sha256']==read(m['source'])['sha256'][m['path']] for m in maps)
checks['source514_unchanged']=len(h['master_identity'])==514 and all(sha(R/p)==v for p,v in h['master_identity'].items())
checks['protected6_unchanged']=len(h['protected'])==6 and all(sha(p)==v for p,v in h['protected'].items())
checks['refs']=git('rev-parse','HEAD')==h['refs']['head']=='6fbf790b1ff60f3a83ba612d3c824b98274fd9ac' and git('rev-parse','master')==h['refs']['master']=='6f68e24e8ddac42b948da8fcc2d636c010751194'
checks['remote_refs']=set(git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture').splitlines())==set(h['refs']['remote'].splitlines())
checks['tracked_and_staged_unchanged']=not git('diff','--name-only','HEAD') and not git('diff','--cached','--name-only')
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  fields=(p/'stat').read_text().rsplit(')',1)[1].split()
  if int(fields[2]) in h['groups'] or int(fields[3]) in h['groups'] or (p/'exe').resolve().name.startswith('julia'):
   matches.append(dict(pid=int(p.name),pgid=int(fields[2]),sid=int(fields[3]),start_ticks=int(fields[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except (FileNotFoundError,ProcessLookupError):pass
checks['fresh170_group_or_session_no_julia']=len(set(h['groups']))==170 and not matches and boot==h['boot_id']
f=tomllib.loads((B/'MA-R/fixtures.toml').read_text());cases=f['cost_cases'];dirs=len(f['directions'])
grid=len(f['bits'])*len(f['sizes'])*len(f['layouts'])*dirs
correctness=grid+(len(f['specials'])+len(f['mixed_stored_ambient'])+len(f['matching_rounding'])+len(f['scoped_mismatch'])+2)*dirs
per_arm=correctness+sum(k=='retained_outputs' for k in f['specials'])*dirs
setups=correctness+dirs+len(cases)*3
ledger=dict(correctness_cases=correctness,correctness_calls_per_arm=per_arm,direct_smoke_correctness_entries=per_arm*3+dirs,correctness_smoke_setups=correctness+dirs,pfi_constructors=sum(k=='copied_pfi' for k in f['specials'])*dirs,pfi_copies=sum(k=='copied_pfi' for k in f['specials'])*dirs,cost_setups=len(cases)*3,total_setups=setups,cost_calls=len(cases)*3*10*2*4,windows=len(cases)*3*10*2,warm_windows=len(cases)*3*3*2,measured_windows=len(cases)*3*7*2)
checks['exact_fixture_evidence']=cases==e['cost_cases'] and len(cases)==52 and sum(c['eligible'] for c in cases)==36 and sum(c['scalar']=='Rational{BigInt}' for c in cases)==2
checks['source_derived_counts']=ledger==dict(correctness_cases=160,correctness_calls_per_arm=162,direct_smoke_correctness_entries=488,correctness_smoke_setups=162,pfi_constructors=2,pfi_copies=2,cost_setups=156,total_setups=318,cost_calls=12480,windows=3120,warm_windows=936,measured_windows=2184)
u=(B/'MA-U/candidate.jl').read_text();old=(B/'MA-R/candidate.jl').read_text();tail=u[u.index('# UNEXECUTED.'):]
checks['candidate_guard_only_inverse']=tail.replace('return _dense_ma_rounding_matches()','return Base.MPFR.rounding_raw(BigFloat) == Base.MPFR.ROUNDING_MODE[]')==old and u!=old
checks['instrumented_identical']=(B/'MA-U/instrumented.jl').read_bytes()==(B/'MA-R/instrumented.jl').read_bytes()
inst=(B/'MA-U/instrumented.jl').read_text()
for direction in ('forward','transpose'):
 start=inst.index('function instrumented_'+direction+'!');end=inst.index('\nend',start)+4
 actual=inst[start:end].replace('instrumented_'+direction+'!','candidate_'+direction+'!').replace('    _route_entries[] += 1\n','').replace('    _route_scratches[] += 1\n','')
 actual=actual.replace('    if !_dense_ma_eligible(dest, backend, rhs)\n        _route_fallbacks[] += 1\n        return reference_'+direction+'!(dest, backend, rhs)\n    end','    _dense_ma_eligible(dest, backend, rhs) || return reference_'+direction+'!(dest, backend, rhs)')
 start=u.index('function candidate_'+direction+'!');end=u.index('\nend',start)+4
 checks['instrumented_'+direction+'_entry_inverse']=actual==u[start:end]
checks['twelve_product_sites']=u.count('_dense_ma_mul!(product,')==12
old_result=read(B/'MA-S-2/aggregate.json');new_result=read(B/'MA-V/aggregate.json')
checks['stored_old_rejected48of52']=old_result['accepted'] is False and len(old_result['cases'])==52 and sum(c['accepted'] for c in old_result['cases'])==48
checks['stored_guard_accepted12of12']=new_result['accepted'] is True and len(new_result['cases'])==12 and all(c['accepted'] for c in new_result['cases'])
paths=[Path(p) for p in e['sha256']]+[D/'evidence.json',D/'entry.py',D/'work-ledger.md',D/'STATUS.md.before-MA-W',D/'roadmap.md.before-MA-W',D/'review-check.py']
obj=dict(all_passed=all(v is True for v in checks.values()),checks=checks,ledger=ledger,host=dict(time=time.time(),boot_id=boot,groups=h['groups'],matches=matches),sha256={str(p):sha(p) for p in paths},scope='Independent newly authored read-only Python checks; no Julia, imports of old auditors or old script execution. All33 evidence hashes verified freshly, plus entry hashes, source514/protected6 and six current preserved continuation maps. Prior launch manifests and all prior raw measurements were not independently replayed. Computed checks establish bytes/counts/record fields, not manual numerical or plan acceptance.')
with (D/'review-check.json').open('x') as out:json.dump(obj,out,indent=2);out.write('\n')
print(json.dumps(dict(all_passed=obj['all_passed'],checks=checks,ledger=ledger,bindings=len(obj['sha256']))))
require(obj['all_passed'],'review checks failed')
