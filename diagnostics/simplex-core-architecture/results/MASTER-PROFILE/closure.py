from pathlib import Path
import json,hashlib,subprocess,time
D=Path(__file__).resolve().parent;R=D.parents[3]
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def save(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2);f.write('\n')
def git(*args):return subprocess.check_output(['git',*args],cwd=R)
def bound(x):return bool(x) and all(sha(p)==v for p,v in x.items())
def main():
 old=read(D/'host.json');post=read(D/'postcheck.json');review=read(D/'result-review.json');admit=read(D/'admission-review.json');pins=read(D/'pins.json');mapping=read(D/'continuation-map.json');names=read(D/'publication-names.json')
 checks={'result_accepted':review['accepted'] is True and review['findings']==[], 'result_bindings':bound(review['sha256']),'postcheck_PASS':post['all_passed'] is True and bound(post['sha256']),'admission':admit['accepted'] is True and admit['findings']==[] and bound(admit['sha256']),'pins_current':all(sha(p)==v['sha256'] and str(Path(p).resolve())==v['resolved'] for p,v in pins['inventory'].items()),'source_membership':set(pins['inventory'])==set(pins['files'])|{str(p) for root in pins['trees'] for p in Path(root).rglob('*') if p.is_file()},'master_unchanged':git('rev-parse','master').decode().strip()==old['refs']['master'],'head_unchanged':git('rev-parse','HEAD').decode().strip()==old['refs']['head'],'remote_unchanged':git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture').decode().strip()==old['refs']['remote'],'master_source514':all(sha(R/p)==v and git('show','master:'+p)==(R/p).read_bytes() for p,v in old['master_identity'].items()),'protected':bound(old['protected']),'six_old_bindings':len(mapping['old_bindings'])==6 and all(sha(x['preserved'])==x['sha256']==read(x['source'])['sha256'][x['path']] for x in mapping['old_bindings']),'index_empty':git('diff','--cached','--name-only')==b'','authored_diff_clean':subprocess.run(['git','diff','--check'],cwd=R,capture_output=True).returncode==0}
 for i in (1,2,3):
  a=read(D/f'audit-{i}.json');checks[f'audit{i}_PASS']=a['all_passed'] is True and bound(a['sha256'])
 groups=read(D/'posthost-3.json')['groups'];matches=[];boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 for p in Path('/proc').glob('[0-9]*'):
  try:
   s=(p/'stat').read_text();f=s[s.rfind(')')+2:].split()
   if int(f[2]) in groups or int(f[3]) in groups or (p/'comm').read_text().strip().lower().startswith('julia'):matches.append(dict(pid=p.name,pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
  except FileNotFoundError:pass
 checks['all158groups_ANDsessions_noJulia']=len(groups)==158 and not matches
 actual={str(p.relative_to(R)) for p in D.rglob('*') if p.is_file()}|{'diagnostics/simplex-core-architecture/CURRENT-MASTER-TIME-BREAKDOWN.md','diagnostics/simplex-core-architecture/STATUS.md','docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'}
 checks['exact_names']=set(names)==actual|{str((D/'closure.json').relative_to(R)),str((D/'publication.json').relative_to(R))}
 result=dict(all_passed=all(checks.values()),checks=checks,host=dict(boot_id=boot,groups=groups,matches=matches,time=time.time()),sha256={str(R/p):sha(R/p) for p in sorted(actual)})
 save(D/'closure.json',result)
 if not result['all_passed']:raise ValueError(checks)
 print('closure PASS',len(checks),'bindings',len(result['sha256']))
if __name__=='__main__':main()
