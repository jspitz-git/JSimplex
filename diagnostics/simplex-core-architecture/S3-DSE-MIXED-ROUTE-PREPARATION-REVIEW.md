# S3-D independent numerical and work review

Reviewer: fresh gpt-6-astra agent /root/s3d_preparation_review, 2026-10-13.
Disposition: ACCEPTED FOR OFFLINE PREPARATION ONLY. No Critical, Important, or Minor findings.

Independent read-only verification confirmed HEAD adcb1fd8fb040bed63875bfea10142c0de52bfd6
and master 0eb75c3190096946b0e91e5360230ccd7166f298, all 69 current pins,
all 1,168 frozen rational/binary64 entries, reconstructed A/B0/B1/B2, six exact
equations, squared norm, and all 32 source-ordered output weight bits. Both
leaving-row and zero-coefficient-row floor effects are correct. All three clones
match the manifest and invert byte-exactly to current source; only private
renaming and one mode keyword are introduced.

Source supports the conditional ten constructors, twenty updates, sixty outer
solves (40 F/20 B), separately four HH internal unit operations and at most ten
nested orientation solves. These are neither observed counts nor 74 equivalent
backend entries. Partial workspace initialization, unchanged native refinement
default, inner sparse fallback, HH dense controls, and absence of public
trajectory/certification claims are accurately described.

No unnecessary production computation, allocation, or retained memory was
introduced: production/test/CI diff is empty. Planned diagnostic copies and
O(m + history payload) ownership are disclosed; no benchmark or speedup claim
is warranted.

The unimplemented pre-forward internal-attempt observation is honestly stated
and acceptable for preparation only. The S3-E plan requires one bounded driver/
counter review, rejects method overwrite/full-module cloning, and stops this
qualification route if complete accounting cannot be achieved. It provides no
numerical launch authorization.

The reviewer performed independent hash and exact offline checks. No Julia,
import, compilation, native execution, old driver, exclusive script, or numerical
rerun was performed. This review is separate from the author's independent.json.
