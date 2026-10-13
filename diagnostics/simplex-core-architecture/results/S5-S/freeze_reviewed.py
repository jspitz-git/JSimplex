from common_reviewed import *
# Original required796 and admission797 stay immutable.
old=read(H/'required-paths.json')['sha256'];assert all(sha(p)==v for p,v in old.items())
files=set(map(Path,old))|set(essentials())|{p for p in H.iterdir() if p.is_file()}|{p for p in (H/'synthetic-refusal').iterdir() if p.is_file()}
files.discard(H/'required-reviewed-paths.json')
dump(H/'required-reviewed-paths.json',dict(sha256={str(p):sha(p) for p in sorted(files)},scope='Complete selected required paths, preserving original rejected admission.'))
print('reviewed required',len(files))
