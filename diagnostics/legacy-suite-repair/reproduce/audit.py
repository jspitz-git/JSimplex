from pathlib import Path
import json,hashlib,re,subprocess,tomllib,shutil
root=Path(__file__).resolve().parents[3];raw=root/'.superpowers/legacy-suite-repair';out=root/'diagnostics/legacy-suite-repair/results';out.mkdir(exist_ok=True)
expected={'probe':0,'red':1,'green':0,'adjacent':0,'mutation-sum':1,'mutation-snap':1,'probe-final':0,'compiled':0}
summaries={};pins={}
for name,exitcode in expected.items():
 d=raw/name;p=json.loads((d/'process.json').read_text());assert p['returncode']==exitcode and p['sources_unchanged']
 log=(d/'run.log').read_text();failed=log.count('Test Failed at');errors=log.count('Error During Test at')
 assert failed=={'red':25,'mutation-sum':64,'mutation-snap':29}.get(name,0)
 assert errors==(2 if name=='red' else 0)
 for f in ('run.log','process.json'):shutil.copyfile(d/f,out/f'{name}-{f}')
 identities=json.loads((d/'preflight.json').read_text());src={str(Path(k).relative_to(root)):v for k,v in identities.items() if k.startswith(str(root/'src')+'/')}
 assert src
 for path,digest in src.items():
  assert hashlib.sha256(subprocess.check_output(['git','show','6bf7d2f:'+path],cwd=root)).hexdigest()==digest
  assert hashlib.sha256((root/path).read_bytes()).hexdigest()==digest
 summaries[name]={'exitcode':exitcode,'failed_assertions':failed,'test_errors':errors,'sources_unchanged':True}
 pins[name]={'preflight_sha256':hashlib.sha256((d/'preflight.json').read_bytes()).hexdigest(),'source_sha256':src}
for name,count in [('green',520),('compiled',520),('adjacent',2262)]:
 log=(raw/name/'run.log').read_text();assert re.search(r'\|\s+'+str(count)+r'\s+'+str(count)+r'\s+',log)
probe=lambda n:tomllib.loads((raw/n/'run.log').read_text().split('\tCommand being timed:')[0])
a,b=probe('probe'),probe('probe-final');assert a==b
for case in b['cases']:
 assert case['original_feasible']
 if case['kind']=='structural':
  assert case['row_residual']==0
  if not case['fixed']:assert case['primal_before']==case['primal_after'] and case['status']=='CONTINUE'
  elif case['count'] in (0,2):assert case['status']=='NUMERICAL_ERROR' and case['primal_before']==case['primal_after'] and case['basis_before']==case['basis_after']
 else:assert case['calls']==5 and case['events']['refactor_pivot']==1 and case['events']['correction']==1
(out/'audit.json').write_text(json.dumps({'production_unchanged_from':'6bf7d2f','checks':summaries,'probe_reproduced':True,'focused_passes':520,'adjacent_passes':2262},indent=2)+'\n')
(out/'provenance.json').write_text(json.dumps(pins,indent=2)+'\n');print(json.dumps(summaries,indent=2))
