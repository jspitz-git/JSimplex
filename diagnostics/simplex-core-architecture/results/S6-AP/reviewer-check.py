"""Fresh exclusive offline reviewer evidence check. Never imports repository code."""
from pathlib import Path
import hashlib,json,subprocess
R=Path.cwd(); H=R/'diagnostics/simplex-core-architecture/results/S6-AP'
cache={}; sizes={}; failures=[]; manifests={}
def sha(p):
    p=Path(p); key=str(p)
    if key not in cache:
        h=hashlib.sha256(); total=0
        with p.open('rb') as f:
            for chunk in iter(lambda:f.read(1048576), b''):
                h.update(chunk); total+=len(chunk)
        cache[key]=h.hexdigest(); sizes[key]=total
    return cache[key]
for name, count in [('entry.json',1947),('provenance.json',21),('independent.json',1970),('independent-supplement.json',4)]:
    p=H/name; sha(p); d=json.loads(p.read_text()); bad=[]
    for path, expected in d['sha256'].items():
        try:
            actual=sha(path)
            if actual!=expected:bad.append(dict(path=path,expected=expected,actual=actual))
        except OSError as e:bad.append(dict(path=path,error=str(e)))
    manifests[name]=dict(expected_count=count,count=len(d['sha256']),matched=len(d['sha256'])-len(bad),all_matched=not bad and len(d['sha256'])==count,checks=d['checks'],all_passed=d['all_passed'])
    failures.extend(bad)
entry=json.loads((H/'entry.json').read_text()); prov=json.loads((H/'provenance.json').read_text()); author=json.loads((H/'independent.json').read_text()); supplement=json.loads((H/'independent-supplement.json').read_text())
raw=(H/'user-failure.log').read_bytes(); lines=raw.decode('utf-8-sig').splitlines()
report=R/'diagnostics/simplex-core-architecture/S6-TEST-MPS-FAILURE-PROVENANCE.md'
plan=R/'docs/superpowers/plans/2026-10-13-test-mps-original-run-linkage.md'
ptext=' '.join(plan.read_text().split())
before=json.loads((H/'before-texts.json').read_text())
preserved=all(sha(m['preserved'])==m['sha256'] for m in before['mappings'])
s0=json.loads((R/'diagnostics/simplex-core-architecture/results/S0/preflight.json').read_text())
model=next(v for v in s0['inputs'] if v['id']=='test')
f11=json.loads((R/'diagnostics/simplex-modernization/F11-results.json').read_text()); records=[]
def walk(v):
    if isinstance(v,dict):
        if v.get('path')==model['resolved']: records.append(v)
        for x in v.values():walk(x)
    elif isinstance(v,list):
        for x in v:walk(x)
walk(f11)
def git(*args):return subprocess.check_output(['git',*args],text=True).strip()
refs=dict(head=git('rev-parse','HEAD'),master=git('rev-parse','master'))
tracked=git('diff','HEAD','--name-only')
checks={
 'all_named_manifest_bindings_match':all(v['all_matched'] for v in manifests.values()),
 'entry_15_and_provenance_17_pass_preserved':len(entry['checks'])==15 and entry['all_passed'] is True and all(entry['checks'].values()) and len(prov['checks'])==17 and prov['all_passed'] is True and all(prov['checks'].values()),
 'author_three_pass_one_false_preserved':len(author['checks'])==4 and author['all_passed'] is False and author['checks']['no_new_execution_admission'] is False and sum(v is True for v in author['checks'].values())==3,
 'supplement_four_pass_actual_plan_unchanged':len(supplement['checks'])==4 and supplement['all_passed'] is True and all(supplement['checks'].values()) and 'SOURCE/EVIDENCE ONLY: no Julia/query/parser/import/compile/native/numerical call' in ptext and 'old script/auditor rerun or new numerical allowance.' in ptext,
 'continuation_snapshots_preserved':preserved,
 'log_raw_identity_size_lines':sha(H/'user-failure.log')=='22da06e3955a94ffa25fc1f0a0630e933c124aa4a137a25e159b57877030e115' and len(raw)==88807 and len(lines)==817,
 'log_exact_events':lines[805]==prov['original_log_lines']['806'] and lines[813]==prov['original_log_lines']['814'] and lines[814]==prov['original_log_lines']['815'],
 'historical_metadata_only_match':len(records)==2 and all((v['rows'],v['columns'],v['nonzeros'],v['decompressed_sha256'])==(614038,526231,1714776,model['sha256']) for v in records) and sha(model['resolved'])==model['sha256'],
 'no_named_input_in_log':'test.mps' not in raw.decode() and 'runtime.mps' not in raw.decode(),
 'current_script_runtime': 'filename = "runtime.mps"' in (H/'windows-test_new.jl.txt').read_text(),
 'conditional_future_only':'Continue only when genuinely new original-run evidence or user clarification is available.' in ptext and 'do not repeat searches' in ptext and 'A later reproduction requires its own reviewed concrete plan and allowance' in ptext,
 'expected_local_refs':refs==dict(head='393067527dc04eb817c6af75347770b69a1905ee',master='d02416c108f06fcd41d58e0a1980b70a51fef9ef'),
 'no_tracked_changes':tracked==''
}
for p in [report,plan,H/'before-texts.json',H/'STATUS.md.before-AP',H/'2026-10-11-simplex-core-architecture.md.before-AP',Path(__file__).resolve()]:sha(p)
out=dict(scope='SOURCE/EVIDENCE ONLY; no existing script import/execution, Julia, MPS/model parse, compiler, native or numerical call. Named historical pins establish present byte preservation, not historical execution or revalidation of old assertions.',checks=checks,all_passed=all(checks.values()),manifests=manifests,failures=failures,refs=refs,tracked_changes=tracked,hash_buffer_bytes=1048576,physical_files_hashed=len(cache),physical_bytes_hashed=sum(sizes.values()),sha256=cache,review_lookup_note='One read-only rg selector included nonexistent src/certificates.jl; rg reported the missing file, then source discovery identified src/native_certificate_recovery.jl. No script/test or numerical operation failed or ran.')
with (H/'reviewer-check.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in out.items() if k not in ['sha256','manifests']}))
print(json.dumps(manifests))
