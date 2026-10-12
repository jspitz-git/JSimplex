import sys
from pathlib import Path
s=Path(sys.argv[1]).read_text()
checks={"destination invalidation oracle": "invalidations==5" in s,"whole-remove kernel oracle": "full-remove kernels FTRAN==6/BTRAN==4/refactorization==2" in s,"setup exclusion": "excluding fixture setup and post-call checks" in s}
for name,ok in checks.items():print(name,ok)
assert all(checks.values()),checks
