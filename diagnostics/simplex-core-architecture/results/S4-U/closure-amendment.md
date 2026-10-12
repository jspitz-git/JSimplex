# S4-U closure failure and separate correction

Original closure.py/json remains frozen:8/9 checks, review_accepted=false, all_passed=false,
exit1. The unchanged review has a newline after 'Critical,'; a literal substring check
incorrectly failed. The combined shell did not use fail-fast and continued to commit/push
 ae874717df9b2d217ea8a138f6624a69184e4b6c despite that failure. This publication-order error
is recorded explicitly, not rewritten as a passing original closure.

NEW closure_supplement.py/json has7/7 checks. It confirms the exact newline cause, normalizes
whitespace only for the acceptance predicate, verifies unchanged original review/hash,
all original closure-bound hashes and all627 pins, and unchanged production/master. It
was run once with fail-fast; no original script, Julia, numerical work or cost was rerun.

The report and independent review are unchanged. STATUS/roadmap before the explanatory
amendment are preserved and mapped in closure-amendment-provenance.json. The original
closure hashes bind those prior texts; the correction does not retroactively alter them.
Bootstrap/controller qualification remains OPEN and no launch is authorized. Subsequent
publication must stop on any failing audit before staging/commit/push.
