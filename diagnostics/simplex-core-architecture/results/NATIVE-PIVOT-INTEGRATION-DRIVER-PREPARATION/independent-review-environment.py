from pathlib import Path
import os,json
D=Path(__file__).resolve().parent
expected=json.loads((D/'environment.json').read_text())
differences={k:dict(expected=v,observed=os.environ.get(k)) for k,v in expected.items() if os.environ.get(k)!=v}
with (D/'independent-review-environment.json').open('x') as f:json.dump(dict(differences=differences,scope='Read-only reviewer process environment; unchanged saved environment'),f,indent=2);f.write('\n')
print(json.dumps(differences,indent=2))
