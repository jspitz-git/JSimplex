"""Exclusive second offline correction: bind original/portable GREEN evidence."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'common_reviewed.py').read_text().replace('common_reviewed.py','common_final.py').replace('launcher-reviewed.py','launcher-final.py').replace('audit-reviewed.py','audit-final.py').replace('required-reviewed-paths.json','required-final-paths.json').replace('admission-acceptance-reviewed.json','admission-acceptance-final.json').replace('admission-reviewed-pins.json','admission-final-pins.json').replace('admission-accepted-review.md','admission-final-review.md')
s=s.replace("H/'reviewed-failure-tests.json']","H/'reviewed-failure-tests.json',H/'review_fix_2.py',H/'final_failure_tests.py',H/'final-failure-tests.json']")
s=s.replace("if stage=='master':req[str(M/REL)]=EXPECTED","if stage=='master':\n   req[str(M/REL)]=EXPECTED;req.update(green_evidence())")
start=s.index('def stage_accepted(stage):');end=s.index('def launch_accepted(stage):',start)
s=s[:start]+'''GREEN_RAW={'process.json','pins.json','current.json','run.log','resources.jsonl','raw/case.toml','raw/report.toml','raw/executed-suffix.jl'}
def green_evidence(hashfn=sha,readfn=read,textfn=lambda p:Path(p).read_text()):
 h=H/'green';audit=readfn(h/'audit.json');post=readfn(h/'postcheck.json');review=textfn(h/'review.md')
 assert audit['all_passed'] is True and audit['checks'] and all(v is True for v in audit['checks'].values())
 assert post['all_passed'] is True and post['checks'] and all(v is True for v in post['checks'].values())
 assert {str(h/n) for n in ('audit.json','pins.json')}.issubset(post['sha256']) and all(hashfn(k)==v for k,v in post['sha256'].items())
 assert 'ACCEPTED' in review and 'Unresolved findings: []' in review
 assert set(audit['raw_sha256'])==GREEN_RAW
 invpaths={str(h/n) for n in ('guard-invocation.json','guard-output.log','attempt-reserved.json')}
 assert set(audit['invocation_sha256'])==invpaths
 files={str(h/n):hashfn(h/n) for n in ('audit.json','postcheck.json','review.md','pins.json')}
 for name,digest in audit['raw_sha256'].items():
  for p in (out('green')/name,h/'portable'/name):
   assert hashfn(p)==digest;files[str(p)]=digest
 for p,digest in audit['invocation_sha256'].items():
  assert hashfn(p)==digest;files[p]=digest
 assert files[str(out('green')/'pins.json')]==files[str(h/'pins.json')]
 return files
def stage_accepted(stage):
 a=read(stage_files(stage)/'stage-acceptance.json');assert stage_record_valid(a,stage)
 if stage=='master':
  evidence=green_evidence();assert set(evidence).issubset(a['sha256']) and all(a['sha256'][k]==v for k,v in evidence.items())
 return a
''' + s[end:]
with (H/'common_final.py').open('x') as f:f.write(s)
for old,new in [('launcher-reviewed.py','launcher-final.py'),('audit-reviewed.py','audit-final.py')]:
 s=(H/old).read_text().replace('from common_reviewed import *','from common_final import *').replace('required-reviewed-paths.json','required-final-paths.json').replace('admission-reviewed-pins.json','admission-final-pins.json').replace('admission-accepted-review.md','admission-final-review.md').replace('admission-acceptance-reviewed.json','admission-acceptance-final.json')
 with (H/new).open('x') as f:f.write(s)
print('Separate final source created; original and first-correction sources preserved')
