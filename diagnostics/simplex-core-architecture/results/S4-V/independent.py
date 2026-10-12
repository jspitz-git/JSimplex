from pathlib import Path
import hashlib,json,gzip,subprocess
D=Path(__file__).resolve().parent
R=D.parents[3]
def h(p):
 v=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1048576),b''):v.update(b)
 return v.hexdigest()
a=json.loads((D/'read-only-audit.json').read_text());m=json.loads((D/'host-metadata.json').read_text());docs=json.loads((D/'installed-documents.json').read_text())
checks={
 'full656_current_hashes':len(a['sha256'])==656 and all(h(p)==v for p,v in a['sha256'].items()),
 'all17_evaluated_checks':len(a['checks'])==17 and all(v is True for v in a['checks'].values()) and a['all_passed'],
 'saved_documents_exact':all((gzip.open(p,'rt').read() if p.endswith('.gz') else Path(p).read_text())==v for p,v in docs.items()),
 'decision_not_impossibility':a['bootstrap_qualified'] is False and a['host_capability_impossible'] is False and a['numerical_authorization'] is False,
 'kernel_six_namespace_options':all('CONFIG_'+k+'=y' in (D/'kernel-config.txt').read_text().splitlines() for k in ['NAMESPACES','USER_NS','PID_NS','NET_NS','IPC_NS','UTS_NS']),
 'bwrap_metadata_current':Path('/usr/bin/bwrap').stat().st_mode==int(m['/usr/bin/bwrap']['mode'],8) and Path('/usr/bin/bwrap').stat().st_mtime_ns==m['/usr/bin/bwrap']['mtime_ns'],
 'U_failed_closure_and_passed_supplement':json.loads((D.parent/'S4-U/closure.json').read_text())['all_passed'] is False and json.loads((D.parent/'S4-U/closure-supplement.json').read_text())['all_passed'] is True,
 'src_test_CI_unchanged':subprocess.check_output(['git','diff','master','--','src','test','.github'],cwd=R,text=True)=='',
}
with (D/'independent.json').open('x') as f:json.dump({'checks':checks,'all_passed':all(checks.values()),'snapshot_sha256':{str(p):h(p) for p in sorted(D.iterdir()) if p.is_file() and p.name!='independent.json'}},f,indent=2);f.write('\n')
print(json.dumps({'checks':len(checks),'all_passed':all(checks.values())}));assert all(checks.values())
