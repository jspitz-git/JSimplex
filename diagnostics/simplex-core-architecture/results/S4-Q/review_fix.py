from pathlib import Path
import json,hashlib,tomllib
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture';E=D/'results/S4-Q';p=D/'S4-HISTORY-LIFECYCLE-COST-MEASUREMENT.md';s=p.read_text();old='''Q inputs.toml binds
all19,138 stored coefficient/RHS/incoming/knownsolution values without regeneration
or old-script reruns.''';new='''Pinned P JSON binds all19,138 stored coefficient/RHS/incoming/known-solution values.
Q inputs.toml preserves the19,042 matrix/RHS/incoming values; the96 known-solution
values remain in pinned P JSON. No input regeneration or old-script rerun occurred.''';assert old in s
with (E/'report-before-input-wording.md').open('x') as f:f.write(s)
t=tomllib.loads((E/'inputs.toml').read_text());count=sum(sum(len(v) for k,v in table.items() if k.endswith('_bits') or k=='bits') for table in t.values());assert count==19042
red={'Q_TOML_has19138_values':count==19138,'Q_TOML_has_knownsolution_keys':any('zF_bits' in v or 'zB_bits' in v for v in t.values())};assert not any(red.values())
p.write_text(s.replace(old,new,1));green={'TOML19042_plus_P96_equals19138':count+96==19138,'report_distinguishes_two_files':'Q inputs.toml preserves the19,042' in p.read_text(),'P_input_frozen':hashlib.sha256((D/'results/S4-P/exact-inputs.json').read_bytes()).hexdigest()=='85874a35de281a9de4ce4d49c7f17f176d37a1597fc557ae64469202fcfd9b06'}
with (E/'review-fix.json').open('x') as f:json.dump(dict(red=red,green=green,all_passed=all(green.values()),scope='One offline wording correction; reviewer Minor treated as Important for exact file binding. No runtime/pin/raw/auditor alteration or rerun'),f,indent=2);f.write('\n')
print(red,green);assert all(green.values())
