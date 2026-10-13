from common_final import *
old=read(H/'required-reviewed-paths.json')['sha256'];assert all(sha(p)==v for p,v in old.items())
files=set(map(Path,old))|set(essentials())|{p for p in H.rglob('*') if p.is_file()}
files.discard(H/'required-final-paths.json')
dump(H/'required-final-paths.json',dict(sha256={str(p):sha(p) for p in sorted(files)},scope='Complete selected requirements after two preserved offline admission amendments.'))
print('final required',len(files))
