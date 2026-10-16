"""Publish exact reviewed admission only after a fresh complete seal/host recheck."""
from pathlib import Path
import importlib.util,json
E=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('new_independent_admission_check',E/'master300-admission-check.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
s=c.rd(c.SP);checks=c.rd(E/'master300-admission-checks.json')
assert checks['all_passed'] is True and checks['check_count']==14687
assert c.sha(c.SP)==checks['pins_sha256']=='4185d72879d51a99f052a496f7bdc967e868962a0fcf4d56f9d896d952d5692f'
assert set(s['files'])==set(s['inventory'])
for n,v in s['inventory'].items():assert {'resolved':str(Path(n).resolve(strict=True)),'sha256':c.sha(n)}==v,n
for root in s['trees']:
 assert not Path(root).is_symlink()
 for p in Path(root).rglob('*'):
  assert not(p.is_symlink() and (p.is_dir() or not p.exists()))
  if p.is_file():assert str(p) in s['inventory']
assert c.git('rev-parse','HEAD',cwd=c.W)==c.git('rev-parse','HEAD',cwd=c.M)==c.COMMIT
assert c.git('ls-remote','origin','refs/heads/master')==c.BASE+'\trefs/heads/master'
assert {k:c.os.environ.get(k) for k in c.rd(c.D/'environment.json')}==c.rd(c.D/'environment.json')
fresh=c.host(s['groups'])
assert not fresh['matches'] and len(fresh['groups'])==220
assert all(fresh[k]==s[k] for k in ['head','master','boot_id'])
assert fresh['memory']['available_kib']>=6*1024**2 and fresh['memory']['swap_used_kib']<=1024**2
assert set(p.name for p in c.RUN.iterdir())=={'sealed.json','config.json','host.json'}
c.save(E/'master300-admission-final-host.json',fresh)
evidence=[E/'master300-admission-check.py',E/'master300-admission-checks.json',E/'master300-admission-host.json',E/'master300-admission-final-host.json',E/'master300-admission.md',Path(__file__),E/'integration.json']
a=dict(accepted=True,findings=[],scope='actual-master exact-stage admission',phase='master300',pins_sha256=c.sha(c.SP),sha256={**{n:v['sha256'] for n,v in s['inventory'].items()},str(c.SP):c.sha(c.SP)},evidence_sha256={str(p):c.sha(p) for p in evidence},production_commit=c.COMMIT,diagnostic_head=c.HEAD,limitations=['No numerical execution or result yet','Only master300 admitted; any master600 requires separately reviewed pure-timeout result and exact-stage admission','Prior cost evidence reused without a universal speedup claim','Inaccessible system exe links and pinned-runtime loader/cache coverage remain stated limits'])
assert set(a['sha256'])==set(s['files'])|{str(c.SP)}
c.save(c.RUN/'admission.json',a)
print(json.dumps(dict(accepted=True,scope=a['scope'],phase=a['phase'],sha256_entries=len(a['sha256']),pins_sha256=a['pins_sha256'],admission_sha256=c.sha(c.RUN/'admission.json'),fresh_memory=fresh['memory'],no_julia=True,historical_groups_and_sessions=220)))
