"""Exclusive final S2-E closure, run only after review and continuation."""
from pathlib import Path
import json,hashlib,subprocess
R=Path.cwd();E=R/'diagnostics/simplex-core-architecture/results/S2-E';D=E.parent/'S2-D';C=E.parent/'S2-C';base='36b718e9e30102807a22522efdef5a37b1f42a2c';master='d02416c108f06fcd41d58e0a1980b70a51fef9ef'
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def git(*args):return subprocess.check_output(['git',*args],text=True).strip()
mapper={str(R/'diagnostics/simplex-core-architecture/STATUS.md'):E/'STATUS.md.before-S2-E',str(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'):E/'roadmap.md.before-S2-E'}
def bindings(o,m=mapper):
 def mapped(p):
  absolute=str(Path(p) if Path(p).is_absolute() else R/p)
  return m.get(absolute,Path(absolute))
 return all(sha(mapped(p))==h for p,h in o['sha256'].items())
pins=read(D/'launch-pins.json');review=read(E/'result-review-check.json');audit=read(D/'audit.json');post=read(E/'postcheck.json');supp=read(E/'postcheck-supplement.json');pub=read(D/'publication.json')
expected=pub['expected_staged_names'];newD={'launch-pins.json','allowance.json','numerical-review.md','attempt-reserved.json','invocation.json','launcher.log','audit.json'}
allD={str(p.relative_to(R)) for p in D.rglob('*') if p.is_file()};oldD={p for p in expected if p.startswith(str(D.relative_to(R))+'/')}
checks={
 'sole_admitted_attempt':read(D/'allowance.json')['attempts']==1 and read(D/'invocation.json')['returncode']==0 and read(E/'qualification-1/process.json')['reason']=='exit0',
 'audit21_pass':audit['all_passed'] is True and len(audit['checks'])==21 and all(audit['checks'].values()),
 'full826_with_explicit_continuation_map':len(pins['inventory'])==826 and all(sha(mapper.get(p,p))==v['sha256'] and str(Path(p).resolve(strict=True))==v['resolved'] for p,v in pins['inventory'].items()),
 'full801_and780_unchanged':all(all(sha(p)==v['sha256'] for p,v in read(D/n)['inventory'].items()) for n in ['admission-pins-reviewed.json','admission-pins.json']),
 'admission35_830_bindings':len(read(E/'admission-review-check.json')['checks'])==35 and len(read(E/'admission-review-check.json')['sha256'])==830 and bindings(read(E/'admission-review-check.json')),
 'sealed_allowance_hashes':bindings(read(D/'allowance.json')),
 'seal8_bindings':read(E/'seal-review.json')['accepted'] is True and len(read(E/'seal-review.json')['checks'])==8 and bindings(read(E/'seal-review.json')),
 'entry16_bindings':read(E/'entry.json')['all_passed'] is True and len(read(E/'entry.json')['checks'])==16 and bindings(read(E/'entry.json')),
 'Dclosure24_127':read(D/'closure.json')['all_passed'] is True and len(read(D/'closure.json')['sha256'])==127 and bindings(read(D/'closure.json')),
 'Dpublication6_128':pub['all_passed'] is True and len(pub['sha256'])==128 and bindings(pub),
 'all129_committed_original_blobs':len(expected)==129 and all(subprocess.check_output(['git','show',base+':'+p])==Path(mapper.get(str(R/p),R/p)).read_bytes() for p in expected),
 'only_seven_new_D_paths':allD==oldD|{str((D/n).relative_to(R)) for n in newD},
 'original_postcheck_false12of14_preserved':post['all_passed'] is False and sum(post['checks'].values())==12 and len(post['checks'])==14,
 'separate_supplement6_pass':supp['all_passed'] is True and len(supp['checks'])==6 and all(supp['checks'].values()) and bindings(supp),
 'all15_original_portable':len(post['raw_pairs'])==15 and all(sha(p)==v['sha256']==sha(v['portable'])==v['portable_sha256'] for p,v in post['raw_pairs'].items()),
 'audit_raw15_invocation3':len(audit['raw_sha256'])==15 and len(audit['invocation_sha256'])==3 and all(sha(p)==h for key in ['raw_sha256','invocation_sha256'] for p,h in audit[key].items()),
 'final_independent_result_accepted':review['accepted'] is True and review['all_passed'] is True and review['unresolved_findings']==[] and all(review['checks'].values()),
 'final_review_bindings':bindings(review),
 'fresh_host5_and28_groups_sessions_noJulia':read(E/'pre-continuation-host.json')['all_passed'] is True and len(read(E/'pre-continuation-host.json')['groups'])==28 and not read(E/'pre-continuation-host.json')['matches'],
 'HEAD_master_unchanged':git('rev-parse','HEAD')==base and git('rev-parse','master')==master,
 'actual_source_test_env_CI_unchanged':not git('diff','--name-only','master','--','src','test','.github','Project.toml'),
 'only_two_tracked_continuation_edits':set(git('diff','--name-only').splitlines())=={str(Path(p).relative_to(R)) for p in mapper},
 'index_empty':not git('diff','--cached','--name-only'),
 'no_python_bytecache':not list(D.rglob('__pycache__')) and not list(E.rglob('__pycache__')),
}
reports=[R/'diagnostics/simplex-core-architecture'/n for n in ['S2-PRICE-AUDIT-VALUES-QUALIFICATION.md','S2-PRICE-AUDIT-VALUES-QUALIFICATION-REVIEW.md']]
paths=sorted({p for p in E.rglob('*') if p.is_file()}|{D/n for n in newD}|{Path(p) for p in mapper}|set(reports))
o={'checks':checks,'all_passed':all(checks.values()),'sha256':{str(p):sha(p) for p in paths},'continuation_mapping':{p:str(v) for p,v in mapper.items()},'scope':'S2-E completed one qualification; mixed cost, no promotion; allowance consumed; all old scripts/raw frozen'}
with (E/'closure-final.json').open('x') as f:json.dump(o,f,indent=2);f.write('\n')
print(json.dumps({'checks':checks,'bindings':len(paths)}))
if not o['all_passed']:raise SystemExit(1)
